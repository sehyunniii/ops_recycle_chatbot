// frontend/vite.config.js

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // ⭐️⭐️⭐️ 이 'server' 블록을 추가하세요 ⭐️⭐️⭐️
  server: {
    proxy: {
      // '/api'로 시작하는 모든 요청을
      '/api': {
        // 8000번 백엔드 서버로 전달
        target: 'http://127.0.0.1:8000',
        changeOrigin: true, // CORS를 위해 Origin 헤더 변경
      }
    }
  }
})