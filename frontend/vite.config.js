import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  root: '.',
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/pivots': 'http://localhost:8000',
      '/mappings': 'http://localhost:8000',
      '/convert': 'http://localhost:8000',
      '/harvest': 'http://localhost:8000',
      '/list-sets': 'http://localhost:8000',
      '/source-formats': 'http://localhost:8000',
      '/template-fields': 'http://localhost:8000',
      '/arc': 'http://localhost:8000',
    },
  },
})
