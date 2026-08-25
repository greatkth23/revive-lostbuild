import { z } from 'zod';

export type DecimalString = string;
export const decimalStringSchema = z.string().regex(/^-?\d+(?:\.\d+)?$/, 'Expected a decimal string');
export const contractSchemaVersion = z.literal('1');

export const warningSchema = z.object({
  schemaVersion: contractSchemaVersion,
  code: z.string().min(1),
  severity: z.enum(['info', 'warning', 'incomplete']),
  path: z.string().min(1),
  message: z.string().min(1)
});
export type Warning = z.infer<typeof warningSchema>;

export const provenanceSchema = z.object({
  schemaVersion: contractSchemaVersion,
  sourceType: z.string().min(1),
  path: z.string().min(1),
  label: z.string().min(1),
  value: z.string(),
  parsed: z.boolean(),
  eligible: z.boolean(),
  applied: z.boolean(),
  excludedReason: z.string(),
  note: z.string()
});
export type Provenance = z.infer<typeof provenanceSchema>;

const decimalMapSchema = z.record(z.string(), decimalStringSchema);
const equipmentValuesSchema = z.object({
  mainStat: decimalStringSchema,
  baseWeaponAttack: decimalStringSchema,
  weaponAttackFlat: decimalStringSchema,
  weaponAttackPercent: decimalStringSchema,
  baseAttackPowerFlat: decimalStringSchema,
  baseAttackPowerPercent: decimalStringSchema,
  attackPowerFlat: decimalStringSchema,
  attackPowerPercent: decimalStringSchema,
  additionalDamage: decimalStringSchema,
  damageToEnemy: decimalStringSchema,
  criticalRate: decimalStringSchema,
  criticalDamage: decimalStringSchema,
  criticalHitDamage: decimalStringSchema,
  nonDirectionalDamage: decimalStringSchema
});

const normalizedEquipmentSchema = equipmentValuesSchema.extend({
  weaponAdditionalDamage: decimalStringSchema,
  necklaceAdditionalDamage: decimalStringSchema,
  otherAdditionalDamage: decimalStringSchema,
  necklaceDamageToEnemy: decimalStringSchema,
  braceletDamageToEnemy: decimalStringSchema,
  otherDamageToEnemy: decimalStringSchema,
  braceletCriticalHitDamage: decimalStringSchema,
  braceletNonDirectionalDamage: decimalStringSchema,
  hasMasterElixir: z.boolean(),
  items: z.array(z.object({
    type: z.string(),
    name: z.string(),
    grade: z.string(),
    tooltipText: z.string(),
    values: equipmentValuesSchema
  }))
});

const engravingEffectSchema = z.object({
  generalDamage: decimalStringSchema,
  raidCaptainCoefficient: decimalStringSchema,
  attackSpeed: decimalStringSchema,
  attackPowerPercent: decimalStringSchema,
  attackPowerPerStack: decimalStringSchema,
  maxStacks: z.number().int().nonnegative(),
  criticalRate: decimalStringSchema
});

const skillGemEffectSchema = z.object({
  skillName: z.string(),
  effectType: z.enum(['damage', 'cooldownReduction']),
  value: decimalStringSchema,
  sourceGemIndex: z.number().int().nonnegative()
});

const tripodDamageEffectSchema = z.object({
  type: z.enum(['DAMAGE_INCREASE', 'ADDITIONAL_ATTACK', 'INCREASED_TOTAL_DAMAGE']),
  label: z.string(),
  percent: decimalStringSchema,
  multiplier: decimalStringSchema,
  applicationMode: z.enum(['MULTIPLIER', 'EMBEDDED_MOTION_HIT'])
});

const arkGridFactorSchema = z.object({
  factorId: z.string(),
  corePath: z.string(),
  coreName: z.string(),
  coreGrade: z.string(),
  category: z.string(),
  value: decimalStringSchema,
  scopeKind: z.enum(['ALL', 'SKILL_TAG', 'SKILL_NAMES', 'SINGLE_CAST_EXCLUDED']),
  scopeValue: z.union([z.string(), z.array(z.string())]),
  condition: z.string(),
  requiredPoints: z.number().int().nonnegative(),
  contributionPaths: z.array(z.string())
});

export const normalizedBuildSchema = z.object({
  endpointSources: z.array(z.enum([
    'profiles',
    'equipment',
    'avatars',
    'combatSkills',
    'engravings',
    'cards',
    'gems',
    'arkPassive',
    'arkGrid'
  ])).length(9),
  profile: z.object({
    className: z.string(),
    characterLevel: z.number().int().nonnegative(),
    expeditionLevel: z.number().int().nonnegative(),
    criticalStat: decimalStringSchema,
    swiftnessStat: decimalStringSchema,
    specializationStat: decimalStringSchema,
    profileAttackPower: decimalStringSchema,
    criticalRateFromStat: decimalStringSchema,
    attackSpeedFromSwiftness: decimalStringSchema,
    moveSpeedFromSwiftness: decimalStringSchema
  }),
  equipment: normalizedEquipmentSchema,
  avatars: z.object({
    mainStatPercent: decimalStringSchema,
    items: z.array(z.object({
      type: z.string(),
      name: z.string(),
      grade: z.string(),
      isInner: z.boolean(),
      applied: z.boolean(),
      mainStatPercent: decimalStringSchema
    }))
  }),
  pet: z.object({
    mainStatPercent: decimalStringSchema,
    additionalDamagePercent: decimalStringSchema,
    demonDamagePercent: decimalStringSchema,
    source: z.string()
  }),
  engravings: z.object({
    names: z.array(z.string()),
    stoneLevelTotal: z.number().int().nonnegative(),
    stoneBaseAttackPercent: decimalStringSchema,
    effects: z.record(z.string(), engravingEffectSchema)
  }),
  cards: z.object({ damagePercent: decimalStringSchema }),
  gems: z.object({
    baseAttackPercent: decimalStringSchema,
    items: z.array(z.object({
      slot: z.number().int().nullable(),
      name: z.string(),
      level: z.number().int().nonnegative(),
      grade: z.string(),
      baseAttackPercent: decimalStringSchema,
      tooltipText: z.string(),
      skillEffects: z.array(skillGemEffectSchema)
    })),
    skillEffects: z.array(skillGemEffectSchema)
  }),
  arkPassive: z.object({
    karmaWeaponAttackPercent: decimalStringSchema,
    karmaEvolutionDamage: decimalStringSchema,
    evolutionDamageByName: decimalMapSchema,
    skillDamageByName: decimalMapSchema,
    criticalRateByName: decimalMapSchema,
    criticalDamageByName: decimalMapSchema,
    criticalHitDamageByName: decimalMapSchema,
    additionalDamageByName: decimalMapSchema,
    speedByName: z.record(z.string(), z.object({
      attackSpeed: decimalStringSchema,
      moveSpeed: decimalStringSchema
    })),
    effects: z.array(z.object({
      name: z.string(),
      rawName: z.string(),
      level: z.number().int().nullable(),
      description: z.string()
    })),
    points: z.array(z.object({
      path: z.string(),
      name: z.string(),
      value: z.number(),
      karmaLevel: z.number().int().nonnegative(),
      tooltipText: z.string()
    }))
  }),
  combatSkills: z.object({
    skillNames: z.array(z.string()),
    hasExposedWeakness: z.boolean(),
    selectedTripods: z.array(z.object({
      skillName: z.string(),
      name: z.string(),
      tier: z.number().int().nullable(),
      tooltipText: z.string(),
      damagePercent: decimalStringSchema,
      criticalDamagePercent: decimalStringSchema,
      damageEffects: z.array(tripodDamageEffectSchema)
    }))
  }),
  arkGrid: z.object({
    attackPowerPercent: decimalStringSchema,
    additionalDamagePercent: decimalStringSchema,
    bossDamagePercent: decimalStringSchema,
    attackPowerFlat: decimalStringSchema,
    weaponAttackFlat: decimalStringSchema,
    weaponAttackPercent: decimalStringSchema,
    generalDamagePercent: decimalStringSchema,
    criticalRate: decimalStringSchema,
    criticalDamage: decimalStringSchema,
    criticalHitDamagePercent: decimalStringSchema,
    attackSpeed: decimalStringSchema,
    moveSpeed: decimalStringSchema,
    enemyDefenseReductionPercent: decimalStringSchema,
    skillDamagePercent: decimalStringSchema,
    gemEffects: z.object({
      attackPowerPercent: decimalStringSchema,
      additionalDamagePercent: decimalStringSchema,
      bossDamagePercent: decimalStringSchema
    }),
    aggregateEffects: z.object({
      attackPowerPercent: decimalStringSchema,
      additionalDamagePercent: decimalStringSchema,
      bossDamagePercent: decimalStringSchema
    }),
    effectiveBaseEffects: z.object({
      attackPowerPercent: decimalStringSchema,
      additionalDamagePercent: decimalStringSchema,
      bossDamagePercent: decimalStringSchema
    }),
    coreEffects: decimalMapSchema,
    coreDamageFactors: z.array(arkGridFactorSchema),
    activeGems: z.array(z.object({
      path: z.string(),
      slotIndex: z.number().int(),
      gemIndex: z.number().int(),
      grade: z.string(),
      tooltipText: z.string(),
      values: z.object({
        attackPowerPercent: decimalStringSchema,
        additionalDamagePercent: decimalStringSchema,
        bossDamagePercent: decimalStringSchema
      })
    })),
    activeAggregateEffects: z.array(z.object({
      path: z.string(),
      name: z.string(),
      level: z.number().int().nonnegative(),
      tooltipText: z.string(),
      values: z.object({
        attackPowerPercent: decimalStringSchema,
        additionalDamagePercent: decimalStringSchema,
        bossDamagePercent: decimalStringSchema
      })
    })),
    cores: z.array(z.object({
      path: z.string(),
      name: z.string(),
      grade: z.string(),
      point: z.number().int().nonnegative()
    }).passthrough())
  }),
  provenance: z.array(provenanceSchema)
});
export type NormalizedBuild = z.infer<typeof normalizedBuildSchema>;

export const buildSnapshotSchema = z.object({
  schemaVersion: contractSchemaVersion,
  snapshotId: z.string().min(1),
  characterName: z.string().min(1),
  classId: z.literal('weather-artist'),
  calculatorVersion: z.string().min(1),
  parserVersion: z.string().min(1),
  catalogVersion: z.string().min(1),
  calculatedAttackPower: decimalStringSchema,
  warnings: z.array(warningSchema),
  build: normalizedBuildSchema
});
export type BuildSnapshot = z.infer<typeof buildSnapshotSchema>;

const catalogId = z.string().min(1);
const slotId = z.string().min(1);
export const buildPatchSchema = z.discriminatedUnion('kind', [
  z.object({ schemaVersion: contractSchemaVersion, kind: z.literal('set-skill-level'), skillId: catalogId, level: z.number().int().min(1).max(14) }),
  z.object({ schemaVersion: contractSchemaVersion, kind: z.literal('set-tripod-option'), skillId: catalogId, tripodSlotId: slotId, optionId: catalogId }),
  z.object({ schemaVersion: contractSchemaVersion, kind: z.literal('set-gem-level'), gemSlotId: slotId, level: z.number().int().min(1).max(10) }),
  z.object({ schemaVersion: contractSchemaVersion, kind: z.literal('set-engraving-level'), engravingId: catalogId, level: z.number().int().min(0).max(3) }),
  z.object({ schemaVersion: contractSchemaVersion, kind: z.literal('set-ark-passive-level'), nodeId: catalogId, level: z.number().int().min(0) }),
  z.object({ schemaVersion: contractSchemaVersion, kind: z.literal('set-ark-grid-gem-level'), gemId: catalogId, level: z.number().int().min(0) }),
  z.object({ schemaVersion: contractSchemaVersion, kind: z.literal('reset-section'), sectionId: catalogId })
]);
export type BuildPatch = z.infer<typeof buildPatchSchema>;

export interface Scenario {
  schemaVersion: '1';
  id: string;
  bossConditionId: string;
  directionalSuccessBySkill: Record<string, boolean>;
}

export interface HitDamageResult {
  schemaVersion: '1';
  hitName: string;
  nonCriticalDamage: DecimalString;
  criticalDamage: DecimalString;
  expectedDamage: DecimalString;
}

export interface SkillDamageResult {
  schemaVersion: '1';
  skillId: string;
  nonCriticalDamage: DecimalString;
  criticalDamage: DecimalString;
  expectedDamage: DecimalString;
  criticalRate: DecimalString;
  criticalMultiplier: DecimalString;
  hits: HitDamageResult[];
  rationale: string[];
}

export interface ApiSuccess<T> {
  schemaVersion: '1';
  ok: true;
  data: T;
  warnings: Warning[];
}

export interface ApiFailure {
  schemaVersion: '1';
  ok: false;
  error: {
    code: string;
    message: string;
    requestId: string;
  };
}

export type ApiEnvelope<T> = ApiSuccess<T> | ApiFailure;

export const hitDamageResultSchema = z.object({
  schemaVersion: contractSchemaVersion,
  hitName: z.string().min(1),
  nonCriticalDamage: decimalStringSchema,
  criticalDamage: decimalStringSchema,
  expectedDamage: decimalStringSchema
});
export type HitDamageResultContract = z.infer<typeof hitDamageResultSchema>;

export const skillDamageResultSchema = z.object({
  schemaVersion: contractSchemaVersion,
  skillId: z.string().min(1),
  nonCriticalDamage: decimalStringSchema,
  criticalDamage: decimalStringSchema,
  expectedDamage: decimalStringSchema,
  criticalRate: decimalStringSchema,
  criticalMultiplier: decimalStringSchema,
  hits: z.array(hitDamageResultSchema),
  rationale: z.array(z.string())
});

export const apiEnvelopeSchema = <T extends z.ZodTypeAny>(dataSchema: T) => z.discriminatedUnion('ok', [
  z.object({ schemaVersion: contractSchemaVersion, ok: z.literal(true), data: dataSchema, warnings: z.array(warningSchema) }),
  z.object({
    schemaVersion: contractSchemaVersion,
    ok: z.literal(false),
    error: z.object({ code: z.string().min(1), message: z.string().min(1), requestId: z.string().min(1) })
  })
]);

export type DirectionTag = 'NON_DIRECTIONAL' | 'FRONTAL_ATTACK' | 'BACK_ATTACK';

export interface SkillHitDefinition {
  name: string;
  coefficient: DecimalString;
  constant: DecimalString;
  tripodSource?: string;
}

export interface SkillCatalogEntry {
  id: string;
  displayName: string;
  directionTag: DirectionTag;
  tags: string[];
  hitMotionCoefficient: DecimalString;
  hits: SkillHitDefinition[];
}

export interface EditableSectionDescriptor {
  id: string;
  label: string;
  editable: boolean;
  lockReason?: string;
}

export interface EquipmentGrowthMetadata {
  editingLocked: true;
  reason: 'NO_VERIFIED_DATASET';
  requiredDataset: string;
}
