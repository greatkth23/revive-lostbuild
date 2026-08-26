import { readFileSync, writeFileSync } from 'node:fs';

const target = process.env.TARGET;
const namespaceId = process.env.KV_NAMESPACE_ID;
const output = process.argv[2];
if (!['preview', 'production'].includes(target) || !/^[a-f0-9]{32}$/i.test(namespaceId ?? '') || !output) {
  throw new Error('TARGET (preview|production), a 32-hex KV_NAMESPACE_ID, and output path are required');
}
const config = JSON.parse(readFileSync('apps/worker/wrangler.jsonc', 'utf8').replace(/\/\/[^\n]*\n/g, '\n'));
config.name = `weather-artist-simulator-${target}`;
config.kv_namespaces = [{ binding: 'SNAPSHOTS', id: namespaceId }];
writeFileSync(output, `${JSON.stringify(config, null, 2)}\n`, { mode: 0o600 });
