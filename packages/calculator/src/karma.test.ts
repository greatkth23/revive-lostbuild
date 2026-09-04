import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';
import { calculateAllSkillDamage, parseBuildSnapshot } from './index.js';
import { dec } from './decimal.js';

const fixture = JSON.parse(readFileSync(new URL(
  '../../../api-chatgpt-conversation-6a6309ab-7de4-8342/outputs/봄날꽃씨_우레바람_current-v2.7.2_api_raw.json',
  import.meta.url
), 'utf8'));

function parseKarma(description: string, tooltip?: string) {
  const raw = structuredClone(fixture);
  raw.responses.arkPassive.Points[0] = {
    Name: '진화', Value: 140, Description: description, Tooltip: tooltip
  };
  return parseBuildSnapshot(raw);
}

// All 35 rank/level combinations supplied by the user, including both sides of promotions.
const rankRanges = [
  [1, 1, 5, '0.01'], [2, 5, 9, '0.02'], [3, 9, 13, '0.03'],
  [4, 13, 17, '0.04'], [5, 17, 21, '0.05'], [6, 21, 30, '0.06']
] as const;
const table = rankRanges.flatMap(([rank, first, last, damage]) =>
  Array.from({ length: last - first + 1 }, (_, offset) => ({ rank, level: first + offset, damage }))
);

describe('user-confirmed evolution karma rules', () => {
  test.each(table)('$rank rank / $level level gives $damage evolution damage', ({ rank, level, damage }) => {
    const parsed = parseKarma(`${rank}랭크 ${level}레벨`);
    expect(parsed.build.arkPassive.karmaEvolutionDamage).toBe(damage);
    expect(parsed.build.arkPassive.points[0]?.karmaLevel).toBe(level);
    expect(parsed.build.arkPassive.karmaWeaponAttackPercent).toBe('0.028');
    expect(parsed.warnings.some(({ code }) => code.startsWith('KARMA_EVOLUTION'))).toBe(false);
    expect(parsed.build.provenance).toContainEqual(expect.objectContaining({
      label: '진화 카르마 진화형 피해', value: damage,
      sourceType: 'OFFICIAL_API+USER_VERIFIED_RULE', parsed: true, applied: true
    }));
  });

  test.each(['카르마 5레벨', '카르마 21레벨', '카르마', '7랭크 30레벨'])('%s never defaults to 6%% or infers rank from level', (description) => {
    const parsed = parseKarma(description);
    expect(parsed.build.arkPassive.karmaEvolutionDamage).toBe('0');
    expect(parsed.warnings).toContainEqual(expect.objectContaining({ code: 'KARMA_EVOLUTION_UNKNOWN', severity: 'incomplete' }));
  });

  test('accepts markup and the Tooltip field when Description is empty', () => {
    const parsed = parseKarma('', '<font>랭크: 2</font><br>5레벨');
    expect(parsed.build.arkPassive.karmaEvolutionDamage).toBe('0.02');
    expect(parsed.build.provenance).toContainEqual(expect.objectContaining({
      label: '진화 카르마 진화형 피해', path: 'arkPassive.Points[0].Tooltip', value: '0.02'
    }));
  });

  test.each(['0', '2'])('retains an explicit %s%% tooltip when rank is absent', (damage) => {
    const parsed = parseKarma(`카르마 진화형 피해가 ${damage}% 증가`);
    expect(parsed.build.arkPassive.karmaEvolutionDamage).toBe(dec(damage).div(100).toString());
    expect(parsed.warnings.some(({ code }) => code.startsWith('KARMA_EVOLUTION'))).toBe(false);
  });

  test('rank takes precedence over a conflicting tooltip without double counting', () => {
    const parsed = parseKarma('2랭크 5레벨 진화형 피해가 6% 증가, 낙인력 2% 증가, 최대 생명력 2000 증가');
    expect(parsed.build.arkPassive.karmaEvolutionDamage).toBe('0.02');
    expect(parsed.warnings).toContainEqual(expect.objectContaining({ code: 'KARMA_EVOLUTION_CONFLICT' }));
  });

  test.each(rankRanges)('rank %i adds to existing evolution damage in every skill', (rank, level, _last, damage) => {
    const baseline = calculateAllSkillDamage(parseKarma('0랭크 0레벨'));
    const changed = calculateAllSkillDamage(parseKarma(`${rank}랭크 ${level}레벨 낙인력 ${rank}% 최대 생명력 ${level * 400}`));
    for (const [index, result] of changed.entries()) {
      const before = baseline[index]!;
      const existingEvolution = before.checkpoints.arkPassive.appliedEffects
        .filter(({ category }) => category === 'evolutionDamage')
        .reduce((sum, effect) => sum.plus(effect.value), dec(0));
      const expectedRatio = dec(1).plus(existingEvolution).plus(damage).div(dec(1).plus(existingEvolution));
      expect(result.checkpoints.arkPassive.appliedEffects.filter(({ name }) => name === '진화 카르마'))
        .toEqual([{ name: '진화 카르마', category: 'evolutionDamage', value: damage }]);
      for (const key of ['nonCriticalDamage', 'criticalDamage', 'expectedDamage'] as const) {
        // Each hit is floored separately; account only for that integer-rounding error.
        expect(dec(result[key]).minus(dec(before[key]).times(expectedRatio)).abs().toNumber())
          .toBeLessThanOrEqual(result.hits.length * 2);
        expect(dec(result[key]).gt(before[key])).toBe(true);
      }
    }
  });
});
