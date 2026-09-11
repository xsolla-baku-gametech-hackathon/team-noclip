// Local-dev-only Vite plugin that serves the api/ Vercel serverless
// functions under `npm run dev`, so /api/* actually works without needing
// `vercel dev` installed. Not used in the production build — Vercel serves
// api/ natively there. Each handler already speaks the (req, res) => void
// contract with res.status().json(), so we just adapt Node's raw
// req/res to that shape and route by matching the api/ directory structure,
// including [param] dynamic segments.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const API_DIR = path.join(__dirname, 'api');

function collectRoutes(dir, urlPrefix, routes) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('_')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      collectRoutes(full, `${urlPrefix}/${entry.name}`, routes);
      continue;
    }
    if (!entry.name.endsWith('.js')) continue;
    const base = entry.name.replace(/\.js$/, '');
    const routePath = base === 'index' ? urlPrefix : `${urlPrefix}/${base}`;
    const paramNames = [];
    let hasCatchAll = false;
    const regexStr = routePath
      .split('/')
      .map((seg) => {
        const catchAll = seg.match(/^\[\.\.\.(.+)\]$/);
        if (catchAll) {
          hasCatchAll = true;
          paramNames.push({ name: catchAll[1], multi: true });
          return '(.+)';
        }
        const single = seg.match(/^\[(.+)\]$/);
        if (single) {
          paramNames.push({ name: single[1], multi: false });
          return '([^/]+)';
        }
        return seg.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      })
      .join('/');
    routes.push({ regex: new RegExp(`^${regexStr}/?$`), paramNames, filePath: full, hasCatchAll });
  }
}

export default function devApiPlugin() {
  return {
    name: 'dev-api-plugin',
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        if (!req.url || !req.url.startsWith('/api/')) return next();
        if (!fs.existsSync(API_DIR)) return next();

        const routes = [];
        collectRoutes(API_DIR, '/api', routes);
        // Specific routes must win over catch-alls (e.g. media-local's
        // [...key] shouldn't shadow a literal /api/me/media route).
        routes.sort((a, b) => Number(a.hasCatchAll) - Number(b.hasCatchAll));

        const urlObj = new URL(req.url, 'http://localhost');
        const match = routes.find((r) => r.regex.test(urlObj.pathname));
        if (!match) {
          res.statusCode = 404;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'Not found' }));
          return;
        }

        const m = urlObj.pathname.match(match.regex);
        const query = Object.fromEntries(urlObj.searchParams);
        match.paramNames.forEach((param, i) => {
          query[param.name] = param.multi ? m[i + 1].split('/') : m[i + 1];
        });

        let body;
        if (req.method !== 'GET' && req.method !== 'HEAD') {
          const chunks = [];
          for await (const chunk of req) chunks.push(chunk);
          const raw = Buffer.concat(chunks).toString('utf-8');
          try {
            body = raw ? JSON.parse(raw) : undefined;
          } catch {
            body = undefined;
          }
        }

        req.query = query;
        req.body = body;
        res.status = (code) => {
          res.statusCode = code;
          return res;
        };
        res.json = (obj) => {
          if (!res.getHeader('Content-Type')) res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify(obj));
        };

        try {
          const mod = await import(`${pathToFileURL(match.filePath).href}?t=${Date.now()}`);
          await mod.default(req, res);
        } catch (err) {
          res.statusCode = 500;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: err instanceof Error ? err.message : 'Internal error' }));
        }
      });
    },
  };
}
