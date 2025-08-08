import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const allowedHostsFromEnv = process.env.ALLOWED_HOSTS
  ? process.env.ALLOWED_HOSTS.split(',')
  : [];

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'build',
  },
  server: {
    // Dockerコンテナ外や他のマシンからアクセスできるようにホストを0.0.0.0に設定
    host: '0.0.0.0',
    // '*' は常に許可し、.envファイルから読み込んだホストも追加する
    allowedHosts: ['*', ...allowedHostsFromEnv],
    proxy: {
      // DjangoバックエンドへのAPIリクエストをプロキシする設定
      // /api で始まるリクエストのみをバックエンドに転送する
      '^/api/.*': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
});