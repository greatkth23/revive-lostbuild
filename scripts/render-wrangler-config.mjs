import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const target = process.env.TARGET;
const namespaceId = process.env.KV_NAMESPACE_ID;
if (!['preview', 'production'].includes(target ?? '')) {
  throw new Error('TARGET must be preview or production');
}
if (!/^[a-f0-9]{32}$/i.test(namespaceId ?? '')) {
  throw new Error('KV_NAMESPACE_ID must be exactly 32 hexadecimal characters');
}

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const workerDirectory = resolve(root, 'apps/worker');
const output = resolve(workerDirectory, `wrangler.${target}.json`);
const expectedOutput = `${workerDirectory}${sep}wrangler.${target}.json`;
if (output !== expectedOutput || relative(workerDirectory, output).startsWith('..')) {
  throw new Error('Generated Wrangler config must stay inside apps/worker');
}

const source = resolve(workerDirectory, 'wrangler.jsonc');
const config = JSON.parse(readFileSync(source, 'utf8').replace(/\/\/[^\n]*\n/g, '\n'));
config.name = `weather-artist-simulator-${target}`;
config.kv_namespaces = [{ binding: 'SNAPSHOTS', id: namespaceId }];
writeFileSync(output, `${JSON.stringify(config, null, 2)}\n`, {
  encoding: 'utf8',
  flag: 'wx',
  mode: 0o600,
});

process.stdout.write(`${relative(root, output).split(sep).join('/')}\n`);
