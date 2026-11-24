import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The browser calls /chat and /health on this same server; Vite forwards them
// to the FastAPI backend, which only listens on this machine. That way other
// people on the network only need the frontend's address, and there is no CORS.
const BACKEND = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const lanServer = {
  host: true,        // listen on all interfaces so others on the network can connect
  port: 5180,        // 5173 is taken by another app on this machine
  strictPort: true,  // fail instead of silently moving to another port
  proxy: {
    '/chat': BACKEND,
    '/health': BACKEND,
  },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: lanServer,
  preview: lanServer,
})
