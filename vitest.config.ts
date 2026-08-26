import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  resolve: {
    alias: {
      'cloudflare:workers': fileURLToPath(
        new URL('./apps/worker/src/cloudflare-workers-test-shim.ts', import.meta.url),
      ),
    },
  },
  test: {
    include: ['packages/*/src/**/*.test.ts', 'apps/*/src/**/*.test.{ts,tsx}']
  }
});
