import { defineConfig } from 'vitest/config';
import { loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  // Use the same PORT precedence as the backend's dotenv configuration.
  const rootEnv = loadEnv(mode, '..', '');
  const backendEnv = loadEnv(mode, '../backend', '');
  const frontendEnv = loadEnv(mode, '.', '');
  const backendPort = process.env.PORT || rootEnv.PORT || backendEnv.PORT || '5001';
  const apiTarget = process.env.API_PROXY_TARGET || frontendEnv.API_PROXY_TARGET || `http://127.0.0.1:${backendPort}`;
  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': { target: apiTarget, changeOrigin: true },
      },
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/test/setup.js',
      css: true,
    },
  };
});
