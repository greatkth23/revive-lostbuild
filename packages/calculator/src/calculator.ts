import type {
  BuildSnapshot,
  CalculationCheckpointsContract,
  DirectionTag,
  HitDamageResult,
  NormalizedBuild,
  SkillDamageResult
} from '@weather-artist/contracts';
import { weatherArtistCatalog } from '@weather-artist/catalog';
import { reconstructAttackPower, type AttackPowerCheckpoints } from './attack-power.js';
import { Decimal, dec, decimalString, product, sum } from './decimal.js';

type ParsedSnapshot = Omit<BuildSnapshot, 'build'> & { build: NormalizedBuild };
type ArkGridFactor = NormalizedBuild['arkGrid']['coreDamageFactors'][number];

export interface DirectionalAttackResult {
  tag: DirectionTag;
  label: string;
  success: boolean;
  applied: boolean;
  damagePercent: string;
  criticalRate: string;
}

export interface EmbeddedTripodEffect {
  tripodName: string;
  type: string;
  label: string;
  percent: string;
  applicationMode: 'EMBEDDED_MOTION_HIT';
}

export type CalculationCheckpoints = CalculationCheckpointsContract;
export type DetailedSkillDamageResult = SkillDamageResult;

const SKILL_NAME_TO_ID: Record<string, string> = Object.fromEntries(
  weatherArtistCatalog.skills.map((skill) => [skill.displayName, skill.id])
);
const SUPPORTED_GENERAL_DAMAGE_ENGRAVINGS = ['원한', '저주받은 인형', '질량 증가', '타격의 대가'];
const FIXED = {
  defenseConstant: new Decimal('6500'),
  enemyDefense: new Decimal('5850'),
  enemyDamageTakenMultiplier: new Decimal('0.76'),
  baseCriticalDamage: new Decimal('2'),
  combatBlessingAttackSpeedPercent: new Decimal('0.09'),
  combatBlessingMoveSpeedPercent: new Decimal('0.09'),
  feastAttackSpeedPercent: new Decimal('0.05'),
  feastMoveSpeedPercent: new Decimal('0.05'),
  speedCap: new Decimal('1.4')
};

function requireBuild(snapshot: BuildSnapshot): asserts snapshot is ParsedSnapshot {
  if (!snapshot.build) throw new Error('BuildSnapshot does not contain normalized build data.');
}

function resolveSkill(skillIdOrName: string) {
  const skillId = SKILL_NAME_TO_ID[skillIdOrName] ?? skillIdOrName;
  const skill = weatherArtistCatalog.skills.find((entry) => entry.id === skillId);
  if (!skill) throw new Error(`Unsupported Weather Artist skill '${skillIdOrName}'.`);
  return skill;
}

export function directionalAttackBonus(tag: DirectionTag, success = true): DirectionalAttackResult {
  const rule = tag === 'BACK_ATTACK'
    ? { label: '백 어택', damagePercent: '0.05', criticalRate: '0.1' }
    : tag === 'FRONTAL_ATTACK'
      ? { label: '헤드 어택', damagePercent: '0.2', criticalRate: '0' }
      : { label: '비방향성', damagePercent: '0', criticalRate: '0' };
  const applied = success && tag !== 'NON_DIRECTIONAL';
  return {
    tag,
    label: rule.label,
    success,
    applied,
    damagePercent: applied ? rule.damagePercent : '0',
    criticalRate: applied ? rule.criticalRate : '0'
  };
}

export function calculateAttackPower(snapshot: BuildSnapshot): AttackPowerCheckpoints {
  requireBuild(snapshot);
  return reconstructAttackPower(snapshot.build);
}

function sonicBreakthrough(build: NormalizedBuild): Decimal {
  const node = build.arkPassive.effects.find((effect) => effect.name === '음속 돌파');
  if (!node) return new Decimal(0);
  const level = node.level ?? 2;
  const massSpeed = dec(build.engravings.effects['질량 증가']?.attackSpeed ?? 0);
  const gale = build.arkPassive.speedByName['질풍노도'] ?? { attackSpeed: '0', moveSpeed: '0' };
  const rawAttackSpeed = dec(1)
    .plus(build.profile.attackSpeedFromSwiftness)
    .plus(massSpeed)
    .plus(FIXED.combatBlessingAttackSpeedPercent)
    .plus(FIXED.feastAttackSpeedPercent)
    .plus(gale.attackSpeed)
    .plus(build.arkGrid.attackSpeed);
  const rawMoveSpeed = dec(1)
    .plus(build.profile.moveSpeedFromSwiftness)
    .plus(FIXED.combatBlessingMoveSpeedPercent)
    .plus(FIXED.feastMoveSpeedPercent)
    .plus(gale.moveSpeed)
    .plus(build.arkGrid.moveSpeed);
  const attackIncrease = rawAttackSpeed.minus(1);
  const moveIncrease = rawMoveSpeed.minus(1);
  const capIncrease = new Decimal('0.4');
  const baseRate = level <= 1 ? new Decimal('0.05') : new Decimal('0.10');
  const bothBonus = level <= 1 ? new Decimal('0.04') : new Decimal('0.08');
  const overRate = level <= 1 ? new Decimal('0.15') : new Decimal('0.30');
  const maximum = level <= 1 ? new Decimal('0.12') : new Decimal('0.24');
  const base = baseRate.times(Decimal.min(attackIncrease, capIncrease).plus(Decimal.min(moveIncrease, capIncrease)));
  const both = attackIncrease.gt(capIncrease) && moveIncrease.gt(capIncrease) ? bothBonus : new Decimal(0);
  const over = overRate.times(Decimal.max(attackIncrease.minus(capIncrease), 0).plus(Decimal.max(moveIncrease.minus(capIncrease), 0)));
  return Decimal.min(maximum, base.plus(both).plus(over));
}

function regularGemEffect(build: NormalizedBuild, skillName: string): { damage: Decimal; cooldown: Decimal } {
  let damage = new Decimal(0);
  let cooldown = new Decimal(0);
  for (const effect of build.gems.skillEffects) {
    if (effect.skillName !== skillName) continue;
    if (effect.effectType === 'damage') damage = Decimal.max(damage, effect.value);
    if (effect.effectType === 'cooldownReduction') cooldown = Decimal.max(cooldown, effect.value);
  }
  return { damage, cooldown };
}

function skillDamageScope(
  effectName: string,
  skill: (typeof weatherArtistCatalog.skills)[number]
): boolean {
  if (effectName === '공간 가르기') return skill.id === 'space-cutting';
  if (effectName === '단련된 가르기') return skill.id === 'thunderstorm';
  if (effectName === '바람의 길') return skill.tags.includes('UMBRELLA_SKILL');
  if (effectName === '풀려난 힘') return skill.tags.includes('HYPER_AWAKENING_SKILL');
  return true;
}

function arkGridFactorScope(
  factor: ArkGridFactor,
  skill: (typeof weatherArtistCatalog.skills)[number]
): boolean {
  if (factor.scopeKind === 'ALL') return true;
  if (factor.scopeKind === 'SKILL_TAG') return skill.tags.includes(factor.scopeValue as never);
  if (factor.scopeKind === 'SKILL_NAMES') return (factor.scopeValue as string[]).includes(skill.displayName);
  return false;
}

function floorString(value: Decimal): string {
  return value.toDecimalPlaces(0, Decimal.ROUND_FLOOR).toFixed(0);
}

function hitResult(
  name: string,
  hitBase: Decimal,
  commonMultiplier: Decimal,
  criticalMultiplier: Decimal,
  criticalRate: Decimal
): HitDamageResult & { nonCriticalRaw: Decimal; criticalRaw: Decimal; expectedRaw: Decimal } {
  const nonCriticalRaw = hitBase.times(commonMultiplier);
  const criticalRaw = nonCriticalRaw.times(criticalMultiplier);
  const expectedRaw = criticalRaw.times(criticalRate).plus(nonCriticalRaw.times(dec(1).minus(criticalRate)));
  return {
    schemaVersion: '1',
    hitName: name,
    nonCriticalDamage: floorString(nonCriticalRaw),
    criticalDamage: floorString(criticalRaw),
    expectedDamage: floorString(expectedRaw),
    nonCriticalRaw,
    criticalRaw,
    expectedRaw
  };
}

export function calculateSkillDamage(
  snapshot: BuildSnapshot,
  skillIdOrName: string,
  options: { directionalSuccess?: boolean } = {}
): DetailedSkillDamageResult {
  requireBuild(snapshot);
  const build = snapshot.build;
  const skill = resolveSkill(skillIdOrName);
  const attackPower = reconstructAttackPower(build);
  const direction = directionalAttackBonus(skill.directionTag, options.directionalSuccess ?? true);

  const motionCoefficients = skill.hits.map((hit) => dec(hit.coefficient).times(skill.hitMotionCoefficient));
  const selectedTripods = build.combatSkills.selectedTripods.filter((tripod) => tripod.skillName === skill.displayName);
  const multiplierTripods = selectedTripods.flatMap((tripod) => tripod.damageEffects
    .filter((effect) => effect.applicationMode === 'MULTIPLIER')
    .map((effect) => ({ ...effect, tripodName: tripod.name })));
  const embeddedTripodEffects: EmbeddedTripodEffect[] = selectedTripods.flatMap((tripod) => tripod.damageEffects
    .filter((effect) => effect.applicationMode === 'EMBEDDED_MOTION_HIT')
    .map((effect) => ({
      tripodName: tripod.name,
      type: effect.type,
      label: effect.label,
      percent: effect.percent,
      applicationMode: 'EMBEDDED_MOTION_HIT' as const
    })));
  const tripodDamageMultiplier = product(multiplierTripods.map((effect) => effect.multiplier));
  const tripodCriticalDamage = sum(selectedTripods.map((tripod) => tripod.criticalDamagePercent));

  const evolutionParts = Object.entries(build.arkPassive.evolutionDamageByName)
    .filter(([name, value]) => name !== '음속 돌파' && !dec(value).isZero())
    .map(([, value]) => dec(value));
  if (!dec(build.arkPassive.karmaEvolutionDamage).isZero()) evolutionParts.push(dec(build.arkPassive.karmaEvolutionDamage));
  const sonic = sonicBreakthrough(build);
  if (!sonic.isZero()) evolutionParts.push(sonic);
  const evolutionDamage = sum(evolutionParts);
  const appliedArkPassiveEffects: CalculationCheckpoints['arkPassive']['appliedEffects'] = [
    ...Object.entries(build.arkPassive.evolutionDamageByName)
      .filter(([name, value]) => name !== '음속 돌파' && !dec(value).isZero())
      .map(([name, value]) => ({ name, category: 'evolutionDamage', value })),
    ...(!dec(build.arkPassive.karmaEvolutionDamage).isZero()
      ? [{ name: '진화 카르마', category: 'evolutionDamage', value: build.arkPassive.karmaEvolutionDamage }]
      : []),
    ...(!sonic.isZero()
      ? [{ name: '음속 돌파', category: 'evolutionDamage', value: decimalString(sonic) }]
      : [])
  ];

  const generalEngravingParts: Decimal[] = [];
  for (const engravingName of SUPPORTED_GENERAL_DAMAGE_ENGRAVINGS) {
    const effect = build.engravings.effects[engravingName];
    if (!effect) continue;
    const hitMasterEligible = engravingName !== '타격의 대가'
      || (skill.tags.includes('NON_DIRECTIONAL') && !skill.tags.includes('AWAKENING_SKILL' as never));
    if (hitMasterEligible && !dec(effect.generalDamage).isZero()) generalEngravingParts.push(dec(effect.generalDamage));
  }

  const appliedSkillDamageEffects = Object.entries(build.arkPassive.skillDamageByName)
    .filter(([name, value]) => !dec(value).isZero() && skillDamageScope(name, skill));
  appliedArkPassiveEffects.push(...appliedSkillDamageEffects.map(([name, value]) => ({ name, category: 'skillDamage', value })));
  appliedArkPassiveEffects.push(...Object.entries(build.arkPassive.additionalDamageByName)
    .filter(([, value]) => !dec(value).isZero())
    .map(([name, value]) => ({ name, category: 'additionalDamage', value })));
  const appliedCoreFactors = build.arkGrid.coreDamageFactors.filter((factor) => arkGridFactorScope(factor, skill));
  const subtitleCoreFactors = appliedCoreFactors.filter((factor) => ['generalDamagePercent', 'bossDamagePercent', 'skillDamagePercent'].includes(factor.category));
  const gem = regularGemEffect(build, skill.displayName);

  const rawMoveSpeed = dec(1)
    .plus(build.profile.moveSpeedFromSwiftness)
    .plus(FIXED.combatBlessingMoveSpeedPercent)
    .plus(FIXED.feastMoveSpeedPercent)
    .plus(build.arkPassive.speedByName['질풍노도']?.moveSpeed ?? 0)
    .plus(build.arkGrid.moveSpeed);
  const raidCaptainEffect = build.engravings.effects['돌격대장'];
  const parsedRaidCaptainCoefficient = dec(raidCaptainEffect?.raidCaptainCoefficient ?? 0);
  const raidCaptainCoefficient = parsedRaidCaptainCoefficient.isZero()
    ? new Decimal('0.48')
    : parsedRaidCaptainCoefficient;
  const raidCaptain = raidCaptainEffect
    ? Decimal.max(0, Decimal.min(rawMoveSpeed, FIXED.speedCap).minus(1)).times(raidCaptainCoefficient)
    : new Decimal(0);
  const arkGridBossDamage = dec(build.arkGrid.effectiveBaseEffects.bossDamagePercent);

  const subtitlePercentages: Decimal[] = [
    ...generalEngravingParts,
    evolutionDamage,
    dec(build.calculationInputs.pet.demonDamagePercent).plus(build.calculationInputs.accountBonuses.collectionDemonDamagePercent),
    build.cards.damagePercent,
    raidCaptain,
    ...appliedSkillDamageEffects.map(([, value]) => dec(value)),
    build.equipment.necklaceDamageToEnemy,
    build.equipment.braceletDamageToEnemy,
    build.equipment.otherDamageToEnemy,
    build.equipment.braceletNonDirectionalDamage,
    arkGridBossDamage,
    ...subtitleCoreFactors.map((factor) => dec(factor.value)),
    ...multiplierTripods.map((effect) => dec(effect.percent)),
    gem.damage,
    direction.damagePercent
  ].map(dec);
  const totalSubtitleMultiplier = product(subtitlePercentages.map((value) => dec(1).plus(value)));

  const additionalDamagePercent = dec(build.equipment.weaponAdditionalDamage)
    .plus(build.equipment.necklaceAdditionalDamage)
    .plus(build.equipment.otherAdditionalDamage)
    .plus(sum(Object.values(build.arkPassive.additionalDamageByName)))
    .plus(build.calculationInputs.pet.additionalDamagePercent)
    .plus(build.arkGrid.additionalDamagePercent);
  const defenseRetentionMultiplier = product(appliedCoreFactors
    .filter((factor) => factor.category === 'enemyDefenseReductionPercent')
    .map((factor) => dec(1).minus(factor.value)));
  const effectiveDefense = FIXED.enemyDefense.times(defenseRetentionMultiplier);
  const defenseMultiplier = FIXED.defenseConstant.div(FIXED.defenseConstant.plus(effectiveDefense));
  const commonDamageMultiplier = dec(1)
    .plus(additionalDamagePercent)
    .times(totalSubtitleMultiplier)
    .times(FIXED.enemyDamageTakenMultiplier)
    .times(defenseMultiplier);

  const adrenalineCrit = dec(build.engravings.effects['아드레날린']?.criticalRate ?? 0);
  const arkPassiveCriticalRateEntries = Object.entries(build.arkPassive.criticalRateByName)
    .filter(([, value]) => !dec(value).isZero());
  appliedArkPassiveEffects.push(...arkPassiveCriticalRateEntries.map(([name, value]) => ({ name, category: 'criticalRate', value })));
  const criticalRateComponents: CalculationCheckpoints['criticalRate']['components'] = [
    { label: '치명 스탯', value: build.profile.criticalRateFromStat },
    { label: '장비 치명타 적중률', value: build.equipment.criticalRate },
    { label: '아드레날린', value: decimalString(adrenalineCrit) },
    ...arkPassiveCriticalRateEntries.map(([name, value]) => ({ label: `아크패시브 ${name}`, value })),
    { label: '급소 노출', value: build.combatSkills.hasExposedWeakness ? '0.1' : '0' },
    { label: '아크그리드 치명타 적중률', value: build.arkGrid.criticalRate },
    { label: direction.label, value: direction.criticalRate }
  ];
  const criticalRate = Decimal.min(1, Decimal.max(0,
    dec(build.profile.criticalRateFromStat)
      .plus(build.equipment.criticalRate)
      .plus(adrenalineCrit)
      .plus(sum(Object.values(build.arkPassive.criticalRateByName)))
      .plus(build.combatSkills.hasExposedWeakness ? '0.1' : 0)
      .plus(build.arkGrid.criticalRate)
      .plus(direction.criticalRate)
  ));
  const arkPassiveCriticalDamageEntries = Object.entries(build.arkPassive.criticalDamageByName)
    .filter(([, value]) => !dec(value).isZero());
  appliedArkPassiveEffects.push(...arkPassiveCriticalDamageEntries.map(([name, value]) => ({ name, category: 'criticalDamage', value })));
  const criticalDamageAdditiveComponents: CalculationCheckpoints['criticalMultiplier']['additiveComponents'] = [
    { label: '기본 치명타 피해', value: decimalString(FIXED.baseCriticalDamage) },
    { label: '장비 치명타 피해', value: build.equipment.criticalDamage },
    ...arkPassiveCriticalDamageEntries.map(([name, value]) => ({ label: `아크패시브 ${name}`, value })),
    { label: '아크그리드 치명타 피해', value: build.arkGrid.criticalDamage },
    { label: '트라이포드 치명타 피해', value: decimalString(tripodCriticalDamage) }
  ];
  const criticalDamageMultiplier = FIXED.baseCriticalDamage
    .plus(build.equipment.criticalDamage)
    .plus(sum(Object.values(build.arkPassive.criticalDamageByName)))
    .plus(build.arkGrid.criticalDamage)
    .plus(tripodCriticalDamage);
  const coreCriticalMultiplier = product(appliedCoreFactors
    .filter((factor) => factor.category === 'criticalHitDamagePercent')
    .map((factor) => dec(1).plus(factor.value)));
  const criticalHitDamageMultiplier = dec(1)
    .plus(build.arkPassive.criticalHitDamageByName['회심'] ?? 0)
    .times(dec(1).plus(build.equipment.braceletCriticalHitDamage))
    .times(coreCriticalMultiplier);
  const fullCriticalMultiplier = criticalDamageMultiplier.times(criticalHitDamageMultiplier);
  const arkPassiveCriticalHitEntries = Object.entries(build.arkPassive.criticalHitDamageByName)
    .filter(([, value]) => !dec(value).isZero());
  appliedArkPassiveEffects.push(...arkPassiveCriticalHitEntries.map(([name, value]) => ({ name, category: 'criticalHitDamage', value })));
  const criticalDamageMultiplicativeComponents: CalculationCheckpoints['criticalMultiplier']['multiplicativeComponents'] = [
    ...arkPassiveCriticalHitEntries.map(([name, value]) => ({ label: `아크패시브 ${name}`, value: decimalString(dec(1).plus(value)) })),
    { label: '팔찌 입는 치명타 피해', value: decimalString(dec(1).plus(build.equipment.braceletCriticalHitDamage)) },
    ...appliedCoreFactors
      .filter((factor) => factor.category === 'criticalHitDamagePercent')
      .map((factor) => ({ label: factor.coreName, value: decimalString(dec(1).plus(factor.value)) }))
  ];

  const internalHits = skill.hits.map((hit, index) => {
    const coefficient = motionCoefficients[index]!;
    const hitBase = coefficient.times(attackPower.usedForDamage).plus(hit.constant);
    return hitResult(hit.name, hitBase, commonDamageMultiplier, fullCriticalMultiplier, criticalRate);
  });
  const nonCriticalRaw = sum(internalHits.map((hit) => hit.nonCriticalRaw));
  const criticalRaw = sum(internalHits.map((hit) => hit.criticalRaw));
  const expectedRaw = sum(internalHits.map((hit) => hit.expectedRaw));
  const repeatedUmbrellaFactors = appliedCoreFactors.filter((factor) => factor.coreName.includes('우산의 춤')
    && factor.category === 'skillDamagePercent'
    && factor.value === '0.002');

  const result: DetailedSkillDamageResult = {
    schemaVersion: '1',
    skillId: skill.id,
    nonCriticalDamage: floorString(nonCriticalRaw),
    criticalDamage: floorString(criticalRaw),
    expectedDamage: floorString(expectedRaw),
    criticalRate: decimalString(criticalRate),
    criticalMultiplier: decimalString(fullCriticalMultiplier),
    hits: internalHits.map(({ nonCriticalRaw: _n, criticalRaw: _c, expectedRaw: _e, ...hit }) => hit),
    rationale: [
      `current-v2.7.2 calculated attack power ${attackPower.usedForDamage}`,
      `Ark Grid aggregate/gem provenance retained; effective attack/additional categories deduplicated`,
      `direction=${direction.tag}; applied=${direction.applied}`,
      ...snapshot.warnings.map((item) => `${item.path}: ${item.message}`)
    ],
    checkpoints: {
      attackPower,
      motionCoefficients: motionCoefficients.map(decimalString),
      criticalRate: { components: criticalRateComponents, result: decimalString(criticalRate) },
      criticalMultiplier: {
        additiveComponents: criticalDamageAdditiveComponents,
        additiveResult: decimalString(criticalDamageMultiplier),
        multiplicativeComponents: criticalDamageMultiplicativeComponents,
        result: decimalString(fullCriticalMultiplier)
      },
      selectedTripods,
      regularGem: { damagePercent: decimalString(gem.damage), cooldownReductionPercent: decimalString(gem.cooldown) },
      directional: direction,
      arkPassive: { appliedEffects: appliedArkPassiveEffects },
      arkGrid: {
        appliedFactors: appliedCoreFactors,
        repeatedPointMultiplier: decimalString(product(repeatedUmbrellaFactors.map((factor) => dec(1).plus(factor.value)))),
        commonDamageMultiplier: decimalString(commonDamageMultiplier)
      },
      tripodDamageMultiplier: decimalString(tripodDamageMultiplier),
      embeddedTripodEffects
    }
  };
  return result;
}

export function calculateAllSkillDamage(
  snapshot: BuildSnapshot,
  options: { directionalSuccessBySkill?: Record<string, boolean> } = {}
): DetailedSkillDamageResult[] {
  return weatherArtistCatalog.skills.map((skill) => calculateSkillDamage(snapshot, skill.id, {
    directionalSuccess: options.directionalSuccessBySkill?.[skill.id] ?? true
  }));
}
