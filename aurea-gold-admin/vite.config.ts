import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import history from 'connect-history-api-fallback';

export default defineConfig({
  appType: 'spa',
  plugins: [
    react(),
    {
      name: 'force-spa-fallback',
      configureServer(server) {
        // força o fallback a ser o PRIMEIRO middleware
        // @ts-ignore - tipos declarados em /types
        server.middlewares.stack.unshift({
          route: '',
          handle: history({
            index: '/index.html',
            disableDotRule: true,
            htmlAcceptHeaders: ['text/html', 'application/xhtml+xml'],
          })
        });
      },
    },
  ],
});
