// Dev-only file server for the local-disk storage fallback in _lib/storage.js.
// In production, BLOB_READ_WRITE_TOKEN is set and storeFile() returns a real
// Vercel Blob public URL instead — this route is never hit there since no
// media_assets row would ever contain an /api/media-local/ url in that mode.
import path from 'node:path';
import { readLocalFile } from '../_lib/storage.js';

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

  const keyParts = req.query.key;
  const key = Array.isArray(keyParts) ? keyParts.join('/') : String(keyParts || '');
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
