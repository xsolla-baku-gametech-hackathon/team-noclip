// Media storage abstraction. Real cloud storage (Vercel Blob) when
// BLOB_READ_WRITE_TOKEN is set — provision from the Vercel dashboard's
// Storage tab. Falls back to local disk under .local-media/ for dev, using
// the same dual-mode pattern as db.js's local Postgres fallback. Callers
// never touch either backend directly, so switching is a config change,
// not a code change.
import { put } from '@vercel/blob';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const BLOB_TOKEN = process.env.BLOB_READ_WRITE_TOKEN;
const LOCAL_MEDIA_DIR = path.join(process.cwd(), '.local-media');

export function isBlobConfigured() {
  return Boolean(BLOB_TOKEN);
}

// Serverless functions on Vercel's default runtime cap request bodies —
// this proxy-upload path is sized for screenshots and short clips, not
// arbitrarily large video files. Callers should check this before reading
// a large file into memory.
export const MAX_UPLOAD_BYTES = 4 * 1024 * 1024;

export async function storeFile(buffer, { userId, filename, contentType }) {
  const safeName = filename.replace(/[^a-zA-Z0-9_.-]/g, '_');
  const key = `${userId}/${crypto.randomUUID()}-${safeName}`;

  if (BLOB_TOKEN) {
    const blob = await put(key, buffer, { access: 'public', token: BLOB_TOKEN, contentType });
    return { storageKey: key, url: blob.url };
  }

  const fullPath = path.join(LOCAL_MEDIA_DIR, key);
  fs.mkdirSync(path.dirname(fullPath), { recursive: true });
  fs.writeFileSync(fullPath, buffer);
  return { storageKey: key, url: `/api/media-local/${key}` };
}

export function readLocalFile(key) {
  const fullPath = path.join(LOCAL_MEDIA_DIR, key);
  if (!fullPath.startsWith(LOCAL_MEDIA_DIR) || !fs.existsSync(fullPath)) return null;
  return fs.readFileSync(fullPath);
}
