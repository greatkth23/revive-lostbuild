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
