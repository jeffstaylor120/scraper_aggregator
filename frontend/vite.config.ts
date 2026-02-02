import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// When running in Docker, set VITE_API_PROXY_TARGET=http://api:8000 so /api proxies to api service.
const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // listen on 0.0.0.0 so Docker port mapping works
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true, rewrite: (path) => path.replace(/^\/api/, '') },
    },
  },
})
