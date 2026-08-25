import { calculateAttackPower } from '@weather-artist/calculator';
import type { BuildPatch, BuildSnapshot, NormalizedBuild } from '@weather-artist/contracts';

const ZERO = '0';
const ZERO_ARK_GRID_VALUES = {
  attackPowerPercent: ZERO,
  additionalDamagePercent: ZERO,
  bossDamagePercent: ZERO
};

function restoreSection(candidate: NormalizedBuild, baseline: NormalizedBuild, sectionId: string): void {
  switch (sectionId) {
    case 'equipment':
    case 'accessories':
      candidate.equipment = structuredClone(baseline.equipment);
      return;
    case 'gems':
      candidate.gems = structuredClone(baseline.gems);
      return;
    case 'engravings':
      candidate.engravings = structuredClone(baseline.engravings);
      return;
    case 'ark-passive':
      candidate.arkPassive = structuredClone(baseline.arkPassive);
      return;
    case 'ark-grid':
      candidate.arkGrid = structuredClone(baseline.arkGrid);
      return;
    case 'cards-avatar-pet':
      candidate.cards = structuredClone(baseline.cards);
      candidate.avatars = structuredClone(baseline.avatars);
      candidate.pet = structuredClone(baseline.pet);
      return;
    case 'skills-tripods':
      candidate.combatSkills = structuredClone(baseline.combatSkills);
      return;
    default:
      throw new Error(`Unknown section: ${sectionId}`);
  }
}

function disableSection(build: NormalizedBuild, sectionId: string): void {
  switch (sectionId) {
    case 'gems':
      build.gems = { baseAttackPercent: ZERO, items: [], skillEffects: [] };
      return;
    case 'engravings':
      build.engravings = { names: [], stoneLevelTotal: 0, stoneBaseAttackPercent: ZERO, effects: {} };
      return;
    case 'ark-passive':
      build.arkPassive = {
        karmaWeaponAttackPercent: ZERO,
        karmaEvolutionDamage: ZERO,
        evolutionDamageByName: {},
        skillDamageByName: {},
        criticalRateByName: {},
        criticalDamageByName: {},
        criticalHitDamageByName: {},
        additionalDamageByName: {},
        speedByName: {},
        effects: [],
        points: []
      };
      return;
    case 'ark-grid':
      build.arkGrid = {
        attackPowerPercent: ZERO,
        additionalDamagePercent: ZERO,
        bossDamagePercent: ZERO,
        attackPowerFlat: ZERO,
        weaponAttackFlat: ZERO,
        weaponAttackPercent: ZERO,
        generalDamagePercent: ZERO,
        criticalRate: ZERO,
        criticalDamage: ZERO,
        criticalHitDamagePercent: ZERO,
        attackSpeed: ZERO,
        moveSpeed: ZERO,
        enemyDefenseReductionPercent: ZERO,
        skillDamagePercent: ZERO,
        gemEffects: { ...ZERO_ARK_GRID_VALUES },
        aggregateEffects: { ...ZERO_ARK_GRID_VALUES },
        effectiveBaseEffects: { ...ZERO_ARK_GRID_VALUES },
        coreEffects: {},
        coreDamageFactors: [],
        activeGems: [],
        activeAggregateEffects: [],
        cores: []
      };
      return;
    case 'cards-avatar-pet':
      build.cards = { damagePercent: ZERO };
      build.avatars = { mainStatPercent: ZERO, items: [] };
      build.pet = {
        mainStatPercent: ZERO,
        additionalDamagePercent: ZERO,
        demonDamagePercent: ZERO,
        source: 'disabled by validated section patch'
      };
      return;
    case 'skills-tripods':
      build.combatSkills = {
        skillNames: [...build.combatSkills.skillNames],
        hasExposedWeakness: false,
        selectedTripods: []
      };
      return;
    default:
      throw new Error(`Section cannot be disabled: ${sectionId}`);
  }
}

export function applyBuildPatches(snapshot: BuildSnapshot, patches: BuildPatch[]): BuildSnapshot {
  const candidate = structuredClone(snapshot);
  for (const patch of patches) {
    if (patch.kind === 'reset-section') {
      restoreSection(candidate.build, snapshot.build, patch.sectionId);
    } else if (patch.kind === 'set-section-enabled') {
      if (patch.enabled) restoreSection(candidate.build, snapshot.build, patch.sectionId);
      else disableSection(candidate.build, patch.sectionId);
    } else {
      throw new Error(`Unsupported patch operation: ${patch.kind}`);
    }
  }
  candidate.calculatedAttackPower = calculateAttackPower(candidate).final;
  return candidate;
}
