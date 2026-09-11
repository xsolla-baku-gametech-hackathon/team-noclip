// Consolidated device-pairing routes (see api/auth/[...action].js for why).
// URLs unchanged:
//   POST /api/device/start
//   POST /api/device/approve
//   GET  /api/device/poll?code=...
import { ensureSchema, requireDb, DbNotConfigured } from '../_lib/db.js';
import { getAuthedUserId, generateDeviceToken, hashDeviceToken, generatePairingCode } from '../_lib/auth.js';

const EXPIRES_MINUTES = 10;

async function handleStart(req, res) {
  await ensureSchema();
  const db = requireDb();

  let code;
  for (let attempt = 0; attempt < 5; attempt++) {
    code = generatePairingCode();
    const existing = await db`SELECT 1 FROM device_logins WHERE code = ${code}`;
    if (existing.length === 0) break;
  }

  const expiresAt = new Date(Date.now() + EXPIRES_MINUTES * 60 * 1000).toISOString();
  await db`INSERT INTO device_logins (code, status, expires_at) VALUES (${code}, 'pending', ${expiresAt})`;

  res.status(200).json({ code, expires_in_seconds: EXPIRES_MINUTES * 60 });
}

async function handleApprove(req, res) {
  const userId = await getAuthedUserId(req);
  if (!userId) {
    res.status(401).json({ error: 'Not signed in.' });
    return;
  }

  const { code } = req.body || {};
  if (!code) {
    res.status(400).json({ error: 'Missing code.' });
    return;
  }

  await ensureSchema();
  const db = requireDb();

  const rows = await db`SELECT code, status, expires_at FROM device_logins WHERE code = ${code.toUpperCase()}`;
  if (rows.length === 0) {
    res.status(404).json({ error: 'Invalid pairing code.' });
    return;
  }
  const login = rows[0];
  if (login.status !== 'pending') {
    res.status(409).json({ error: 'This code was already used.' });
    return;
  }
  if (new Date(login.expires_at).getTime() < Date.now()) {
    res.status(410).json({ error: 'This code has expired. Restart login from the app.' });
    return;
  }

  const deviceToken = generateDeviceToken();
  await db`
    UPDATE device_logins SET status = 'approved', device_token = ${deviceToken}, user_id = ${userId}
    WHERE code = ${login.code}
  `;
  await db`INSERT INTO device_tokens (token_hash, user_id) VALUES (${hashDeviceToken(deviceToken)}, ${userId})`;

  res.status(200).json({ ok: true });
}

async function handlePoll(req, res) {
  const code = String(req.query.code || '').toUpperCase();
  if (!code) {
    res.status(400).json({ error: 'Missing code.' });
    return;
  }

  await ensureSchema();
  const db = requireDb();

  const rows = await db`SELECT status, device_token, expires_at FROM device_logins WHERE code = ${code}`;
  if (rows.length === 0) {
    res.status(404).json({ error: 'Invalid pairing code.' });
    return;
  }
  const login = rows[0];

  if (login.status === 'approved' && login.device_token) {
    const token = login.device_token;
    await db`UPDATE device_logins SET status = 'consumed', device_token = NULL WHERE code = ${code}`;
    res.status(200).json({ status: 'approved', device_token: token });
    return;
  }

  if (new Date(login.expires_at).getTime() < Date.now()) {
    res.status(200).json({ status: 'expired' });
    return;
  }

  res.status(200).json({ status: login.status });
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }

  const action = Array.isArray(req.query.action) ? req.query.action[0] : req.query.action;

  try {
    if (action === 'start' && req.method === 'POST') return await handleStart(req, res);
    if (action === 'approve' && req.method === 'POST') return await handleApprove(req, res);
    if (action === 'poll' && req.method === 'GET') return await handlePoll(req, res);

    res.status(404).json({ error: 'Not found.' });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}
