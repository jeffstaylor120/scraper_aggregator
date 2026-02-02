import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// When running in Docker, set VITE_API_PROXY_TARGET=http://api:8000 so /api proxies to api service.
const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'
// Comma-separated hosts to allow (e.g. newsletter.auxelion.com). Set in Coolify or .env.
const allowedHosts = process.env.VITE_ALLOWED_HOSTS
  ? process.env.VITE_ALLOWED_HOSTS.split(',').map((h) => h.trim()).filter(Boolean)
  : []

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // listen on 0.0.0.0 so Docker port mapping works
    ...(allowedHosts.length > 0 && { allowedHosts }),
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true, rewrite: (path) => path.replace(/^\/api/, '') },
    },
  },
})
