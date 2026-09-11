import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import devApiPlugin from './dev-api-plugin.js'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Vite only exposes VITE_-prefixed vars to import.meta.env by default.
  // The api/*.js handlers run as plain Node (process.env), same as they will
  // on Vercel, so copy everything from .env.local into process.env here too —
  // dev-only, this block never runs in the production build.
  const env = loadEnv(mode, process.cwd(), '')
  for (const [key, value] of Object.entries(env)) {
    if (!(key in process.env)) process.env[key] = value
  }

  return {
    plugins: [react(), devApiPlugin()],
  }
})
