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
  --rules-version current-v2.4.1 `
  --skill "공간 가르기"
```

The parsed JSON records calculator, parser, ruleset, DB release, scenario
preset, per-source application state, and structured fallback usage.

Calculation reports intentionally omit the former `핵심 원본 데이터 발췌`
and ArkGrid before/after comparison sections. Inspect source data at:

- `outputs/*_api_raw.json` → `responses` and endpoint `rawBody`
- `outputs/*_parsed.json` → normalized blocks and provenance
- [ARKGRID_CORE_EFFECT_REFERENCE.md](ARKGRID_CORE_EFFECT_REFERENCE.md) →
  Weather Artist core thresholds, categories, conditions, and exclusions

## Build the knowledge database

```powershell
python build_damage_db.py
```

This creates `db/weather-artist-v0.3.1.sqlite3`. Existing files are preserved by
default; use `--force` only when intentionally rebuilding that exact database.

The first release is intentionally narrow:

- class: 기상술사
- skills registered: 우레바람, 칼바람, 공간 가르기
- damage models: 우레바람 maximum hold and 공간 가르기 two-hit cast
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
