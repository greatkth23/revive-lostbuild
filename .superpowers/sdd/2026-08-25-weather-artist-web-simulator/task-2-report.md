# Task 2 report — TypeScript parser and damage-calculator parity

## Outcome

- Ported the six-skill Weather Artist `current-v2.7.2` parsing and one-cast damage domain to `@weather-artist/calculator` using `decimal.js` at precision 40 with explicit half-even arithmetic and final `ROUND_FLOOR` damage rounding.
- Added a pure `parseBuildSnapshot(rawBundle)` boundary for the nine saved Lost Ark endpoint payloads. It has no filesystem, HTTP, or report-generation dependency.
- Extended the schema-version `1` `BuildSnapshot` contract with required normalized build data and structured provenance/warnings. Every serialized decimal remains a string.
- Parsed equipment, accessories, bracelet, armlet, avatars, fixed pet scenario effects, engravings and ability-stone levels, cards, regular gems, Ark Passive effects/points/karma, selected combat-skill tripods, and Ark Grid cores/active gems/aggregate effects.
- Preserved the Task 1 catalog IDs/tags and locked equipment-growth metadata. No equipment-growth edit data was introduced and no Arcana behavior was ported.
- Matched freshly generated Python `current-v2.7.2` checkpoints for calculated attack power and all six skills' cast totals and independently floored per-hit values.

## Public API

- `parseBuildSnapshot(rawBundle)`
- `calculateAttackPower(snapshot)`
- `calculateSkillDamage(snapshot, skillIdOrName, options?)`
- `calculateAllSkillDamage(snapshot, options?)`
- `directionalAttackBonus(tag, success?)`
- `tooltipToText(raw)`
- `resolveArkGridGradeValues(text, grade)`

## TDD evidence

### Parser RED — missing parser behaviors

Command:

```text
npm test -- packages/calculator/src/parser.test.ts
```

Output (exit 1):

```text
❯ packages/calculator/src/parser.test.ts (8 tests | 8 failed) 47ms
  × ... normalizes all nine endpoint payloads ... → parseBuildSnapshot is not a function
  × ... parses equipment, armlet, accessory ... → parseBuildSnapshot is not a function
  × ... derives enlightenment karma ... → parseBuildSnapshot is not a function
  × ... ArkGrid Effects aggregate values ... → parseBuildSnapshot is not a function
  × ... relic or ancient side ... → resolveArkGridGradeValues is not a function
  × ... selected tripod effects ... → parseBuildSnapshot is not a function
  × ... path-bearing incomplete warning ... → parseBuildSnapshot is not a function
  × ... flattens official JSON tooltips ... → tooltipToText is not a function

Test Files  1 failed (1)
Tests       8 failed (8)
```

This was the intended failure: none of the public parser functions existed.

### Parser GREEN — initial eight behaviors

Command:

```text
npm test -- packages/calculator/src/parser.test.ts
```

Output (exit 0):

```text
✓ packages/calculator/src/parser.test.ts (8 tests) 132ms

Test Files  1 passed (1)
Tests       8 passed (8)
```

### Warning-provenance RED/GREEN

RED command:

```text
npm test -- packages/calculator/src/parser.test.ts
```

RED output (exit 1):

```text
❯ packages/calculator/src/parser.test.ts (9 tests | 1 failed) 155ms
× ... preserves fallback and calculated-attack provenance ...
  expected [KARMA_EVOLUTION_FALLBACK] to deeply equal
  [KARMA_EVOLUTION_FALLBACK, FIXED_EXPEDITION_STAT_MISMATCH,
   CALCULATED_ATTACK_POWER_OVERRIDE]

Test Files  1 failed (1)
Tests       1 failed | 8 passed (9)
```

GREEN command:

```text
npm test -- packages/calculator/src/parser.test.ts
```

GREEN output (exit 0):

```text
✓ packages/calculator/src/parser.test.ts (9 tests) 151ms

Test Files  1 passed (1)
Tests       9 passed (9)
```

### Ark Passive point / Ark Grid component-retention RED/GREEN

RED command:

```text
npm test -- packages/calculator/src/parser.test.ts
```

RED output (exit 1):

```text
❯ packages/calculator/src/parser.test.ts (9 tests | 1 failed) 154ms
× ... normalizes all nine endpoint payloads ...
  Target cannot be null or undefined.

Test Files  1 failed (1)
Tests       1 failed | 8 passed (9)
```

The missing observable data was `arkPassive.points`, `arkGrid.activeGems`, and `arkGrid.activeAggregateEffects`.

GREEN output after adding those required normalized arrays (exit 0):

```text
✓ packages/calculator/src/parser.test.ts (9 tests) 147ms

Test Files  1 passed (1)
Tests       9 passed (9)
```

### Calculator RED — missing damage engine

Command:

```text
npm test -- packages/calculator/src/calculator.test.ts
```

Output (exit 1):

```text
❯ packages/calculator/src/calculator.test.ts (13 tests | 13 failed) 196ms
  × calculated attack-power checkpoint → calculateAttackPower is not a function
  × six Python parity cases → calculateSkillDamage is not a function
  × regular skill gems → calculateAllSkillDamage is not a function
  × umbrella/single-skill scopes → calculateAllSkillDamage is not a function
  × tripod embedded-effect dedupe → calculateSkillDamage is not a function
  × repeated 18–20P multipliers → calculateSkillDamage is not a function
  × directional success rules → directionalAttackBonus is not a function

Test Files  1 failed (1)
Tests       13 failed (13)
```

### Calculator GREEN — exact six-skill parity

Command:

```text
npm test -- packages/calculator/src/calculator.test.ts
```

Output (exit 0):

```text
✓ packages/calculator/src/calculator.test.ts (13 tests) 208ms

Test Files  1 passed (1)
Tests       13 passed (13)
```

An intermediate run had 7/13 passing and showed the same small overage on all six totals. The root cause was traced to applying pet demon damage `0.005` and collection demon damage `0.065` as separate multipliers. Python first sums them to `0.07`; one corrected multiplier made all six literal golden checks pass.

### Required normalized-build contract RED/GREEN

RED command:

```text
npm test -- packages/contracts/src/contracts.test.ts
```

RED output (exit 1):

```text
❯ packages/contracts/src/contracts.test.ts (4 tests | 1 failed) 12ms
× requires normalized endpoint sections on a serialized build snapshot
  expected [Function] to throw an error

Test Files  1 failed (1)
Tests       1 failed | 3 passed (4)
```

GREEN command/output (exit 0):

```text
npm test -- packages/contracts/src/contracts.test.ts packages/calculator/src/parser.test.ts packages/calculator/src/calculator.test.ts

✓ packages/contracts/src/contracts.test.ts (4 tests) 9ms
✓ packages/calculator/src/parser.test.ts (9 tests) 160ms
✓ packages/calculator/src/calculator.test.ts (13 tests) 223ms

Test Files  3 passed (3)
Tests       26 passed (26)
```

### Raid Captain fallback review regression RED/GREEN

RED command/output (exit 1):

```text
npm test -- packages/calculator/src/parser.test.ts packages/calculator/src/calculator.test.ts

× falls back to the current-v2.7.2 Raid Captain coefficient when its live description has no number
  expected '1437368671' to be '1713343456'

Test Files  2 failed (2)
Tests       2 failed | 22 passed (24)
```

One simultaneous proposed parser test was discarded after directly checking the Python function proved its expectation contradicted the authoritative parser. The valid Raid Captain regression demonstrated that JavaScript string truthiness retained a parsed `'0'` coefficient instead of taking Python's `0.48` fallback.

GREEN command/output after the single fallback fix (exit 0):

```text
npm test -- packages/calculator/src/parser.test.ts packages/calculator/src/calculator.test.ts

✓ packages/calculator/src/parser.test.ts (9 tests) 155ms
✓ packages/calculator/src/calculator.test.ts (14 tests) 232ms

Test Files  2 passed (2)
Tests       23 passed (23)
```

## Python-derived parity checkpoints

The literals below were generated by importing the authoritative `lostark_damage_test.py`, loading only the shared `봄날꽃씨_우레바람_current-v2.7.2_api_raw.json`, then calling `parse_all(...)` and `calculate(..., current-v2.7.2, skill)` for each supported skill. The approximately 975 KB raw fixture was not copied.

Calculated attack power used for every skill:

```text
258720.5038308918678085116909739914291229
```

Common critical rate:

```text
0.9582
```

| Stable ID | Skill | Non-critical | Critical | Expected | Critical multiplier |
|---|---|---:|---:|---:|---:|
| `thunderstorm` | 우레바람 | 583971628 | 1762610564 | 1713343456 | 3.0183154064 |
| `space-cutting` | 공간 가르기 | 427626447 | 1290711496 | 1254634541 | 3.0183154064 |
| `piercing-wind` | 바람송곳 | 316438287 | 955110558 | 928414057 | 3.0183154064 |
| `raging-blizzard` | 칼바람 | 168176514 | 915718688 | 884471425 | 5.4449855264 |
| `sweeping-strike` | 몰아치기 | 159445441 | 812903623 | 785589071 | 5.0983183664 |
| `tornado-walk` | 회오리 걸음 | 269437847 | 813248405 | 790517123 | 3.0183154064 |

Per-hit checkpoints `(non-critical / critical / expected)`:

```text
우레바람 최대 홀딩: 583971628 / 1762610564 / 1713343456
공간 가르기 1타:    128284705 / 387203703 / 376380889
공간 가르기 2타:    299341742 / 903507792 / 878253651
바람송곳 전체:       316438287 / 955110558 / 928414057
칼바람 전체:         168176514 / 915718688 / 884471425
몰아치기 1타:         24576750 / 125300096 / 121089861
몰아치기 2타:         57269889 / 291980130 / 282169242
몰아치기 3타:         77598801 / 395623396 / 382329968
회오리 걸음 1타:     188531809 / 569048466 / 553142869
회오리 걸음 2타:      80906037 / 244199939 / 237374253
```

Named intermediate checkpoints:

- Main stat: `817450.95`.
- Weapon attack: `274541.568`; karma weapon attack: `0.028`.
- Ark Grid gem values: attack `0.0139`, additional `0.0416`, boss `0.042`.
- Ark Grid aggregate `Effects[]`: attack `0.0143`, additional `0.042`, boss `0.0425`.
- Effective deduplicated base categories: aggregate values above; calculated attack percent including core is `0.0411`.
- Space Cutting coefficients after the ruleset-only `1.292` correction: `51.77044`, `120.802`; constants remain `6117`, `14283`.
- Relic `우산의 춤` 18P/19P/20P keeps three independent `0.002` factors; repeated multiplier: `1.006012008`.
- Molachigi `공간베기` `0.948` additional attack is marked `EMBEDDED_MOTION_HIT` and excluded from the tripod multiplier; resulting tripod multiplier is `1.6`.
- Regular gem damage/cooldown is `0.4` / `0.22` for 바람송곳, 칼바람, 몰아치기, 회오리 걸음, and `0` / `0` for 우레바람 and 공간 가르기.
- Applied Ark Passive skill effects: 우레바람 = 바람의 길/풀려난 힘/단련된 가르기; 공간 가르기 = 바람의 길/공간 가르기; remaining four = 바람의 길 only.
- All six remain `NON_DIRECTIONAL`; the reusable rule separately verifies back success `+5%/+10%p`, head success `+20%/+0%p`, and zero bonus for misses.

## Files changed

- `package-lock.json`
- `packages/calculator/package.json`
- `packages/calculator/src/index.ts`
- `packages/calculator/src/decimal.ts`
- `packages/calculator/src/attack-power.ts`
- `packages/calculator/src/parser.ts`
- `packages/calculator/src/calculator.ts`
- `packages/calculator/src/parser.test.ts`
- `packages/calculator/src/calculator.test.ts`
- `packages/contracts/src/index.ts`
- `packages/contracts/src/contracts.test.ts`
- `.superpowers/sdd/2026-08-25-weather-artist-web-simulator/task-2-report.md`

## Verification

### Python 35-test suite

Command:

```text
python -m unittest discover -s api-chatgpt-conversation-6a6309ab-7de4-8342/work -p test_*.py -v
```

Output (exit 0):

```text
Ran 35 tests in 1.005s

OK
```

### Full npm typecheck

Command:

```text
npm run typecheck
```

Exit 0 for web, worker, calculator, catalog, and contracts workspaces.

### Full npm test

Command/output (exit 0):

```text
npm test

✓ packages/catalog/src/catalog.test.ts (3 tests) 4ms
✓ packages/contracts/src/contracts.test.ts (4 tests) 10ms
✓ packages/calculator/src/parser.test.ts (9 tests) 163ms
✓ packages/calculator/src/calculator.test.ts (14 tests) 244ms

Test Files  4 passed (4)
Tests       30 passed (30)
```

### Full npm build

Command:

```text
npm run build
```

Output (exit 0): Vite built 26 modules, Wrangler completed the Worker dry run, and calculator/catalog/contracts completed TypeScript builds.

`git diff --check` also exited 0; its only output was Git's Windows LF-to-CRLF working-copy notice.

## Self-review

- Confirmed the raw fixture is referenced in tests from its existing repository location and was not duplicated.
- Confirmed production parser/calculator modules contain no filesystem, HTTP, environment-secret, or report-generation access.
- Confirmed the nine endpoint names are required and serialized `BuildSnapshot.build` is mandatory.
- Confirmed all decimal API/calculation fields and provenance numeric values are strings; integer levels, points, indexes, and counts remain integers.
- Confirmed active Ark Grid gems and aggregate effects are retained separately for audit, while `effectiveBaseEffects` selects aggregate categories without adding individual gem values again.
- Confirmed 18P/19P/20P multiplicative factors remain separate and relic/ancient slash selection is grade-sensitive.
- Confirmed the embedded Molachigi additional hit is present as provenance but excluded from the multiplier list.
- Confirmed all six catalog direction tags remain untouched and `Space Cutting` alone uses `1.292`.
- Confirmed equipment-growth editing remains locked in Task 1's catalog and no growth table was invented.
- Confirmed no Arcana parser/calculator behavior was added.

## Concerns

- The authoritative Python `calculate()` currently forms the Ark Grid boss subtitle from both `gemEffects.bossDamagePercent` and `pointEffects.bossDamagePercent`, even though parser provenance marks matching individual gem categories as superseded by `Effects[]`. TypeScript deliberately reproduces that current Python path to meet the required fresh golden totals, while its normalized `effectiveBaseEffects` and attack/additional categories preserve the explicit dedupe model. If the Python boss path is later corrected to use `effectiveBaseEffects`, the six golden totals must be regenerated and this port updated in lockstep.
- Pet and collection scenario bonuses remain the verified `current-v2.7.2` fixed values because the nine endpoint payloads expose no separate editable pet endpoint. They are explicitly labeled as fixed-scenario provenance rather than presented as parsed API fields.

---

# Task 2 review fix round 1/5

This section supersedes the original boss-damage concern and all original six-skill damage literals above. The binding duplicate-elimination ruling was applied to the authoritative Python engine first, and the TypeScript implementation was then brought back to corrected Python parity.

## Corrected behavior

- Python and TypeScript now take the Ark Grid base boss category exclusively from `effectiveBaseEffects.bossDamagePercent`. Active-gem and aggregate `Effects[]` values remain separately serialized for audit, while core factors remain independently multiplicative.
- Raw endpoint payloads are validated for the expected top-level object/array shape, required nested arrays, and a non-empty character name before normalization. Malformed values fail with a path-bearing error instead of silently becoming zero.
- Ark Grid core parsing now covers combined and individual attack/move speed, percent-plus-flat and direct flat weapon attack, and multiplicative incoming critical-hit damage.
- An activated, damage-relevant Ark Grid option with no recognized component emits an `UNPARSED_DAMAGE_TOOLTIP` incomplete warning.
- Ark Grid `REPLACE` aggregation no longer pre-adds the replacement. Normalized totals and the effective factor now both equal the replacement value.
- Ark Passive node provenance now marks nodes without a one-cast calculator component ineligible/unapplied. Numeric fallback use emits an `ARK_PASSIVE_EFFECT_FALLBACK` warning and separate `VERIFIED_FALLBACK`, `parsed: false` provenance.

## TDD evidence

### Python Ark Grid boss duplicate

RED command (working directory `api-chatgpt-conversation-6a6309ab-7de4-8342/work`):

```text
python -m unittest test_lostark_damage_test.ParserTests.test_calculation_uses_aggregate_arkgrid_boss_damage_without_gem_duplicate -v
```

RED output (exit 1):

```text
test_calculation_uses_aggregate_arkgrid_boss_damage_without_gem_duplicate (...) ... FAIL
AssertionError: 404934344 != 769398033
Ran 1 test in 0.016s
FAILED (failures=1)
```

GREEN command was identical. GREEN output (exit 0):

```text
test_calculation_uses_aggregate_arkgrid_boss_damage_without_gem_duplicate (...) ... ok
Ran 1 test in 0.014s
OK
```

### Corrected six-skill TypeScript parity

After regenerating the literals from the corrected Python engine, RED command:

```text
npm test -- --run packages/calculator/src/calculator.test.ts
```

RED output (exit 1):

```text
❯ packages/calculator/src/calculator.test.ts (14 tests | 6 failed) 237ms
Test Files  1 failed (1)
Tests       6 failed | 8 passed (14)

thunderstorm example:
Expected nonCriticalDamage 561355853, received 583971628
Expected criticalDamage 1694349020, received 1762610564
Expected expectedDamage 1646989906, received 1713343456
```

GREEN command was identical after changing the calculator to `effectiveBaseEffects`. GREEN output (exit 0):

```text
✓ packages/calculator/src/calculator.test.ts (14 tests) 221ms
Test Files  1 passed (1)
Tests       14 passed (14)
```

A direct mutation regression was then retained: changing `gemEffects` and `aggregateEffects` while leaving `effectiveBaseEffects` unchanged does not change any damage total.

### Endpoint shape validation

RED command:

```text
npm test -- --run packages/calculator/src/parser.test.ts -t "rejects present-but-null"
```

RED output (exit 1):

```text
× rejects present-but-null or wrong-shaped endpoint payloads and an empty character name
profiles: expected [Function] to throw an error
Test Files  1 failed (1)
Tests       1 failed | 9 skipped (10)
```

GREEN command was identical. GREEN output (exit 0):

```text
✓ packages/calculator/src/parser.test.ts (10 tests | 9 skipped) 82ms
Test Files  1 passed (1)
Tests       1 passed | 9 skipped (10)
```

### Ark Grid missing categories and activated-option warning

RED command:

```text
npm test -- --run packages/calculator/src/parser.test.ts -t "calculator-connected Ark Grid|activated Ark Grid core"
```

RED output (exit 1):

```text
× parses calculator-connected Ark Grid speed, flat weapon attack, and incoming critical-hit damage
received attackSpeed 0, moveSpeed 0, weaponAttackFlat 0, criticalHitDamagePercent 0
× warns when an activated Ark Grid core damage option has no recognized component
expected UNPARSED_DAMAGE_TOOLTIP at arkGrid.Slots[0].Tooltip.options[0]
Test Files  1 failed (1)
Tests       2 failed | 10 skipped (12)
```

GREEN command was identical. GREEN output (exit 0):

```text
✓ packages/calculator/src/parser.test.ts (12 tests | 10 skipped) 45ms
Test Files  1 passed (1)
Tests       2 passed | 10 skipped (12)
```

The Python-compatible percent-plus-flat weapon-attack wording was separately tightened with a real RED/GREEN:

```text
npm test -- --run packages/calculator/src/parser.test.ts -t "calculator-connected Ark Grid"

RED: expected weaponAttackFlat "1000", received "0" (1 failed, 13 skipped)
GREEN: 1 passed, 13 skipped
```

### Ark Grid REPLACE aggregation

RED command:

```text
npm test -- --run packages/calculator/src/parser.test.ts -t "replaces an Ark Grid factor once"
```

RED output (exit 1):

```text
expected '0.4' to be '0.2'
Test Files  1 failed (1)
Tests       1 failed | 12 skipped (13)
```

GREEN command was identical. GREEN output (exit 0):

```text
✓ packages/calculator/src/parser.test.ts (13 tests | 12 skipped) 29ms
Test Files  1 passed (1)
Tests       1 passed | 12 skipped (13)
```

### Ark Passive eligibility and fallback audit

RED command:

```text
npm test -- --run packages/calculator/src/parser.test.ts -t "marks ignored Ark Passive"
```

RED output (exit 1):

```text
expected provenance for 환기 with eligible false, applied false, and a one-cast exclusion reason
received arkPassive.Effects[0] with eligible true and applied true
Test Files  1 failed (1)
Tests       1 failed | 13 skipped (14)
```

GREEN command was identical. GREEN output (exit 0):

```text
✓ packages/calculator/src/parser.test.ts (14 tests | 13 skipped) 35ms
Test Files  1 passed (1)
Tests       1 passed | 13 skipped (14)
```

The retained test also checks the real fixture's `환기`, `치명`, `신속`, `잠재력 해방`, and `즉각적인 주문` nodes as ineligible/unapplied, plus path-bearing fallback warning/provenance.

## Corrected Python-derived parity checkpoints

The same shared raw file was loaded in place and no copy was made. Attack power remains `258720.5038308918678085116909739914291229`, critical rate remains `0.9582`, and critical multipliers remain unchanged.

| Stable ID | Skill | Non-critical | Critical | Expected |
|---|---|---:|---:|---:|
| `thunderstorm` | 우레바람 | 561355853 | 1694349020 | 1646989906 |
| `space-cutting` | 공간 가르기 | 411065534 | 1240725435 | 1206045651 |
| `piercing-wind` | 바람송곳 | 304183416 | 918121491 | 892458879 |
| `raging-blizzard` | 칼바람 | 161663454 | 880255170 | 850218036 |
| `sweeping-strike` | 몰아치기 | 153270514 | 781421879 | 755165152 |
| `tornado-walk` | 회오리 걸음 | 259003186 | 781753307 | 759902352 |

Per-hit checkpoints `(non-critical / critical / expected)`:

```text
우레바람 최대 홀딩: 561355853 / 1694349020 / 1646989906
공간 가르기 1타:    123316556 / 372208262 / 361804589
공간 가르기 2타:    287748977 / 868517172 / 844241062
바람송곳 전체:       304183416 / 918121491 / 892458879
칼바람 전체:         161663454 / 880255170 / 850218036
몰아치기 1타:         23624953 / 120447534 / 116400350
몰아치기 2타:         55051968 / 280672463 / 271241526
몰아치기 3타:         74593592 / 380301881 / 367523275
회오리 걸음 1타:     181230439 / 547010627 / 531721016
회오리 걸음 2타:      77772746 / 234742679 / 228181336
```

## Files changed in this fix round

- `api-chatgpt-conversation-6a6309ab-7de4-8342/work/lostark_damage_test.py`
- `api-chatgpt-conversation-6a6309ab-7de4-8342/work/test_lostark_damage_test.py`
- `packages/calculator/src/calculator.ts`
- `packages/calculator/src/calculator.test.ts`
- `packages/calculator/src/parser.ts`
- `packages/calculator/src/parser.test.ts`
- `.superpowers/sdd/2026-08-25-weather-artist-web-simulator/task-2-report.md`

## Focused and full verification

Focused calculator/contracts command:

```text
npm test -- --run packages/contracts/src/contracts.test.ts packages/calculator/src/parser.test.ts packages/calculator/src/calculator.test.ts
```

Python full-suite command:

```text
python -m unittest discover -s api-chatgpt-conversation-6a6309ab-7de4-8342/work -p 'test_*.py' -v
```

Latest Python output before commit:

```text
Ran 36 tests in 0.733s
OK
```

Full npm commands:

```text
npm test
npm run typecheck
npm run build
```

Final fresh output after the last source change (all exit 0):

```text
Focused calculator/contracts:
✓ contracts 4, calculator 15, parser 14
Test Files  3 passed (3)
Tests       33 passed (33)

npm test:
✓ catalog 3, contracts 4, calculator 15, parser 14
Test Files  4 passed (4)
Tests       36 passed (36)

npm run typecheck:
web, worker, calculator, catalog, contracts all exited 0

npm run build:
Vite 26 modules built; Wrangler dry run exited; calculator/catalog/contracts TypeScript builds exited 0
```

## Self-review

- Confirmed the Python and TypeScript boss multiplier paths use only the effective base category; core boss factors remain separate.
- Confirmed the six corrected literals and all ten independently floored hit rows came from the corrected Python engine using the single existing raw fixture.
- Confirmed validation happens before any permissive `object()`/`array()` normalization and prevents an invalid empty-name snapshot.
- Confirmed REPLACE changes totals from prior `p` to replacement `r` exactly once, while ADD and ADD_TO_PREVIOUS preserve prior behavior.
- Confirmed Ark Passive fallback numerics are no longer represented as parsed official values and ignored nodes carry an exclusion reason.
- Confirmed no Arcana behavior, equipment-growth editing, filesystem/HTTP access in pure modules, stable IDs, schema version, or decimal serialization was changed.

## Concerns after fix round

- The real fixture's active `불타는 일격` 10P burn option has no single-cast tick/coefficient model. It is now surfaced as an incomplete `UNPARSED_DAMAGE_TOOLTIP` warning rather than silently contributing zero.
- Endpoint validation intentionally targets the current nine-endpoint API shapes. A future API envelope change will fail fast with a precise path and will require an explicit parser update.

---

# Task 2 review fix round 2/5

## Changes

- Added a shared object-array validator for every endpoint collection the parser iterates: profile stats, equipment, avatars, skills/tripods, the selected engraving collection, cards/effect items, gems, Ark Passive points/effects, and Ark Grid slots/gems/effects.
- A null, array, or primitive member now fails before normalization with its exact `responses...array[index]` path.
- Restored the parser's supported engraving compatibility rule: a non-empty `ArkPassiveEffects` array is preferred; when that field is missing, null, or empty, a valid `Effects` array is required and used. A malformed non-empty preferred collection still fails instead of falling through.
- The deferred 싹쓸바람 replacement behavior was not changed.

## TDD RED/GREEN evidence

### Endpoint array member validation

RED command:

```text
npm test -- --run packages/calculator/src/parser.test.ts -t "rejects non-object members"
```

RED output (exit 1):

```text
× rejects non-object members from every endpoint array the parser consumes
responses.profiles.Stats[0]: expected [Function] to throw an error
Test Files  1 failed (1)
Tests       1 failed | 14 skipped (15)
```

The table starts with the requested `profiles.Stats[0]` and `equipment[0]` regressions and also exercises every other direct or nested collection consumed by `array(...)`.

GREEN command was identical. GREEN output (exit 0):

```text
✓ packages/calculator/src/parser.test.ts (15 tests | 14 skipped) 120ms
Test Files  1 passed (1)
Tests       1 passed | 14 skipped (15)
```

### Legacy engraving Effects fallback

RED command:

```text
npm test -- --run packages/calculator/src/parser.test.ts -t "accepts legacy engraving"
```

RED output (exit 1):

```text
× accepts legacy engraving Effects fallback and rejects payloads with neither valid collection
Malformed Lost Ark endpoint payload: responses.engravings.ArkPassiveEffects must be an array
Test Files  1 failed (1)
Tests       1 failed | 15 skipped (16)
```

GREEN command was identical. GREEN output (exit 0):

```text
✓ packages/calculator/src/parser.test.ts (16 tests | 15 skipped) 94ms
Test Files  1 passed (1)
Tests       1 passed | 15 skipped (16)
```

The regression independently covers missing, null, and empty `ArkPassiveEffects` with a valid legacy `Effects` array. It also rejects null/missing fallback collections and a null legacy member with the precise `Effects[0]` path.

## Files changed in this fix round

- `packages/calculator/src/parser.ts`
- `packages/calculator/src/parser.test.ts`
- `.superpowers/sdd/2026-08-25-weather-artist-web-simulator/task-2-report.md`

## Focused evidence

Command:

```text
npm test -- --run packages/contracts/src/contracts.test.ts packages/calculator/src/parser.test.ts packages/calculator/src/calculator.test.ts
```

Output (exit 0):

```text
✓ packages/contracts/src/contracts.test.ts (4 tests) 9ms
✓ packages/calculator/src/calculator.test.ts (15 tests) 256ms
✓ packages/calculator/src/parser.test.ts (16 tests) 515ms
Test Files  3 passed (3)
Tests       35 passed (35)
```

Focused calculator TypeScript check also exited 0:

```text
npm run typecheck --workspace @weather-artist/calculator
```

## Self-review

- Compared every `array(...)` parser loop with validation coverage; every consumed endpoint array and each nested array now validates member object shape before the permissive parsing helpers run.
- Confirmed current API engraving payloads still accept a valid non-empty `ArkPassiveEffects` array even though their legacy `Effects` field is null.
- Confirmed legacy entries are actually parsed into the same five engraving names, stone level total `5`, and stone base attack `0.015`, rather than merely passing validation.
- Confirmed invalid preferred collection members do not silently fall back and invalid legacy members carry an indexed error path.
- Confirmed no calculator math, catalog IDs/tags, schema/decimal serialization, equipment growth, Arcana behavior, or 싹쓸바람 logic changed.

## Concerns

- No new unresolved implementation concern. Validation remains intentionally structural: endpoint array members must be non-null objects, while the existing field parsers continue to handle optional API fields.

## Final verification

Fresh Python/full npm/typecheck/build results after the final source change (all exit 0):

```text
python -m unittest discover -s api-chatgpt-conversation-6a6309ab-7de4-8342/work -p 'test_*.py' -v
Ran 36 tests in 0.730s
OK

npm test
✓ catalog 3, contracts 4, calculator 15, parser 16
Test Files  4 passed (4)
Tests       38 passed (38)

npm run typecheck
web, worker, calculator, catalog, contracts all exited 0

npm run build
Vite transformed 26 modules; Wrangler dry run exited; calculator/catalog/contracts TypeScript builds exited 0
```
