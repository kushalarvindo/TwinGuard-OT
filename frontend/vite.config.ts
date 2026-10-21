import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      'three/addons/controls/OrbitControls.js': path.resolve(__dirname, 'src/vendor/OrbitControls.js'),
      'three/addons/controls/OrbitControls': path.resolve(__dirname, 'src/vendor/OrbitControls.js'),
      'three': path.resolve(__dirname, 'src/vendor/three.module.js'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
