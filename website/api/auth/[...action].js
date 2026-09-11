// Consolidated auth routes — Vercel's Hobby plan caps a deployment at 12
// serverless functions, so every /api/auth/* endpoint is dispatched from
// this one file instead of one file per route. URLs are unchanged:
//   POST /api/auth/login
//   POST /api/auth/signup
//   POST /api/auth/logout
//   POST /api/auth/session
//   POST /api/auth/device-token
import { ensureSchema, requireDb, DbNotConfigured } from '../_lib/db.js';
import {
  createSessionToken,
  setSessionCookie,
  clearSessionCookie,
  hashPassword,
  verifyPassword,
  getAuthedUserId,
  generateDeviceToken,
  hashDeviceToken,
} from '../_lib/auth.js';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

async function handleSignup(req, res) {
  const { email, password, name } = req.body || {};
  if (!email || !EMAIL_PATTERN.test(email)) {
    res.status(400).json({ error: 'Enter a valid email address.' });
    return;
  }
  if (!password || password.length < 8) {
    res.status(400).json({ error: 'Password must be at least 8 characters.' });
    return;
  }

  await ensureSchema();
  const db = requireDb();

  const existing = await db`SELECT id FROM users WHERE email = ${email}`;
  if (existing.length > 0) {
    res.status(409).json({ error: 'An account with this email already exists.' });
    return;
  }

  const rows = await db`
    INSERT INTO users (email, name, password_hash)
    VALUES (${email}, ${name || email.split('@')[0]}, ${hashPassword(password)})
    RETURNING id, email, name, picture
  `;
  const user = rows[0];

  setSessionCookie(req, res, createSessionToken(user.id));
  res.status(200).json({ user });
}

async function handleLogin(req, res) {
  const { email, password } = req.body || {};
  if (!email || !password) {
    res.status(400).json({ error: 'Email and password are required.' });
    return;
  }

  await ensureSchema();
  const db = requireDb();

  const rows = await db`SELECT id, email, name, picture, password_hash FROM users WHERE email = ${email}`;
  const user = rows[0];

  if (!user || !user.password_hash || !verifyPassword(password, user.password_hash)) {
    res.status(401).json({ error: 'Incorrect email or password.' });
    return;
  }

  setSessionCookie(req, res, createSessionToken(user.id));
  res.status(200).json({ user: { id: user.id, email: user.email, name: user.name, picture: user.picture } });
}

async function handleLogout(req, res) {
  clearSessionCookie(req, res);
  res.status(200).json({ ok: true });
}

async function handleSession(req, res) {
  const { access_token: accessToken } = req.body || {};
  if (!accessToken) {
    res.status(400).json({ error: 'Missing access_token.' });
    return;
  }

  const verifyRes = await fetch(
    `https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=${encodeURIComponent(accessToken)}`
  );
  if (!verifyRes.ok) {
    res.status(401).json({ error: 'Google rejected this access token.' });
    return;
  }
  const tokenInfo = await verifyRes.json();

  const clientId = process.env.VITE_GOOGLE_CLIENT_ID;
  if (clientId && tokenInfo.aud !== clientId) {
    res.status(401).json({ error: 'Access token was not issued for this app.' });
    return;
  }
  if (!tokenInfo.email || tokenInfo.email_verified !== 'true') {
    res.status(401).json({ error: 'Google account has no verified email.' });
    return;
  }

  const profileRes = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!profileRes.ok) {
    res.status(502).json({ error: 'Failed to fetch Google profile.' });
    return;
  }
  const profile = await profileRes.json();

  await ensureSchema();
  const db = requireDb();
  const rows = await db`
    INSERT INTO users (email, name, picture)
    VALUES (${profile.email}, ${profile.name || profile.email}, ${profile.picture || null})
    ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name, picture = EXCLUDED.picture
    RETURNING id, email, name, picture
  `;
  const user = rows[0];

  setSessionCookie(req, res, createSessionToken(user.id));
  res.status(200).json({ user });
}

async function handleDeviceToken(req, res) {
  const userId = await getAuthedUserId(req);
  if (!userId) {
    res.status(401).json({ error: 'Not signed in.' });
    return;
  }

  await ensureSchema();
  const db = requireDb();

  const token = generateDeviceToken();
  await db`INSERT INTO device_tokens (token_hash, user_id) VALUES (${hashDeviceToken(token)}, ${userId})`;

  res.status(200).json({ token });
}

const ROUTES = {
  signup: handleSignup,
  login: handleLogin,
  logout: handleLogout,
  session: handleSession,
  'device-token': handleDeviceToken,
};

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed. Use POST.' });
    return;
  }

  const action = Array.isArray(req.query.action) ? req.query.action[0] : req.query.action;
  const route = ROUTES[action];
  if (!route) {
    res.status(404).json({ error: 'Not found.' });
    return;
  }

  try {
    await route(req, res);
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}
