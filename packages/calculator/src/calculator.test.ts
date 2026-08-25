import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';
import { skillDamageResultSchema } from '@weather-artist/contracts';
import {
  calculateAllSkillDamage,
  calculateAttackPower,
  calculateSkillDamage,
  directionalAttackBonus,
  parseBuildSnapshot
} from './index.js';

const rawFixturePath = new URL(
  '../../../api-chatgpt-conversation-6a6309ab-7de4-8342/outputs/봄날꽃씨_우레바람_current-v2.7.2_api_raw.json',
  import.meta.url
);

function snapshot() {
  return parseBuildSnapshot(JSON.parse(readFileSync(rawFixturePath, 'utf8')));
}

const pythonGolden = {
  thunderstorm: {
    nonCriticalDamage: '583971628', criticalDamage: '1762610564', expectedDamage: '1713343456',
    criticalMultiplier: '3.0183154064',
    hits: [['최대 홀딩', '583971628', '1762610564', '1713343456']]
  },
  'space-cutting': {
    nonCriticalDamage: '427626447', criticalDamage: '1290711496', expectedDamage: '1254634541',
    criticalMultiplier: '3.0183154064',
    hits: [
      ['1타', '128284705', '387203703', '376380889'],
      ['2타', '299341742', '903507792', '878253651']
    ]
  },
  'piercing-wind': {
    nonCriticalDamage: '316438287', criticalDamage: '955110558', expectedDamage: '928414057',
    criticalMultiplier: '3.0183154064',
    hits: [['전체 타격', '316438287', '955110558', '928414057']]
  },
  'raging-blizzard': {
    nonCriticalDamage: '168176514', criticalDamage: '915718688', expectedDamage: '884471425',
    criticalMultiplier: '5.4449855264',
    hits: [['전체 타격', '168176514', '915718688', '884471425']]
  },
  'sweeping-strike': {
    nonCriticalDamage: '159445441', criticalDamage: '812903623', expectedDamage: '785589071',
    criticalMultiplier: '5.0983183664',
    hits: [
      ['1타', '24576750', '125300096', '121089861'],
      ['2타', '57269889', '291980130', '282169242'],
      ['3타(공간베기)', '77598801', '395623396', '382329968']
    ]
  },
  'tornado-walk': {
    nonCriticalDamage: '269437847', criticalDamage: '813248405', expectedDamage: '790517123',
    criticalMultiplier: '3.0183154064',
    hits: [
      ['1타', '188531809', '569048466', '553142869'],
      ['2타', '80906037', '244199939', '237374253']
    ]
  }
} as const;

describe('current-v2.7.2 damage parity', () => {
  test('reconstructs and uses the official calculated attack-power checkpoint at precision 40', () => {
    // Break caught: using profiles.Stats[공격력], dropping karma, or rounding an intermediate stage.
    const parsed = snapshot();
    expect(calculateAttackPower(parsed).final).toBe('258720.5038308918678085116909739914291229');
    expect(parsed.calculatedAttackPower).toBe('258720.5038308918678085116909739914291229');
    expect(calculateAttackPower(parsed)).toMatchObject({
      finalMainStat: '817450.95',
      finalWeaponAttack: '274541.568',
      karmaWeaponAttackPercent: '0.028',
      profileAttackPower: '236442',
      usedForDamage: '258720.5038308918678085116909739914291229'
    });
  });

  test.each(Object.entries(pythonGolden))('%s matches Python cast totals and every independently floored hit', (skillId, golden) => {
    // Break caught: any multiplier ordering/scope drift or flooring the cast before its hits.
    const result = calculateSkillDamage(snapshot(), skillId);

    expect(skillDamageResultSchema.safeParse(result).success).toBe(true);
    expect(result).toMatchObject({
      schemaVersion: '1',
      skillId,
      nonCriticalDamage: golden.nonCriticalDamage,
      criticalDamage: golden.criticalDamage,
      expectedDamage: golden.expectedDamage,
      criticalRate: '0.9582',
      criticalMultiplier: golden.criticalMultiplier
    });
    expect(result.hits.map((hit) => [
      hit.hitName,
      hit.nonCriticalDamage,
      hit.criticalDamage,
      hit.expectedDamage
    ])).toEqual(golden.hits);
  });

  test('applies regular damage gems only to their own skill and retains cooldown as non-cast provenance', () => {
    // Break caught: applying a gem globally, summing duplicates, or treating cooldown reduction as cast damage.
    const results = calculateAllSkillDamage(snapshot());
    expect(Object.fromEntries(results.map((result) => [result.skillId, [
      result.checkpoints.regularGemDamagePercent,
      result.checkpoints.regularGemCooldownReductionPercent
    ]]))).toEqual({
      thunderstorm: ['0', '0'],
      'space-cutting': ['0', '0'],
      'piercing-wind': ['0.4', '0.22'],
      'raging-blizzard': ['0.4', '0.22'],
      'sweeping-strike': ['0.4', '0.22'],
      'tornado-walk': ['0.4', '0.22']
    });
  });

  test('falls back to the current-v2.7.2 Raid Captain coefficient when its live description has no number', () => {
    // Break caught: a present engraving with a parsed zero coefficient silently loses its damage multiplier.
    const parsed = snapshot();
    const baseline = calculateSkillDamage(parsed, 'thunderstorm').expectedDamage;
    parsed.build.engravings.effects['돌격대장']!.raidCaptainCoefficient = '0';
    expect(calculateSkillDamage(parsed, 'thunderstorm').expectedDamage).toBe(baseline);
  });

  test('uses umbrella, hyper-awakening, enlightenment, and single-skill scopes independently', () => {
    // Break caught: applying Space Cutting or hyper-awakening effects to every umbrella skill.
    const results = calculateAllSkillDamage(snapshot());
    const scopes = Object.fromEntries(results.map((result) => [
      result.skillId,
      result.checkpoints.appliedSkillDamageEffects
    ]));
    expect(scopes).toEqual({
      thunderstorm: ['바람의 길', '풀려난 힘', '단련된 가르기'],
      'space-cutting': ['바람의 길', '공간 가르기'],
      'piercing-wind': ['바람의 길'],
      'raging-blizzard': ['바람의 길'],
      'sweeping-strike': ['바람의 길'],
      'tornado-walk': ['바람의 길']
    });
    expect(results.find((result) => result.skillId === 'space-cutting')?.checkpoints.motionCoefficients).toEqual(['51.77044', '120.802']);
  });

  test('does not multiply Molachigi Space Slash after its 94.8% additional hit is embedded in the motion model', () => {
    // Break caught: the embedded third hit is multiplied a second time by 1.948.
    const result = calculateSkillDamage(snapshot(), 'sweeping-strike');
    expect(result.checkpoints.tripodDamageMultiplier).toBe('1.6');
    expect(result.checkpoints.embeddedTripodEffects).toEqual([
      expect.objectContaining({ tripodName: '공간베기', percent: '0.948', applicationMode: 'EMBEDDED_MOTION_HIT' })
    ]);
  });

  test('applies each active 18P, 19P, and 20P Ark Grid factor as a repeated multiplier', () => {
    // Break caught: adding three 0.2% thresholds into one 0.6% multiplier.
    const result = calculateSkillDamage(snapshot(), 'thunderstorm');
    expect(result.checkpoints.appliedArkGridFactors.filter((factor) =>
      factor.coreName.includes('우산의 춤') && factor.value === '0.002'
    ).map((factor) => factor.requiredPoints)).toEqual([18, 19, 20]);
    expect(result.checkpoints.repeatedUmbrellaPointMultiplier).toBe('1.006012008');
  });
});

describe('directional attack rule', () => {
  test('applies back/head success bonuses and removes them on miss or NON_DIRECTIONAL tags', () => {
    // Break caught: inheriting direction, retaining a missed bonus, or mixing head and back rules.
    expect(directionalAttackBonus('BACK_ATTACK', true)).toEqual({
      tag: 'BACK_ATTACK', label: '백 어택', success: true, applied: true, damagePercent: '0.05', criticalRate: '0.1'
    });
    expect(directionalAttackBonus('FRONTAL_ATTACK', true)).toEqual({
      tag: 'FRONTAL_ATTACK', label: '헤드 어택', success: true, applied: true, damagePercent: '0.2', criticalRate: '0'
    });
    expect(directionalAttackBonus('BACK_ATTACK', false)).toMatchObject({ applied: false, damagePercent: '0', criticalRate: '0' });
    expect(directionalAttackBonus('NON_DIRECTIONAL', true)).toMatchObject({ applied: false, damagePercent: '0', criticalRate: '0' });
  });

  test('all six catalog skills remain unchanged when directional success is toggled', () => {
    // Break caught: assigning an accidental head/back tag to a supported Weather Artist skill.
    const parsed = snapshot();
    for (const skillId of Object.keys(pythonGolden)) {
      expect(calculateSkillDamage(parsed, skillId, { directionalSuccess: false }).expectedDamage)
        .toBe(calculateSkillDamage(parsed, skillId, { directionalSuccess: true }).expectedDamage);
    }
  });
});
