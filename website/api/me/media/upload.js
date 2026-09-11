// Desktop app uploads a captured screenshot/video here (device Bearer token
// auth, same credential as sync-session). Body carries the file as base64 —
// simplest thing that works from Python without a multipart dependency.
// Sized for screenshots and short clips; see MAX_UPLOAD_BYTES.
import { ensureSchema, requireDb, slugify, DbNotConfigured } from '../../_lib/db.js';
import { getAuthedUserId } from '../../_lib/auth.js';
import { storeFile, MAX_UPLOAD_BYTES } from '../../_lib/storage.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed. Use POST.' });
    return;
  }

  try {
    const userId = await getAuthedUserId(req);
    if (!userId) {
      res.status(401).json({ error: 'Not signed in. Pair the desktop app first.' });
      return;
    }

    const {
      game_name: gameName,
      session_id: sessionId,
      type,
      filename,
      content_type: contentType,
      captured_at: capturedAt,
      duration_seconds: durationSeconds,
      data_base64: dataBase64,
    } = req.body || {};

    if (!type || !['screenshot', 'video'].includes(type)) {
      res.status(400).json({ error: "type must be 'screenshot' or 'video'." });
      return;
    }
    if (!filename || !dataBase64) {
      res.status(400).json({ error: 'Missing filename or data_base64.' });
      return;
    }

    const buffer = Buffer.from(dataBase64, 'base64');
    if (buffer.length > MAX_UPLOAD_BYTES) {
      res.status(413).json({
        error: `File is ${buffer.length} bytes, over the ${MAX_UPLOAD_BYTES}-byte proxy-upload limit. Large video clips need direct-to-storage upload, not implemented yet.`,
      });
      return;
    }

    await ensureSchema();
    const db = requireDb();

    let gameId = null;
    if (gameName) {
      const slug = slugify(gameName);
      const rows = await db`
        INSERT INTO games (slug, title) VALUES (${slug}, ${gameName})
        ON CONFLICT (slug) DO UPDATE SET title = EXCLUDED.title
        RETURNING id
      `;
      gameId = rows[0].id;
    }

    const { storageKey, url } = await storeFile(buffer, { userId, filename, contentType });

    const rows = await db`
      INSERT INTO media_assets (user_id, game_id, session_id, type, storage_key, url, mime_type, size_bytes, duration_seconds, captured_at)
      VALUES (${userId}, ${gameId}, ${sessionId || null}, ${type}, ${storageKey}, ${url}, ${contentType || null}, ${buffer.length}, ${durationSeconds || null}, ${capturedAt || null})
      RETURNING id, type, url, mime_type, size_bytes, duration_seconds, captured_at, created_at
    `;

    res.status(200).json({ media: rows[0] });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: `Upload failed: ${err.message}` });
  }
}
