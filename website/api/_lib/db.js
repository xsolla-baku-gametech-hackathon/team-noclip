// Shared Postgres access for the authenticated app's API routes.
// Requires DATABASE_URL (or POSTGRES_URL) — set this as a Vercel Environment
// Variable after provisioning a Postgres database (Vercel Postgres / Neon)
// from the Vercel project dashboard's Storage tab.
import { neon } from '@neondatabase/serverless';
import pg from 'pg';

const connectionString = process.env.DATABASE_URL || process.env.POSTGRES_URL;
const isLocalPostgres = connectionString && /localhost|127\.0\.0\.1/.test(connectionString);

function createLocalSql(cs) {
  // @neondatabase/serverless talks to Neon's HTTP proxy, not raw Postgres —
  // it can't reach a plain local instance. For local dev against a real
  // local Postgres, fall back to `pg` behind the same tagged-template call
  // shape every handler already uses. Production (a real Neon connection
  // string) never takes this path.
  const pool = new pg.Pool({ connectionString: cs });
  return async (strings, ...values) => {
    const text = strings.reduce((acc, s, i) => acc + s + (i < values.length ? `$${i + 1}` : ''), '');
    const { rows } = await pool.query(text, values);
    return rows;
  };
}

export const sql = connectionString ? (isLocalPostgres ? createLocalSql(connectionString) : neon(connectionString)) : null;

export class DbNotConfigured extends Error {
  constructor() {
    super('Database is not configured. Set DATABASE_URL as a Vercel Environment Variable.');
    this.name = 'DbNotConfigured';
  }
}

export function requireDb() {
  if (!sql) throw new DbNotConfigured();
  return sql;
}

let schemaReady = false;

// Idempotent CREATE TABLE IF NOT EXISTS — fine at hackathon scale; swap for a
// real migration tool before this needs to survive schema changes in prod.
export async function ensureSchema() {
  if (schemaReady) return;
  const db = requireDb();

  await db`CREATE EXTENSION IF NOT EXISTS pgcrypto`;

  await db`
    CREATE TABLE IF NOT EXISTS users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      picture TEXT,
      password_hash TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
  `;
  await db`ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT`;

  await db`
    CREATE TABLE IF NOT EXISTS games (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      slug TEXT UNIQUE NOT NULL,
      title TEXT NOT NULL,
      cover_image_url TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
  `;

  await db`
    CREATE TABLE IF NOT EXISTS user_games (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
      first_played_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      last_played_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      total_sessions INTEGER NOT NULL DEFAULT 0,
      UNIQUE(user_id, game_id)
    )
  `;
  await db`CREATE INDEX IF NOT EXISTS idx_user_games_user ON user_games(user_id)`;

  await db`
    CREATE TABLE IF NOT EXISTS game_sessions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
      external_session_id TEXT,
      window_title TEXT,
      started_at TIMESTAMPTZ,
      ended_at TIMESTAMPTZ,
      duration_seconds INTEGER,
      events JSONB NOT NULL DEFAULT '[]',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(user_id, external_session_id)
    )
  `;
  await db`CREATE INDEX IF NOT EXISTS idx_sessions_user ON game_sessions(user_id)`;
  await db`CREATE INDEX IF NOT EXISTS idx_sessions_game ON game_sessions(game_id)`;
  await db`CREATE INDEX IF NOT EXISTS idx_sessions_created ON game_sessions(created_at)`;

  await db`
    CREATE TABLE IF NOT EXISTS recaps (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      session_id UUID NOT NULL UNIQUE REFERENCES game_sessions(id) ON DELETE CASCADE,
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
      previously_on TEXT NOT NULL,
      priorities JSONB NOT NULL DEFAULT '[]',
      inventory JSONB NOT NULL DEFAULT '[]',
      generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
  `;
  await db`CREATE INDEX IF NOT EXISTS idx_recaps_user ON recaps(user_id)`;

  await db`
    CREATE TABLE IF NOT EXISTS device_logins (
      code TEXT PRIMARY KEY,
      status TEXT NOT NULL DEFAULT 'pending',
      device_token TEXT,
      user_id UUID REFERENCES users(id) ON DELETE CASCADE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      expires_at TIMESTAMPTZ NOT NULL
    )
  `;

  await db`
    CREATE TABLE IF NOT EXISTS device_tokens (
      token_hash TEXT PRIMARY KEY,
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      last_used_at TIMESTAMPTZ
    )
  `;
  await db`CREATE INDEX IF NOT EXISTS idx_device_tokens_user ON device_tokens(user_id)`;

  await db`
    CREATE TABLE IF NOT EXISTS media_assets (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      game_id UUID REFERENCES games(id) ON DELETE SET NULL,
      session_id UUID REFERENCES game_sessions(id) ON DELETE SET NULL,
      type TEXT NOT NULL CHECK (type IN ('screenshot', 'video')),
      storage_key TEXT NOT NULL,
      url TEXT NOT NULL,
      mime_type TEXT,
      size_bytes BIGINT,
      duration_seconds INTEGER,
      captured_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
  `;
  await db`CREATE INDEX IF NOT EXISTS idx_media_user ON media_assets(user_id)`;
  await db`CREATE INDEX IF NOT EXISTS idx_media_game ON media_assets(game_id)`;
  await db`CREATE INDEX IF NOT EXISTS idx_media_created ON media_assets(created_at)`;

  await db`
    CREATE TABLE IF NOT EXISTS share_packages (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
      recap_id UUID REFERENCES recaps(id) ON DELETE SET NULL,
      media_ids JSONB NOT NULL DEFAULT '[]',
      title TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
  `;
  await db`CREATE INDEX IF NOT EXISTS idx_share_user ON share_packages(user_id)`;

  schemaReady = true;
}

export function slugify(name) {
  return String(name)
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'game';
}
