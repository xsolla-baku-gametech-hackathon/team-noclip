// Session + device-token auth for the authenticated app's API.
//
// Two credential types, both scoped to a user_id server-side (never trusted
// from the client):
//  - Web session: a signed, expiring cookie (HMAC'd with SESSION_SECRET).
//  - Device token: an opaque random token (desktop app), stored hashed in
//    the device_tokens table — the desktop pairs for one via /api/device/*.
import crypto from 'node:crypto';
import { requireDb, ensureSchema } from './db.js';

const SESSION_COOKIE = 'synapsex_session';
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30;

function getSecret() {
  const secret = process.env.SESSION_SECRET;
  if (!secret) throw new Error('SESSION_SECRET is not configured.');
  return secret;
}

function sign(value) {
  return crypto.createHmac('sha256', getSecret()).update(value).digest('base64url');
}

function timingSafeEqualStr(a, b) {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

export function createSessionToken(userId) {
  const expires = Date.now() + SESSION_MAX_AGE_SECONDS * 1000;
  const payload = `${userId}.${expires}`;
  return `${payload}.${sign(payload)}`;
}

export function verifySessionToken(token) {
  if (!token) return null;
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const [userId, expires, sig] = parts;
  const expected = sign(`${userId}.${expires}`);
  if (!timingSafeEqualStr(sig, expected)) return null;
  if (Date.now() > Number(expires)) return null;
  return { userId };
}

function parseCookies(req) {
  const header = req.headers.cookie;
  if (!header) return {};
  return Object.fromEntries(
    header.split(';').map((c) => {
      const idx = c.indexOf('=');
      return [c.slice(0, idx).trim(), decodeURIComponent(c.slice(idx + 1))];
    })
  );
}

function isHttps(req) {
  return req.headers['x-forwarded-proto'] === 'https';
}

export function setSessionCookie(req, res, token) {
  const secureFlag = isHttps(req) ? ' Secure;' : '';
  res.setHeader(
    'Set-Cookie',
    `${SESSION_COOKIE}=${token}; Path=/; HttpOnly;${secureFlag} SameSite=Lax; Max-Age=${SESSION_MAX_AGE_SECONDS}`
  );
}

export function clearSessionCookie(req, res) {
  const secureFlag = isHttps(req) ? ' Secure;' : '';
  res.setHeader('Set-Cookie', `${SESSION_COOKIE}=; Path=/; HttpOnly;${secureFlag} SameSite=Lax; Max-Age=0`);
}

function getCookieUserId(req) {
  const token = parseCookies(req)[SESSION_COOKIE];
  return verifySessionToken(token)?.userId ?? null;
}

function getBearerToken(req) {
  const header = req.headers.authorization || '';
  const match = header.match(/^Bearer (.+)$/);
  return match ? match[1] : null;
}

export function hashDeviceToken(token) {
  return crypto.createHash('sha256').update(token).digest('hex');
}

export function generateDeviceToken() {
  return crypto.randomBytes(32).toString('base64url');
}

// Password hashing (scrypt — built into Node, no extra dependency).
export function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const derived = crypto.scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${derived}`;
}

export function verifyPassword(password, stored) {
  if (!stored || !stored.includes(':')) return false;
  const [salt, hash] = stored.split(':');
  const derived = crypto.scryptSync(password, salt, 64).toString('hex');
  const a = Buffer.from(hash, 'hex');
  const b = Buffer.from(derived, 'hex');
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

export function generatePairingCode() {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let code = '';
  for (let i = 0; i < 8; i++) code += alphabet[crypto.randomInt(alphabet.length)];
  return code;
}

// Resolves the authenticated user id from either a web session cookie or a
// device Bearer token. Returns null if neither is present/valid — callers
// must respond 401, never fall back to a client-supplied id.
export async function getAuthedUserId(req) {
  const cookieUserId = getCookieUserId(req);
  if (cookieUserId) return cookieUserId;

  const bearer = getBearerToken(req);
  if (!bearer) return null;

  await ensureSchema();
  const db = requireDb();
  const rows = await db`
    SELECT user_id FROM device_tokens WHERE token_hash = ${hashDeviceToken(bearer)}
  `;
  if (rows.length === 0) return null;

  db`UPDATE device_tokens SET last_used_at = now() WHERE token_hash = ${hashDeviceToken(bearer)}`.catch(() => {});
  return rows[0].user_id;
}
