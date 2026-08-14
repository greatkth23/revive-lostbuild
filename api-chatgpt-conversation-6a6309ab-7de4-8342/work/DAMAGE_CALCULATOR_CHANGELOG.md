# Damage calculator changelog

## v2.7.2 official-rule/report update

- Applied the confirmed 2026-02-11 Space Cutting increase to motion
  coefficients only: `40.07 → 51.77044` and `93.50 → 120.80200`
  (`×1.292`). Motion constants remain `6117` and `14283`.
- Promoted reconstructed attack power from a comparison override to the
  official `current-v2.7.2` damage input.
- Made raw API and parsed JSON outputs opt-in through `--emit-debug-json`.
- Moved API call results and parsing/provenance to the bottom of calculation
  reports and standardized report-only numeric formatting to two decimals.
- Added explicit critical-rate, critical-damage, and on-critical multiplier
  formulas to reports.
- Defined `NON_DIRECTIONAL` as an authoritative non-directional skill tag.
- Corrected the Space Cutting discrepancy hypothesis after confirming that the
  skill has no damage gem. The leading candidate is now a supplied motion
  formula that predates the reported 2026-02-11 29.2% skill damage increase.

## 2.7.2 — calculated-attack comparison rule

- Added the user-requested comparison rule that uses reconstructed attack
  power for downstream skill damage even when it differs from profile attack.
- Kept `current-v2.7.1` unchanged so the profile-attack calculation remains
  reproducible; this patch changes only the attack value selected by damage.

## 2.7.1 — embedded tripod-hit deduplication

- Linked 몰아치기's supplied third-hit formula to the selected `공간베기`
  tripod instead of treating it as an unrelated base hit.
- Verified that `(1타 + 2타) × 94.8%` reproduces the supplied third-hit
  coefficient and constant after rounding.
- Kept the third hit in the cast total while suppressing the second `×1.948`
  multiplier, eliminating the duplicate `공간베기` application.
- Added explicit `tripodSource` and `EMBEDDED_MOTION_HIT` provenance plus a
  regression check that embedded hits cannot also enter the multiplier group.

## 2.7.0 — all selected tripod damage effects

- Reclassified every user-provided motion coefficient and constant as a
  tripod-free base skill formula.
- Added generic parsing for selected-tripod direct damage increases,
  tooltip-described additional attacks, increased total damage, and
  skill-specific critical damage.
- Applied each parsed damage effect as an independent multiplier and added
  skill-specific critical damage to the critical-damage group.
- Covered the current 봄날꽃씨 setup: `큰 센바람`, `집중 공격`, `거대 돌풍`,
  `공간베기`, `초고속 회전`, `우레`, `벼락`, and `역류`.
- Preserved speed/control-only tripods in provenance while excluding them from
  single-cast damage, and exposed every decision in generated reports.
- Added `우레바람` to the refreshed umbrella-skill integrated report.

## 2.6.0 — Armlet equipment and separate Reflux multiplier

- Added explicit `완갑` tooltip parsing for main stat, flat weapon attack,
  flat base attack, and percentage base attack.
- Inserted the Armlet base-attack stage as
  `(sqrt(main stat × weapon attack ÷ 6) + flat base attack) ×
  (1 + base-attack percentages)` before flat/final attack-power effects.
- Corrected the four Gale umbrella-skill models so `역류` is not assumed to
  be embedded in the supplied motion coefficients.
- Parsed each selected `역류` tooltip and applied its conditional increase as
  an independent damage multiplier: 60% for the captured 바람송곳/몰아치기
  setup and 95% for 칼바람/회오리 걸음.
- Kept the new behavior behind `current-v2.6.0` so older rulesets remain
  reproducible.

## 2.5.0 — Gale umbrella-skill models

- Confirmed `공간 가르기` as an umbrella skill and regenerated both character
  reports with umbrella-scoped Ark Passive and ArkGrid effects.
- Added user-provided motion formulas for `바람송곳`, `칼바람`, `몰아치기`,
  and `회오리 걸음`.
- Bound each formula to 봄날꽃씨's selected tripod variant and added
  skill-specific critical-damage handling for `우레` and `벼락`.
- Applied each skill's regular damage gem exactly once and retained cooldown
  gems as rotation/DPS-only data.
- Added the `weather-artist-v0.4` knowledge DB release and snapshot regression
  coverage for all four skills.

## 2.4.2 — enlightenment Karma weapon attack

- Changed enlightenment Karma weapon attack to `Karma level × 0.1%`.
- Parsed the Karma level from `ArkPassive.Points[].Description` instead of
  using a fixed 2.7% fallback.
- Split the report's ArkGrid attack-power subtotal into gem, aggregate
  `Effects[]`, and core contributions so the combined value is not mistaken
  for core-only.
- Fixed double counting between per-gem tooltip values and the top-level
  `ArkGrid.Effects[]` value generated from those same gem-effect levels.
  `Effects[]` is authoritative; per-gem values remain provenance-only.

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
