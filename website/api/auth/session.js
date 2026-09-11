// Establishes the real server-side session after the client completes
// Google Sign-In. The client sends the Google access token it just obtained;
// this handler verifies it directly with Google (never trusts a client-
// supplied email), upserts the user, and issues our own signed session
// cookie. This is the credential every other /api/me/* route trusts.
import { ensureSchema, requireDb, DbNotConfigured } from '../_lib/db.js';
import { createSessionToken, setSessionCookie } from '../_lib/auth.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed. Use POST.' });
    return;
  }

  const { access_token: accessToken } = req.body || {};
  if (!accessToken) {
    res.status(400).json({ error: 'Missing access_token.' });
    return;
  }

  try {
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
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: `Sign-in failed: ${err.message}` });
  }
}
