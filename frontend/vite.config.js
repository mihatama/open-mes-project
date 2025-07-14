import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Djangoサーバーに転送するパスのプレフィックス
      '/users': {
        target: 'http://backend:8000', // Dockerコンテナ名で指定
        changeOrigin: true,
      },
      '/api': {
        target: 'http://backend:8000', // Dockerコンテナ名で指定
        changeOrigin: true,
      },
      '/master': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/production': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/inventory_api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    }
  }
})