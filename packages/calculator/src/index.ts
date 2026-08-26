export const calculatorVersion = 'current-v2.7.2';

export {
  ENDPOINT_SOURCES,
  PARSER_VERSION,
  parseBuildSnapshot,
  resolveArkGridGradeValues,
  tooltipToText
} from './parser.js';

export {
  calculateAllSkillDamage,
  calculateAttackPower,
  calculateSkillDamage,
  directionalAttackBonus,
  type CalculationCheckpoints,
  type DetailedSkillDamageResult,
  type DirectionalAttackResult
} from './calculator.js';

export type { AttackPowerCheckpoints } from './attack-power.js';
