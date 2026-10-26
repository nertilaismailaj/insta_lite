import { defineConfig, minimal2023Preset } from '@vite-pwa/assets-generator/config'

// Generates the PNG icons the manifest needs from public/icon.svg.
// Run with: npm run generate-icons
export default defineConfig({
  preset: {
    ...minimal2023Preset,
    // Android crops maskable icons to its own shape, so pad with the brand color, not white.
    maskable: { ...minimal2023Preset.maskable, resizeOptions: { background: '#aa3bff' } },
    apple: { ...minimal2023Preset.apple, resizeOptions: { background: '#aa3bff' } },
  },
  images: ['public/icon.svg'],
})
