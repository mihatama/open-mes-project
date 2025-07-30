import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Dockerコンテナ外や他のマシンからアクセスできるようにホストを0.0.0.0に設定
    host: '0.0.0.0',
    // Vite開発サーバーにアクセスを許可するホストのリスト
    allowedHosts: ['*'],
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