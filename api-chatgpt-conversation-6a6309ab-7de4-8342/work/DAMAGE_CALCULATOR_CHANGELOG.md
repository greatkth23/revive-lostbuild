# Damage calculator changelog

## 2.4.1 — ArkGrid core stacking operators

- Kept simple stat increases, including flat and percentage attack/weapon
  attack, critical, and speed values, in additive groups.
- Added `ADD_TO_PREVIOUS` handling for wording that says `추가로 증가`.
- Kept every other active core threshold as an independent multiplicative
  factor; 18P, 19P, and 20P therefore multiply once per active point.
- Added explicit relic/ancient selection for unresolved `A/B%` core text.
- Persisted factor contributions and operators in parsed JSON and calculation
  reports, and added the `weather-artist-v0.3.1` knowledge DB release.

## 2.4.0 — ArkGrid core threshold effects

- Parsed each `ArkGrid.Slots[]` core name, grade-resolved tooltip, current
  point total, and `[nP]` activation threshold.
- Connected active core effects to attack/weapon attack, additional damage,
  general/boss/skill damage, critical rate/damage, critical-hit damage,
  attack/move speed, and enemy-defense reduction categories.
- Preserved cooldown effects for future rotation/DPS calculations while
  excluding them from single-cast damage.
- Added skill-name and skill-tag scope checks for Weather Artist order-core
  effects and explicit exclusion records for utility, support, defensive, and
  coefficient-less proc effects.
- Removed the raw-data excerpt and ArkGrid before/after comparison sections
  from generated calculation reports.
- Added a repository-level ArkGrid core reference and raw/parsed source lookup
  instructions for other workers.
- Added the `weather-artist-v0.3` knowledge DB release and core-effect tests.

## 2.3.0 — multi-skill and multi-hit estimates

- Added `공간 가르기` as a two-hit skill model: 1st hit
  `40.07 × attack + 6,117`, 2nd hit `93.50 × attack + 14,283`.
- Added skill-selectable CLI, filenames, parsing, calculation, validation, and
  reports while preserving the existing `우레바람` model.
- Applied the Ark Passive `공간 가르기` +200% skill-damage effect to both
  hits and excluded `단련된 가르기`, `바람의 길`, and `풀려난 힘` by
  explicit skill scope.
- Added per-hit non-critical, critical, and expected damage alongside cast
  totals.
- Marked the non-directional classification used for Hit Master as
  provisional because the official API snapshot has no direction-type field
  for this enlightenment X-key skill.
- Added the `weather-artist-v0.2` seed and persisted both hit records in the
  knowledge database.

## 2.2.0 — v2.1.0 data-source audit corrections

- Included active `ArkGrid.Effects[]` attack power, additional damage, and
  boss damage in their intended calculation groups.
- Parsed the full `보스 등급 이상 몬스터에게 주는 피해` ArkGrid wording.
- Parsed Hit Master (`타격의 대가`) directly from its current API sentence.
- Preserved the reconstructed attack-power calculation for audit display while
  using profile attack power for downstream damage when the two values differ.
- Parsed regular-gem skill damage and cooldown reduction by canonical skill;
  skill damage now participates in matching-skill damage calculations.
- Split provenance state into `parsed`, `eligible`, `applied`, and
  `excludedReason`, and exposed structured fallback ledgers.
- Added a regression test for the audited `봄날꽃씨` API snapshot.
- Added the `weather-artist-v0.1` versioned SQLite schema, seed data, and
  deterministic database builder.

## 2.1.0 — current rules

- Adopted the workbook attack-power pipeline.
- Added flat weapon attack and flat attack power parsing.
- Added live engraving-description parsing.
- Added Cursed Doll, current Grudge, current Mass Increase, current
  Adrenaline, and current Raid Captain values.
- Preserved explicit user overrides: final-only flooring, additive
  avatar/pet main-stat percentages, and Sonic Breakthrough 15%/30%
  over-cap coefficients.
- Added versioned filenames, manifests, and CLI selection.

## 2.0.0 — season3 workbook compatibility

- Reproduces the workbook's intermediate flooring at main stat, weapon
  attack, and attack power.
- Uses the workbook's Sonic Breakthrough 10%/20% over-cap coefficients.
- Uses the workbook sample's expedition/potion and feast constants.

## 1.0.0 — conversation example

- Original API parser and single-skill damage model.
- Uses example fallback effect values and final-only flooring.
