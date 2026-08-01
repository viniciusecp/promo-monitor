import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { TanStackRouterVite } from '@tanstack/router-plugin/vite'
import path from 'node:path'

export default defineConfig({
  plugins: [
    TanStackRouterVite({ target: 'react', autoCodeSplitting: true }),
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    // Espelha o proxy do nginx de produção: em dev o painel também fala com a
    // API pela própria origem. Sem isto o cookie de sessão (SameSite=Lax) não
    // seria enviado de :3000 para :4999 e o `pnpm dev` viveria deslogado.
    proxy: {
      '/api': {
        target: 'http://localhost:4999',
        // changeOrigin fica FALSE de propósito: ele reescreveria o Host para
        // localhost:4999 e aí a checagem de Origin do backend veria Origin
        // (:3000) diferente do Host (:4999) e barraria todo POST/PUT em dev.
        // Mantendo o Host original, dev e produção enxergam a mesma coisa.
        changeOrigin: false,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
})
