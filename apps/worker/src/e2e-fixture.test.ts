import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';

const fixturePath = new URL('../../../scripts/fixtures/weather-artist-e2e.json', import.meta.url);
const fixture = JSON.parse(readFileSync(fixturePath, 'utf8')) as {
  catalog: { skills: Array<{ id: string }> };
  load: { snapshot: { snapshotId: string }; baseline: DamageResult[] };
  simulation: { snapshotId: string; baseline: DamageResult[]; candidate: DamageResult[] };
};
type DamageResult = {
  nonCriticalDamage: string;
  criticalDamage: string;
  expectedDamage: string;
  hits: Array<{ nonCriticalDamage: string; criticalDamage: string; expectedDamage: string }>;
};

describe('browser release fixture', () => {
  test('uses one Worker-compatible opaque snapshot UUID', () => {
    const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

    expect(fixture.load.snapshot.snapshotId).toMatch(uuid);
    expect(fixture.simulation.snapshotId).toBe(fixture.load.snapshot.snapshotId);
  });

  test('uses long internally consistent values for every supported skill and hit', () => {
    expect(fixture.load.baseline).toHaveLength(fixture.catalog.skills.length);
    expect(fixture.simulation.baseline.map((result) => result.expectedDamage))
      .toEqual(Array(fixture.catalog.skills.length).fill('1000000000.125'));
    expect(fixture.simulation.candidate.map((result) => result.expectedDamage))
      .toEqual(Array(fixture.catalog.skills.length).fill('800000000.125'));
    for (const [results, expected] of [
      [fixture.load.baseline, '1000000000.125'],
      [fixture.simulation.baseline, '1000000000.125'],
      [fixture.simulation.candidate, '800000000.125']
    ] as const) {
      expect(results.every((result) => result.nonCriticalDamage === expected
        && result.criticalDamage === expected
        && result.expectedDamage === expected
        && result.hits.every((hit) => hit.nonCriticalDamage === expected
          && hit.criticalDamage === expected
          && hit.expectedDamage === expected))).toBe(true);
    }
  });
});
