import { describe, expect, expectTypeOf, it } from 'vitest';
import { z } from 'zod';
import {
  apiEnvelopeSchema,
  buildPatchSchema,
  buildSnapshotSchema,
  skillDamageResultSchema,
  warningSchema,
  type BuildSnapshot,
  type DecimalString
} from './index.js';

describe('build patch contract', () => {
  it('accepts a catalog-targeted patch and rejects an unknown command shape', () => {
    const validPatch = {
      schemaVersion: '1',
      kind: 'set-skill-level',
      skillId: 'space-cutting',
      level: 12
    };

    expect(buildPatchSchema.parse(validPatch)).toEqual(validPatch);
    expect(() => buildPatchSchema.parse({ kind: 'set-skill-level', level: 12 })).toThrow();
    expect(() => buildPatchSchema.parse({ kind: 'invented-command' })).toThrow();
  });

  it('requires a contract version on every persisted patch and serialized response type', () => {
    const patch = { schemaVersion: '1', kind: 'set-skill-level', skillId: 'space-cutting', level: 12 };
    const warning = { schemaVersion: '1', code: 'INCOMPLETE', severity: 'incomplete', path: 'items.0', message: '검증 불완전' };
    const result = {
      schemaVersion: '1',
      skillId: 'space-cutting',
      nonCriticalDamage: '1',
      criticalDamage: '2',
      expectedDamage: '1.5',
      criticalRate: '0.5',
      criticalMultiplier: '2',
      hits: [],
      rationale: []
    };

    expect(buildPatchSchema.parse(patch)).toEqual(patch);
    expect(() => buildPatchSchema.parse({ ...patch, schemaVersion: undefined })).toThrow();
    expect(warningSchema.parse(warning).schemaVersion).toBe('1');
    expect(skillDamageResultSchema.parse(result).schemaVersion).toBe('1');
    expect(apiEnvelopeSchema(z.string()).parse({ schemaVersion: '1', ok: true, data: 'ready', warnings: [warning] }).schemaVersion).toBe('1');
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
