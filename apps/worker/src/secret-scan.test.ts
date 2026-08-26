import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, describe, expect, test } from 'vitest';
import { assertNoLiteralSecretAssignments, assertNoMarker } from '../../../scripts/secret-scan-lib.mjs';

const temporaryDirectories: string[] = [];
const sentinel = 'LOSTARK_API_TOKEN_SENTINEL_NEVER_SHIP';

afterEach(() => {
  for (const directory of temporaryDirectories.splice(0)) {
    rmSync(directory, { recursive: true, force: true });
  }
});

describe('release secret scanner', () => {
  test.each(['web', 'worker'])('fails when the %s bundle contains the injected sentinel', (bundle) => {
    const directory = mkdtempSync(join(tmpdir(), 'weather-secret-scan-'));
    temporaryDirectories.push(directory);
    const web = join(directory, 'web.js');
    const worker = join(directory, 'worker.js');
    writeFileSync(web, bundle === 'web' ? sentinel : 'safe web bundle');
    writeFileSync(worker, bundle === 'worker' ? sentinel : 'safe worker bundle');

    expect(() => assertNoMarker([web, worker], sentinel)).toThrow('secret marker found in release bundle');
  });

  test('allows required binding names but rejects a literal secret assignment', () => {
    const directory = mkdtempSync(join(tmpdir(), 'weather-config-scan-'));
    temporaryDirectories.push(directory);
    const safe = join(directory, 'safe.json');
    const unsafe = join(directory, 'unsafe.json');
    writeFileSync(safe, '{"secrets":{"required":["LOSTARK_API_TOKEN"]}}');
    writeFileSync(unsafe, '{"LOSTARK_API_TOKEN":"literal-value"}');

    expect(() => assertNoLiteralSecretAssignments([safe])).not.toThrow();
    expect(() => assertNoLiteralSecretAssignments([unsafe])).toThrow('literal secret assignment found in Worker config');
  });
});
