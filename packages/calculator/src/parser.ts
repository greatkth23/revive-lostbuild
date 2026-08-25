import type {
  BuildSnapshot,
  NormalizedBuild,
  Provenance,
  Warning
} from '@weather-artist/contracts';
import { WEATHER_ARTIST_CATALOG_VERSION } from '@weather-artist/catalog';
import { reconstructAttackPower } from './attack-power.js';
import { Decimal, dec, decimalString, percent, sum } from './decimal.js';

export const PARSER_VERSION = 'lostark-api-ts-v1';
export const ENDPOINT_SOURCES = [
  'profiles',
  'equipment',
  'avatars',
  'combatSkills',
  'engravings',
  'cards',
  'gems',
  'arkPassive',
  'arkGrid'
] as const;

type JsonObject = Record<string, unknown>;
type ParsedBuildSnapshot = Omit<BuildSnapshot, 'build'> & { build: NormalizedBuild };

interface ParseContext {
  warnings: Warning[];
  provenance: Provenance[];
}

interface ArkGridComponent {
  category: string;
  value: Decimal;
  scopeKind: 'ALL' | 'SKILL_TAG' | 'SKILL_NAMES' | 'SINGLE_CAST_EXCLUDED';
  scopeValue: string | string[];
  condition: string;
  operator: 'ADD' | 'MULTIPLY' | 'ADD_TO_PREVIOUS' | 'REPLACE';
}

const ZERO = new Decimal(0);
const ONE = new Decimal(1);
const PERCENT_NUMBER = '([0-9]+(?:\\.[0-9]+)?)\\s*%';
const PLAIN_NUMBER = '([0-9][0-9,]*(?:\\.[0-9]+)?)';
const ARKGRID_MULTIPLICATIVE = new Set([
  'generalDamagePercent',
  'bossDamagePercent',
  'skillDamagePercent',
  'criticalHitDamagePercent',
  'enemyDefenseReductionPercent'
]);
const ARKGRID_TOTAL_KEYS = [
  'attackPowerFlat',
  'attackPowerPercent',
  'weaponAttackFlat',
  'weaponAttackPercent',
  'additionalDamagePercent',
  'bossDamagePercent',
  'generalDamagePercent',
  'criticalRate',
  'criticalDamage',
  'criticalHitDamagePercent',
  'attackSpeed',
  'moveSpeed',
  'enemyDefenseReductionPercent',
  'skillDamagePercent'
] as const;
const ARKGRID_SKILL_NAMES = [
  '회오리 걸음',
  '몰아치기',
  '바람송곳',
  '칼바람',
  '여우비 기본 공격',
  '여우비',
  '소나기',
  '싹쓸바람',
  '뙤약볕',
  '센바람'
];
const SUPPORT_ARKGRID_TERMS = ['낙인력', '아군 공격력 강화', '아군 피해량 강화', '아공강', '아피강'];

const EFFECT_FALLBACKS: Record<string, Partial<Record<string, string>>> = {
  '한계 돌파': { evolutionDamage: '0.3' },
  '무한한 마력': { evolutionDamage: '0.08' },
  '혼신의 강타': { evolutionDamage: '0.02', criticalRate: '0.12' },
  '분쇄': { evolutionDamage: '0.2' },
  '풀려난 힘': { skillDamage: '0.15' },
  '바람의 길': { skillDamage: '0.024' },
  '기민함': { criticalRate: '0.12', criticalDamage: '0.48' },
  '단련된 가르기': { skillDamage: '0.75' },
  '회심': { criticalHitDamage: '0.12' }
};

function object(value: unknown): JsonObject {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as JsonObject
    : {};
}

function array(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function text(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function integer(value: unknown): number {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? Math.trunc(parsed) : 0;
}

function stripMarkup(value: string): string {
  return value
    .replaceAll('&lt;', '<')
    .replaceAll('&gt;', '>')
    .replaceAll('&amp;', '&')
    .replaceAll('&quot;', '"')
    .replaceAll('&#39;', "'")
    .replace(/<BR\s*\/?>/gi, '\n')
    .replace(/<\/?[^>]+>/g, '')
    .replaceAll('\\n', '\n')
    .replaceAll('\u00a0', ' ')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function collectTooltipStrings(value: unknown, output: string[]): void {
  if (typeof value === 'string') {
    const cleaned = stripMarkup(value);
    if (cleaned) output.push(cleaned);
    return;
  }
  if (Array.isArray(value)) {
    for (const child of value) collectTooltipStrings(child, output);
    return;
  }
  if (value !== null && typeof value === 'object') {
    for (const [key, child] of Object.entries(value)) {
      if (['type', 'key', 'slotdata', 'qualityvalue'].includes(key.toLowerCase())) continue;
      collectTooltipStrings(child, output);
    }
  }
}

export function tooltipToText(raw: unknown): string {
  if (raw === null || raw === undefined) return '';
  let parsed: unknown = raw;
  if (typeof raw === 'string') {
    try {
      parsed = JSON.parse(raw) as unknown;
    } catch {
      return stripMarkup(raw);
    }
  }
  const values: string[] = [];
  collectTooltipStrings(parsed, values);
  const withoutAdjacentDuplicates: string[] = [];
  for (const value of values) {
    if (withoutAdjacentDuplicates.at(-1) !== value) withoutAdjacentDuplicates.push(value);
  }
  return withoutAdjacentDuplicates.join('\n');
}

function matches(textValue: string, pattern: RegExp): Decimal[] {
  const flags = pattern.flags.includes('g') ? pattern.flags : `${pattern.flags}g`;
  return [...textValue.matchAll(new RegExp(pattern.source, flags))]
    .map((match) => match[1])
    .filter((value): value is string => value !== undefined)
    .map((value) => dec(value));
}

function max(values: Iterable<Decimal>): Decimal {
  let result = ZERO;
  for (const value of values) if (value.gt(result)) result = value;
  return result;
}

function sumUnique(values: Iterable<Decimal>): Decimal {
  const seen = new Set<string>();
  let result = ZERO;
  for (const value of values) {
    const key = value.toFixed();
    if (!seen.has(key)) {
      seen.add(key);
      result = result.plus(value);
    }
  }
  return result;
}

function percentMatches(textValue: string, pattern: RegExp): Decimal[] {
  return matches(textValue, pattern).map((value) => value.div(100));
}

function warning(
  context: ParseContext,
  code: string,
  severity: Warning['severity'],
  path: string,
  message: string
): void {
  if (context.warnings.some((item) => item.code === code && item.path === path && item.message === message)) return;
  context.warnings.push({ schemaVersion: '1', code, severity, path, message });
}

function provenance(
  context: ParseContext,
  path: string,
  label: string,
  value: Decimal.Value | string | number | boolean,
  options: Partial<Omit<Provenance, 'schemaVersion' | 'path' | 'label' | 'value'>> = {}
): void {
  const valueString = value instanceof Decimal
    ? decimalString(value)
    : typeof value === 'boolean'
      ? String(value)
      : String(value);
  context.provenance.push({
    schemaVersion: '1',
    sourceType: options.sourceType ?? 'OFFICIAL_API',
    path,
    label,
    value: valueString,
    parsed: options.parsed ?? true,
    eligible: options.eligible ?? true,
    applied: options.applied ?? true,
    excludedReason: options.excludedReason ?? '',
    note: options.note ?? ''
  });
}

function canonicalSkill(name: string): string {
  const compact = name.trim();
  if (compact === '우뢰바람') return '우레바람';
  if (compact === '공간가르기') return '공간 가르기';
  if (compact === '회오리걸음') return '회오리 걸음';
  return compact;
}

function parseProfile(bodyValue: unknown, context: ParseContext): NormalizedBuild['profile'] {
  const body = object(bodyValue);
  const stats = new Map<string, JsonObject>();
  for (const value of array(body.Stats)) {
    const item = object(value);
    stats.set(text(item.Type), item);
  }
  const critical = stats.get('치명') ?? {};
  const swiftness = stats.get('신속') ?? {};
  const specialization = stats.get('특화') ?? {};
  const attack = stats.get('공격력') ?? {};
  const criticalTooltip = tooltipToText(critical.Tooltip);
  const swiftnessTooltip = tooltipToText(swiftness.Tooltip);
  let criticalRate = max(percentMatches(criticalTooltip, new RegExp(`치명타\\s*적중률(?:이|은)?\\s*\\+?${PERCENT_NUMBER}`, 'i')));
  let attackSpeed = max(percentMatches(swiftnessTooltip, new RegExp(`공격\\s*속도(?:가|는)?\\s*\\+?${PERCENT_NUMBER}`, 'i')));
  let moveSpeed = max(percentMatches(swiftnessTooltip, new RegExp(`이동\\s*속도(?:가|는)?\\s*\\+?${PERCENT_NUMBER}`, 'i')));
  if (criticalRate.isZero() && critical.Value) {
    criticalRate = dec(critical.Value as Decimal.Value).times('0.0003578586');
    warning(context, 'PROFILE_CRIT_FALLBACK', 'warning', 'profiles.Stats[치명].Tooltip', '치명 툴팁 환산값이 없어 고정 계수를 사용했습니다.');
  }
  if ((attackSpeed.isZero() || moveSpeed.isZero()) && swiftness.Value) {
    const fallback = dec(swiftness.Value as Decimal.Value).times('0.000171759');
    if (attackSpeed.isZero()) attackSpeed = fallback;
    if (moveSpeed.isZero()) moveSpeed = fallback;
    warning(context, 'PROFILE_SWIFTNESS_FALLBACK', 'warning', 'profiles.Stats[신속].Tooltip', '신속 툴팁 환산값이 없어 고정 계수를 사용했습니다.');
  }
  provenance(context, 'profiles.Stats[공격력]', '프로필 공격력(검산용)', dec(attack.Value as Decimal.Value));
  return {
    className: text(body.CharacterClassName),
    characterLevel: integer(body.CharacterLevel),
    expeditionLevel: integer(body.ExpeditionLevel),
    criticalStat: decimalString(dec(critical.Value as Decimal.Value)),
    swiftnessStat: decimalString(dec(swiftness.Value as Decimal.Value)),
    specializationStat: decimalString(dec(specialization.Value as Decimal.Value)),
    profileAttackPower: decimalString(dec(attack.Value as Decimal.Value)),
    criticalRateFromStat: decimalString(criticalRate),
    attackSpeedFromSwiftness: decimalString(attackSpeed),
    moveSpeedFromSwiftness: decimalString(moveSpeed)
  };
}

function emptyEquipmentValues(): NormalizedBuild['equipment']['items'][number]['values'] {
  return {
    mainStat: '0',
    baseWeaponAttack: '0',
    weaponAttackFlat: '0',
    weaponAttackPercent: '0',
    baseAttackPowerFlat: '0',
    baseAttackPowerPercent: '0',
    attackPowerFlat: '0',
    attackPowerPercent: '0',
    additionalDamage: '0',
    damageToEnemy: '0',
    criticalRate: '0',
    criticalDamage: '0',
    criticalHitDamage: '0',
    nonDirectionalDamage: '0'
  };
}

function parseEquipment(bodyValue: unknown, context: ParseContext): NormalizedBuild['equipment'] {
  const totals: Record<string, Decimal> = Object.fromEntries([
    ...Object.keys(emptyEquipmentValues()),
    'weaponAdditionalDamage',
    'necklaceAdditionalDamage',
    'otherAdditionalDamage',
    'necklaceDamageToEnemy',
    'braceletDamageToEnemy',
    'otherDamageToEnemy',
    'braceletCriticalHitDamage',
    'braceletNonDirectionalDamage'
  ].map((key) => [key, ZERO]));
  const items: NormalizedBuild['equipment']['items'] = [];
  let hasMasterElixir = false;

  for (const [index, rawItem] of array(bodyValue).entries()) {
    const item = object(rawItem);
    const type = text(item.Type);
    const tooltipText = tooltipToText(item.Tooltip);
    const lines = tooltipText.split('\n').map((line) => line.trim());
    const mainStat = max(matches(tooltipText, new RegExp(`지능\\s*\\+?${PLAIN_NUMBER}`, 'g')));
    const weaponAttackNumber = max(matches(tooltipText, new RegExp(`무기\\s*공격력\\s*\\+?${PLAIN_NUMBER}(?:\\s*\\n|$)`, 'g')));
    const weaponAttackPercent = sumUnique(percentMatches(tooltipText, new RegExp(`무기\\s*공격력\\s*\\+?${PERCENT_NUMBER}`, 'g')));
    const attackPowerFlat = sumUnique(lines
      .filter((line) => /^공격력\s*\+?[0-9,]+(?:\.\d+)?$/.test(line))
      .map((line) => dec(line.match(/[0-9,]+(?:\.\d+)?/)?.[0] ?? 0)));
    const attackPowerPercent = sumUnique(lines
      .filter((line) => /^공격력\s*\+?[0-9]+(?:\.\d+)?%/.test(line))
      .map((line) => percent(line.match(/[0-9]+(?:\.\d+)?/)?.[0] ?? 0)));
    const baseAttackPowerFlat = type === '완갑'
      ? sumUnique(matches(tooltipText, new RegExp(`기본\\s*공격력\\s*\\+?${PLAIN_NUMBER}(?:\\s*\\n|$)`, 'g')))
      : ZERO;
    const baseAttackPowerPercent = type === '완갑'
      ? sumUnique(percentMatches(tooltipText, new RegExp(`기본\\s*공격력(?:이)?\\s*\\+?${PERCENT_NUMBER}`, 'g')))
      : ZERO;
    const additionalDamage = sumUnique(percentMatches(tooltipText, new RegExp(`추가\\s*피해\\s*\\+?${PERCENT_NUMBER}`, 'g')));
    const damageToEnemy = sumUnique(percentMatches(tooltipText, new RegExp(`(?:^|\\n)\\s*적에게\\s*주는\\s*피해(?:가|량이)?\\s*\\+?${PERCENT_NUMBER}`, 'g')));
    const criticalRate = sumUnique(percentMatches(tooltipText, new RegExp(`치명타\\s*적중률(?:이|은)?\\s*\\+?${PERCENT_NUMBER}`, 'g')));
    const conditionalCritical = sumUnique(percentMatches(tooltipText, new RegExp(`(?:공격이\\s*)?치명타(?:로|가)?\\s*적중[^%\\n]{0,45}?피해(?:가|량이)?\\s*\\+?${PERCENT_NUMBER}`, 'g')));
    let criticalDamage = sumUnique(percentMatches(tooltipText, new RegExp(`치명타\\s*피해(?:가|량이)?\\s*\\+?${PERCENT_NUMBER}`, 'g')));
    if (!conditionalCritical.isZero() && criticalDamage.eq(conditionalCritical)) criticalDamage = ZERO;
    const nonDirectionalDamage = sumUnique(percentMatches(tooltipText, new RegExp(`비방향성(?:\\s*공격)?\\s*피해(?:가|량이)?\\s*\\+?${PERCENT_NUMBER}`, 'g')));

    const values = {
      ...emptyEquipmentValues(),
      mainStat: decimalString(mainStat),
      baseWeaponAttack: type === '무기' ? decimalString(weaponAttackNumber) : '0',
      weaponAttackFlat: type === '무기' ? '0' : decimalString(weaponAttackNumber),
      weaponAttackPercent: decimalString(weaponAttackPercent),
      baseAttackPowerFlat: decimalString(baseAttackPowerFlat),
      baseAttackPowerPercent: decimalString(baseAttackPowerPercent),
      attackPowerFlat: decimalString(attackPowerFlat),
      attackPowerPercent: decimalString(attackPowerPercent),
      additionalDamage: decimalString(additionalDamage),
      damageToEnemy: decimalString(damageToEnemy),
      criticalRate: decimalString(criticalRate),
      criticalDamage: decimalString(criticalDamage),
      criticalHitDamage: type === '팔찌' ? decimalString(conditionalCritical) : '0',
      nonDirectionalDamage: type === '팔찌' ? decimalString(nonDirectionalDamage) : '0'
    };
    items.push({ type, name: text(item.Name), grade: text(item.Grade), tooltipText, values });

    totals.mainStat = totals.mainStat!.plus(mainStat);
    if (type === '무기') totals.baseWeaponAttack = Decimal.max(totals.baseWeaponAttack!, weaponAttackNumber);
    else totals.weaponAttackFlat = totals.weaponAttackFlat!.plus(weaponAttackNumber);
    totals.weaponAttackPercent = totals.weaponAttackPercent!.plus(weaponAttackPercent);
    totals.baseAttackPowerFlat = totals.baseAttackPowerFlat!.plus(baseAttackPowerFlat);
    totals.baseAttackPowerPercent = totals.baseAttackPowerPercent!.plus(baseAttackPowerPercent);
    totals.attackPowerFlat = totals.attackPowerFlat!.plus(attackPowerFlat);
    totals.attackPowerPercent = totals.attackPowerPercent!.plus(attackPowerPercent);
    if (type === '무기') totals.weaponAdditionalDamage = totals.weaponAdditionalDamage!.plus(additionalDamage);
    else if (type === '목걸이') totals.necklaceAdditionalDamage = totals.necklaceAdditionalDamage!.plus(additionalDamage);
    else totals.otherAdditionalDamage = totals.otherAdditionalDamage!.plus(additionalDamage);
    if (type === '목걸이') totals.necklaceDamageToEnemy = totals.necklaceDamageToEnemy!.plus(damageToEnemy);
    else if (type === '팔찌') totals.braceletDamageToEnemy = totals.braceletDamageToEnemy!.plus(damageToEnemy);
    else totals.otherDamageToEnemy = totals.otherDamageToEnemy!.plus(damageToEnemy);
    totals.criticalRate = totals.criticalRate!.plus(criticalRate);
    totals.criticalDamage = totals.criticalDamage!.plus(criticalDamage);
    if (type === '팔찌') {
      totals.braceletCriticalHitDamage = totals.braceletCriticalHitDamage!.plus(conditionalCritical);
      totals.braceletNonDirectionalDamage = totals.braceletNonDirectionalDamage!.plus(nonDirectionalDamage);
    }
    if (tooltipText.includes('회심')) hasMasterElixir = true;
    for (const [key, value] of Object.entries(values)) {
      if (value !== '0') provenance(context, `equipment[${index}].Tooltip`, `${type} ${key}`, value, { sourceType: 'OFFICIAL_TOOLTIP' });
    }
  }
  if (totals.mainStat!.isZero()) warning(context, 'MISSING_EQUIPMENT_MAIN_STAT', 'incomplete', 'equipment[*].Tooltip', '장비 툴팁에서 지능을 추출하지 못했습니다.');
  if (totals.baseWeaponAttack!.isZero()) warning(context, 'MISSING_WEAPON_ATTACK', 'incomplete', 'equipment[*].Tooltip', '무기 툴팁에서 기본 무기 공격력을 추출하지 못했습니다.');

  return {
    mainStat: decimalString(totals.mainStat!),
    baseWeaponAttack: decimalString(totals.baseWeaponAttack!),
    weaponAttackFlat: decimalString(totals.weaponAttackFlat!),
    weaponAttackPercent: decimalString(totals.weaponAttackPercent!),
    baseAttackPowerFlat: decimalString(totals.baseAttackPowerFlat!),
    baseAttackPowerPercent: decimalString(totals.baseAttackPowerPercent!),
    attackPowerFlat: decimalString(totals.attackPowerFlat!),
    attackPowerPercent: decimalString(totals.attackPowerPercent!),
    additionalDamage: decimalString(totals.weaponAdditionalDamage!.plus(totals.necklaceAdditionalDamage!).plus(totals.otherAdditionalDamage!)),
    damageToEnemy: decimalString(totals.necklaceDamageToEnemy!.plus(totals.braceletDamageToEnemy!).plus(totals.otherDamageToEnemy!)),
    criticalRate: decimalString(totals.criticalRate!),
    criticalDamage: decimalString(totals.criticalDamage!),
    criticalHitDamage: decimalString(totals.braceletCriticalHitDamage!),
    nonDirectionalDamage: decimalString(totals.braceletNonDirectionalDamage!),
    weaponAdditionalDamage: decimalString(totals.weaponAdditionalDamage!),
    necklaceAdditionalDamage: decimalString(totals.necklaceAdditionalDamage!),
    otherAdditionalDamage: decimalString(totals.otherAdditionalDamage!),
    necklaceDamageToEnemy: decimalString(totals.necklaceDamageToEnemy!),
    braceletDamageToEnemy: decimalString(totals.braceletDamageToEnemy!),
    otherDamageToEnemy: decimalString(totals.otherDamageToEnemy!),
    braceletCriticalHitDamage: decimalString(totals.braceletCriticalHitDamage!),
    braceletNonDirectionalDamage: decimalString(totals.braceletNonDirectionalDamage!),
    hasMasterElixir,
    items
  };
}

function parseAvatars(bodyValue: unknown, context: ParseContext): NormalizedBuild['avatars'] {
  const rawItems = array(bodyValue).map(object);
  const groups = new Map<string, number[]>();
  rawItems.forEach((item, index) => {
    const type = text(item.Type) || `unknown-${index}`;
    groups.set(type, [...(groups.get(type) ?? []), index]);
  });
  const selected = new Set<number>();
  for (const indices of groups.values()) {
    selected.add(indices.find((index) => rawItems[index]?.IsInner === true) ?? indices[0]!);
  }
  let total = ZERO;
  const statTypes = new Set(['무기', '머리', '상의', '하의']);
  const items = rawItems.map((item, index) => {
    const type = text(item.Type);
    const normalizedType = type.replace(/\s*아바타$/, '');
    const applied = selected.has(index);
    const value = applied && statTypes.has(normalizedType) && text(item.Grade) === '전설' ? new Decimal('0.02') : ZERO;
    total = total.plus(value);
    provenance(context, `avatars[${index}]`, `${type} 아바타 주스탯`, value, {
      sourceType: 'OFFICIAL_API+VERIFIED_RULE',
      applied,
      eligible: applied,
      excludedReason: applied ? '' : '부위별 효과 아바타 하나만 선택'
    });
    return {
      type,
      name: text(item.Name),
      grade: text(item.Grade),
      isInner: item.IsInner === true,
      applied,
      mainStatPercent: decimalString(value)
    };
  });
  return { mainStatPercent: decimalString(total), items };
}

function parseEngravings(bodyValue: unknown, context: ParseContext): NormalizedBuild['engravings'] {
  const body = object(bodyValue);
  const entries = array(body.ArkPassiveEffects).length > 0 ? array(body.ArkPassiveEffects) : array(body.Effects);
  const effects: NormalizedBuild['engravings']['effects'] = {};
  let stoneLevelTotal = 0;
  for (const [index, rawEntry] of entries.entries()) {
    const entry = object(rawEntry);
    const rawName = text(entry.Name);
    const name = rawName.replace(/\s*Lv\.?\s*\d+.*$/, '').trim();
    const description = tooltipToText(entry.Description ?? entry.Tooltip);
    const stoneLevel = integer(entry.AbilityStoneLevel);
    stoneLevelTotal += stoneLevel;
    const generalDamage = max(percentMatches(description, new RegExp(`(?:(?:보스\\s*및\\s*레이드\\s*몬스터에게|적에게)\\s*주는\\s*피해(?:량)?|공격(?:의)?\\s*피해)(?:이|가)?\\s*\\+?${PERCENT_NUMBER}`, 'g')));
    const raidCaptainCoefficient = max(percentMatches(description, new RegExp(`이동\\s*속도\\s*증가량의\\s*${PERCENT_NUMBER}\\s*만큼`, 'g')));
    const attackSpeedReduction = max(percentMatches(description, new RegExp(`공격\\s*속도(?:가|는)?\\s*${PERCENT_NUMBER}\\s*감소`, 'g')));
    const perStack = max(percentMatches(description, new RegExp(`공격력(?:이|은)?\\s*\\+?${PERCENT_NUMBER}\\s*증가`, 'g')));
    const maxStacks = integer(description.match(/최대\s*(\d+)\s*중첩/)?.[1] ?? 1);
    const criticalRate = max(percentMatches(description, new RegExp(`치명타\\s*적중률(?:이|은)?[^%\\n]{0,35}?${PERCENT_NUMBER}\\s*증가`, 'g')));
    effects[name] = {
      generalDamage: decimalString(generalDamage),
      raidCaptainCoefficient: decimalString(raidCaptainCoefficient),
      attackSpeed: decimalString(attackSpeedReduction.neg()),
      attackPowerPercent: decimalString(perStack.times(maxStacks)),
      attackPowerPerStack: decimalString(perStack),
      maxStacks,
      criticalRate: decimalString(criticalRate)
    };
    provenance(context, `engravings.entries[${index}]`, name, entry.Level ? String(entry.Level) : '0', { sourceType: 'OFFICIAL_API' });
  }
  const stoneBaseAttackPercent = stoneLevelTotal >= 5 ? '0.015' : '0';
  if (stoneBaseAttackPercent !== '0') provenance(context, 'engravings.ArkPassiveEffects[].AbilityStoneLevel', '어빌리티 스톤 기본 공격력', stoneBaseAttackPercent, { sourceType: 'OFFICIAL_API+VERIFIED_RULE' });
  return { names: Object.keys(effects).sort(), stoneLevelTotal, stoneBaseAttackPercent, effects };
}

function parseCards(bodyValue: unknown, context: ParseContext): NormalizedBuild['cards'] {
  const body = object(bodyValue);
  let total = ZERO;
  for (const [effectIndex, rawEffect] of array(body.Effects).entries()) {
    for (const [itemIndex, rawItem] of array(object(rawEffect).Items).entries()) {
      const item = object(rawItem);
      const description = tooltipToText(item.Description ?? item);
      const values = [
        ...percentMatches(description, new RegExp(`(?:주는\\s*피해|피해가|피해량이)[^%\\n]{0,30}?${PERCENT_NUMBER}`, 'g')),
        ...percentMatches(description, new RegExp(`(?:성|암|화|수|토|뇌|신성)?속성\\s*피해\\s*\\+?${PERCENT_NUMBER}`, 'g'))
      ];
      const value = sumUnique(values);
      total = total.plus(value);
      if (!value.isZero()) provenance(context, `cards.Effects[${effectIndex}].Items[${itemIndex}]`, text(item.Name) || '카드 피해', value);
    }
  }
  if (array(body.Cards).length > 0 && total.isZero()) warning(context, 'UNPARSED_CARD_DAMAGE', 'incomplete', 'cards.Effects', '장착 카드는 있으나 피해 증가 카드 효과를 파싱하지 못했습니다.');
  return { damagePercent: decimalString(total) };
}

function parseGems(bodyValue: unknown, context: ParseContext): NormalizedBuild['gems'] {
  const body = object(bodyValue);
  const items: NormalizedBuild['gems']['items'] = [];
  const skillEffects: NormalizedBuild['gems']['skillEffects'] = [];
  let baseAttackPercent = ZERO;
  for (const [index, rawGem] of array(body.Gems).entries()) {
    const gem = object(rawGem);
    const tooltipText = tooltipToText(gem.Tooltip);
    const baseValues = [
      ...percentMatches(tooltipText, new RegExp(`기본\\s*공격력(?:이)?\\s*(?:\\+|증가\\s*)?${PERCENT_NUMBER}`, 'gi')),
      ...percentMatches(tooltipText, new RegExp(`${PERCENT_NUMBER}[^%\\n]{0,20}기본\\s*공격력\\s*증가`, 'gi'))
    ];
    const baseValue = max(baseValues);
    baseAttackPercent = baseAttackPercent.plus(baseValue);
    const itemEffects: NormalizedBuild['gems']['skillEffects'] = [];
    const damagePattern = new RegExp(`(?:\\[[^\\]\\n]+\\]\\s*)?([가-힣A-Za-z0-9·' ]+?)\\s+피해(?:량)?(?:이|가)?\\s*\\+?${PERCENT_NUMBER}\\s*증가`, 'gi');
    for (const match of tooltipText.matchAll(damagePattern)) {
      const skillName = canonicalSkill(match[1] ?? '');
      if (['추가', '기본 공격력'].includes(skillName)) continue;
      const effect = { skillName, effectType: 'damage' as const, value: decimalString(percent(match[2] ?? 0)), sourceGemIndex: index };
      itemEffects.push(effect);
      skillEffects.push(effect);
      provenance(context, `gems.Gems[${index}].Tooltip`, `일반 보석 ${skillName} 피해`, effect.value, { sourceType: 'OFFICIAL_TOOLTIP' });
    }
    const cooldownPattern = new RegExp(`(?:\\[[^\\]\\n]+\\]\\s*)?([가-힣A-Za-z0-9·' ]+?)\\s+재사용\\s*대기시간(?:이|가)?\\s*\\+?${PERCENT_NUMBER}\\s*감소`, 'gi');
    for (const match of tooltipText.matchAll(cooldownPattern)) {
      const skillName = canonicalSkill(match[1] ?? '');
      const effect = { skillName, effectType: 'cooldownReduction' as const, value: decimalString(percent(match[2] ?? 0)), sourceGemIndex: index };
      itemEffects.push(effect);
      skillEffects.push(effect);
      provenance(context, `gems.Gems[${index}].Tooltip`, `일반 보석 ${skillName} 재사용 대기시간 감소`, effect.value, { sourceType: 'OFFICIAL_TOOLTIP', eligible: false, applied: false, excludedReason: '1회 피해에는 영향 없음' });
    }
    items.push({
      slot: gem.Slot === null || gem.Slot === undefined ? null : integer(gem.Slot),
      name: text(gem.Name),
      level: integer(gem.Level),
      grade: text(gem.Grade),
      baseAttackPercent: decimalString(baseValue),
      tooltipText,
      skillEffects: itemEffects
    });
    if (!baseValue.isZero()) provenance(context, `gems.Gems[${index}].Tooltip`, `${text(gem.Name)} 기본 공격력`, baseValue, { sourceType: 'OFFICIAL_TOOLTIP' });
  }
  return { baseAttackPercent: decimalString(baseAttackPercent), items, skillEffects };
}

function effectName(summary: string, rawName: string): string {
  const fromSummary = summary.match(/(?:깨달음|진화|도약)\s+\d+티어\s+(.+?)\s+Lv\.?\s*\d+/)?.[1];
  const candidate = canonicalSkill(fromSummary ?? rawName)
    .replace(/\s*Lv\.?\s*\d+.*$/, '')
    .replace(/\s*[ⅠⅡⅢIVX]+$/, '')
    .trim();
  const known = Object.keys(EFFECT_FALLBACKS).find((name) => `${candidate}\n${summary}`.includes(name));
  return known ?? candidate;
}

function parseArkPassive(bodyValue: unknown, context: ParseContext): NormalizedBuild['arkPassive'] {
  const body = object(bodyValue);
  const evolutionDamageByName: Record<string, string> = {};
  const skillDamageByName: Record<string, string> = {};
  const criticalRateByName: Record<string, string> = {};
  const criticalDamageByName: Record<string, string> = {};
  const criticalHitDamageByName: Record<string, string> = {};
  const additionalDamageByName: Record<string, string> = {};
  const speedByName: Record<string, { attackSpeed: string; moveSpeed: string }> = {};
  const effects: NormalizedBuild['arkPassive']['effects'] = [];

  for (const [index, rawEffect] of array(body.Effects).entries()) {
    const effect = object(rawEffect);
    const rawName = text(effect.Name);
    const summary = tooltipToText(effect.Description);
    const detail = tooltipToText(effect.ToolTip ?? effect.Tooltip);
    const description = [summary, detail].filter(Boolean).join('\n');
    const name = effectName(summary, rawName);
    const levelText = `${summary} ${description}`.match(/(?:Lv\.?\s*|레벨\s*)(\d+)/)?.[1];
    const level = levelText === undefined ? null : integer(levelText);
    let evolution = max(percentMatches(description, new RegExp(`진화형\\s*피해(?:가|량이)?\\s*\\+?${PERCENT_NUMBER}`, 'g')));
    let criticalRate = max(percentMatches(description, new RegExp(`치명타\\s*적중률(?:이|은)?\\s*\\+?${PERCENT_NUMBER}`, 'g')));
    const combinedSpeed = max(percentMatches(description, new RegExp(`공격\\s*및\\s*이동\\s*속도(?:가|는)?\\s*\\+?${PERCENT_NUMBER}`, 'g')));
    let skillDamage = ZERO;
    if (['바람의 길', '풀려난 힘', '단련된 가르기', '공간 가르기'].includes(name)) {
      skillDamage = max(percentMatches(description, new RegExp(`(?:피해량|주는\\s*피해)(?:이|가)?\\s*\\+?${PERCENT_NUMBER}`, 'g')));
    }
    let criticalHitDamage = name === '회심'
      ? max(percentMatches(description, new RegExp(`치명타로\\s*적중\\s*시[^%\\n]{0,35}?피해(?:가|량이)?\\s*\\+?${PERCENT_NUMBER}`, 'g')))
      : ZERO;
    let criticalDamage = ZERO;
    const fallbackComponents: Array<{ category: string; value: Decimal }> = [];
    if (name === '기민함') {
      criticalRate = new Decimal('0.12');
      criticalDamage = new Decimal('0.48');
      fallbackComponents.push(
        { category: 'criticalRate', value: criticalRate },
        { category: 'criticalDamage', value: criticalDamage }
      );
    }
    const fallback = EFFECT_FALLBACKS[name] ?? {};
    if (evolution.isZero() && fallback.evolutionDamage) { evolution = dec(fallback.evolutionDamage); fallbackComponents.push({ category: 'evolutionDamage', value: evolution }); }
    if (skillDamage.isZero() && fallback.skillDamage) { skillDamage = dec(fallback.skillDamage); fallbackComponents.push({ category: 'skillDamage', value: skillDamage }); }
    if (criticalRate.isZero() && fallback.criticalRate) { criticalRate = dec(fallback.criticalRate); fallbackComponents.push({ category: 'criticalRate', value: criticalRate }); }
    if (criticalDamage.isZero() && fallback.criticalDamage) { criticalDamage = dec(fallback.criticalDamage); fallbackComponents.push({ category: 'criticalDamage', value: criticalDamage }); }
    if (criticalHitDamage.isZero() && fallback.criticalHitDamage) { criticalHitDamage = dec(fallback.criticalHitDamage); fallbackComponents.push({ category: 'criticalHitDamage', value: criticalHitDamage }); }
    if (!evolution.isZero()) evolutionDamageByName[name] = decimalString(evolution);
    if (!skillDamage.isZero()) skillDamageByName[name] = decimalString(skillDamage);
    if (!criticalRate.isZero()) criticalRateByName[name] = decimalString(criticalRate);
    if (!criticalDamage.isZero()) criticalDamageByName[name] = decimalString(criticalDamage);
    if (!criticalHitDamage.isZero()) criticalHitDamageByName[name] = decimalString(criticalHitDamage);
    if (!combinedSpeed.isZero()) speedByName[name] = { attackSpeed: decimalString(combinedSpeed), moveSpeed: decimalString(combinedSpeed) };
    effects.push({ name, rawName, level, description });
    const hasCalculatorComponent = !evolution.isZero()
      || !skillDamage.isZero()
      || !criticalRate.isZero()
      || !criticalDamage.isZero()
      || !criticalHitDamage.isZero()
      || !combinedSpeed.isZero()
      || name === '음속 돌파';
    provenance(context, `arkPassive.Effects[${index}]`, name, level ?? 0, {
      sourceType: name === '음속 돌파' ? 'OFFICIAL_API+VERIFIED_RULE' : 'OFFICIAL_API',
      eligible: hasCalculatorComponent,
      applied: hasCalculatorComponent,
      excludedReason: hasCalculatorComponent ? '' : '1회 피해 계산에 연결되지 않은 스탯·자원·시전 속도·재사용 대기시간 노드',
      note: name === '음속 돌파' ? '노드 레벨을 음속 돌파 계산 규칙에 사용' : ''
    });
    if (fallbackComponents.length > 0) {
      warning(
        context,
        'ARK_PASSIVE_EFFECT_FALLBACK',
        'warning',
        `arkPassive.Effects[${index}]`,
        `'${name}'의 ${fallbackComponents.map(({ category }) => category).join(', ')} 수치에 current-v2.7.2 검증 fallback을 사용했습니다.`
      );
      for (const component of fallbackComponents) {
        provenance(context, `arkPassive.Effects[${index}].fallback.${component.category}`, `${name} ${component.category} fallback`, component.value, {
          sourceType: 'VERIFIED_FALLBACK',
          parsed: false,
          note: '공식 API 노드 선택·레벨과 current-v2.7.2 검증 규칙으로 보완'
        });
      }
    }
  }

  let karmaWeaponAttack = ZERO;
  let karmaEvolution = ZERO;
  const points: NormalizedBuild['arkPassive']['points'] = [];
  for (const [index, rawPoint] of array(body.Points).entries()) {
    const point = object(rawPoint);
    const name = text(point.Name);
    const pointText = tooltipToText(point.Description ?? point.Tooltip);
    const karmaLevel = Math.max(0, ...matches(pointText, /([0-9]+)\s*레벨/g).map((value) => value.toNumber()));
    points.push({
      path: `arkPassive.Points[${index}]`,
      name,
      value: Number(point.Value ?? 0),
      karmaLevel,
      tooltipText: pointText
    });
    if (name.includes('깨달음') || pointText.includes('깨달음')) {
      if (karmaLevel > 0) {
        karmaWeaponAttack = new Decimal(karmaLevel).times('0.001');
        provenance(context, `arkPassive.Points[${index}].Description`, '깨달음 카르마 무기 공격력', karmaWeaponAttack, { sourceType: 'OFFICIAL_API+VERIFIED_RULE', note: `${karmaLevel}레벨 × 0.1%` });
      }
    }
    if (name.includes('진화') || pointText.includes('진화')) {
      const parsed = max(percentMatches(pointText, new RegExp(`진화형\\s*피해(?:가|량이)?[^%\\n]{0,25}?${PERCENT_NUMBER}`, 'g')));
      if (!parsed.isZero()) karmaEvolution = parsed;
      else if (pointText && (pointText.includes('랭크') || pointText.includes('카르마'))) {
        karmaEvolution = new Decimal('0.06');
        warning(context, 'KARMA_EVOLUTION_FALLBACK', 'warning', `arkPassive.Points[${index}]`, '진화 카르마 수치를 파싱하지 못해 검증된 예시값 +6.0%를 사용했습니다.');
      }
    }
  }
  return {
    karmaWeaponAttackPercent: decimalString(karmaWeaponAttack),
    karmaEvolutionDamage: decimalString(karmaEvolution),
    evolutionDamageByName,
    skillDamageByName,
    criticalRateByName,
    criticalDamageByName,
    criticalHitDamageByName,
    additionalDamageByName,
    speedByName,
    effects,
    points
  };
}

function parseTripodDamageEffects(tooltipText: string): Array<{
  type: 'DAMAGE_INCREASE' | 'ADDITIONAL_ATTACK' | 'INCREASED_TOTAL_DAMAGE';
  label: string;
  percent: string;
  multiplier: string;
}> {
  const output: Array<{
    type: 'DAMAGE_INCREASE' | 'ADDITIONAL_ATTACK' | 'INCREASED_TOTAL_DAMAGE';
    label: string;
    percent: string;
    multiplier: string;
  }> = [];
  const patterns: Array<[typeof output[number]['type'], string, RegExp]> = [
    ['DAMAGE_INCREASE', '피해 증가', new RegExp(`적에게\\s*주는\\s*피해(?:가|를|량이)?\\s*\\+?${PERCENT_NUMBER}\\s*(?:증가|증가시킨다)`, 'g')],
    ['ADDITIONAL_ATTACK', '추가 공격 피해', new RegExp(`(?:적에게\\s*)?(?:총\\s*)?\\+?${PERCENT_NUMBER}\\s*추가\\s*피해`, 'g')],
    ['INCREASED_TOTAL_DAMAGE', '총 증가 피해', new RegExp(`총\\s*\\+?${PERCENT_NUMBER}\\s*(?:의\\s*)?증가된\\s*피해`, 'g')]
  ];
  for (const [type, label, pattern] of patterns) {
    const seen = new Set<string>();
    for (const value of matches(tooltipText, pattern)) {
      const valueText = decimalString(value.div(100));
      if (seen.has(valueText)) continue;
      seen.add(valueText);
      output.push({ type, label, percent: valueText, multiplier: decimalString(ONE.plus(value.div(100))) });
    }
  }
  return output;
}

function parseCombatSkills(bodyValue: unknown, context: ParseContext): NormalizedBuild['combatSkills'] {
  const skillNames: string[] = [];
  const selectedTripods: NormalizedBuild['combatSkills']['selectedTripods'] = [];
  let hasExposedWeakness = false;
  for (const [skillIndex, rawSkill] of array(bodyValue).entries()) {
    const skill = object(rawSkill);
    const skillName = canonicalSkill(text(skill.Name));
    skillNames.push(skillName);
    for (const [tripodIndex, rawTripod] of array(skill.Tripods).entries()) {
      const tripod = object(rawTripod);
      if (tripod.IsSelected !== true) continue;
      const name = text(tripod.Name);
      const tooltipText = tooltipToText(tripod.Tooltip);
      const rawEffects = parseTripodDamageEffects(tooltipText);
      const damageEffects = rawEffects.map((effect) => ({
        ...effect,
        applicationMode: effect.type === 'ADDITIONAL_ATTACK' && skillName === '몰아치기' && name === '공간베기'
          ? 'EMBEDDED_MOTION_HIT' as const
          : 'MULTIPLIER' as const
      }));
      const damagePercent = name === '역류'
        ? sum(damageEffects.filter((effect) => effect.type === 'DAMAGE_INCREASE').map((effect) => effect.percent))
        : ZERO;
      const criticalDamage = sumUnique(percentMatches(tooltipText, new RegExp(`치명타\\s*피해(?:가|량이)?\\s*\\+?${PERCENT_NUMBER}\\s*(?:증가|증가시킨다)`, 'g')));
      selectedTripods.push({
        skillName,
        name,
        tier: tripod.Tier === undefined || tripod.Tier === null ? null : integer(tripod.Tier),
        tooltipText,
        damagePercent: decimalString(damagePercent),
        criticalDamagePercent: decimalString(criticalDamage),
        damageEffects
      });
      if (name.includes('급소 노출')) {
        hasExposedWeakness = true;
        provenance(context, `combatSkills[${skillIndex}].Tripods[${tripodIndex}]`, '급소 노출', '0.1', { sourceType: 'OFFICIAL_API+VERIFIED_RULE' });
      }
    }
  }
  return { skillNames, selectedTripods, hasExposedWeakness };
}

export function resolveArkGridGradeValues(value: string, coreGrade: string): string {
  const ancient = coreGrade.includes('고대');
  return value.replace(/(?<![0-9.])([0-9]+(?:\.[0-9]+)?)\s*\/\s*([0-9]+(?:\.[0-9]+)?)(\s*%)?/g, (_all, relic: string, ancientValue: string, percentSuffix: string | undefined) => `${ancient ? ancientValue : relic}${percentSuffix ? '%' : ''}`);
}

function extractArkGridOptions(tooltipText: string): Array<{ requiredPoints: number; text: string }> {
  const options: Array<{ requiredPoints: number; text: string }> = [];
  let current: { requiredPoints: number; text: string } | undefined;
  let inOptions = false;
  for (const rawLine of tooltipText.split('\n')) {
    const line = rawLine.trim();
    if (line === '코어 옵션') { inOptions = true; continue; }
    if (['코어 옵션 발동 조건', '분해불가'].includes(line)) {
      if (current) options.push(current);
      current = undefined;
      inOptions = false;
      continue;
    }
    if (!inOptions) continue;
    const start = line.match(/^\[(\d+)P\]\s*(.*)$/);
    if (start) {
      if (current) options.push(current);
      current = { requiredPoints: integer(start[1]), text: (start[2] ?? '').trim() };
    } else if (current && line) current.text += `\n${line}`;
  }
  if (current) options.push(current);
  return options;
}

function parseArkGridDamageValues(value: string): Record<'attackPowerPercent' | 'additionalDamagePercent' | 'bossDamagePercent', Decimal> {
  const attackPowerPercent = max(percentMatches(value, new RegExp(`(?:^|\\s)공격력(?:이)?\\s*(?:\\+|증가\\s*)?${PERCENT_NUMBER}`, 'gm')));
  const additionalDamagePercent = max(percentMatches(value, new RegExp(`추가\\s*피해(?:가|량이)?\\s*(?:\\+|증가\\s*)?${PERCENT_NUMBER}`, 'g')));
  const bossDamagePercent = max(percentMatches(value, new RegExp(`(?:보스(?:\\s*등급\\s*이상\\s*몬스터)?에게\\s*주는\\s*피해|보스\\s*피해)(?:가|량이)?\\s*(?:\\+|증가\\s*)?${PERCENT_NUMBER}`, 'g')));
  return { attackPowerPercent, additionalDamagePercent, bossDamagePercent };
}

function parseArkGridComponents(rawText: string, coreName: string, coreGrade: string): ArkGridComponent[] {
  const value = resolveArkGridGradeValues(rawText, coreGrade);
  const components: ArkGridComponent[] = [];
  const condition = value.includes('기류 보호막')
    ? '기류 보호막 보유(최대 유리 조건)'
    : value.includes('여우비 상태')
      ? '여우비 상태(최대 유리 조건)'
      : value.includes("'운명") || value.includes('운명:')
        ? '운명 효과 활성(최대 유리 조건)'
        : '';
  const add = (
    category: string,
    parsedValue: Decimal,
    scopeKind: ArkGridComponent['scopeKind'] = 'ALL',
    scopeValue: string | string[] = '',
    operator: ArkGridComponent['operator'] = 'ADD'
  ): void => { components.push({ category, value: parsedValue, scopeKind, scopeValue, condition, operator }); };
  const operatorAt = (tail: string, multiplicative: boolean): ArkGridComponent['operator'] => !multiplicative ? 'ADD' : /^\s*추가로\s*증가/.test(tail) ? 'ADD_TO_PREVIOUS' : 'MULTIPLY';
  const addPattern = (
    category: string,
    pattern: RegExp,
    scopeKind: ArkGridComponent['scopeKind'] = 'ALL',
    scopeValue: string | string[] = '',
    multiplicative = false,
    source = value
  ): void => {
    for (const match of source.matchAll(new RegExp(pattern.source, pattern.flags.includes('g') ? pattern.flags : `${pattern.flags}g`))) {
      add(category, percent(match[1] ?? 0), scopeKind, scopeValue, operatorAt(source.slice(match.index! + match[0].length, match.index! + match[0].length + 24), multiplicative));
    }
  };

  addPattern('skillDamagePercent', new RegExp(`우산\\s*스킬의\\s*피해량이\\s*${PERCENT_NUMBER}`, 'g'), 'SKILL_TAG', 'UMBRELLA_SKILL', true);
  addPattern('skillDamagePercent', new RegExp(`기상\\s*스킬의\\s*피해량이\\s*${PERCENT_NUMBER}`, 'g'), 'SKILL_TAG', 'WEATHER_SKILL', true);
  for (const match of value.matchAll(new RegExp(`([^.\\n]+?)의\\s*피해량이\\s*${PERCENT_NUMBER}`, 'g'))) {
    const prefix = match[1] ?? '';
    if (prefix.includes('우산 스킬') || prefix.includes('기상 스킬')) continue;
    const names = ARKGRID_SKILL_NAMES.filter((name) => prefix.includes(name));
    if (names.includes('여우비 기본 공격')) names.splice(names.indexOf('여우비'), 1);
    if (names.length > 0) add('skillDamagePercent', percent(match[2] ?? 0), 'SKILL_NAMES', names, operatorAt(value.slice(match.index! + match[0].length, match.index! + match[0].length + 24), true));
  }

  let generalText = value;
  const criticalPattern = new RegExp(`치명타(?:로)?(?:\\s*적중)?\\s*시\\s*적에게\\s*주는\\s*피해(?:가|량이)?\\s*${PERCENT_NUMBER}`, 'g');
  addPattern('criticalHitDamagePercent', criticalPattern, 'ALL', '', true);
  generalText = generalText.replace(criticalPattern, '');
  const bossPattern = new RegExp(`보스(?:\\s*등급)?\\s*이상\\s*적에게\\s*주는\\s*피해(?:가|량이)?\\s*${PERCENT_NUMBER}`, 'g');
  addPattern('bossDamagePercent', bossPattern, 'ALL', '', true);
  generalText = generalText.replace(bossPattern, '');
  addPattern('generalDamagePercent', new RegExp(`적에게\\s*주는\\s*피해(?:가|량이)?\\s*${PERCENT_NUMBER}`, 'g'), 'ALL', '', true, generalText);
  addPattern('additionalDamagePercent', new RegExp(`추가\\s*피해(?:가|량이)?\\s*${PERCENT_NUMBER}`, 'g'));
  addPattern('criticalRate', new RegExp(`치명타\\s*적중률(?:이)?\\s*${PERCENT_NUMBER}`, 'g'));
  addPattern('criticalDamage', new RegExp(`(?<!입는\\s)치명타\\s*피해(?:가|량이)?\\s*${PERCENT_NUMBER}`, 'g'));
  addPattern('criticalHitDamagePercent', new RegExp(`입는\\s*치명타\\s*피해(?:가|량이|량을)?\\s*${PERCENT_NUMBER}`, 'g'), 'ALL', '', true);
  addPattern('enemyDefenseReductionPercent', new RegExp(`모든\\s*방어력을\\s*${PERCENT_NUMBER}\\s*감소`, 'g'), 'ALL', '', true);
  addPattern('weaponAttackPercent', new RegExp(`무기\\s*공격력이\\s*${PERCENT_NUMBER}`, 'g'));
  const combinedSpeedPattern = new RegExp(`공격\\s*및\\s*이동\\s*속도(?:가|는)?\\s*${PERCENT_NUMBER}`, 'g');
  addPattern('attackSpeed', combinedSpeedPattern);
  addPattern('moveSpeed', combinedSpeedPattern);
  addPattern('attackSpeed', new RegExp(`(?<!및\\s)공격\\s*속도(?:가|는)?\\s*${PERCENT_NUMBER}`, 'g'));
  addPattern('moveSpeed', new RegExp(`(?<!및\\s)이동\\s*속도(?:가|는)?\\s*${PERCENT_NUMBER}`, 'g'));
  const noPercentWeaponAttackText = value.replace(new RegExp(`무기\\s*공격력이\\s*${PERCENT_NUMBER}`, 'g'), '');
  for (const match of noPercentWeaponAttackText.matchAll(new RegExp(`무기\\s*공격력이\\s*${PLAIN_NUMBER}\\s*(?:추가로\\s*)?증가`, 'g'))) add('weaponAttackFlat', dec(match[1] ?? 0));
  if (value.includes('무기 공격력')) {
    for (const match of noPercentWeaponAttackText.matchAll(new RegExp(`추가로\\s*${PLAIN_NUMBER}\\s*증가`, 'g'))) add('weaponAttackFlat', dec(match[1] ?? 0));
  }
  const attackText = value.replace(/무기\s*공격력/g, '');
  addPattern('attackPowerPercent', new RegExp(`(?<!아군\\s)공격력이\\s*${PERCENT_NUMBER}`, 'g'), 'ALL', '', false, attackText);
  const noPercentAttackText = attackText.replace(new RegExp(PERCENT_NUMBER, 'g'), '');
  for (const match of noPercentAttackText.matchAll(new RegExp(`(?<!아군\\s)공격력이\\s*${PLAIN_NUMBER}\\s*(?:추가로\\s*)?증가`, 'g'))) add('attackPowerFlat', dec(match[1] ?? 0));
  if (!value.includes('무기 공격력') && value.includes('공격력')) {
    for (const match of noPercentAttackText.matchAll(new RegExp(`추가로\\s*${PLAIN_NUMBER}\\s*증가`, 'g'))) add('attackPowerFlat', dec(match[1] ?? 0));
  }
  if (coreName.includes('바람의 칼날')) {
    const replacement = value.match(new RegExp(`피해\\s*증가량을\\s*${PERCENT_NUMBER}\\s*(?:로)?\\s*변경`));
    if (replacement) add('skillDamagePercent', percent(replacement[1] ?? 0), 'SKILL_NAMES', ['칼바람'], 'REPLACE');
  }
  return components;
}

function parseArkGrid(bodyValue: unknown, context: ParseContext): NormalizedBuild['arkGrid'] {
  const body = object(bodyValue);
  const gemTotals = { attackPowerPercent: ZERO, additionalDamagePercent: ZERO, bossDamagePercent: ZERO };
  const aggregateTotals = { attackPowerPercent: ZERO, additionalDamagePercent: ZERO, bossDamagePercent: ZERO };
  const aggregateCategories = new Set<keyof typeof aggregateTotals>();
  const coreTotals: Record<string, Decimal> = Object.fromEntries(ARKGRID_TOTAL_KEYS.map((key) => [key, ZERO]));
  const cores: NormalizedBuild['arkGrid']['cores'] = [];
  const factors: NormalizedBuild['arkGrid']['coreDamageFactors'] = [];
  const activeGems: NormalizedBuild['arkGrid']['activeGems'] = [];
  const activeAggregateEffects: NormalizedBuild['arkGrid']['activeAggregateEffects'] = [];

  for (const [slotIndex, rawSlot] of array(body.Slots).entries()) {
    const slot = object(rawSlot);
    const corePath = `arkGrid.Slots[${slotIndex}]`;
    const coreName = text(slot.Name) || '이름 없는 아크그리드 코어';
    const coreGrade = text(slot.Grade);
    const point = integer(slot.Point);
    const tooltipText = tooltipToText(slot.Tooltip);
    const options = extractArkGridOptions(tooltipText).map((option, optionIndex) => {
      const path = `${corePath}.Tooltip.options[${optionIndex}]`;
      const activated = point >= option.requiredPoints;
      const components = activated ? parseArkGridComponents(option.text, coreName, coreGrade) : [];
      if (activated && components.length === 0 && /(?:피해|공격력|치명타|재사용|방어력|공격\s*(?:및\s*이동\s*)?속도|이동\s*속도)/.test(option.text)) {
        warning(context, 'UNPARSED_DAMAGE_TOOLTIP', 'incomplete', path, `'${coreName}'의 활성 ${option.requiredPoints}P 옵션을 분류하지 못했습니다.`);
      }
      for (const component of components) {
        if (!ARKGRID_MULTIPLICATIVE.has(component.category)) {
          coreTotals[component.category] = (coreTotals[component.category] ?? ZERO).plus(component.value);
          provenance(context, path, `${coreName} ${component.category}`, component.value, { sourceType: 'OFFICIAL_TOOLTIP+DERIVED' });
          continue;
        }
        let matchingIndex = -1;
        for (let factorIndex = factors.length - 1; factorIndex >= 0; factorIndex -= 1) {
          const factor = factors[factorIndex]!;
          if (factor.corePath === corePath
            && factor.category === component.category
            && factor.scopeKind === component.scopeKind
            && JSON.stringify(factor.scopeValue) === JSON.stringify(component.scopeValue)) {
            matchingIndex = factorIndex;
            break;
          }
        }
        if (component.operator === 'ADD_TO_PREVIOUS' && matchingIndex >= 0) {
          const prior = factors[matchingIndex]!;
          coreTotals[component.category] = (coreTotals[component.category] ?? ZERO).plus(component.value);
          prior.value = decimalString(dec(prior.value).plus(component.value));
          prior.contributionPaths.push(path);
        } else if (component.operator === 'REPLACE' && matchingIndex >= 0) {
          const prior = factors[matchingIndex]!;
          coreTotals[component.category] = coreTotals[component.category]!.minus(prior.value).plus(component.value);
          prior.value = decimalString(component.value);
          prior.contributionPaths.push(path);
        } else {
          coreTotals[component.category] = (coreTotals[component.category] ?? ZERO).plus(component.value);
          factors.push({
            factorId: `${corePath}:${component.category}:${factors.length + 1}`,
            corePath,
            coreName,
            coreGrade,
            category: component.category,
            value: decimalString(component.value),
            scopeKind: component.scopeKind,
            scopeValue: component.scopeValue,
            condition: component.condition,
            requiredPoints: option.requiredPoints,
            contributionPaths: [path]
          });
        }
        provenance(context, path, `${coreName} ${component.category}`, component.value, { sourceType: 'OFFICIAL_TOOLTIP+DERIVED', note: `연산자=${component.operator}` });
      }
      return { requiredPoints: option.requiredPoints, text: option.text, resolvedText: resolveArkGridGradeValues(option.text, coreGrade), activated, path };
    });
    if (tooltipText && options.length === 0) warning(context, 'UNPARSED_ARKGRID_CORE', 'incomplete', `${corePath}.Tooltip`, `'${coreName}' 툴팁에서 [nP] 코어 옵션을 찾지 못했습니다.`);
    cores.push({ path: corePath, name: coreName, grade: coreGrade, point, options });

    for (const [gemIndex, rawGem] of array(slot.Gems).entries()) {
      const gem = object(rawGem);
      if (gem.IsActive !== true) continue;
      const path = `${corePath}.Gems[${gemIndex}].Tooltip`;
      const tooltip = tooltipToText(gem.Tooltip);
      const supportOnly = SUPPORT_ARKGRID_TERMS.some((term) => tooltip.includes(term));
      const scrubbed = tooltip.split('\n').filter((line) => !SUPPORT_ARKGRID_TERMS.some((term) => line.includes(term))).join('\n');
      const values = parseArkGridDamageValues(scrubbed);
      activeGems.push({
        path: `${corePath}.Gems[${gemIndex}]`,
        slotIndex: integer(slot.Index),
        gemIndex: integer(gem.Index),
        grade: text(gem.Grade),
        tooltipText: tooltip,
        values: {
          attackPowerPercent: decimalString(values.attackPowerPercent),
          additionalDamagePercent: decimalString(values.additionalDamagePercent),
          bossDamagePercent: decimalString(values.bossDamagePercent)
        }
      });
      for (const key of Object.keys(values) as Array<keyof typeof values>) {
        gemTotals[key] = gemTotals[key].plus(values[key]);
        if (!values[key].isZero()) provenance(context, path, `아크그리드 젬 ${key}`, values[key], { sourceType: 'OFFICIAL_TOOLTIP' });
      }
      if (Object.values(values).every((value) => value.isZero()) && !supportOnly) {
        warning(context, 'UNPARSED_DAMAGE_TOOLTIP', 'incomplete', path, '활성 아크그리드 젬의 개인 피해 효과를 분류하지 못했습니다.');
      }
    }
  }

  for (const [index, rawEffect] of array(body.Effects).entries()) {
    const effect = object(rawEffect);
    const path = `arkGrid.Effects[${index}]`;
    const name = text(effect.Name) || '아크그리드 누적 효과';
    const tooltip = tooltipToText(effect.Tooltip);
    if (SUPPORT_ARKGRID_TERMS.some((term) => name.includes(term) || tooltip.includes(term))) continue;
    const values = parseArkGridDamageValues(tooltip);
    const parsedAny = Object.values(values).some((value) => !value.isZero());
    if (!parsedAny) {
      if (/(?:피해|공격|치명타)/.test(`${name}\n${tooltip}`)) warning(context, 'UNPARSED_DAMAGE_TOOLTIP', 'incomplete', `${path}.Tooltip`, `'${name}' 효과의 수치를 분류하지 못했습니다.`);
      continue;
    }
    activeAggregateEffects.push({
      path,
      name,
      level: integer(effect.Level),
      tooltipText: tooltip,
      values: {
        attackPowerPercent: decimalString(values.attackPowerPercent),
        additionalDamagePercent: decimalString(values.additionalDamagePercent),
        bossDamagePercent: decimalString(values.bossDamagePercent)
      }
    });
    for (const key of Object.keys(values) as Array<keyof typeof values>) {
      aggregateTotals[key] = aggregateTotals[key].plus(values[key]);
      if (!values[key].isZero()) {
        aggregateCategories.add(key);
        provenance(context, `${path}.Tooltip`, `아크그리드 누적 효과 ${name} ${key}`, values[key], { sourceType: 'OFFICIAL_TOOLTIP' });
      }
    }
  }

  const effective = {
    attackPowerPercent: aggregateCategories.has('attackPowerPercent') ? aggregateTotals.attackPowerPercent : gemTotals.attackPowerPercent,
    additionalDamagePercent: aggregateCategories.has('additionalDamagePercent') ? aggregateTotals.additionalDamagePercent : gemTotals.additionalDamagePercent,
    bossDamagePercent: aggregateCategories.has('bossDamagePercent') ? aggregateTotals.bossDamagePercent : gemTotals.bossDamagePercent
  };
  for (const item of context.provenance) {
    if (item.path.startsWith('arkGrid.Slots[') && item.label.startsWith('아크그리드 젬 ')) {
      const category = item.label.replace('아크그리드 젬 ', '') as keyof typeof aggregateTotals;
      if (aggregateCategories.has(category)) {
        item.applied = false;
        item.excludedReason = '동일 젬 효과 레벨의 ArkGrid.Effects[] 통합값 사용';
        item.note = '개별 젬 값은 검산·출처용이며 중복 합산하지 않음';
      }
    }
  }
  const combined: Record<string, string> = {};
  for (const key of ARKGRID_TOTAL_KEYS) {
    const base = key in effective ? effective[key as keyof typeof effective] : ZERO;
    combined[key] = decimalString(base.plus(coreTotals[key] ?? ZERO));
  }
  return {
    attackPowerPercent: combined.attackPowerPercent!,
    additionalDamagePercent: combined.additionalDamagePercent!,
    bossDamagePercent: combined.bossDamagePercent!,
    attackPowerFlat: combined.attackPowerFlat!,
    weaponAttackFlat: combined.weaponAttackFlat!,
    weaponAttackPercent: combined.weaponAttackPercent!,
    generalDamagePercent: combined.generalDamagePercent!,
    criticalRate: combined.criticalRate!,
    criticalDamage: combined.criticalDamage!,
    criticalHitDamagePercent: combined.criticalHitDamagePercent!,
    attackSpeed: combined.attackSpeed!,
    moveSpeed: combined.moveSpeed!,
    enemyDefenseReductionPercent: combined.enemyDefenseReductionPercent!,
    skillDamagePercent: combined.skillDamagePercent!,
    gemEffects: {
      attackPowerPercent: decimalString(gemTotals.attackPowerPercent),
      additionalDamagePercent: decimalString(gemTotals.additionalDamagePercent),
      bossDamagePercent: decimalString(gemTotals.bossDamagePercent)
    },
    aggregateEffects: {
      attackPowerPercent: decimalString(aggregateTotals.attackPowerPercent),
      additionalDamagePercent: decimalString(aggregateTotals.additionalDamagePercent),
      bossDamagePercent: decimalString(aggregateTotals.bossDamagePercent)
    },
    effectiveBaseEffects: {
      attackPowerPercent: decimalString(effective.attackPowerPercent),
      additionalDamagePercent: decimalString(effective.additionalDamagePercent),
      bossDamagePercent: decimalString(effective.bossDamagePercent)
    },
    coreEffects: Object.fromEntries(ARKGRID_TOTAL_KEYS.map((key) => [key, decimalString(coreTotals[key] ?? ZERO)])),
    coreDamageFactors: factors,
    activeGems,
    activeAggregateEffects,
    cores
  };
}

function snapshotId(bundle: JsonObject, characterName: string): string {
  const captured = text(bundle.capturedAtKst) || 'uncaptured';
  return `${characterName}:${captured}`;
}

function validateObjectArray(value: unknown, path: string): JsonObject[] {
  if (!Array.isArray(value)) {
    throw new Error(`Malformed Lost Ark endpoint payload: ${path} must be an array`);
  }
  return value.map((member, index) => {
    if (member === null || typeof member !== 'object' || Array.isArray(member)) {
      throw new Error(`Malformed Lost Ark endpoint payload: ${path}[${index}] must be an object`);
    }
    return member as JsonObject;
  });
}

function validateEndpointPayloads(bundle: JsonObject): JsonObject {
  if (bundle.responses === null || typeof bundle.responses !== 'object' || Array.isArray(bundle.responses)) {
    throw new Error('Malformed Lost Ark endpoint payload: responses must be an object');
  }
  const responses = bundle.responses as JsonObject;
  const missing = ENDPOINT_SOURCES.filter((key) => !(key in responses));
  if (missing.length > 0) throw new Error(`Missing Lost Ark endpoint payloads: ${missing.join(', ')}`);

  const arrayEndpoints = ['equipment', 'avatars', 'combatSkills'] as const;
  for (const endpoint of arrayEndpoints) {
    if (!Array.isArray(responses[endpoint])) {
      throw new Error(`Malformed Lost Ark endpoint payload: responses.${endpoint} must be an array`);
    }
  }
  const objectEndpoints = ['profiles', 'engravings', 'cards', 'gems', 'arkPassive', 'arkGrid'] as const;
  for (const endpoint of objectEndpoints) {
    const value = responses[endpoint];
    if (value === null || typeof value !== 'object' || Array.isArray(value)) {
      throw new Error(`Malformed Lost Ark endpoint payload: responses.${endpoint} must be an object`);
    }
  }

  const profiles = responses.profiles as JsonObject;
  const engravings = responses.engravings as JsonObject;
  const cards = responses.cards as JsonObject;
  const gems = responses.gems as JsonObject;
  const arkPassive = responses.arkPassive as JsonObject;
  const arkGrid = responses.arkGrid as JsonObject;

  validateObjectArray(profiles.Stats, 'responses.profiles.Stats');
  validateObjectArray(responses.equipment, 'responses.equipment');
  validateObjectArray(responses.avatars, 'responses.avatars');
  const combatSkills = validateObjectArray(responses.combatSkills, 'responses.combatSkills');
  for (const [skillIndex, skill] of combatSkills.entries()) {
    validateObjectArray(skill.Tripods, `responses.combatSkills[${skillIndex}].Tripods`);
  }
  const arkPassiveEngravings = engravings.ArkPassiveEffects;
  if (Array.isArray(arkPassiveEngravings) && arkPassiveEngravings.length > 0) {
    validateObjectArray(arkPassiveEngravings, 'responses.engravings.ArkPassiveEffects');
  } else if (arkPassiveEngravings === undefined || arkPassiveEngravings === null || Array.isArray(arkPassiveEngravings)) {
    validateObjectArray(engravings.Effects, 'responses.engravings.Effects');
  } else {
    throw new Error('Malformed Lost Ark endpoint payload: responses.engravings.ArkPassiveEffects must be an array, null, or absent');
  }
  validateObjectArray(cards.Cards, 'responses.cards.Cards');
  const cardEffects = validateObjectArray(cards.Effects, 'responses.cards.Effects');
  for (const [effectIndex, effect] of cardEffects.entries()) {
    validateObjectArray(effect.Items, `responses.cards.Effects[${effectIndex}].Items`);
  }
  validateObjectArray(gems.Gems, 'responses.gems.Gems');
  validateObjectArray(arkPassive.Points, 'responses.arkPassive.Points');
  validateObjectArray(arkPassive.Effects, 'responses.arkPassive.Effects');
  const arkGridSlots = validateObjectArray(arkGrid.Slots, 'responses.arkGrid.Slots');
  for (const [slotIndex, slot] of arkGridSlots.entries()) {
    validateObjectArray(slot.Gems, `responses.arkGrid.Slots[${slotIndex}].Gems`);
  }
  validateObjectArray(arkGrid.Effects, 'responses.arkGrid.Effects');
  return responses;
}

export function parseBuildSnapshot(rawBundle: unknown): ParsedBuildSnapshot {
  const bundle = object(rawBundle);
  const responses = validateEndpointPayloads(bundle);
  const context: ParseContext = { warnings: [], provenance: [] };
  const profileBody = object(responses.profiles);
  const characterName = text(bundle.characterName) || text(profileBody.CharacterName);
  if (!characterName.trim()) {
    throw new Error('Malformed Lost Ark endpoint payload: responses.profiles.CharacterName must be a non-empty string');
  }
  const build: NormalizedBuild = {
    endpointSources: [...ENDPOINT_SOURCES],
    profile: parseProfile(responses.profiles, context),
    equipment: parseEquipment(responses.equipment, context),
    avatars: parseAvatars(responses.avatars, context),
    pet: {
      mainStatPercent: '0.01',
      additionalDamagePercent: '0.01',
      demonDamagePercent: '0.005',
      source: 'current-v2.7.2 verified fixed scenario'
    },
    engravings: parseEngravings(responses.engravings, context),
    cards: parseCards(responses.cards, context),
    gems: parseGems(responses.gems, context),
    arkPassive: parseArkPassive(responses.arkPassive, context),
    combatSkills: parseCombatSkills(responses.combatSkills, context),
    arkGrid: parseArkGrid(responses.arkGrid, context),
    provenance: context.provenance
  };
  if (build.profile.className !== '기상술사') {
    warning(context, 'UNSUPPORTED_CLASS', 'incomplete', 'profiles.CharacterClassName', `지원 대상은 기상술사이며 현재 클래스는 '${build.profile.className}'입니다.`);
  }
  const calculatedAttackPower = reconstructAttackPower(build).final;
  if (build.profile.expeditionLevel !== 272) {
    warning(
      context,
      'FIXED_EXPEDITION_STAT_MISMATCH',
      'warning',
      'profiles.ExpeditionLevel',
      `현재 원정대 레벨은 ${build.profile.expeditionLevel}이지만 current-v2.7.2 고정 주스탯 +680을 사용했습니다.`
    );
  }
  if (!dec(calculatedAttackPower).eq(build.profile.profileAttackPower)) {
    warning(
      context,
      'CALCULATED_ATTACK_POWER_OVERRIDE',
      'warning',
      'profiles.Stats[공격력]',
      '재구성 공격력과 API 프로필 공격력이 달라 current-v2.7.2의 재구성 공격력을 피해 계산에 사용합니다.'
    );
    provenance(context, 'calculation.attackPower.final', '재구성 공격력', calculatedAttackPower, {
      sourceType: 'DERIVED_CURRENT_V2_7_2',
      note: `API 프로필 공격력 ${build.profile.profileAttackPower}은 검산용으로만 유지`
    });
  }
  return {
    schemaVersion: '1',
    snapshotId: snapshotId(bundle, characterName),
    characterName,
    classId: 'weather-artist',
    calculatorVersion: 'current-v2.7.2',
    parserVersion: PARSER_VERSION,
    catalogVersion: WEATHER_ARTIST_CATALOG_VERSION,
    calculatedAttackPower,
    warnings: context.warnings,
    build
  };
}
