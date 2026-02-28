import { defineConfig, loadEnv } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import path from 'path'

export default defineConfig(({ mode }) => {
  const rootDir = path.resolve(__dirname, '..')
  const env = loadEnv(mode, rootDir, '')
  
  const frontendPort = parseInt(env.FRONTEND_PORT || '8500')
  const backendHost = env.BACKEND_HOST || 'localhost'
  const backendPort = parseInt(env.BACKEND_PORT || '8100')
  const apiUrl = `http://${backendHost}:${backendPort}`
  
  return {
    plugins: [svelte()],
    base: '/static/',
    envDir: rootDir,
    define: {
      'import.meta.env.BACKEND_PORT': JSON.stringify(backendPort),
      'import.meta.env.BACKEND_HOST': JSON.stringify(backendHost),
      'import.meta.env.FRONTEND_PORT': JSON.stringify(frontendPort),
    },
    server: {
      port: frontendPort,
      proxy: {
        '/api': {
          target: apiUrl,
          changeOrigin: true,
        },
        '/health': {
          target: apiUrl,
          changeOrigin: true,
        },
      },
    },
    build: {
      target: 'esnext',
    },
  }
})
