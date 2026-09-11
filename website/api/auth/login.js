import { ensureSchema, requireDb, DbNotConfigured } from '../_lib/db.js';
import { createSessionToken, setSessionCookie, verifyPassword } from '../_lib/auth.js';

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

  const { email, password } = req.body || {};
  if (!email || !password) {
    res.status(400).json({ error: 'Email and password are required.' });
    return;
  }

  try {
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
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: `Sign-in failed: ${err.message}` });
  }
}
