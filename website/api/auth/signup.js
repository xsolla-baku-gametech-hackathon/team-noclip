import { ensureSchema, requireDb, DbNotConfigured } from '../_lib/db.js';
import { createSessionToken, setSessionCookie, hashPassword } from '../_lib/auth.js';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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

  const { email, password, name } = req.body || {};
  if (!email || !EMAIL_PATTERN.test(email)) {
    res.status(400).json({ error: 'Enter a valid email address.' });
    return;
  }
  if (!password || password.length < 8) {
    res.status(400).json({ error: 'Password must be at least 8 characters.' });
    return;
  }

  try {
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
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: `Sign-up failed: ${err.message}` });
  }
}
