import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      server: {
        port: 5173,
        host: '0.0.0.0',
        fs: {
          // Allow importing files from the monorepo root (../contracts, etc.)
          allow: [
            path.resolve(__dirname, '.'),
            path.resolve(__dirname, '..'),
          ],
        },
      },
      plugins: [react()],
      optimizeDeps: {
        include: ['zod'],
      },
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
          // Optional alias to simplify imports from shared contracts
          'contracts': path.resolve(__dirname, '../contracts'),
        }
      }
    };
});
