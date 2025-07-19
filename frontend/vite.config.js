import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // DjangoバックエンドへのAPIリクエストをプロキシする設定
      // /api で始まるリクエストのみをバックエンドに転送する
      '^/api/.*': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    }
  }
})