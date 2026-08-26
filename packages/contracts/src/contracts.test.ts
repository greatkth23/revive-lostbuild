import { describe, expect, expectTypeOf, it } from 'vitest';
import { z } from 'zod';
import {
  apiEnvelopeSchema,
  buildPatchSchema,
  buildSnapshotSchema,
  characterLoadDataSchema,
  decimalStringSchema,
  skillDamageResultSchema,
  simulationDataSchema,
  weatherArtistCatalogSchema,
  warningSchema,
  type BuildSnapshot,
  type DecimalString
} from './index.js';

describe('build patch contract', () => {
  it('accepts a catalog-backed section enabled state', () => {
    // Break caught: simulations cannot represent a validated nonnumeric setting change.
    const patch = { schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: false };

    expect(buildPatchSchema.parse(patch)).toEqual(patch);
    expect(() => buildPatchSchema.parse({ ...patch, enabled: 'false' })).toThrow();
  });

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
    expect(buildPatchSchema.parse(patch)).toEqual(patch);
    expect(() => buildPatchSchema.parse({ ...patch, schemaVersion: undefined })).toThrow();
    expect(warningSchema.parse(warning).schemaVersion).toBe('1');
    expect(apiEnvelopeSchema(z.string()).parse({ schemaVersion: '1', ok: true, data: 'ready', warnings: [warning] }).schemaVersion).toBe('1');
  });
});

describe('decimal-string contracts', () => {
  it('keeps calculated numeric boundaries as strings and rejects JSON numbers', () => {
    expectTypeOf<BuildSnapshot['calculatedAttackPower']>().toEqualTypeOf<DecimalString>();

    expect(decimalStringSchema.parse('123456.789')).toBe('123456.789');
    expect(() => decimalStringSchema.parse(123456.789)).toThrow();
  });

  it('requires normalized endpoint sections on a serialized build snapshot', () => {
    const headerOnlySnapshot = {
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

    expect(() => buildSnapshotSchema.parse(headerOnlySnapshot)).toThrow();
  });
});

describe('web response contracts', () => {
  it('preserves the typed calculation breakdown through runtime parsing', () => {
    // Break caught: Zod strips calculator checkpoints before the Worker can transport them to the UI.
    const result = {
      schemaVersion: '1', skillId: 'thunderstorm', nonCriticalDamage: '1', criticalDamage: '2', expectedDamage: '1.5', criticalRate: '0.5', criticalMultiplier: '2', hits: [], rationale: [],
      checkpoints: {
        attackPower: {
          equipmentMainStat: '100', accountMainStatFlat: '10', baseMainStat: '110', avatarMainStatPercent: '0.08', petMainStatPercent: '0.01', finalMainStat: '119.9',
          baseWeaponAttack: '200', equipmentWeaponAttackFlat: '1', arkGridWeaponAttackFlat: '2', weaponAttackSubtotal: '203', equipmentWeaponAttackPercent: '0.03', karmaWeaponAttackPercent: '0.01', arkGridWeaponAttackPercent: '0.02', weaponAttackPercent: '0.06', finalWeaponAttack: '215.18',
          rootAttackPower: '65.57', armletBaseAttackFlat: '3', gemsBaseAttackPercent: '0.01', stoneBaseAttackPercent: '0.02', equipmentBaseAttackPercent: '0.03', baseAttackPercent: '0.06', afterBaseAttackPercent: '72.47',
          equipmentAttackPowerFlat: '4', arkGridAttackPowerFlat: '5', attackPowerFlat: '9', equipmentAttackPowerPercent: '0.01', adrenalineAttackPowerPercent: '0.02', arkGridAttackPowerPercent: '0.03', attackPowerPercent: '0.06',
          profileAttackPower: '70', final: '86.36', usedForDamage: '86.36', usedForDamageSource: 'CALCULATED_OFFICIAL'
        },
        motionCoefficients: ['1'],
        criticalRate: { components: [{ label: '치명 스탯', value: '0.3' }], result: '0.5' },
        criticalMultiplier: { additiveComponents: [{ label: '기본 치명타 피해', value: '2' }], additiveResult: '2', multiplicativeComponents: [{ label: '회심', value: '1' }], result: '2' },
        selectedTripods: [],
        regularGem: { damagePercent: '0', cooldownReductionPercent: '0' },
        directional: { tag: 'NON_DIRECTIONAL', label: '비방향성', success: false, applied: false, damagePercent: '0', criticalRate: '0' },
        arkPassive: { appliedEffects: [{ name: '바람의 길', category: 'skillDamage', value: '0.1' }] },
        arkGrid: { appliedFactors: [], repeatedPointMultiplier: '1', commonDamageMultiplier: '2' },
        tripodDamageMultiplier: '1', embeddedTripodEffects: []
      }
    };

    expect(skillDamageResultSchema.parse(result).checkpoints).toEqual(result.checkpoints);
    expect(() => skillDamageResultSchema.parse({ ...result, schemaVersion: undefined })).toThrow();
  });

  it('rejects incomplete catalog, load, and simulation success data before a client dereferences it', () => {
    // Break caught: fragment guards let malformed 200 responses crash the editor or silently format missing values as zero.
    expect(() => weatherArtistCatalogSchema.parse({ schemaVersion: '1', version: 'v', skills: [{ id: 'x' }], editableSections: [], equipmentGrowth: {} })).toThrow();
    expect(() => characterLoadDataSchema.parse({ cacheHit: 'false', snapshot: {}, baseline: [] })).toThrow();
    expect(() => simulationDataSchema.parse({ schemaVersion: '1', snapshotId: 'id', patches: [{ kind: 'reset-section' }], baseline: [], candidate: [] })).toThrow();
  });
});
