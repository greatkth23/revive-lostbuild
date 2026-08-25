import { describe, expect, expectTypeOf, it } from 'vitest';
import {
  buildPatchSchema,
  buildSnapshotSchema,
  type BuildSnapshot,
  type DecimalString
} from './index.js';

describe('build patch contract', () => {
  it('accepts a catalog-targeted patch and rejects an unknown command shape', () => {
    const validPatch = {
      kind: 'set-skill-level',
      skillId: 'space-cutting',
      level: 12
    };

    expect(buildPatchSchema.parse(validPatch)).toEqual(validPatch);
    expect(() => buildPatchSchema.parse({ kind: 'set-skill-level', level: 12 })).toThrow();
    expect(() => buildPatchSchema.parse({ kind: 'invented-command' })).toThrow();
  });
});

describe('decimal-string contracts', () => {
  it('keeps calculated numeric boundaries as strings and rejects JSON numbers', () => {
    expectTypeOf<BuildSnapshot['calculatedAttackPower']>().toEqualTypeOf<DecimalString>();

    const snapshot = {
      schemaVersion: '1',
      snapshotId: 'snapshot-1',
      characterName: '봄날꽃씨',
      classId: 'weather-artist',
      calculatorVersion: 'current-v2.7.2',
      parserVersion: '1',
      catalogVersion: '1',
      calculatedAttackPower: '123456.789',
      warnings: []
    };

    expect(buildSnapshotSchema.parse(snapshot).calculatedAttackPower).toBe('123456.789');
    expect(() => buildSnapshotSchema.parse({ ...snapshot, calculatedAttackPower: 123456.789 })).toThrow();
  });
});
