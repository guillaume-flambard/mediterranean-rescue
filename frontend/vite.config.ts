import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // En développement, Vite renvoie les appels /api vers Django (`uv run manage.py runserver`).
    // Si Django tourne sur un autre port : API_TARGET=http://127.0.0.1:8001 pnpm dev
    proxy: { '/api': process.env.API_TARGET ?? 'http://127.0.0.1:8000' },
  },
})
