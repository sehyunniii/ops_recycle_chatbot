// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  server: {
    // ⭐️ 1. ngrok 접속을 허용하는 설정 (추가됨)
    host: true,
    allowedHosts: [
      'suborbital-lillian-wily.ngrok-free.dev'
    ],

    // ⭐️ 2. 기존 백엔드 프록시 설정 (그대로 유지!)
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
