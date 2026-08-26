import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, test } from 'vitest';

describe('local simulator preview', () => {
  test('starts as a vite-node script but remains inert when imported by Vitest', async () => {
    // Break caught: vite-node exits immediately because its argv does not match import.meta.url.
    const previewModule = await import('../../../scripts/local-preview');
    expect(previewModule.shouldStartLocalPreview({})).toBe(true);
    expect(previewModule.shouldStartLocalPreview({ VITEST: 'true' })).toBe(false);
  });

  test('recomputes the stored snapshot instead of serving display-only E2E damage', async () => {
    // Break caught: the inspection server exposes the E2E sentinel 1,000,000,000.125 as damage.
    const modulePath = '../../../scripts/local-preview';
    const previewModule = await import(modulePath).catch(() => undefined);
    expect(previewModule).toBeDefined();

    const fixture = JSON.parse(readFileSync(resolve('scripts/fixtures/weather-artist-e2e.json'), 'utf8'));
    const load = previewModule!.buildLocalLoadData(fixture);

    expect(load.baseline.map((result: { skillId: string; expectedDamage: string }) => [result.skillId, result.expectedDamage])).toEqual([
      ['thunderstorm', '1646989906'],
      ['space-cutting', '1206045651'],
      ['piercing-wind', '892458879'],
      ['raging-blizzard', '850218036'],
      ['sweeping-strike', '755165152'],
      ['tornado-walk', '759902352']
    ]);
  });

  test('recalculates a patched candidate instead of serving the E2E candidate sentinel', async () => {
    // Break caught: changing a section returns the canned 800,000,000.125 E2E value.
    const previewModule = await import('../../../scripts/local-preview');
    expect(previewModule.buildLocalSimulationData).toBeDefined();
    const fixture = JSON.parse(readFileSync(resolve('scripts/fixtures/weather-artist-e2e.json'), 'utf8'));
    const patches = [{ schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: false }] as const;
    const simulation = previewModule.buildLocalSimulationData(fixture, patches, {
      schemaVersion: '1',
      id: 'default',
      bossConditionId: 'default',
      directionalSuccessBySkill: {}
    });
    const baseline = simulation.baseline.find((result: { skillId: string }) => result.skillId === 'thunderstorm');
    const candidate = simulation.candidate.find((result: { skillId: string }) => result.skillId === 'thunderstorm');

    expect(simulation.patches).toEqual(patches);
    expect(baseline?.expectedDamage).toBe('1646989906');
    expect(candidate?.expectedDamage).not.toBe('800000000.125');
    expect(Number(candidate?.expectedDamage)).toBeLessThan(Number(baseline?.expectedDamage));
  });

  test('serves the real calculated load and simulation envelopes over HTTP', async () => {
    // Break caught: localhost is wired to the canned E2E baseline/candidate instead of the calculator.
    const previewModule = await import('../../../scripts/local-preview');
    expect(previewModule.createLocalPreviewServer).toBeDefined();
    const fixture = JSON.parse(readFileSync(resolve('scripts/fixtures/weather-artist-e2e.json'), 'utf8'));
    const server = previewModule.createLocalPreviewServer({
      fixture,
      staticRoot: resolve('apps/web/dist')
    });
    await new Promise<void>((resolveListen) => server.listen(0, '127.0.0.1', resolveListen));
    const address = server.address();
    if (!address || typeof address === 'string') throw new Error('preview server did not expose a TCP port');
    const origin = `http://127.0.0.1:${address.port}`;
    try {
      const loadResponse = await fetch(`${origin}/api/v1/characters/load`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'x-anonymous-client-id': 'vitest-local-preview' },
        body: JSON.stringify({ characterName: '봄날꽃씨', forceRefresh: false })
      });
      const load = await loadResponse.json() as any;
      expect(load.data.baseline[0].expectedDamage).toBe('1646989906');

      const simulationResponse = await fetch(`${origin}/api/v1/simulations`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'x-anonymous-client-id': 'vitest-local-preview' },
        body: JSON.stringify({
          patches: [{ schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: false }],
          scenario: { schemaVersion: '1', id: 'default', bossConditionId: 'default', directionalSuccessBySkill: {} }
        })
      });
      const simulation = await simulationResponse.json() as any;
      expect(simulation.data.baseline[0].expectedDamage).toBe('1646989906');
      expect(simulation.data.candidate[0].expectedDamage).not.toBe('800000000.125');
    } finally {
      await new Promise<void>((resolveClose, rejectClose) => server.close((error: Error | undefined) => error ? rejectClose(error) : resolveClose()));
    }
  });
});
