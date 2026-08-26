import { existsSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';

const root = resolve(import.meta.dirname, '../../..');
const script = resolve(root, 'scripts/render-wrangler-config.mjs');
const generated = ['preview', 'production'].map((target) =>
  resolve(root, `apps/worker/wrangler.${target}.json`),
);

function runRenderer(target: string, namespaceId: string) {
  return spawnSync(process.execPath, [script], {
    cwd: root,
    env: {
      ...process.env,
      TARGET: target,
      KV_NAMESPACE_ID: namespaceId,
    },
    encoding: 'utf8',
  });
}

afterEach(() => {
  for (const path of generated) {
    rmSync(path, { force: true });
  }
});

describe('render-wrangler-config', () => {
  it.each(['preview', 'production'])('renders the isolated %s target config', (target) => {
    const namespaceId = target === 'preview'
      ? '0123456789abcdef0123456789abcdef'
      : 'fedcba9876543210fedcba9876543210';

    const result = runRenderer(target, namespaceId);

    expect(result.status, result.stderr).toBe(0);
    expect(result.stdout).toBe(`apps/worker/wrangler.${target}.json\n`);
    const config = JSON.parse(readFileSync(resolve(root, result.stdout.trim()), 'utf8'));
    expect(config.name).toBe(`weather-artist-simulator-${target}`);
    expect(config.kv_namespaces).toEqual([{ binding: 'SNAPSHOTS', id: namespaceId }]);
    expect(config.durable_objects.bindings).toEqual([
      { name: 'UPSTREAM_BUDGET', class_name: 'UpstreamBudget' },
    ]);
  });

  it.each([
    ['staging', '0123456789abcdef0123456789abcdef'],
    ['preview', 'not-a-kv-id'],
  ])('rejects invalid deployment input (%s)', (target, namespaceId) => {
    const result = runRenderer(target, namespaceId);

    expect(result.status).not.toBe(0);
    expect(generated.some((path) => existsSync(path))).toBe(false);
  });

  it('refuses to overwrite an existing generated config', () => {
    const output = generated[0]!;
    writeFileSync(output, 'keep-me\n', { encoding: 'utf8', mode: 0o600 });

    const result = runRenderer('preview', '0123456789abcdef0123456789abcdef');

    expect(result.status).not.toBe(0);
    expect(readFileSync(output, 'utf8')).toBe('keep-me\n');
  });
});
