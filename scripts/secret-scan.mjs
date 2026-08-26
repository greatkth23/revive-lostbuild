import { readFileSync, existsSync, statSync } from 'node:fs';
import { globSync } from 'node:fs';

const sentinel = 'LOSTARK_API_TOKEN_SENTINEL_NEVER_SHIP';
const targets = [
  ...globSync('apps/web/dist/**/*', { nodir: true }),
  'apps/worker/src/index.ts',
  'apps/worker/wrangler.jsonc'
].filter((target) => existsSync(target) && statSync(target).isFile());
const forbidden = [sentinel, /LOSTARK_API_TOKEN\s*[:=]\s*['"][^'"]+/];
for (const target of targets) {
  const text = readFileSync(target, 'utf8');
  if (forbidden.some((pattern) => typeof pattern === 'string' ? text.includes(pattern) : pattern.test(text))) {
    throw new Error(`secret-like material found in ${target}`);
  }
}
console.log(`secret scan passed (${targets.length} files; no values printed)`);
