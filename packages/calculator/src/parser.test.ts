import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';
import { buildSnapshotSchema } from '@weather-artist/contracts';
import {
  parseBuildSnapshot,
  resolveArkGridGradeValues,
  tooltipToText
} from './index.js';

const rawFixturePath = new URL(
  '../../../api-chatgpt-conversation-6a6309ab-7de4-8342/outputs/봄날꽃씨_우레바람_current-v2.7.2_api_raw.json',
  import.meta.url
);

function loadRawFixture(): unknown {
  return JSON.parse(readFileSync(rawFixturePath, 'utf8'));
}

describe('Weather Artist raw endpoint parser', () => {
  test('normalizes all nine endpoint payloads into the versioned snapshot contract', () => {
    // Break caught: omitting one endpoint or leaking numeric values as JS numbers.
    const snapshot = parseBuildSnapshot(loadRawFixture());

    expect(buildSnapshotSchema.safeParse(snapshot).success).toBe(true);
    expect(snapshot.schemaVersion).toBe('1');
    expect(snapshot.characterName).toBe('봄날꽃씨');
    expect(snapshot.build.endpointSources).toEqual([
      'profiles',
      'equipment',
      'avatars',
      'combatSkills',
      'engravings',
      'cards',
      'gems',
      'arkPassive',
      'arkGrid'
    ]);
    expect(snapshot.build.profile.className).toBe('기상술사');
    expect(snapshot.build.equipment.items).toHaveLength(17);
    expect(snapshot.build.avatars.items).toHaveLength(11);
    expect(snapshot.build.gems.items).toHaveLength(11);
    expect((snapshot.build.arkPassive as typeof snapshot.build.arkPassive & { points: unknown[] }).points).toHaveLength(3);
    expect(snapshot.build.combatSkills.skillNames).toHaveLength(22);
    expect(snapshot.build.arkGrid.cores).toHaveLength(6);
    const arkGrid = snapshot.build.arkGrid as typeof snapshot.build.arkGrid & {
      activeGems: Array<{ path: string; values: Record<string, string> }>;
      activeAggregateEffects: Array<{ path: string; name: string; values: Record<string, string> }>;
    };
    expect(arkGrid.activeGems).toHaveLength(24);
    expect(arkGrid.activeGems[0]).toMatchObject({
      path: 'arkGrid.Slots[0].Gems[0]',
      values: { additionalDamagePercent: '0.004' }
    });
    expect(arkGrid.activeAggregateEffects).toHaveLength(3);
    expect(arkGrid.activeAggregateEffects.at(-1)).toMatchObject({
      path: 'arkGrid.Effects[4]',
      name: '보스 피해',
      values: { bossDamagePercent: '0.0425' }
    });
  });

  test('parses equipment, armlet, accessory, avatar, pet, engraving, stone, and card checkpoints', () => {
    // Break caught: collapsing armlet base attack into final attack or skipping non-skill sections.
    const { build } = parseBuildSnapshot(loadRawFixture());

    expect(build.equipment).toMatchObject({
      mainStat: '747822',
      baseWeaponAttack: '241367',
      weaponAttackFlat: '10969',
      weaponAttackPercent: '0.06',
      baseAttackPowerFlat: '2030',
      attackPowerPercent: '0.019',
      weaponAdditionalDamage: '0.3',
      necklaceAdditionalDamage: '0.026',
      necklaceDamageToEnemy: '0.012',
      criticalRate: '0.073',
      criticalDamage: '0.132',
      braceletCriticalHitDamage: '0.015'
    });
    expect(build.equipment.items.find((item) => item.type === '완갑')?.values.baseAttackPowerFlat).toBe('2030');
    expect(build.equipment.items.some((item) => item.type === '팔찌')).toBe(true);
    expect(build.avatars.mainStatPercent).toBe('0.08');
    expect(build.pet).toMatchObject({ mainStatPercent: '0.01', additionalDamagePercent: '0.01' });
    expect(build.engravings.stoneLevelTotal).toBe(5);
    expect(build.engravings.stoneBaseAttackPercent).toBe('0.015');
    expect(build.engravings.effects['아드레날린']).toMatchObject({
      attackPowerPercent: '0.1038',
      criticalRate: '0.2'
    });
    expect(build.cards.damagePercent).toBe('0.15');
  });

  test('derives enlightenment karma weapon attack and regular skill gems', () => {
    // Break caught: treating the karma point Value as percent or double-counting duplicate skill gems.
    const { build } = parseBuildSnapshot(loadRawFixture());

    expect(build.arkPassive.karmaWeaponAttackPercent).toBe('0.028');
    expect(build.gems.baseAttackPercent).toBe('0.104');
    expect(build.gems.skillEffects.filter((effect) => effect.skillName === '바람송곳')).toEqual([
      expect.objectContaining({ effectType: 'damage', value: '0.4' }),
      expect.objectContaining({ effectType: 'cooldownReduction', value: '0.22' })
    ]);
  });

  test('uses ArkGrid Effects aggregate values instead of adding the same active-gem effects twice', () => {
    // Break caught: gem + Effects[] double counting raises all three base categories.
    const { arkGrid } = parseBuildSnapshot(loadRawFixture()).build;

    expect(arkGrid.gemEffects).toEqual({
      attackPowerPercent: '0.0139',
      additionalDamagePercent: '0.0416',
      bossDamagePercent: '0.042'
    });
    expect(arkGrid.aggregateEffects).toEqual({
      attackPowerPercent: '0.0143',
      additionalDamagePercent: '0.042',
      bossDamagePercent: '0.0425'
    });
    expect(arkGrid.effectiveBaseEffects).toEqual(arkGrid.aggregateEffects);
    expect(arkGrid.attackPowerPercent).toBe('0.0411');
  });

  test('selects the relic or ancient side of slash values and keeps 18P, 19P, and 20P factors separate', () => {
    // Break caught: choosing the wrong slash branch or summing repeated multiplicative thresholds.
    expect(resolveArkGridGradeValues('피해량이 8 / 18% 증가', '유물')).toBe('피해량이 8% 증가');
    expect(resolveArkGridGradeValues('피해량이 8 / 18% 증가', '고대')).toBe('피해량이 18% 증가');

    const factors = parseBuildSnapshot(loadRawFixture()).build.arkGrid.coreDamageFactors;
    const repeated = factors.filter(
      (factor) => factor.coreName.includes('우산의 춤')
        && factor.category === 'skillDamagePercent'
        && factor.value === '0.002'
    );
    expect(repeated.map((factor) => factor.requiredPoints)).toEqual([18, 19, 20]);
  });

  test('retains selected tripod effects and marks the additional Space Slash hit as embedded provenance', () => {
    // Break caught: dropping the official tooltip or later multiplying the 94.8% embedded hit again.
    const selected = parseBuildSnapshot(loadRawFixture()).build.combatSkills.selectedTripods;
    const spaceSlash = selected.find((tripod) => tripod.skillName === '몰아치기' && tripod.name === '공간베기');

    expect(spaceSlash?.damageEffects).toContainEqual({
      type: 'ADDITIONAL_ATTACK',
      label: '추가 공격 피해',
      percent: '0.948',
      multiplier: '1.948',
      applicationMode: 'EMBEDDED_MOTION_HIT'
    });
  });

  test('returns a path-bearing incomplete warning for an active damage tooltip it cannot classify', () => {
    // Break caught: silently treating an unknown damage tooltip as a zero-valued effect.
    const raw = structuredClone(loadRawFixture()) as {
      responses: { arkGrid: { Slots: Array<{ Gems?: unknown[] }> } };
    };
    raw.responses.arkGrid.Slots[0]!.Gems ??= [];
    raw.responses.arkGrid.Slots[0]!.Gems.push({
      Index: 99,
      IsActive: true,
      Grade: '고대',
      Tooltip: JSON.stringify({ Element_000: { value: '알 수 없는 개인 피해 증폭 효과' } })
    });

    const snapshot = parseBuildSnapshot(raw);
    expect(snapshot.warnings).toContainEqual(expect.objectContaining({
      code: 'UNPARSED_DAMAGE_TOOLTIP',
      severity: 'incomplete',
      path: 'arkGrid.Slots[0].Gems[4].Tooltip'
    }));
  });

  test('preserves fallback and calculated-attack provenance as structured path-bearing warnings', () => {
    // Break caught: dropping Python fallback/mismatch warnings while normalizing the snapshot.
    const parsed = parseBuildSnapshot(loadRawFixture());
    expect(parsed.warnings.map(({ code, path }) => ({ code, path }))).toEqual([
      { code: 'KARMA_EVOLUTION_FALLBACK', path: 'arkPassive.Points[0]' },
      { code: 'FIXED_EXPEDITION_STAT_MISMATCH', path: 'profiles.ExpeditionLevel' },
      { code: 'CALCULATED_ATTACK_POWER_OVERRIDE', path: 'profiles.Stats[공격력]' }
    ]);
    expect(parsed.build.provenance).toContainEqual(expect.objectContaining({
      path: 'arkPassive.Points[1].Description',
      value: '0.028',
      applied: true
    }));
  });

  test('flattens official JSON tooltips without repeating adjacent wrapper values', () => {
    // Break caught: parsing JSON syntax or duplicated wrapper strings as game tooltip content.
    const tooltip = JSON.stringify({
      Element_000: { type: 'ItemTitle', value: '공격력 +1.43%' },
      Element_001: { value: '공격력 +1.43%' },
      Element_002: { value: '<FONT>보스 피해 +4.25%</FONT><BR>적용' }
    });

    expect(tooltipToText(tooltip)).toBe('공격력 +1.43%\n보스 피해 +4.25%\n적용');
  });
});
