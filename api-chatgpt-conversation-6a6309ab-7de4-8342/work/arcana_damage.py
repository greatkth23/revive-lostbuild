#!/usr/bin/env python3
"""황후 아르카나 4스택 루인 스킬의 1회 피해 추정기.

공통 공격력/장비/각인/카드/ArkGrid 파싱은 기존 계산기를 재사용한다.
아르카나 어댑터는 스킬 본체와 별도 루인 효과, 스킬별 치명타율,
뭉툭한 가시 전환 및 확률 트라이포드를 분리해 계산한다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import lostark_damage_test as base


CALCULATOR_VERSION = "2.8.0"
RULE_VERSION = "arcana-current-v2.8.0"
CHARACTER_NAME = "나츠노소라"
RUIN_COEFFICIENT = Decimal("15.90")
RUIN_CONSTANT = Decimal("0")

ARCANA_SKILLS = (
    base.CELESTIAL_RAIN_SKILL,
    base.SERENDIPITY_SKILL,
    base.SECRET_GARDEN_SKILL,
    base.FOUR_OF_A_KIND_SKILL,
)

SCENARIOS = {
    "baseline": {
        "label": "조건부 버프 미적용·비방향 기준",
        "rotationReady": False,
        "directionalSuccess": False,
    },
    "rotation-ready": {
        "label": "스택 준비·방향성 성공 기준",
        "rotationReady": True,
        "directionalSuccess": True,
    },
}
PRIMARY_SCENARIO = "rotation-ready"


def D(value: Any) -> Decimal:
    return base.dec(value)


def first_percent(text: str, pattern: str, default: str = "0") -> Decimal:
    match = re.search(pattern, text, re.I | re.S)
    return D(match.group(1)) / Decimal("100") if match else D(default)


def effect_text(parsed: dict[str, Any], name: str) -> str:
    return str((parsed["arkPassive"]["effects"].get(name) or {}).get("description") or "")


def tripod(parsed: dict[str, Any], skill: str, name: str) -> dict[str, Any]:
    return next(
        (
            item
            for item in parsed["combatSkills"]["selectedTripods"]
            if item["skill"] == skill and item["name"] == name
        ),
        {},
    )


def tripod_text(parsed: dict[str, Any], skill: str, name: str) -> str:
    return str(tripod(parsed, skill, name).get("tooltipText") or "")


def core_option_texts(parsed: dict[str, Any], core_fragment: str) -> list[str]:
    result: list[str] = []
    for core in parsed["arkGrid"].get("cores") or []:
        if core_fragment not in str(core.get("name") or ""):
            continue
        result.extend(
            str(option.get("resolvedText") or option.get("text") or "")
            for option in core.get("options") or []
            if option.get("activated")
        )
    return result


def extract_arcana_mechanics(parsed: dict[str, Any]) -> dict[str, Any]:
    whisper = effect_text(parsed, "황후의 속삭임")
    greed = effect_text(parsed, "황후의 탐욕")
    banquet = effect_text(parsed, "황후의 연회")
    mercy = effect_text(parsed, "황제의 자비")
    blunt = effect_text(parsed, "뭉툭한 가시")
    stream = tripod_text(parsed, "스트림 오브 엣지", "다크니스 엣지")
    scratch = tripod_text(parsed, "스크래치 딜러", "안전 장치")
    dark_fate = tripod_text(parsed, "운명의 부름", "어두운 운명")

    infinity = "\n".join(core_option_texts(parsed, "인피니티 덱"))
    edge_combo = "\n".join(core_option_texts(parsed, "엣지 콤보"))
    stream_core = "\n".join(core_option_texts(parsed, "스트림 오브 엣지"))

    stream_crit_max = first_percent(
        stream, r"최대\s*([0-9]+(?:\.[0-9]+)?)\s*%"
    )
    stream_crit_per_hit = first_percent(
        stream, r"([0-9]+(?:\.[0-9]+)?)\s*%\s*씩"
    )
    stream_stacks = (
        int((stream_crit_max / stream_crit_per_hit).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if stream_crit_per_hit
        else 0
    )
    core_crit_damage_per_stack = first_percent(
        stream_core,
        r"중첩\s*당\s*치명타\s*피해량이\s*([0-9]+(?:\.[0-9]+)?)\s*%",
    )

    return {
        "specializationRuinDamage": D(parsed["profile"].get("ruinDamageFromSpecialization")),
        "greedRuinDamage": first_percent(greed, r"루인\s*스킬의\s*피해량이\s*([0-9.]+)\s*%"),
        "whisperRuinDamage": first_percent(whisper, r"루인\s*스킬의\s*피해량이\s*([0-9.]+)\s*%"),
        "banquetFourStackDamage": first_percent(banquet, r"4스택\s*이상의\s*루인\s*피해량이\s*([0-9.]+)\s*%"),
        "mercyConditionalDamage": first_percent(mercy, r"적에게\s*주는\s*피해가\s*([0-9.]+)\s*%"),
        "bluntCritCap": first_percent(blunt, r"최대\s*([0-9.]+)\s*%\s*로\s*제한"),
        "bluntConversionRate": first_percent(blunt, r"초과한[^%]+?([0-9.]+)\s*%가\s*진화형"),
        "bluntEvolutionMaximum": first_percent(blunt, r"최대\s*([0-9.]+)\s*%까지\s*적용"),
        "streamCriticalRate": stream_crit_max,
        "streamStacks": stream_stacks,
        "streamCoreCriticalDamage": core_crit_damage_per_stack * stream_stacks,
        "scratchMoveSpeed": first_percent(scratch, r"이동속도가\s*([0-9.]+)\s*%"),
        "darkFateCriticalDamage": first_percent(dark_fate, r"치명타\s*피해가\s*([0-9.]+)\s*%"),
        "infinityRuinDamage": first_percent(infinity, r"루인\s*스킬의\s*피해량이\s*([0-9.]+)\s*%"),
        "balanceConditionalRuinDamage": first_percent(infinity, r"균형.*?루인\s*스킬의\s*피해량이\s*([0-9.]+)\s*%"),
        "edgeComboConditionalRuinDamage": first_percent(edge_combo, r"8\.0초[^.]+루인\s*스킬의\s*피해량이\s*([0-9.]+)\s*%"),
        "rainCoreDamageFactors": [
            D(value) / Decimal("100")
            for value in re.findall(
                r"셀레스티얼\s*레인의\s*피해량이\s*([0-9.]+)\s*%",
                stream_core,
            )
        ],
    }


def skill_tripod_mechanics(parsed: dict[str, Any], skill: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "criticalRate": Decimal("0"),
        "directFactors": [],
        "ruinFactors": [],
        "defenseIgnoreChance": Decimal("0"),
        "defenseIgnoreRate": Decimal("0"),
        "ruinCriticalBonusChance": Decimal("0"),
        "ruinCriticalDamageBonus": Decimal("0"),
    }
    if skill == base.CELESTIAL_RAIN_SKILL:
        result["criticalRate"] = first_percent(
            tripod_text(parsed, skill, "급소 타격"), r"치명타\s*적중률이\s*([0-9.]+)\s*%"
        )
        strengthened = first_percent(
            tripod_text(parsed, skill, "강화된 일격"), r"피해가\s*([0-9.]+)\s*%"
        )
        stack_damage = first_percent(
            tripod_text(parsed, skill, "약점 포착"), r"~\s*([0-9.]+)\s*%"
        )
        result["directFactors"].append(("강화된 일격", strengthened))
        result["ruinFactors"].extend((("강화된 일격", strengthened), ("약점 포착 4스택", stack_damage)))
    elif skill == base.FOUR_OF_A_KIND_SKILL:
        card = first_percent(
            tripod_text(parsed, skill, "카드 강화"), r"피해가\s*([0-9.]+)\s*%"
        )
        full_text = tripod_text(parsed, skill, "풀 하우스")
        result["criticalRate"] = first_percent(full_text, r"치명타\s*적중률이\s*([0-9.]+)\s*%")
        boss = first_percent(full_text, r"피격이상\s*면역인\s*적에게\s*주는\s*피해가\s*([0-9.]+)\s*%")
        result["directFactors"].extend((("카드 강화", card), ("풀 하우스", boss)))
        result["ruinFactors"].extend((("카드 강화", card), ("풀 하우스", boss)))
    elif skill == base.SECRET_GARDEN_SKILL:
        result["criticalRate"] = first_percent(
            tripod_text(parsed, skill, "급소 타격"), r"치명타\s*적중률이\s*([0-9.]+)\s*%"
        )
        complete = first_percent(
            tripod_text(parsed, skill, "완전한 비밀"), r"([0-9.]+)\s*%\s*증가된\s*피해"
        )
        chance = first_percent(
            tripod_text(parsed, skill, "시크릿 찬스"), r"스택트\s*피해\s*효과가\s*([0-9.]+)\s*%"
        )
        result["directFactors"].append(("완전한 비밀 4스택 추가 본체", complete))
        result["ruinFactors"].append(("시크릿 찬스", chance))
    elif skill == base.SERENDIPITY_SKILL:
        pierce = tripod_text(parsed, skill, "꿰뚫는 일격")
        result["defenseIgnoreChance"] = first_percent(pierce, r"([0-9.]+)\s*%\s*확률")
        result["defenseIgnoreRate"] = first_percent(pierce, r"방어력을\s*([0-9.]+)\s*%\s*무시")
        lucky = tripod_text(parsed, skill, "우연한 일격")
        per_stack = first_percent(lucky, r"중첩당\s*([0-9.]+)\s*%\s*확률")
        result["ruinCriticalBonusChance"] = min(Decimal("1"), per_stack * Decimal("4"))
        result["ruinCriticalDamageBonus"] = first_percent(lucky, r"치명타\s*피해가\s*([0-9.]+)\s*%")
        total = first_percent(
            tripod_text(parsed, skill, "연속된 어둠"), r"총\s*스킬\s*피해량이\s*([0-9.]+)\s*%"
        )
        result["directFactors"].append(("연속된 어둠", total))
    return result


def product(factors: list[tuple[str, Decimal]]) -> Decimal:
    value = Decimal("1")
    for _, percent in factors:
        value *= Decimal("1") + percent
    return value


def common_factors(seed: dict[str, Any]) -> list[tuple[str, Decimal]]:
    skill = seed["skillName"]
    excluded = {"진화형 피해", "돌격대장"}
    result: list[tuple[str, Decimal]] = []
    for item in seed["damageGroups"]["subtitles"]:
        name = str(item["name"])
        if name in excluded or name.startswith("일반 보석 ") or name.startswith(skill + " "):
            continue
        if D(item["percent"]):
            result.append((name, D(item["percent"])))
    return result


def effective_raid_captain(parsed: dict[str, Any], scenario: dict[str, Any]) -> tuple[Decimal, Decimal]:
    coefficient = D(
        parsed["engravings"]["parsedEffects"].get("돌격대장", {}).get("raidCaptainCoefficient")
    )
    move = (
        Decimal("1")
        + D(parsed["profile"]["moveSpeedFromSwiftness"])
        + base.RULESETS[base.DEFAULT_RULE_VERSION]["combatBlessingMoveSpeedPercent"]
        + base.RULESETS[base.DEFAULT_RULE_VERSION]["feastMoveSpeedPercent"]
    )
    if scenario["rotationReady"]:
        move += scenario["mechanics"]["scratchMoveSpeed"]
    capped = min(move, base.FIXED["speedCap"])
    return capped, max(Decimal("0"), capped - Decimal("1")) * coefficient


def critical_state(
    seed: dict[str, Any],
    mechanics: dict[str, Any],
    tripod_data: dict[str, Any],
    scenario: dict[str, Any],
    *,
    directional_critical: Decimal = Decimal("0"),
) -> dict[str, Decimal]:
    raw = D(seed["critical"]["rateRaw"]) + D(tripod_data["criticalRate"]) + directional_critical
    if scenario["rotationReady"]:
        raw += D(mechanics["streamCriticalRate"])
    cap = D(mechanics["bluntCritCap"] or Decimal("1"))
    converted = min(
        max(Decimal("0"), raw - cap) * D(mechanics["bluntConversionRate"]),
        D(mechanics["bluntEvolutionMaximum"]),
    )
    return {"raw": raw, "capped": min(cap, max(Decimal("0"), raw)), "convertedEvolution": converted}


def component_damage(
    *,
    name: str,
    hit_bases: list[tuple[str, Decimal]],
    seed: dict[str, Any],
    parsed: dict[str, Any],
    mechanics: dict[str, Any],
    tripod_data: dict[str, Any],
    scenario: dict[str, Any],
    factors: list[tuple[str, Decimal]],
    directional_damage: Decimal = Decimal("0"),
    directional_critical: Decimal = Decimal("0"),
    defense_ignore_probability: bool = False,
    ruin_critical_probability: bool = False,
) -> dict[str, Any]:
    crit = critical_state(
        seed, mechanics, tripod_data, scenario,
        directional_critical=directional_critical,
    )
    evolution_base = sum(
        (D(item["value"]) for item in seed["damageGroups"]["evolutionParts"]),
        Decimal("0"),
    )
    move_speed, raid = effective_raid_captain(parsed, scenario)
    all_factors = [
        *common_factors(seed),
        ("진화형 피해", evolution_base + crit["convertedEvolution"]),
        ("돌격대장", raid),
        ("마나 효율 증가", D(parsed["engravings"]["parsedEffects"].get("마나 효율 증가", {}).get("generalDamage"))),
        *factors,
    ]
    if directional_damage:
        all_factors.append(("방향성 적중", directional_damage))

    defense = D(seed["enemy"]["defenseMultiplier"])
    defense_expected = defense
    if defense_ignore_probability and tripod_data["defenseIgnoreChance"]:
        ignored_defense = D(seed["enemy"]["effectiveDefense"]) * (Decimal("1") - D(tripod_data["defenseIgnoreRate"]))
        ignored_multiplier = D(seed["enemy"]["defenseConstant"]) / (D(seed["enemy"]["defenseConstant"]) + ignored_defense)
        chance = D(tripod_data["defenseIgnoreChance"])
        defense_expected = defense * (Decimal("1") - chance) + ignored_multiplier * chance
    else:
        ignored_multiplier = defense

    common = (
        D(seed["damageGroups"]["additionalDamageMultiplier"])
        * product(all_factors)
        * D(seed["enemy"]["damageTakenMultiplier"])
        * defense_expected
    )
    critical_damage = (
        D(seed["critical"]["damageMultiplier"])
        - D(parsed["arkGrid"].get("criticalDamage"))
        - D(seed["critical"].get("skillTripodCriticalDamage"))
    )
    if scenario["rotationReady"]:
        critical_damage += D(mechanics["streamCoreCriticalDamage"])
        critical_damage += D(mechanics["darkFateCriticalDamage"])
    critical_hit_multiplier = D(seed["critical"]["criticalHitDamageMultiplier"])
    critical_damage_expected = critical_damage
    if ruin_critical_probability and tripod_data["ruinCriticalBonusChance"]:
        critical_damage_expected += (
            D(tripod_data["ruinCriticalBonusChance"])
            * D(tripod_data["ruinCriticalDamageBonus"])
        )

    hits: list[dict[str, Any]] = []
    for hit_name, hit_base in hit_bases:
        noncritical = hit_base * common
        critical = noncritical * critical_damage_expected * critical_hit_multiplier
        expected = critical * crit["capped"] + noncritical * (Decimal("1") - crit["capped"])
        hits.append({
            "name": hit_name,
            "base": hit_base,
            "nonCriticalRaw": noncritical,
            "criticalRaw": critical,
            "expectedRaw": expected,
        })
    return {
        "name": name,
        "hits": hits,
        "base": sum((item["base"] for item in hits), Decimal("0")),
        "nonCriticalRaw": sum((item["nonCriticalRaw"] for item in hits), Decimal("0")),
        "criticalRaw": sum((item["criticalRaw"] for item in hits), Decimal("0")),
        "expectedRaw": sum((item["expectedRaw"] for item in hits), Decimal("0")),
        "critical": crit,
        "criticalDamage": critical_damage,
        "criticalDamageExpected": critical_damage_expected,
        "criticalHitMultiplier": critical_hit_multiplier,
        "evolutionBase": evolution_base,
        "raidCaptain": raid,
        "moveSpeed": move_speed,
        "defenseMultiplierExpected": defense_expected,
        "defenseMultiplierNormal": defense,
        "defenseMultiplierIgnored": ignored_multiplier,
        "factors": all_factors,
    }


def calculate_skill(
    parsed: dict[str, Any],
    skill: str,
    mechanics: dict[str, Any],
    scenario_name: str,
) -> dict[str, Any]:
    scenario = {**SCENARIOS[scenario_name], "mechanics": mechanics}
    seed = base.calculate(parsed, True, base.DEFAULT_RULE_VERSION, skill)
    model = base.get_skill_model(skill)
    tripod_data = skill_tripod_mechanics(parsed, skill)
    attack = D(seed["attackPower"]["usedForDamage"])
    direct_bases = [
        (hit["name"], D(hit["coefficient"]) * attack + D(hit["constant"]))
        for hit in model["hits"]
    ]
    gem = D(base.regular_gem_effect_for_skill(parsed["gems"], skill)["damagePercent"])
    rain_core = mechanics["rainCoreDamageFactors"] if skill == base.CELESTIAL_RAIN_SKILL else []
    direct_factors = [
        (f"일반 보석 {skill}", gem),
        *tripod_data["directFactors"],
        *((f"아크그리드 {skill}", value) for value in rain_core),
    ]
    direction_damage = Decimal("0")
    direction_crit = Decimal("0")
    if scenario["directionalSuccess"] and "BACK_ATTACK" in model["tags"]:
        direction_damage, direction_crit = Decimal("0.05"), Decimal("0.10")
    elif scenario["directionalSuccess"] and "FRONTAL_ATTACK" in model["tags"]:
        direction_damage = Decimal("0.20")

    direct = component_damage(
        name="스킬 본체",
        hit_bases=direct_bases,
        seed=seed,
        parsed=parsed,
        mechanics=mechanics,
        tripod_data=tripod_data,
        scenario=scenario,
        factors=direct_factors,
        directional_damage=direction_damage,
        directional_critical=direction_crit,
        defense_ignore_probability=skill == base.SERENDIPITY_SKILL,
    )

    ruin_factors: list[tuple[str, Decimal]] = [
        (f"일반 보석 {skill}", gem),
        ("특화 루인 피해", mechanics["specializationRuinDamage"]),
        ("황후의 탐욕", mechanics["greedRuinDamage"]),
        ("황후의 연회 4스택", mechanics["banquetFourStackDamage"]),
        ("황후의 속삭임", mechanics["whisperRuinDamage"]),
        ("인피니티 덱 10P", mechanics["infinityRuinDamage"]),
        *tripod_data["ruinFactors"],
        *((f"아크그리드 {skill}", value) for value in rain_core),
    ]
    if scenario["rotationReady"]:
        ruin_factors.append(("엣지 콤보 17P", mechanics["edgeComboConditionalRuinDamage"]))
    ruin = component_damage(
        name="연결된 4스택 루인",
        hit_bases=[("4스택 효과", RUIN_COEFFICIENT * attack + RUIN_CONSTANT)],
        seed=seed,
        parsed=parsed,
        mechanics=mechanics,
        tripod_data=tripod_data,
        scenario=scenario,
        factors=ruin_factors,
        defense_ignore_probability=skill == base.SERENDIPITY_SKILL,
        ruin_critical_probability=skill == base.SERENDIPITY_SKILL,
    )
    return {
        "skill": skill,
        "scenario": scenario_name,
        "scenarioLabel": scenario["label"],
        "seed": seed,
        "tripod": tripod_data,
        "direct": direct,
        "ruin": ruin,
        "total": {
            key: direct[key] + ruin[key]
            for key in ("nonCriticalRaw", "criticalRaw", "expectedRaw")
        },
    }


def calculate_standalone_ruin(
    parsed: dict[str, Any], mechanics: dict[str, Any], scenario_name: str
) -> dict[str, Any]:
    scenario = {**SCENARIOS[scenario_name], "mechanics": mechanics}
    seed = base.calculate(parsed, True, base.DEFAULT_RULE_VERSION, base.FOUR_STACK_RUIN_SKILL)
    attack = D(seed["attackPower"]["usedForDamage"])
    neutral_tripod = skill_tripod_mechanics(parsed, base.FOUR_STACK_RUIN_SKILL)
    factors = [
        ("특화 루인 피해", mechanics["specializationRuinDamage"]),
        ("황후의 탐욕", mechanics["greedRuinDamage"]),
        ("황후의 연회 4스택", mechanics["banquetFourStackDamage"]),
        ("황후의 속삭임", mechanics["whisperRuinDamage"]),
        ("인피니티 덱 10P", mechanics["infinityRuinDamage"]),
    ]
    if scenario["rotationReady"]:
        factors.append(("엣지 콤보 17P", mechanics["edgeComboConditionalRuinDamage"]))
    ruin = component_damage(
        name="공통 4스택 루인",
        hit_bases=[("4스택 효과", RUIN_COEFFICIENT * attack)],
        seed=seed,
        parsed=parsed,
        mechanics=mechanics,
        tripod_data=neutral_tripod,
        scenario=scenario,
        factors=factors,
    )
    return {
        "skill": base.FOUR_STACK_RUIN_SKILL,
        "scenario": scenario_name,
        "scenarioLabel": scenario["label"],
        "seed": seed,
        "ruin": ruin,
        "total": {key: ruin[key] for key in ("nonCriticalRaw", "criticalRaw", "expectedRaw")},
    }


def calculate_suite(parsed: dict[str, Any]) -> dict[str, Any]:
    if parsed["profile"].get("className") != "아르카나":
        raise base.CalculationError("아르카나 캐릭터만 이 어댑터로 계산할 수 있습니다.")
    mechanics = extract_arcana_mechanics(parsed)
    missing = [name for name in (
        "specializationRuinDamage", "greedRuinDamage", "whisperRuinDamage",
        "banquetFourStackDamage", "bluntCritCap", "bluntConversionRate",
    ) if not mechanics[name]]
    if missing:
        raise base.CalculationError("아르카나 핵심 효과 파싱 실패: " + ", ".join(missing))
    calculations: dict[str, Any] = {}
    for scenario in SCENARIOS:
        calculations[scenario] = {
            skill: calculate_skill(parsed, skill, mechanics, scenario)
            for skill in ARCANA_SKILLS
        }
        calculations[scenario][base.FOUR_STACK_RUIN_SKILL] = calculate_standalone_ruin(
            parsed, mechanics, scenario
        )
    return {
        "mechanics": mechanics,
        "primaryScenario": PRIMARY_SCENARIO,
        "calculations": calculations,
    }


def fmt(value: Any) -> str:
    return base.fmt(D(value), 2)


def pfmt(value: Any) -> str:
    return base.pct_fmt(D(value), 2)


def result_int(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_FLOOR))


def factor_text(factors: list[tuple[str, Decimal]]) -> str:
    return " × ".join(f"{name} {fmt(Decimal('1') + value)}" for name, value in factors if value) or "1.00"


def render_report(raw: dict[str, Any], parsed: dict[str, Any], suite: dict[str, Any]) -> str:
    mechanics = suite["mechanics"]
    ready = suite["calculations"][suite["primaryScenario"]]
    seed = ready[base.CELESTIAL_RAIN_SKILL]["seed"]
    ap = seed["attackPower"]
    lines = [
        "# 나츠노소라 아르카나 4스택 루인 스킬 통합 계산 보고서",
        "",
        f"- 계산기/규칙 버전: `{CALCULATOR_VERSION}` / `{RULE_VERSION}`",
        f"- 캐릭터: `{parsed['profile']['characterName']}` / `{parsed['profile']['className']}` / 아이템 레벨 `{parsed['profile']['itemLevel']}`",
        "- 최종 표시는 소수점 아래 2자리이며, 내부 계산은 Decimal 원시값을 유지했습니다.",
        "- 모든 루인 스킬은 **스킬 본체**와 방향성 없는 **4스택 루인 효과**를 별도로 계산한 뒤 합산했습니다.",
        "",
        "## 1. 준비 완료 및 4스택 합산 결과",
        "",
        "모든 주 결과는 `준비 완료` 상태에서 스킬 본체와 4스택 루인 효과를 합산한 기대 피해입니다. 준비 완료는 스트림·안전 장치·어두운 운명·엣지 콤보 17P와 정면/후면 적중을 충족한 상태입니다. 아드레날린 6중첩과 급소 노출도 적용했습니다.",
        "",
        "| 스킬 | 준비 완료 본체 기대 | 준비 완료 4스택 기대 | 준비 완료 합산 기대 피해 |",
        "|---|---:|---:|---:|",
    ]
    for skill in ARCANA_SKILLS:
        r = ready[skill]
        lines.append(
            f"| {skill} | {fmt(result_int(r['direct']['expectedRaw']))} | {fmt(result_int(r['ruin']['expectedRaw']))} | **{fmt(result_int(r['total']['expectedRaw']))}** |"
        )
    r_ruin = ready[base.FOUR_STACK_RUIN_SKILL]
    lines.append(
        f"| 4스택 루인(공통, 트리거 보정 전) | - | {fmt(result_int(r_ruin['ruin']['expectedRaw']))} | **{fmt(result_int(r_ruin['total']['expectedRaw']))}** |"
    )
    lines += [
        "",
        "### 본체+4스택 합산 피해 상태",
        "",
        "확률 트라이포드가 있는 세렌디피티의 비치명타·치명타 열도 해당 확률을 평균한 값입니다.",
        "",
        "| 스킬 | 준비 완료 비치명 | 준비 완료 치명 | 준비 완료 합산 기대 |",
        "|---|---:|---:|---:|",
    ]
    for skill in (*ARCANA_SKILLS, base.FOUR_STACK_RUIN_SKILL):
        r = ready[skill]
        lines.append(
            f"| {skill} | {fmt(result_int(r['total']['nonCriticalRaw']))} | {fmt(result_int(r['total']['criticalRaw']))} | {fmt(result_int(r['total']['expectedRaw']))} |"
        )

    lines += [
        "",
        "## 2. 공격력과 공통 입력",
        "",
        f"`재구성 공격력 = {fmt(ap['final'])}` (API 프로필 `{fmt(ap['profileValueForComparison'])}`, 차이 `{fmt(ap['differenceFromProfile'])}`)",
        "",
        f"공식 v2.7.2 규칙을 이어받아 이후 계산에는 재구성 공격력 **{fmt(ap['usedForDamage'])}**을 사용했습니다.",
        "",
        f"- 특화 `{fmt(parsed['profile']['specializationStat'])}` → 루인 피해 `+{pfmt(mechanics['specializationRuinDamage'])}`",
        f"- 추가 피해 배율: `×{fmt(seed['damageGroups']['additionalDamageMultiplier'])}`",
        f"- 일반 치명타 피해 배율: `{fmt(seed['critical']['damageMultiplier'] - parsed['arkGrid']['criticalDamage'])}`",
        f"- 치명타 시 피해 곱연산(회심·팔찌·코어): `×{fmt(seed['critical']['criticalHitDamageMultiplier'])}`",
        f"- 적 방어 배율: `×{fmt(seed['enemy']['defenseMultiplier'])}`, 적 받는 피해 고정 배율: `×{fmt(seed['enemy']['damageTakenMultiplier'])}`",
        "",
        "### 사용자 제공 모션식과 본체 타격별 기대 피해",
        "",
        "| 스킬·타격 | 모션계수 | 모션상수 | 본체 기초값 | 준비 완료 기대 |",
        "|---|---:|---:|---:|---:|",
    ]
    for skill in ARCANA_SKILLS:
        model = base.get_skill_model(skill)
        r_hits = ready[skill]["direct"]["hits"]
        for model_hit, r_hit in zip(model["hits"], r_hits):
            lines.append(
                f"| {skill} {model_hit['name']} | {fmt(model_hit['coefficient'])} | {fmt(model_hit['constant'])} | {fmt(r_hit['base'])} | {fmt(result_int(r_hit['expectedRaw']))} |"
            )
    lines.append(
        f"| 4스택 루인 효과 | {fmt(RUIN_COEFFICIENT)} | {fmt(RUIN_CONSTANT)} | {fmt(RUIN_COEFFICIENT * D(ap['usedForDamage']))} | 스킬별 보정 |"
    )
    lines += [
        "",
        "## 3. 스킬별 치명타율과 뭉툭한 가시",
        "",
        "뭉툭한 가시 Lv.2는 원시 치명타율을 80.00%로 제한하고, 초과분의 150.00%를 진화형 피해로 바꿉니다. 따라서 치명 트라이포드가 다른 각 스킬/루인 효과마다 진화형 피해도 달라집니다.",
        "",
        "| 스킬·부분 | 준비 완료 원시→적용 치명 | 전환 진화 피해 |",
        "|---|---:|---:|",
    ]
    for skill in ARCANA_SKILLS:
        for key, label in (("direct", "본체"), ("ruin", "4스택")):
            r = ready[skill][key]["critical"]
            lines.append(
                f"| {skill} {label} | {pfmt(r['raw'])} → {pfmt(r['capped'])} | +{pfmt(r['convertedEvolution'])} |"
            )

    lines += [
        "",
        "## 4. 직업 메커니즘 적용",
        "",
        "- 사용자 제공 모션계수·상수는 스킬 본체에만 사용했습니다. `4스택 루인 = 15.90 × 재구성 공격력`은 별도 피해로 계산했습니다.",
        f"- 루인 효과 전용 배율: 특화 `×{fmt(1 + mechanics['specializationRuinDamage'])}`, 황후의 탐욕 `×{fmt(1 + mechanics['greedRuinDamage'])}`, 황후의 연회 `×{fmt(1 + mechanics['banquetFourStackDamage'])}`, 황후의 속삭임 `×{fmt(1 + mechanics['whisperRuinDamage'])}`, 인피니티 덱 10P `×{fmt(1 + mechanics['infinityRuinDamage'])}`.",
        f"- 준비 완료에서는 엣지 콤보 17P `×{fmt(1 + mechanics['edgeComboConditionalRuinDamage'])}`, 다크니스 엣지 치명 `+{pfmt(mechanics['streamCriticalRate'])}`, 별 코어 치명타 피해 `+{pfmt(mechanics['streamCoreCriticalDamage'])}`, 어두운 운명 치명타 피해 `+{pfmt(mechanics['darkFateCriticalDamage'])}`를 적용했습니다.",
        "- 일반 보석 피해는 해당 스킬 본체와 그 스킬로 발동한 스택트/루인 효과에 한 번씩 적용했습니다.",
        "- 마나 효율 증가는 네 루인 스킬과 그 스킬로 발동하는 루인 효과에 `×1.16`으로 적용했습니다.",
        "- 세렌디피티 `꿰뚫는 일격`은 방어력 80.00% 무시가 50.00% 확률로 발동하는 두 방어 상태의 기대값으로 계산했습니다. `우연한 일격`은 4스택에서 80.00% 확률로 루인 치명타 피해 +504.00%가 발동하는 기대값으로 계산했습니다.",
        "- 셀레스티얼 레인: 급소 타격 +45.00%, 강화된 일격 ×1.60, 4스택 약점 포착 ×2.76, 질서 별 코어 ×1.08 ×1.008.",
        "- 포 카드: 풀 하우스 치명 +44.00%, 카드 강화 ×1.75, 풀 하우스 보스 조건 ×1.36. 준비 완료 본체에만 백어택 피해 ×1.05와 치명 +10.00%를 적용했습니다.",
        "- 시크릿 가든: 급소 타격 +40.00%, 완전한 비밀은 4스택 대상 본체 ×1.80, 시크릿 찬스는 루인 효과 ×1.95. 준비 완료 본체에만 백어택 보너스를 적용했습니다.",
        "- 세렌디피티: 연속된 어둠은 본체 ×1.708. 준비 완료 본체에만 헤드어택 피해 ×1.20을 적용했으며 루인 효과에는 방향성 보너스를 적용하지 않았습니다.",
        "",
        "### 세렌디피티 확률 계산 확인",
        "",
    ]
    seren = ready[base.SERENDIPITY_SKILL]
    lines += [
        f"- 정상 방어 배율 `{fmt(seren['ruin']['defenseMultiplierNormal'])}`, 방어 80.00% 무시 배율 `{fmt(seren['ruin']['defenseMultiplierIgnored'])}`, 50.00% 기대 방어 배율 `{fmt(seren['ruin']['defenseMultiplierExpected'])}`.",
        f"- 준비 완료 기본 치명타 피해 `{fmt(seren['ruin']['criticalDamage'])}`에 우연한 일격 기대 증가 `0.80 × 5.04 = 4.03`을 더해 기대 치명타 피해 `{fmt(seren['ruin']['criticalDamageExpected'])}`로 계산했습니다.",
        "",
        "## 5. 의도적으로 제외한 조건",
        "",
        f"- 균형 카드 사용 시 인피니티 덱 루인 피해 +{pfmt(mechanics['balanceConditionalRuinDamage'])}: 카드 획득이 확률적이므로 양 시나리오에서 제외.",
        f"- 황제의 자비 카드 사용 후 피해 +{pfmt(mechanics['mercyConditionalDamage'])}: 카드 사용 시점이 지정되지 않아 제외.",
        "- 도태·심판 등 랜덤 아이덴티티 카드와 파티 시너지: 명시되지 않아 제외.",
        "- 재사용 대기시간 초기화/감소와 공격속도는 1회 피해가 아닌 DPS 요소이므로 제외. 단, 안전 장치 이동속도는 준비 완료의 돌격대장 산식에만 사용.",
        "- `공통 4스택 루인` 행은 트리거 스킬의 보석·트라이포드·방향성 보정을 일부러 제외한 기준값입니다. 실제 사용 피해는 각 스킬 행의 4스택 열을 사용해야 합니다.",
        "",
        "## 6. 검증 및 남은 불확실성",
        "",
        "- API 툴팁은 본체를 `스킬 피해`, 스택 폭발을 `스택트 효과/루인 피해`로 구분합니다. 계산기도 두 부분을 분리했습니다.",
        "- 커뮤니티 직업 가이드로 루인 피해 자체에는 헤드/백 보너스가 적용되지 않는다는 점을 교차 확인했습니다.",
        "- 완전한 비밀은 API 문구와 스킬 설명 자료가 모두 4스택 대상에게 스킬 피해가 증가한다고 설명하므로 본체 ×1.80으로 적용했습니다.",
        "- 실측값이 제공되지 않아 이번 결과는 산식·파싱 검증이며 수치 회귀검증은 수행하지 않았습니다.",
        "",
        "## 7. API 호출 결과와 출처",
        "",
        f"- API 호출 시각(KST): `{raw.get('capturedAtKst')}`",
        "- 디버그 원본/파싱 JSON은 사용자용 산출물로 생성하지 않았습니다.",
        "- 캐릭터 프로필·장비·각인·보석·전투 스킬·아크 패시브·ArkGrid 수치는 Lost Ark Open API 현재 응답을 사용했습니다.",
        "- 루인 방향성 교차 확인: [황후 아르카나 종합 가이드](https://www.inven.co.kr/board/lostark/5346/77994)",
        "- 완전한 비밀 범위 교차 확인: [시크릿 가든 스킬 설명](https://lostark.inven.co.kr/dataninfo/skill/?code=1931001)",
        "- 모션계수·모션상수: 사용자 제공값.",
        "",
        "| 엔드포인트 | HTTP | 호출 시각(KST) |",
        "|---|---:|---|",
    ]
    for name, meta in (raw.get("endpoints") or {}).items():
        lines.append(f"| {name} | {meta.get('status')} | {meta.get('capturedAtKst')} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--character", default=CHARACTER_NAME)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()

    if args.snapshot:
        raw = json.loads(args.snapshot.read_text(encoding="utf-8"))
        responses = base.response_from_raw_bundle(raw)
    else:
        token = os.environ.get("LOSTARK_API_TOKEN", "")
        if not token.strip():
            print("ERROR: LOSTARK_API_TOKEN 환경변수가 없습니다.", file=sys.stderr)
            return 2
        raw, responses = base.fetch_all(token, args.character)

    parsed = base.parse_all(responses, args.character, base.CELESTIAL_RAIN_SKILL)
    suite = calculate_suite(parsed)
    report = render_report(raw, parsed, suite)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / f"{args.character}_아르카나_{RULE_VERSION}_통합계산보고서.md"
    output.write_text(report, encoding="utf-8", newline="\n")
    print(f"통합 계산 보고서: {output.resolve()}")
    for skill, result in suite["calculations"]["rotation-ready"].items():
        print(f"{skill}: 준비 완료 기대 피해={result_int(result['total']['expectedRaw']):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
