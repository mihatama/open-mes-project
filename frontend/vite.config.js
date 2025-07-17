import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // DjangoバックエンドへのAPIリクエストをプロキシする設定
      // /api, /users だけでなく、/quality など他のアプリケーションへのリクエストも転送する
      '^/(api|admin|quality|inventory|production|machine|master|mobile|users|__debug__|static)/.*': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    }
  }
})