// @ts-check
import { defineConfig } from 'astro/config';

// Am I Exposed? rebuild (M0). EN at root, ES under /es/ (mirrors the live site).
// Static output by default; a Vercel adapter is added at the deploy/cutover gate.
export default defineConfig({
  site: 'https://www.am-i-exposed.com',
  build: { format: 'directory' },
});
