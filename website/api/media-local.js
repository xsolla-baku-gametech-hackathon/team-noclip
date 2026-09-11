// Dev-only file server for the local-disk storage fallback in _lib/storage.js
// — GET /api/media-local?key=... (renamed from the bracket route
// api/media-local/[...key].js — see api/auth.js for why). In production,
// BLOB_READ_WRITE_TOKEN is set and storeFile() returns a real Vercel Blob
// public URL instead, so this route is never hit there.
import path from 'node:path';
import { readLocalFile } from './_lib/storage.js';

const CONTENT_TYPES = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.mp4': 'video/mp4',
  '.mov': 'video/quicktime',
  '.webm': 'video/webm',
};

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed. Use GET.' });
    return;
  }

  const key = String(req.query.key || '');
  const data = readLocalFile(key);
  if (!data) {
    res.status(404).json({ error: 'Not found.' });
    return;
  }

  const ext = path.extname(key).toLowerCase();
  res.setHeader('Content-Type', CONTENT_TYPES[ext] || 'application/octet-stream');
  res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
  res.status(200);
  res.end(data);
}
