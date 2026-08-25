import { z } from 'zod';

export type DecimalString = string;
export const decimalStringSchema = z.string().regex(/^-?\d+(?:\.\d+)?$/, 'Expected a decimal string');

export const warningSchema = z.object({
  code: z.string().min(1),
  severity: z.enum(['info', 'warning', 'incomplete']),
  path: z.string().min(1),
  message: z.string().min(1)
});
export type Warning = z.infer<typeof warningSchema>;

export const buildSnapshotSchema = z.object({
  schemaVersion: z.string().min(1),
  snapshotId: z.string().min(1),
  characterName: z.string().min(1),
  classId: z.literal('weather-artist'),
  calculatorVersion: z.string().min(1),
  parserVersion: z.string().min(1),
  catalogVersion: z.string().min(1),
  calculatedAttackPower: decimalStringSchema,
  warnings: z.array(warningSchema)
});
export type BuildSnapshot = z.infer<typeof buildSnapshotSchema>;

const catalogId = z.string().min(1);
const slotId = z.string().min(1);
export const buildPatchSchema = z.discriminatedUnion('kind', [
  z.object({ kind: z.literal('set-skill-level'), skillId: catalogId, level: z.number().int().min(1).max(14) }),
  z.object({ kind: z.literal('set-tripod-option'), skillId: catalogId, tripodSlotId: slotId, optionId: catalogId }),
  z.object({ kind: z.literal('set-gem-level'), gemSlotId: slotId, level: z.number().int().min(1).max(10) }),
  z.object({ kind: z.literal('set-engraving-level'), engravingId: catalogId, level: z.number().int().min(0).max(3) }),
  z.object({ kind: z.literal('set-ark-passive-level'), nodeId: catalogId, level: z.number().int().min(0) }),
  z.object({ kind: z.literal('set-ark-grid-gem-level'), gemId: catalogId, level: z.number().int().min(0) }),
  z.object({ kind: z.literal('reset-section'), sectionId: catalogId })
]);
export type BuildPatch = z.infer<typeof buildPatchSchema>;

export interface Scenario {
  schemaVersion: string;
  id: string;
  bossConditionId: string;
  directionalSuccessBySkill: Record<string, boolean>;
}

export interface HitDamageResult {
  hitName: string;
  nonCriticalDamage: DecimalString;
  criticalDamage: DecimalString;
  expectedDamage: DecimalString;
}

export interface SkillDamageResult {
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
  ok: true;
  data: T;
  warnings: Warning[];
}

export interface ApiFailure {
  ok: false;
  error: {
    code: string;
    message: string;
    requestId: string;
  };
}

export type ApiEnvelope<T> = ApiSuccess<T> | ApiFailure;

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
