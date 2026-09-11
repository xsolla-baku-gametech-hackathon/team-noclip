# Xsolla Game Recap — Website

React + Vite + TypeScript + Tailwind SPA: the public landing page, login, and the authenticated dashboard (Overview, My Games, Recaps, Media, Cloud Sharing, Settings) for [Xsolla Game Recap](../README.md).

## Structure

```
src/main/   Public landing page, login, share pages
src/app/    Authenticated dashboard
src/auth/   Client-side auth helpers (Google Sign-In, session, API client)
api/        Vercel serverless functions (auth, sync, recap generation, media, sharing)
```

## Setup

```bash
npm install
cp .env.example .env.local   # fill in DATABASE_URL, SESSION_SECRET, OPENROUTER_API_KEY, VITE_GOOGLE_CLIENT_ID
npm run dev -- --port 5183
```

`npm run dev` runs a local Vite plugin (`dev-api-plugin.js`) that serves the `api/` functions the same way Vercel does, so the full stack works locally with no extra tooling.

## Environment variables

See [`.env.example`](./.env.example) for the full list and where to get each value. In short:

- `DATABASE_URL` — Postgres connection string (Vercel Postgres / Neon)
- `SESSION_SECRET` — any long random string, signs the session cookie
- `OPENROUTER_API_KEY` — powers AI recap generation
- `VITE_GOOGLE_CLIENT_ID` — Google OAuth Client ID for Sign-In (optional — falls back to a default, or set at runtime via the login page's config modal)
- `BLOB_READ_WRITE_TOKEN` — optional, enables real media storage in production (falls back to local disk in dev)

## Build

```bash
npm run build
```

## Deploying

Deployed to Vercel with **Root Directory** set to `website`. Every API route is a static-filename file under `api/` dispatched by a query param (`?action=`, `?resource=`, etc.) rather than a bracket-named dynamic route — this specific Vercel project doesn't register bracket routes (`[id].js`) as functions, so don't reintroduce them.
