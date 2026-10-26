import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  // Vite rejects unknown Host headers; allow Tailscale hostnames (*.ts.net) for phone access.
  server: { allowedHosts: ['.ts.net'] },
  preview: { allowedHosts: ['.ts.net'] },
  plugins: [
    react(),
    VitePWA({
      // New deploys replace the old service worker on next load, no "update available" prompt.
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon-180x180.png'],
      manifest: {
        name: 'Insta Lite',
        short_name: 'Insta Lite',
        description: 'Time-limited Instagram feed: only posts from a chosen time range.',
        theme_color: '#aa3bff',
        background_color: '#16171d',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: 'pwa-64x64.png', sizes: '64x64', type: 'image/png' },
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png' },
          { src: 'maskable-icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // The app shell (HTML/JS/CSS/icons) is precached: cache-first, works offline.
        // API data must be fresh, so it is network-first, falling back to the last
        // response only when offline.
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname === '/posts',
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-posts',
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 20, maxAgeSeconds: 24 * 60 * 60 },
            },
          },
        ],
      },
    }),
  ],
})
