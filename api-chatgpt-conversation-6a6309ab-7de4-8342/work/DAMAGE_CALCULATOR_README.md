# Damage calculator

## Offline regression tests

Run from this directory:

```powershell
python -m unittest -v
```

The suite includes the immutable `봄날꽃씨` snapshot used by the v2.1.0
data-source audit.

## Rebuild a report from a snapshot

```powershell
python lostark_damage_test.py `
  --snapshot ..\outputs\봄날꽃씨_우레바람_current-v2.1.0_api_raw.json `
  --output-dir ..\outputs `
  --rules-version current-v2.7.2 `
  --skill "몰아치기"
```

The default command now writes the Markdown calculation report only. Add
`--emit-debug-json` when raw API and normalized parser JSON are needed for
debugging; these JSON files are not user-facing reports.

`current-v2.7.2` is the official attack-selection rule. When profile attack and
reconstructed attack differ, skill damage uses reconstructed attack.
`current-v2.7.1` remains available only to reproduce the former profile-attack
selection behavior.

Markdown calculation reports format calculated numbers and percentages to two
decimal places. Their main order is calculation, result, exclusions, validation,
then API call results and parsing/provenance at the bottom. The critical section
shows every critical-rate component, the additive critical-damage multiplier,
and multiplicative on-critical damage factors.

`current-v2.6.0` recognizes `Type == "완갑"` and parses its `지능`, flat
`무기 공격력`, flat `기본 공격력`, and percentage `기본 공격력` values.
The base-attack reconstruction stage is:

```text
(sqrt(final main stat × final weapon attack / 6) + Armlet flat base attack)
× (1 + gem + ability-stone + Armlet base-attack percentages)
```

The stored base-hit motion coefficients and constants do not include tripod
damage multipliers. For 바람송곳, 칼바람, 몰아치기, and 회오리 걸음,
`current-v2.7.1` parses selected tripod tooltips and applies each direct damage
increase, additional attack, or increased-total-damage value. Skill critical
damage such as `우레` and `벼락` is added to the critical-damage group. Speed,
control, and range-only effects remain visible in provenance but do not change
single-cast damage.

When a supplied motion hit is itself created by a tripod, that hit is tagged
with `tripodSource` and the same tooltip percentage is not multiplied again.
The supplied 몰아치기 third hit is `공간베기`: its coefficient/constant equals
`(1타 + 2타) × 94.8%` after rounding. It stays in the hit total, while the
separate `×1.948` multiplier is suppressed.

For tooltip wording such as `60% 추가 피해`, the API does not provide a
separate motion formula for the added attack. The calculator therefore applies
`×1.60` to the complete base-skill damage and states that assumption in the
report. Conditional `역류` remains a maximum-favorable calculation that assumes
the character has a 기류 보호막 when the skill is used.

`arkGrid.pointEffects` is a compatibility key for the API's top-level
`ArkGrid.Effects[]` aggregate effects. It is not a core threshold. Reports
label it `아크그리드 누적 효과(Effects[])`. Because it is calculated from
the same effect levels shown on active gem tooltips, the calculator uses
`Effects[]` as the authoritative value and retains `gemEffects` only for
provenance and fallback when the aggregate API field is absent.

Calculation reports intentionally omit the former `핵심 원본 데이터 발췌`
and ArkGrid before/after comparison sections. API/parsing provenance is placed
at the bottom of each report. For a deeper audit, rerun with
`--emit-debug-json` and inspect:

- `outputs/*_api_raw.json` → `responses` and endpoint `rawBody`
- `outputs/*_parsed.json` → normalized blocks and provenance
- [ARKGRID_CORE_EFFECT_REFERENCE.md](ARKGRID_CORE_EFFECT_REFERENCE.md) →
  Weather Artist core thresholds, categories, conditions, and exclusions

`NON_DIRECTIONAL` is an authoritative direction tag: a skill carrying it is
treated as non-directional, including Hit Master eligibility when it is not an
awakening skill.

## Space Cutting discrepancy resolution

Space Cutting is the only tested skill whose estimate is roughly 27% below the
measured result. Common attack, engraving, card, defense, and ArkGrid factors
also drive the other skills that matched measurement, so they are unlikely to
be the cause. Space Cutting correctly has no damage gem, so gem omission is
ruled out. The leading hypothesis is that the supplied two-hit motion formula
predates the 2026-02-11 balance patch reported as a 29.2% Space Cutting damage
increase. That change is close to the observed discrepancy and would not be
visible in the character API tooltip or profile attack value. The user
subsequently confirmed the correction for v2.7.2: multiply the two motion
coefficients by `1.292`, producing `51.77044` and `120.80200`, while leaving
motion constants `6117` and `14283` unchanged. A missing follow-up hit remains
a secondary diagnostic only if the corrected estimate still misses measurement.

## Build the knowledge database

```powershell
python build_damage_db.py
```

This creates `db/weather-artist-v0.4.sqlite3`. Existing files are preserved by
default; use `--force` only when intentionally rebuilding that exact database.

The first release is intentionally narrow:

- class: 기상술사
- skills registered: 우레바람, 공간 가르기, 바람송곳, 칼바람, 몰아치기,
  회오리 걸음
- damage models: 우레바람 maximum hold, 공간 가르기 two-hit cast, and
  tripod-free base formulas for 바람송곳, 칼바람, 몰아치기, 회오리 걸음;
  the selected tripod effects are read separately from the character snapshot
- verified parser scopes: ArkGrid attack/additional/boss effects, regular-gem
  skill damage/cooldown, and 타격의 대가
- ArkGrid core effects are read from each slot's grade-resolved tooltip and
  activated by `Slot.Point` threshold. Applicable attack, weapon attack,
  additional/general/boss/skill damage, critical, speed, and defense-reduction
  categories are connected to the calculation. Simple stats and wording that
  says `추가로 증가` are additive; other active threshold effects retain
  independent multiplicative factors. Explicit `A/B` values select relic/ancient.
- scenario: the provisional example boss and maximum-favorable external buffs

Unknown coefficients and unverified game tables remain provisional instead of
being silently promoted to verified data.
