import { globSync, rmSync, statSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { assertNoLiteralSecretAssignments, assertNoMarker } from './secret-scan-lib.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const workerScanDirectory = resolve(root, '.secret-scan-worker');
if (dirname(workerScanDirectory) !== root) throw new Error('Worker scan output escaped the repository root');

const marker = 'LOSTARK_API_TOKEN_SENTINEL_NEVER_SHIP';
const releaseEnvironment = {
  ...process.env,
  LOSTARK_API_TOKEN: marker,
  VITE_LOSTARK_API_TOKEN: marker,
};
const viteCli = resolve(root, 'node_modules/vite/bin/vite.js');
const wranglerCli = resolve(root, 'node_modules/wrangler/bin/wrangler.js');

function run(label, command, args, cwd = root) {
  const result = spawnSync(command, args, {
    cwd,
    env: releaseEnvironment,
    stdio: 'inherit',
  });
  if (result.error || result.status !== 0) {
    throw new Error(`${label} failed during release secret scan`);
  }
}

rmSync(workerScanDirectory, { recursive: true, force: true });
try {
  run('web sentinel build', process.execPath, [viteCli, 'build'], resolve(root, 'apps/web'));
  run('Worker sentinel build', process.execPath, [
    wranglerCli, 'deploy', '--dry-run',
    '--config', 'apps/worker/wrangler.jsonc',
    '--outdir', workerScanDirectory,
    '--define', `process.env.LOSTARK_API_TOKEN:${JSON.stringify(marker)}`,
  ]);

  const bundles = [
    ...globSync(resolve(root, 'apps/web/dist/**/*')),
    ...globSync(resolve(workerScanDirectory, '**/*')),
  ].filter((file) => statSync(file).isFile());
  if (bundles.length === 0) throw new Error('release secret scan produced no bundles');
  assertNoMarker(bundles, marker);

  const trackedConfigResult = spawnSync('git', ['ls-files', '--', 'apps/worker/wrangler*.json*'], {
    cwd: root,
    encoding: 'utf8',
  });
  if (trackedConfigResult.error || trackedConfigResult.status !== 0) {
    throw new Error('tracked Worker config discovery failed');
  }
  const trackedConfigs = trackedConfigResult.stdout.trim().split(/\r?\n/).filter(Boolean).map((file) => resolve(root, file));
  assertNoLiteralSecretAssignments(trackedConfigs);
  console.log(`secret build scan passed (${bundles.length} bundle files, ${trackedConfigs.length} tracked configs; no values printed)`);
} finally {
  rmSync(workerScanDirectory, { recursive: true, force: true });
}
