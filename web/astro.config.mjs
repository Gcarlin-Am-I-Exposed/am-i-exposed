// @ts-check
import { defineConfig } from 'astro/config';

// Am I Exposed? rebuild (M0). EN at root, ES under /es/ (mirrors the live site).
// Static output by default; a Vercel adapter is added at the deploy/cutover gate.
export default defineConfig({
  site: 'https://www.am-i-exposed.com',
  build: { format: 'directory' },
  vite: {
    server: {
      // Dev only: forward /api/* to the live functions so the scan island can be
      // tested locally. Has no effect on the static build. In production the api/
      // functions are served from the same origin as the site.
      proxy: {
        '/api': {
          target: 'https://www.am-i-exposed.com',
          changeOrigin: true,
          secure: true,
        },
      },
    },
  },
});
