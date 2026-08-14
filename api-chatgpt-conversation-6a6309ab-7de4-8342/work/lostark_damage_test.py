#!/usr/bin/env python3
"""기상술사 Lost Ark Open API parsing and damage calculation.

The bearer token is read only from LOSTARK_API_TOKEN and is never persisted.
All arithmetic uses Decimal. Rounding and effect formulas are selected through
an explicit, versioned ruleset.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP, getcontext
from pathlib import Path
from typing import Any, Iterable


getcontext().prec = 40

API_BASE = "https://developer-lostark.game.onstove.com"
CHARACTER_NAME = "봄날꽃씨"
CANONICAL_SKILL = "우레바람"
SPACE_CUTTING_SKILL = "공간 가르기"
WIND_GIMLET_SKILL = "바람송곳"
CUTTING_WIND_SKILL = "칼바람"
DOWNPOUR_SKILL = "몰아치기"
WHIRLWIND_STEP_SKILL = "회오리 걸음"
SKILL_ALIASES = {
    "우뢰바람": CANONICAL_SKILL,
    CANONICAL_SKILL: CANONICAL_SKILL,
    "공간가르기": SPACE_CUTTING_SKILL,
    SPACE_CUTTING_SKILL: SPACE_CUTTING_SKILL,
    WIND_GIMLET_SKILL: WIND_GIMLET_SKILL,
    CUTTING_WIND_SKILL: CUTTING_WIND_SKILL,
    DOWNPOUR_SKILL: DOWNPOUR_SKILL,
    "회오리걸음": WHIRLWIND_STEP_SKILL,
    WHIRLWIND_STEP_SKILL: WHIRLWIND_STEP_SKILL,
}
CALCULATOR_VERSION = "2.7.2"
PARSER_VERSION = "lostark-api-v2.7.1"
PARSED_SCHEMA_VERSION = "3.5.1"
DEFAULT_RULE_VERSION = "current-v2.7.2"
DB_RELEASE = "weather-artist-v0.4"
SCENARIO_PRESET_ID = "max-favorable-example-boss-v1"
CALCULATION_MODE = "ESTIMATE_WITH_FALLBACK"

ENDPOINTS = {
    "profiles": "profiles",
    "equipment": "equipment",
    "avatars": "avatars",
    "combatSkills": "combat-skills",
    "engravings": "engravings",
    "cards": "cards",
    "gems": "gems",
    "arkPassive": "arkpassive",
    "arkGrid": "arkgrid",
}

FIXED = {
    "skillCoefficient": Decimal("351.262"),
    "skillConstant": Decimal("52583"),
    "defenseConstant": Decimal("6500"),
    "enemyDefense": Decimal("5850"),
    "enemyDamageTakenMultiplier": Decimal("0.76"),
    "levelMainStat": Decimal("477"),
    "expeditionMainStat": Decimal("680"),
    "collectionMainStat": Decimal("976"),
    "petMainStatPercent": Decimal("0.01"),
    "petAdditionalDamagePercent": Decimal("0.01"),
    "petDemonDamagePercent": Decimal("0.005"),
    "collectionDemonDamagePercent": Decimal("0.065"),
    "feastAttackSpeedPercent": Decimal("0.05"),
    "feastMoveSpeedPercent": Decimal("0.05"),
    "combatBlessingAttackSpeedPercent": Decimal("0.09"),
    "combatBlessingMoveSpeedPercent": Decimal("0.09"),
    "baseCriticalDamage": Decimal("2.0"),
    "speedCap": Decimal("1.4"),
}

# Versioned rules preserve the old result model while allowing the spreadsheet
# formula graph to be reproduced independently. Explicit user corrections take
# precedence in current-v2.1.0.
RULESETS = {
    "example-v1.0.0": {
        "label": "기존 대화 예시 규칙",
        "source": "conversation",
        "attackPipeline": "legacy",
        "intermediateFloorStages": frozenset(),
        "useLiveEngravingDescriptions": False,
        "includeFlatWeaponAttack": False,
        "includeFlatAttackPower": False,
        "includePetMainStat": True,
        "includePetAdditionalDamage": True,
        "levelMainStat": Decimal("477"),
        "expeditionMainStat": Decimal("680"),
        "collectionMainStat": Decimal("976"),
        "feastAttackSpeedPercent": Decimal("0.05"),
        "feastMoveSpeedPercent": Decimal("0.05"),
        "combatBlessingAttackSpeedPercent": Decimal("0.09"),
        "combatBlessingMoveSpeedPercent": Decimal("0.09"),
        "raidCaptainFallbackCoefficient": Decimal("0.40"),
        "criticalStatFallbackCoefficient": Decimal("0.0003578586"),
        "swiftnessSpeedFallbackCoefficient": Decimal("0.000171759"),
        "sonic": {
            1: {
                "baseRate": Decimal("0.05"),
                "bothBonus": Decimal("0.04"),
                "overRate": Decimal("0.15"),
                "maximum": Decimal("0.12"),
            },
            2: {
                "baseRate": Decimal("0.10"),
                "bothBonus": Decimal("0.08"),
                "overRate": Decimal("0.30"),
                "maximum": Decimal("0.24"),
            },
        },
    },
    "season3-xlsx-v2.0.0": {
        "label": "시즌3 엑셀 원본 호환 규칙",
        "source": "시즌3 전용 데미지 계산기.xlsx",
        "attackPipeline": "workbook",
        "intermediateFloorStages": frozenset(
            {"mainStat", "weaponAttack", "attackPower"}
        ),
        "useLiveEngravingDescriptions": True,
        "includeFlatWeaponAttack": True,
        "includeFlatAttackPower": True,
        "includePetMainStat": False,
        "includePetAdditionalDamage": False,
        "levelMainStat": Decimal("477"),
        # 원본 M9는 물약/원정대를 하나로 합친 수동 입력값이다.
        "expeditionMainStat": Decimal("702"),
        "collectionMainStat": Decimal("976"),
        "feastAttackSpeedPercent": Decimal("0.035"),
        "feastMoveSpeedPercent": Decimal("0.035"),
        "combatBlessingAttackSpeedPercent": Decimal("0.09"),
        "combatBlessingMoveSpeedPercent": Decimal("0.09"),
        "raidCaptainFallbackCoefficient": Decimal("0.48"),
        "criticalStatFallbackCoefficient": Decimal("0.0003578586"),
        "swiftnessSpeedFallbackCoefficient": Decimal("0.000171759"),
        "sonic": {
            1: {
                "baseRate": Decimal("0.05"),
                "bothBonus": Decimal("0.04"),
                "overRate": Decimal("0.10"),
                "maximum": Decimal("0.12"),
            },
            2: {
                "baseRate": Decimal("0.10"),
                "bothBonus": Decimal("0.08"),
                "overRate": Decimal("0.20"),
                "maximum": Decimal("0.24"),
            },
        },
    },
    "current-v2.1.0": {
        "label": "엑셀 구조 + 사용자 최신 확정 규칙",
        "source": "season3-xlsx-v2.0.0 + explicit user overrides",
        "attackPipeline": "workbook",
        # 사용자가 확정한 규칙: 최종 데미지 결과에서만 버림.
        "intermediateFloorStages": frozenset(),
        "useLiveEngravingDescriptions": True,
        "includeFlatWeaponAttack": True,
        "includeFlatAttackPower": True,
        "includePetMainStat": True,
        "includePetAdditionalDamage": True,
        "levelMainStat": Decimal("477"),
        "expeditionMainStat": Decimal("680"),
        "collectionMainStat": Decimal("976"),
        "feastAttackSpeedPercent": Decimal("0.05"),
        "feastMoveSpeedPercent": Decimal("0.05"),
        "combatBlessingAttackSpeedPercent": Decimal("0.09"),
        "combatBlessingMoveSpeedPercent": Decimal("0.09"),
        "raidCaptainFallbackCoefficient": Decimal("0.48"),
        "criticalStatFallbackCoefficient": Decimal("0.0003578586"),
        "swiftnessSpeedFallbackCoefficient": Decimal("0.000171759"),
        "sonic": {
            1: {
                "baseRate": Decimal("0.05"),
                "bothBonus": Decimal("0.04"),
                "overRate": Decimal("0.15"),
                "maximum": Decimal("0.12"),
            },
            2: {
                "baseRate": Decimal("0.10"),
                "bothBonus": Decimal("0.08"),
                "overRate": Decimal("0.30"),
                "maximum": Decimal("0.24"),
            },
        },
    },
}

SKILL_MODELS = {
    CANONICAL_SKILL: {
        "displayName": CANONICAL_SKILL,
        "variant": "최대 홀딩",
        "hits": [
            {
                "name": "최대 홀딩",
                "coefficient": Decimal("351.262"),
                "constant": Decimal("52583"),
            }
        ],
        "tags": {
            "NON_DIRECTIONAL",
            "UMBRELLA_SKILL",
            "HYPER_AWAKENING_SKILL",
        },
        "tagVerification": "VERIFIED_BY_SKILL_TAG",
        "source": "LEGACY_EXAMPLE",
    },
    SPACE_CUTTING_SKILL: {
        "displayName": SPACE_CUTTING_SKILL,
        "variant": "1타+2타",
        "hits": [
            {
                "name": "1타",
                "coefficient": Decimal("40.07"),
                "constant": Decimal("6117"),
            },
            {
                "name": "2타",
                "coefficient": Decimal("93.50"),
                "constant": Decimal("14283"),
            },
        ],
        # NON_DIRECTIONAL is authoritative for direction classification. It
        # makes non-awakening skills eligible for Hit Master.
        "tags": {
            "NON_DIRECTIONAL",
            "UMBRELLA_SKILL",
            "ENLIGHTENMENT_X_SKILL",
        },
        "tagVerification": "VERIFIED_BY_SKILL_TAG",
        "source": "USER_VERIFIED",
    },
    WIND_GIMLET_SKILL: {
        "displayName": WIND_GIMLET_SKILL,
        "variant": "역류·큰 센바람·집중 공격",
        "hits": [
            {
                "name": "전체 타격",
                "coefficient": Decimal("52.20"),
                "constant": Decimal("7874"),
            },
        ],
        "tags": {"NON_DIRECTIONAL", "UMBRELLA_SKILL"},
        "requiredTripods": ["역류", "큰 센바람", "집중 공격"],
        "separateDamageTripod": {
            "name": "역류",
            "condition": "기류 보호막 보유",
        },
        "criticalDamageTripod": None,
        "tagVerification": "VERIFIED_BY_SKILL_TAG",
        "source": "USER_VERIFIED",
    },
    CUTTING_WIND_SKILL: {
        "displayName": CUTTING_WIND_SKILL,
        "variant": "거대 돌풍·역류·벼락",
        "hits": [
            {
                "name": "전체 타격",
                "coefficient": Decimal("48.98"),
                "constant": Decimal("7388.5"),
            },
        ],
        "tags": {"NON_DIRECTIONAL", "UMBRELLA_SKILL"},
        "requiredTripods": ["거대 돌풍", "역류", "벼락"],
        "separateDamageTripod": {
            "name": "역류",
            "condition": "기류 보호막 보유",
        },
        "criticalDamageTripod": {
            "name": "벼락",
            "value": Decimal("2.10"),
        },
        "tagVerification": "VERIFIED_BY_SKILL_TAG",
        "source": "USER_VERIFIED",
    },
    DOWNPOUR_SKILL: {
        "displayName": DOWNPOUR_SKILL,
        "variant": "역류·우레·공간베기",
        "hits": [
            {
                "name": "1타",
                "coefficient": Decimal("9.72"),
                "constant": Decimal("1466.7"),
            },
            {
                "name": "2타",
                "coefficient": Decimal("22.65"),
                "constant": Decimal("3417.1"),
            },
            {
                "name": "3타(공간베기)",
                "coefficient": Decimal("30.69"),
                "constant": Decimal("4629.8"),
                "tripodSource": "공간베기",
            },
        ],
        "tags": {"NON_DIRECTIONAL", "UMBRELLA_SKILL"},
        "requiredTripods": ["역류", "우레", "공간베기"],
        "separateDamageTripod": {
            "name": "역류",
            "condition": "기류 보호막 보유",
        },
        "criticalDamageTripod": {
            "name": "우레",
            "value": Decimal("1.80"),
        },
        "tagVerification": "VERIFIED_BY_SKILL_TAG",
        "source": "USER_VERIFIED",
    },
    WHIRLWIND_STEP_SKILL: {
        "displayName": WHIRLWIND_STEP_SKILL,
        "variant": "재빠른 손놀림·역류·초고속 회전",
        "hits": [
            {
                "name": "1타",
                "coefficient": Decimal("22.72"),
                "constant": Decimal("3427.5"),
            },
            {
                "name": "2타",
                "coefficient": Decimal("9.75"),
                "constant": Decimal("1470.9"),
            },
        ],
        "tags": {"NON_DIRECTIONAL", "UMBRELLA_SKILL"},
        "requiredTripods": ["재빠른 손놀림", "역류", "초고속 회전"],
        "separateDamageTripod": {
            "name": "역류",
            "condition": "기류 보호막 보유",
        },
        "criticalDamageTripod": None,
        "tagVerification": "VERIFIED_BY_SKILL_TAG",
        "source": "USER_VERIFIED",
    },
}

# v2.2.0 keeps the explicitly confirmed v2.1.0 arithmetic rules. The version
# bump identifies parser, provenance, ArkGrid point-effect, regular-gem, and
# profile-attack selection behavior added after the v2.1.0 audit.
RULESETS["current-v2.2.0"] = {
    **RULESETS["current-v2.1.0"],
    "label": "v2.1 확정 산식 + 데이터 출처 감사 수정",
    "source": (
        "current-v2.1.0 + calculator_v2.1.0_data_source_audit "
        "+ explicit user corrections"
    ),
}
RULESETS["current-v2.3.0"] = {
    **RULESETS["current-v2.2.0"],
    "label": "v2.2 감사 산식 + 다중 스킬·다중 타격",
    "source": (
        "current-v2.2.0 + user-provided space-cutting hit coefficients "
        "+ explicit scope assumptions"
    ),
}
RULESETS["current-v2.4.0"] = {
    **RULESETS["current-v2.3.0"],
    "label": "v2.3 다중 타격 산식 + ArkGrid 코어 임계 효과",
    "source": (
        "current-v2.3.0 + live ArkGrid.Slots core tooltip thresholds "
        "+ user-provided weather-artist core reference"
    ),
}
RULESETS["current-v2.4.1"] = {
    **RULESETS["current-v2.4.0"],
    "label": "v2.4 코어 임계 효과 + ArkGrid 연산자·등급 분기",
    "source": (
        "current-v2.4.0 + user-confirmed additive/multiplicative core rules "
        "+ relic/ancient slash resolution"
    ),
}
RULESETS["current-v2.4.2"] = {
    **RULESETS["current-v2.4.1"],
    "label": "v2.4.1 ArkGrid 연산 + 깨달음 카르마 레벨 환산",
    "source": (
        "current-v2.4.1 + user-confirmed enlightenment karma "
        "weapon-attack rate (0.1% per level)"
    ),
}
RULESETS["current-v2.5.0"] = {
    **RULESETS["current-v2.4.2"],
    "label": "v2.4.2 계산식 + 질풍노도 우산 스킬 4종",
    "source": (
        "current-v2.4.2 + user-provided wind-gimlet, cutting-wind, "
        "downpour, and whirlwind-step motion formulas"
    ),
}
RULESETS["current-v2.6.0"] = {
    **RULESETS["current-v2.5.0"],
    "label": "v2.5 우산 스킬 산식 + 완갑·역류 분리 적용",
    "source": (
        "current-v2.5.0 + Armlet equipment tooltip fields "
        "+ user-confirmed Reflux exclusion from motion formulas"
    ),
    "includeArmletBaseAttack": True,
    "includeSeparateTripodDamage": True,
}
RULESETS["current-v2.7.0"] = {
    **RULESETS["current-v2.6.0"],
    "label": "v2.6 완갑 산식 + 선택 트라이포드 전체 피해 효과",
    "source": (
        "current-v2.6.0 + official selected-tripod tooltip damage effects "
        "+ user-confirmed tripod-free motion formulas"
    ),
    "applyAllSelectedTripodDamage": True,
}
RULESETS["current-v2.7.1"] = {
    **RULESETS["current-v2.7.0"],
    "label": "v2.7 전체 트라이포드 효과 + 추가 타격 중복 방지",
    "source": (
        "current-v2.7.0 + motion-hit/tripod provenance linkage "
        "+ embedded additional-attack deduplication"
    ),
    "deduplicateEmbeddedTripodHits": True,
}
RULESETS["current-v2.7.2"] = {
    **RULESETS["current-v2.7.1"],
    "label": "공식 재구성 공격력 + 공간 가르기 모션계수 상향",
    "source": (
        "current-v2.7.1 + officially adopted reconstructed attack power "
        "+ user-confirmed Space Cutting motion coefficient x1.292"
    ),
    "useCalculatedAttackForDamage": True,
    "skillMotionCoefficientMultipliers": {
        SPACE_CUTTING_SKILL: Decimal("1.292"),
    },
}

WORKBOOK_FORMULA_EVIDENCE = {
    "sourceWorkbook": "시즌3 전용 데미지 계산기.xlsx",
    "sheet": "데미지 계산기",
    "usedRange": "A1:BI106",
    "mainStat": {
        "cell": "M4",
        "formula": "=ROUNDDOWN(SUM(M8:M15)*(1+P8),0)",
    },
    "weaponAttack": {
        "cell": "M5",
        "formula": "=ROUNDDOWN(SUM(M18:M22)*(1+P18),0)",
    },
    "attackPower": {
        "cell": "P4",
        "formula": (
            "=ROUNDDOWN(((M4*M5/6)^0.5*(1+SUM(P25:P26))"
            "+SUM(M25:M27))*(1+SUM(P29:P34)),0)"
        ),
    },
    "engravingDamage": {
        "cell": "T4",
        "formula": (
            "=(1+T8+V8)*(1+T9+V9)*(1+T11+V11)*(1+T14+V14)"
            "*(1+T15+V15)*(1+T16+V16)*(1+T17+V17)"
            "*(1+T21+V21)*(1+T22+V22)"
        ),
    },
    "skillExpectedDamage": {
        "cell": "BB4",
        "formula": "=SUM(BB8:BB27)",
    },
    "additionalDamage": {
        "cell": "BF4",
        "formula": "=SUM(BF8:BF12)+1",
    },
    "otherDamage": {
        "cell": "BF5",
        "formula": (
            "=(1+BF15)*(1+BF16)*(1+BF17)*(1+BF18)*(1+BF19)"
            "*(1+BF20)*(1+BF21)*(1+BF22)*(1+BF23)"
        ),
    },
    "finalDamage": {
        "cell": "BI4",
        "formula": "=BI8*BI9*BI10*BI11*BI12",
    },
    "sonicBreakthroughLv1": {
        "cell": "AJ62",
        "overCapRate": "0.10",
    },
    "sonicBreakthroughLv2": {
        "cell": "AK62",
        "overCapRate": "0.20",
    },
}

# Values established by the example conversation. They are fallback data only
# when a named effect exists but its current numeric description is unavailable.
EXAMPLE_EFFECT_DB = {
    "원한": {"generalDamage": Decimal("0.2175")},
    "아드레날린": {
        "attackPowerPercent": Decimal("0.1038"),
        "criticalRate": Decimal("0.20"),
    },
    "질량 증가": {
        "generalDamage": Decimal("0.1825"),
        "attackSpeed": Decimal("-0.10"),
    },
    "질풍노도": {
        "attackSpeed": Decimal("0.12"),
        "moveSpeed": Decimal("0.12"),
    },
    "타격의 대가": {"generalDamage": Decimal("0.17")},
    "한계 돌파": {"evolutionDamage": Decimal("0.30")},
    "무한한 마력": {"evolutionDamage": Decimal("0.08")},
    "혼신의 강타": {
        "evolutionDamage": Decimal("0.02"),
        "criticalRate": Decimal("0.12"),
    },
    "분쇄": {"evolutionDamage": Decimal("0.20")},
    "정열의 춤": {"evolutionDamage": Decimal("0.14")},
    "풀려난 힘": {"skillDamage": Decimal("0.15")},
    "바람의 길": {"generalDamage": Decimal("0.024")},
    "기민함": {
        "criticalRate": Decimal("0.12"),
        "criticalDamage": Decimal("0.48"),
    },
    "단련된 가르기": {"skillDamage": Decimal("0.75")},
    "급소 노출": {"criticalRate": Decimal("0.10")},
    "회심": {"criticalHitDamage": Decimal("0.12")},
}

SUPPORTED_GENERAL_DAMAGE_ENGRAVINGS = (
    "원한",
    "저주받은 인형",
    "질량 증가",
    "타격의 대가",
)
SUPPORTED_GENERAL_DAMAGE_ENGRAVING_SET = set(
    SUPPORTED_GENERAL_DAMAGE_ENGRAVINGS
)

SUPPORT_ARKGRID_TERMS = ("낙인력", "아군 공격력 강화", "아군 피해량 강화", "아공강", "아피강")
ARKGRID_SKILL_NAMES = (
    "회오리 걸음",
    "몰아치기",
    "바람송곳",
    "칼바람",
    "여우비 기본 공격",
    "여우비",
    "소나기",
    "싹쓸바람",
    "뙤약볕",
    "센바람",
)
ARKGRID_CORE_TOTAL_KEYS = (
    "attackPowerFlat",
    "attackPowerPercent",
    "weaponAttackFlat",
    "weaponAttackPercent",
    "additionalDamagePercent",
    "bossDamagePercent",
    "generalDamagePercent",
    "criticalRate",
    "criticalDamage",
    "criticalHitDamagePercent",
    "attackSpeed",
    "moveSpeed",
    "enemyDefenseReductionPercent",
)
TRANSCENDENCE_TERMS = ("초월",)
PERCENT = r"([0-9]+(?:\.[0-9]+)?)\s*%"
NUMBER = r"([0-9][0-9,]*(?:\.[0-9]+)?)"


class CalculationError(RuntimeError):
    pass


def now_kst() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat()


def dec(value: Any, default: str = "0") -> Decimal:
    if value is None or value == "":
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    return Decimal(str(value).replace(",", "").strip())


def get_rules(rule_version: str) -> dict[str, Any]:
    try:
        return RULESETS[rule_version]
    except KeyError as exc:
        supported = ", ".join(RULESETS)
        raise CalculationError(
            f"알 수 없는 계산 규칙 버전 '{rule_version}'. 지원: {supported}"
        ) from exc


def floor_decimal(value: Decimal) -> Decimal:
    return value.to_integral_value(rounding=ROUND_FLOOR)


def apply_stage_rounding(
    value: Decimal, stage: str, rules: dict[str, Any]
) -> Decimal:
    if stage in rules["intermediateFloorStages"]:
        return floor_decimal(value)
    return value


def pct(value: Any) -> Decimal:
    return dec(value) / Decimal("100")


def json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, dict):
        return {k: json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [json_ready(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return [json_ready(v) for v in sorted(value)]
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(json_ready(value), ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def strip_markup(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<BR\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</?[^>]+>", "", value)
    value = value.replace("\\n", "\n").replace("\u00a0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _collect_strings(value: Any, out: list[str]) -> None:
    if isinstance(value, str):
        if value.strip():
            out.append(strip_markup(value))
    elif isinstance(value, dict):
        # Tooltip display strings are normally under value/Element_* nodes.
        for key, child in value.items():
            if key.lower() in {"type", "key", "slotdata", "qualityvalue"}:
                continue
            _collect_strings(child, out)
    elif isinstance(value, list):
        for child in value:
            _collect_strings(child, out)


def tooltip_to_text(raw: Any) -> str:
    if raw is None:
        return ""
    parsed: Any = raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return strip_markup(raw)
    strings: list[str] = []
    _collect_strings(parsed, strings)
    # Remove consecutive duplicates created by nested tooltip wrappers while
    # retaining identical values from distinct items (handled per item).
    clean: list[str] = []
    for item in strings:
        if item and (not clean or item != clean[-1]):
            clean.append(item)
    return "\n".join(clean)


def find_numbers(text: str, pattern: str, flags: int = 0) -> list[Decimal]:
    return [dec(match) for match in re.findall(pattern, text, flags)]


def first_or_zero(values: Iterable[Decimal]) -> Decimal:
    for value in values:
        return value
    return Decimal("0")


def max_or_zero(values: Iterable[Decimal]) -> Decimal:
    values = list(values)
    return max(values) if values else Decimal("0")


def sum_unique(values: Iterable[Decimal]) -> Decimal:
    return sum(set(values), Decimal("0"))


def warn_once(warnings: list[str], message: str) -> None:
    if message not in warnings:
        warnings.append(message)


def source(
    *,
    source_type: str,
    path: str,
    label: str,
    value: Decimal | str | int | bool,
    raw: str = "",
    parsed: bool = True,
    eligible: bool | None = None,
    applied: bool = True,
    excluded_reason: str = "",
    note: str = "",
) -> dict[str, Any]:
    if eligible is None:
        eligible = applied
    if not applied and not excluded_reason:
        excluded_reason = note
    return {
        "sourceType": source_type,
        "path": path,
        "label": label,
        "value": value,
        "raw": raw,
        "parsed": parsed,
        "eligible": eligible,
        "applied": applied,
        "excludedReason": excluded_reason,
        "note": note,
    }


def canonical_skill(name: str) -> str:
    return SKILL_ALIASES.get(name, name)


def get_skill_model(skill_name: str) -> dict[str, Any]:
    canonical = canonical_skill(skill_name)
    try:
        return SKILL_MODELS[canonical]
    except KeyError as exc:
        supported = ", ".join(SKILL_MODELS)
        raise CalculationError(
            f"등록되지 않은 스킬 '{skill_name}'. 지원: {supported}"
        ) from exc


def effective_skill_hits(
    skill_name: str, rules: dict[str, Any]
) -> list[dict[str, Any]]:
    """Resolve versioned motion-coefficient changes without altering constants."""
    canonical = canonical_skill(skill_name)
    multiplier = dec(
        (rules.get("skillMotionCoefficientMultipliers") or {}).get(
            canonical, Decimal("1")
        )
    )
    return [
        {
            **hit,
            "originalCoefficient": hit["coefficient"],
            "coefficient": hit["coefficient"] * multiplier,
            "coefficientMultiplier": multiplier,
        }
        for hit in get_skill_model(canonical)["hits"]
    ]


def ark_passive_skill_damage_scope(
    effect_name: str, skill_name: str
) -> tuple[bool, str]:
    canonical = canonical_skill(skill_name)
    tags = get_skill_model(canonical)["tags"]
    if effect_name == SPACE_CUTTING_SKILL:
        return (
            canonical == SPACE_CUTTING_SKILL,
            f"{SPACE_CUTTING_SKILL} 전용 아크 패시브",
        )
    if effect_name == "단련된 가르기":
        return canonical == CANONICAL_SKILL, f"{CANONICAL_SKILL} 전용 효과"
    if effect_name == "바람의 길":
        return (
            "UMBRELLA_SKILL" in tags,
            "우산 스킬 태그 필요",
        )
    if effect_name == "풀려난 힘":
        return (
            "HYPER_AWAKENING_SKILL" in tags,
            "초각성 스킬 태그 필요",
        )
    return True, "일반 스킬 피해 효과"


def engraving_scope(
    engraving_name: str, skill_name: str
) -> tuple[bool, str]:
    if engraving_name != "타격의 대가":
        return True, "등록된 일반 피해 각인"
    tags = get_skill_model(skill_name)["tags"]
    eligible = (
        "NON_DIRECTIONAL" in tags and "AWAKENING_SKILL" not in tags
    )
    return eligible, "비방향성·각성기 제외 조건"


def fetch_endpoint(token: str, character: str, endpoint: str) -> tuple[dict[str, Any], Any]:
    encoded = urllib.parse.quote(character, safe="")
    url = f"{API_BASE}/armories/characters/{encoded}/{endpoint}"
    normalized = token.strip()
    if normalized.lower().startswith("bearer "):
        normalized = normalized[7:].strip()
    request = urllib.request.Request(
        url,
        headers={
            "accept": "application/json",
            "authorization": f"bearer {normalized}",
            "user-agent": "Codex-LostArk-Damage-Parser/1.0",
        },
        method="GET",
    )
    captured = now_kst()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw_bytes = response.read()
            raw_text = raw_bytes.decode("utf-8")
            body = json.loads(raw_text)
            headers = response.headers
            meta = {
                "url": url,
                "capturedAtKst": captured,
                "status": response.status,
                "rateLimit": {
                    "limit": headers.get("X-RateLimit-Limit"),
                    "remaining": headers.get("X-RateLimit-Remaining"),
                    "reset": headers.get("X-RateLimit-Reset"),
                },
                "contentType": headers.get("Content-Type"),
                "rawBody": raw_text,
            }
            return meta, body
    except urllib.error.HTTPError as exc:
        raw_text = exc.read().decode("utf-8", errors="replace")
        raise CalculationError(
            f"{endpoint} API 호출 실패: HTTP {exc.code}; 응답={raw_text[:500]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise CalculationError(f"{endpoint} API 연결 실패: {exc.reason}") from exc


def fetch_all(token: str, character: str) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata: dict[str, Any] = {}
    responses: dict[str, Any] = {}
    for key, endpoint in ENDPOINTS.items():
        meta, body = fetch_endpoint(token, character, endpoint)
        metadata[key] = meta
        responses[key] = body
    raw_bundle = {
        "characterName": character,
        "capturedAtKst": now_kst(),
        "apiBase": API_BASE,
        "authorizationPersisted": False,
        "endpoints": metadata,
        "responses": responses,
    }
    return raw_bundle, responses


def response_from_raw_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    responses = bundle.get("responses")
    if not isinstance(responses, dict):
        raise CalculationError("스냅샷에 responses 객체가 없습니다.")
    return responses


def parse_profile(body: dict[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    body = body or {}
    stats_by_type = {str(item.get("Type")): item for item in body.get("Stats") or []}
    critical = stats_by_type.get("치명") or {}
    swiftness = stats_by_type.get("신속") or {}
    attack = stats_by_type.get("공격력") or {}
    crit_text = tooltip_to_text(critical.get("Tooltip"))
    swift_text = tooltip_to_text(swiftness.get("Tooltip"))

    crit_rate = max_or_zero(
        pct(v)
        for v in find_numbers(
            crit_text, rf"치명타\s*적중률(?:이|은)?\s*\+?{PERCENT}", re.I
        )
    )
    attack_speed = max_or_zero(
        pct(v)
        for v in find_numbers(
            swift_text, rf"공격\s*속도(?:가|는)?\s*\+?{PERCENT}", re.I
        )
    )
    move_speed = max_or_zero(
        pct(v)
        for v in find_numbers(
            swift_text, rf"이동\s*속도(?:가|는)?\s*\+?{PERCENT}", re.I
        )
    )
    if not attack_speed or not move_speed:
        generic = [pct(v) for v in find_numbers(swift_text, PERCENT)]
        if generic:
            attack_speed = attack_speed or generic[0]
            move_speed = move_speed or generic[0]
            warnings.append("신속 툴팁의 명시적 속도 문구를 찾지 못해 첫 퍼센트를 사용했습니다.")
    if not crit_rate:
        generic = [pct(v) for v in find_numbers(crit_text, PERCENT)]
        if generic:
            crit_rate = generic[0]
            warnings.append("치명 툴팁의 명시적 치명타율 문구를 찾지 못해 첫 퍼센트를 사용했습니다.")
    if not crit_rate and critical.get("Value"):
        crit_rate = (
            dec(critical.get("Value"))
            * RULESETS[DEFAULT_RULE_VERSION]["criticalStatFallbackCoefficient"]
        )
        warn_once(
            warnings,
            "치명 툴팁 환산값이 없어 엑셀 계수 0.0003578586을 사용했습니다.",
        )
    if (not attack_speed or not move_speed) and swiftness.get("Value"):
        speed_fallback = (
            dec(swiftness.get("Value"))
            * RULESETS[DEFAULT_RULE_VERSION]["swiftnessSpeedFallbackCoefficient"]
        )
        attack_speed = attack_speed or speed_fallback
        move_speed = move_speed or speed_fallback
        warn_once(
            warnings,
            "신속 툴팁 환산값이 없어 엑셀 계수 0.000171759를 사용했습니다.",
        )

    return {
        "characterName": body.get("CharacterName"),
        "className": body.get("CharacterClassName"),
        "characterLevel": body.get("CharacterLevel"),
        "expeditionLevel": body.get("ExpeditionLevel"),
        "itemLevel": body.get("ItemAvgLevel"),
        "combatPower": body.get("CombatPower"),
        "criticalStat": dec(critical.get("Value")),
        "swiftnessStat": dec(swiftness.get("Value")),
        "profileAttackPower": dec(attack.get("Value")),
        "criticalRateFromStat": crit_rate,
        "attackSpeedFromSwiftness": attack_speed,
        "moveSpeedFromSwiftness": move_speed,
        "sources": [
            source(
                source_type="API_FIELD",
                path="profiles.CharacterLevel",
                label="캐릭터 레벨",
                value=body.get("CharacterLevel") or 0,
            ),
            source(
                source_type="API_FIELD",
                path="profiles.ExpeditionLevel",
                label="원정대 레벨",
                value=body.get("ExpeditionLevel") or 0,
            ),
            source(
                source_type="API_FIELD",
                path="profiles.Stats[치명]",
                label="치명",
                value=dec(critical.get("Value")),
                raw=crit_text,
            ),
            source(
                source_type="API_FIELD",
                path="profiles.Stats[신속]",
                label="신속",
                value=dec(swiftness.get("Value")),
                raw=swift_text,
            ),
            source(
                source_type="API_FIELD",
                path="profiles.Stats[공격력]",
                label="프로필 공격력(검산용)",
                value=dec(attack.get("Value")),
            ),
        ],
    }


def parse_equipment(body: list[dict[str, Any]] | None, warnings: list[str]) -> dict[str, Any]:
    result = {
        "mainStat": Decimal("0"),
        "baseWeaponAttack": Decimal("0"),
        "weaponAttackFlat": Decimal("0"),
        "weaponAttackPercent": Decimal("0"),
        "baseAttackPowerFlat": Decimal("0"),
        "baseAttackPowerPercent": Decimal("0"),
        "attackPowerFlat": Decimal("0"),
        "attackPowerPercent": Decimal("0"),
        "weaponAdditionalDamage": Decimal("0"),
        "necklaceAdditionalDamage": Decimal("0"),
        "otherAdditionalDamage": Decimal("0"),
        "damageToEnemy": Decimal("0"),
        "necklaceDamageToEnemy": Decimal("0"),
        "braceletDamageToEnemy": Decimal("0"),
        "otherDamageToEnemy": Decimal("0"),
        "criticalRate": Decimal("0"),
        "criticalDamage": Decimal("0"),
        "braceletCriticalHitDamage": Decimal("0"),
        "braceletNonDirectionalDamage": Decimal("0"),
        "hasMasterElixir": False,
        "items": [],
        "sources": [],
        "excluded": [],
    }
    for index, item in enumerate(body or []):
        item_type = str(item.get("Type") or "")
        text = tooltip_to_text(item.get("Tooltip"))
        path = f"equipment[{index}]"
        parsed: dict[str, Any] = {
            "type": item_type,
            "name": item.get("Name"),
            "grade": item.get("Grade"),
            "tooltipText": text,
            "values": {},
        }
        if any(term in text for term in TRANSCENDENCE_TERMS):
            result["excluded"].append(
                source(
                    source_type="API_TOOLTIP",
                    path=path,
                    label="초월",
                    value=0,
                    raw="초월",
                    applied=False,
                    note="계획에 따라 전부 제외",
                )
            )

        intelligence = max_or_zero(find_numbers(text, rf"지능\s*\+?{NUMBER}"))
        base_weapon_attack = max_or_zero(
            find_numbers(text, rf"무기\s*공격력\s*\+?{NUMBER}\s*(?:\n|$)")
        )
        attack_flat = sum_unique(
            find_numbers(
                text,
                rf"(?<!무기\s)(?<!아군\s)(?<!기본\s)공격력\s*\+?{NUMBER}\s*(?:\n|$)",
            )
        )
        wa_percent = sum_unique(
            pct(v) for v in find_numbers(text, rf"무기\s*공격력\s*\+?{PERCENT}")
        )
        attack_percent = sum_unique(
            pct(v)
            for v in find_numbers(
                text,
                rf"(?<!무기\s)(?<!아군\s)(?<!기본\s)공격력\s*\+?{PERCENT}",
            )
        )
        # 완갑의 기본 공격력 옵션은 최종 공격력이나 보석/스톤 옵션과
        # 계산 단계가 다르다. 완갑 타입에만 한정해 중복 파싱을 막는다.
        base_attack_flat = Decimal("0")
        base_attack_percent = Decimal("0")
        if item_type == "완갑":
            base_attack_flat = sum_unique(
                find_numbers(
                    text,
                    rf"기본\s*공격력\s*\+?{NUMBER}\s*(?:\n|$)",
                )
            )
            base_attack_percent = sum_unique(
                pct(v)
                for v in find_numbers(
                    text,
                    rf"기본\s*공격력(?:이)?\s*\+?{PERCENT}(?:\s*증가)?",
                )
            )
        additional = sum_unique(
            pct(v) for v in find_numbers(text, rf"추가\s*피해\s*\+?{PERCENT}")
        )
        damage_to_enemy = sum_unique(
            pct(v)
            for v in find_numbers(
                text,
                rf"적에게\s*주는\s*피해(?:가|량이)?\s*(?:\+)?{PERCENT}(?:\s*증가)?",
            )
        )
        crit_rate = sum_unique(
            pct(v)
            for v in find_numbers(
                text,
                rf"치명타\s*적중률(?:이|은)?\s*(?:\+)?{PERCENT}(?:\s*증가)?",
            )
        )
        crit_damage = sum_unique(
            pct(v)
            for v in find_numbers(
                text,
                rf"치명타\s*피해(?:가|량이)?\s*(?:\+)?{PERCENT}(?:\s*증가)?",
            )
        )
        crit_hit_damage = sum_unique(
            pct(v)
            for v in find_numbers(
                text,
                rf"(?:공격이\s*)?치명타(?:로|가)?\s*적중(?:할|한|했을)?\s*(?:시|때)?"
                rf"[^%\n]{{0,45}}?피해(?:가|량이)?\s*(?:\+)?{PERCENT}(?:\s*증가)?",
            )
        )
        non_directional = sum_unique(
            pct(v)
            for v in find_numbers(
                text, rf"비방향성(?:\s*공격)?\s*피해(?:가|량이)?\s*\+?{PERCENT}"
            )
        )
        if item_type == "팔찌" and crit_hit_damage:
            # "치명타 적중 시 적에게 주는 피해" also matches the broad
            # damage-to-enemy pattern. Keep it only in the conditional group.
            damage_to_enemy = max(
                Decimal("0"), damage_to_enemy - crit_hit_damage
            )

        # Standard "치명타 피해 +X%" and conditional "치명타 적중 시 피해"
        # are separate groups; avoid counting the latter twice.
        if crit_hit_damage and crit_damage == crit_hit_damage:
            crit_damage = Decimal("0")

        result["mainStat"] += intelligence
        if item_type == "무기":
            result["baseWeaponAttack"] = max(
                result["baseWeaponAttack"], base_weapon_attack
            )
        else:
            result["weaponAttackFlat"] += base_weapon_attack
        result["weaponAttackPercent"] += wa_percent
        result["baseAttackPowerFlat"] += base_attack_flat
        result["baseAttackPowerPercent"] += base_attack_percent
        result["attackPowerFlat"] += attack_flat
        result["attackPowerPercent"] += attack_percent
        if item_type == "무기":
            result["weaponAdditionalDamage"] += additional
        elif item_type == "목걸이":
            result["necklaceAdditionalDamage"] += additional
        else:
            result["otherAdditionalDamage"] += additional
        result["damageToEnemy"] += damage_to_enemy
        if item_type == "목걸이":
            result["necklaceDamageToEnemy"] += damage_to_enemy
        elif item_type == "팔찌":
            result["braceletDamageToEnemy"] += damage_to_enemy
        else:
            result["otherDamageToEnemy"] += damage_to_enemy
        result["criticalRate"] += crit_rate
        result["criticalDamage"] += crit_damage
        if item_type == "팔찌":
            result["braceletCriticalHitDamage"] += crit_hit_damage
            result["braceletNonDirectionalDamage"] += non_directional
        if "회심" in text:
            result["hasMasterElixir"] = True

        parsed["values"] = {
            "mainStat": intelligence,
            "baseWeaponAttack": (
                base_weapon_attack if item_type == "무기" else Decimal("0")
            ),
            "weaponAttackFlat": (
                Decimal("0") if item_type == "무기" else base_weapon_attack
            ),
            "weaponAttackPercent": wa_percent,
            "baseAttackPowerFlat": base_attack_flat,
            "baseAttackPowerPercent": base_attack_percent,
            "attackPowerFlat": attack_flat,
            "attackPowerPercent": attack_percent,
            "additionalDamage": additional,
            "damageToEnemy": damage_to_enemy,
            "criticalRate": crit_rate,
            "criticalDamage": crit_damage,
            "criticalHitDamage": crit_hit_damage,
            "nonDirectionalDamage": non_directional,
        }
        result["items"].append(parsed)
        for label, value in parsed["values"].items():
            if value:
                result["sources"].append(
                    source(
                        source_type="API_TOOLTIP",
                        path=f"{path}.Tooltip",
                        label=f"{item_type} {label}",
                        value=value,
                        raw=text,
                    )
                )
    if not result["mainStat"]:
        warnings.append("장비 툴팁에서 지능을 추출하지 못했습니다.")
    if not result["baseWeaponAttack"]:
        warnings.append("무기 툴팁에서 기본 무기 공격력을 추출하지 못했습니다.")
    return result


def parse_avatars(body: list[dict[str, Any]] | None, warnings: list[str]) -> dict[str, Any]:
    grouped: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, avatar in enumerate(body or []):
        grouped[str(avatar.get("Type") or f"unknown-{index}")].append((index, avatar))
    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    total = Decimal("0")
    stat_types = {"무기", "머리", "상의", "하의"}
    for avatar_type, candidates in grouped.items():
        inner = [(i, a) for i, a in candidates if a.get("IsInner") is True]
        chosen_index, chosen = (inner or candidates)[0]
        grade = str(chosen.get("Grade") or "")
        normalized_type = re.sub(r"\s*아바타$", "", avatar_type)
        value = (
            Decimal("0.02")
            if normalized_type in stat_types and grade == "전설"
            else Decimal("0")
        )
        if normalized_type not in stat_types:
            note = "주스탯 적용 부위가 아니므로 0%"
        elif grade and grade != "전설":
            note = "예시 DB에 해당 등급이 없어 0%"
            warnings.append(
                f"{avatar_type} 아바타 등급 '{grade}'은 예시 DB에 없어 주스탯 0%로 처리했습니다."
            )
        else:
            note = "전설 부위당 +2% 예시값"
        selected.append(
            source(
                source_type="API_FIELD+EXAMPLE_DB",
                path=f"avatars[{chosen_index}]",
                label=f"{avatar_type} 아바타 주스탯",
                value=value,
                raw=f"{chosen.get('Name')} / {grade} / IsInner={chosen.get('IsInner')}",
                note=note,
            )
        )
        total += value
        for index, avatar in candidates:
            if index != chosen_index:
                excluded.append(
                    source(
                        source_type="API_FIELD",
                        path=f"avatars[{index}]",
                        label=f"{avatar_type} 중복 아바타",
                        value=0,
                        raw=f"{avatar.get('Name')} / IsInner={avatar.get('IsInner')}",
                        applied=False,
                        note="부위별 효과 아바타 하나만 선택",
                    )
                )
    return {"mainStatPercent": total, "selected": selected, "excluded": excluded}


def flatten_descriptions(value: Any) -> str:
    strings: list[str] = []
    _collect_strings(value, strings)
    return "\n".join(strings)


def parse_engravings(body: dict[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    body = body or {}
    entries = body.get("ArkPassiveEffects") or body.get("Effects") or []
    found: dict[str, dict[str, Any]] = {}
    parsed_effects: dict[str, dict[str, Decimal | int]] = {}
    sources: list[dict[str, Any]] = []
    stone_total = 0
    for index, entry in enumerate(entries):
        raw_name = str(entry.get("Name") or "")
        name = re.sub(r"\s*Lv\.?\s*\d+.*$", "", raw_name).strip()
        description = tooltip_to_text(entry.get("Description") or entry.get("Tooltip"))
        stone_level = int(entry.get("AbilityStoneLevel") or 0)
        stone_total += stone_level
        general_damage = max_or_zero(
            pct(v)
            for v in find_numbers(
                description,
                rf"(?:"
                rf"(?:보스\s*및\s*레이드\s*몬스터에게|적에게)\s*주는\s*"
                rf"피해(?:량)?"
                rf"|공격(?:의)?\s*피해"
                rf")(?:이|가)?\s*(?:\+)?{PERCENT}(?:\s*증가)?",
            )
        )
        raid_coefficient = max_or_zero(
            pct(v)
            for v in find_numbers(
                description,
                rf"이동\s*속도\s*증가량의\s*{PERCENT}\s*만큼",
            )
        )
        attack_speed_reduction = max_or_zero(
            pct(v)
            for v in find_numbers(
                description,
                rf"공격\s*속도(?:가|는)?\s*{PERCENT}\s*감소",
            )
        )
        per_stack_attack = max_or_zero(
            pct(v)
            for v in find_numbers(
                description,
                rf"공격력(?:이|은)?\s*(?:\+)?{PERCENT}\s*증가",
            )
        )
        stack_match = re.search(r"최대\s*(\d+)\s*중첩", description)
        max_stacks = int(stack_match.group(1)) if stack_match else 1
        attack_power = per_stack_attack * max_stacks
        critical_rate = max_or_zero(
            pct(v)
            for v in find_numbers(
                description,
                rf"치명타\s*적중률(?:이|은)?[^%\n]{{0,35}}?{PERCENT}\s*증가",
            )
        )
        parsed_effects[name] = {
            "generalDamage": general_damage,
            "raidCaptainCoefficient": raid_coefficient,
            "attackSpeed": -attack_speed_reduction,
            "attackPowerPercent": attack_power,
            "attackPowerPerStack": per_stack_attack,
            "maxStacks": max_stacks,
            "criticalRate": critical_rate,
        }
        found[name] = {
            "name": name,
            "rawName": raw_name,
            "grade": entry.get("Grade"),
            "level": entry.get("Level"),
            "abilityStoneLevel": stone_level,
            "description": description,
            "parsed": parsed_effects[name],
        }
        sources.append(
            source(
                source_type="API_FIELD",
                path=f"engravings.entries[{index}]",
                label=name,
                value=entry.get("Level") or 0,
                raw=description,
            )
        )
    stone_base_attack = Decimal("0.015") if stone_total >= 5 else Decimal("0")
    if stone_base_attack:
        sources.append(
            source(
                source_type="API_FIELD+EXAMPLE_DB",
                path="engravings.ArkPassiveEffects[].AbilityStoneLevel",
                label="어빌리티 스톤 기본 공격력",
                value=stone_base_attack,
                raw=f"각인 돌 레벨 합계={stone_total}",
                note="예시 임계값 합계 5 이상 → +1.5%",
            )
        )
    return {
        "entries": found,
        "parsedEffects": parsed_effects,
        "names": sorted(found),
        "stoneLevelTotal": stone_total,
        "stoneBaseAttackPercent": stone_base_attack,
        "sources": sources,
    }


def parse_cards(body: dict[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    body = body or {}
    total = Decimal("0")
    sources: list[dict[str, Any]] = []
    for effect_index, effect in enumerate(body.get("Effects") or []):
        for item_index, item in enumerate(effect.get("Items") or []):
            text = tooltip_to_text(item.get("Description") or item)
            values = [
                pct(v)
                for v in find_numbers(
                    text,
                    rf"(?:주는\s*피해|피해가|피해량이)[^%\n]{{0,30}}?{PERCENT}",
                )
            ]
            values += [
                pct(v)
                for v in find_numbers(
                    text, rf"(?:성|암|화|수|토|뇌|신성)?속성\s*피해\s*\+?{PERCENT}"
                )
            ]
            value = sum_unique(values)
            if value:
                total += value
                sources.append(
                    source(
                        source_type="API_FIELD",
                        path=f"cards.Effects[{effect_index}].Items[{item_index}]",
                        label=str(item.get("Name") or "카드 피해"),
                        value=value,
                        raw=text,
                    )
                )
    if body.get("Cards") and not total:
        warnings.append("장착 카드는 있으나 피해 증가 카드 효과를 파싱하지 못했습니다.")
    return {"damagePercent": total, "sources": sources}


def parse_gems(
    body: dict[str, Any] | None,
    warnings: list[str],
    target_skill: str = CANONICAL_SKILL,
) -> dict[str, Any]:
    body = body or {}
    target_skill = canonical_skill(target_skill)
    total_base_attack = Decimal("0")
    sources: list[dict[str, Any]] = []
    gems: list[dict[str, Any]] = []
    skill_effects: list[dict[str, Any]] = []
    for index, gem in enumerate(body.get("Gems") or []):
        text = tooltip_to_text(gem.get("Tooltip"))
        values = [
            pct(v)
            for v in find_numbers(
                text,
                rf"기본\s*공격력(?:이)?\s*(?:\+|증가\s*)?{PERCENT}(?:\s*증가)?",
                re.I,
            )
        ]
        # Some tooltip versions put the percentage before "기본 공격력 증가".
        values += [
            pct(v)
            for v in find_numbers(
                text, rf"{PERCENT}[^%\n]{{0,20}}기본\s*공격력\s*증가", re.I
            )
        ]
        value = max_or_zero(values)
        total_base_attack += value

        damage_matches = re.findall(
            rf"(?:\[[^\]\n]+\]\s*)?([가-힣A-Za-z0-9·' ]+?)\s+"
            rf"피해(?:량)?(?:이|가)?\s*(?:\+)?{PERCENT}\s*증가",
            text,
            re.I,
        )
        cooldown_matches = re.findall(
            rf"(?:\[[^\]\n]+\]\s*)?([가-힣A-Za-z0-9·' ]+?)\s+"
            rf"재사용\s*대기시간(?:이|가)?\s*(?:\+)?{PERCENT}\s*감소",
            text,
            re.I,
        )
        parsed_skill_effects: list[dict[str, Any]] = []
        for raw_skill, raw_value in damage_matches:
            skill_name = canonical_skill(raw_skill.strip())
            if skill_name in {"추가", "기본 공격력"}:
                continue
            skill_value = pct(raw_value)
            item = {
                "skillName": skill_name,
                "effectType": "damage",
                "value": skill_value,
                "sourceGemIndex": index,
            }
            parsed_skill_effects.append(item)
            skill_effects.append(item)
            sources.append(
                source(
                    source_type="OFFICIAL_TOOLTIP",
                    path=f"gems.Gems[{index}].Tooltip",
                    label=f"일반 보석 {skill_name} 피해",
                    value=skill_value,
                    raw=text,
                    eligible=skill_name == target_skill,
                    applied=skill_name == target_skill,
                    excluded_reason=(
                        ""
                        if skill_name == target_skill
                        else f"현재 계산 스킬은 {target_skill}"
                    ),
                )
            )
        for raw_skill, raw_value in cooldown_matches:
            skill_name = canonical_skill(raw_skill.strip())
            cooldown_value = pct(raw_value)
            item = {
                "skillName": skill_name,
                "effectType": "cooldownReduction",
                "value": cooldown_value,
                "sourceGemIndex": index,
            }
            parsed_skill_effects.append(item)
            skill_effects.append(item)
            sources.append(
                source(
                    source_type="OFFICIAL_TOOLTIP",
                    path=f"gems.Gems[{index}].Tooltip",
                    label=f"일반 보석 {skill_name} 재사용 대기시간 감소",
                    value=cooldown_value,
                    raw=text,
                    eligible=False,
                    applied=False,
                    excluded_reason="1회 피해에는 영향이 없고 로테이션/DPS에서 사용",
                )
            )
        parsed = {
            "slot": gem.get("Slot"),
            "name": gem.get("Name"),
            "level": gem.get("Level"),
            "grade": gem.get("Grade"),
            "baseAttackPercent": value,
            "skillEffects": parsed_skill_effects,
            "tooltipText": text,
        }
        gems.append(parsed)
        if value:
            sources.append(
                source(
                    source_type="API_TOOLTIP",
                    path=f"gems.Gems[{index}].Tooltip",
                    label=f"{gem.get('Name')} 기본 공격력",
                    value=value,
                    raw=text,
                )
            )
    return {
        "baseAttackPercent": total_base_attack,
        "skillEffects": skill_effects,
        "gems": gems,
        "sources": sources,
    }


def regular_gem_effect_for_skill(
    parsed_gems: dict[str, Any], skill_name: str
) -> dict[str, Any]:
    canonical = canonical_skill(skill_name)
    damage_values: list[Decimal] = []
    cooldown_values: list[Decimal] = []
    matched: list[dict[str, Any]] = []
    for item in parsed_gems.get("skillEffects") or []:
        if canonical_skill(str(item.get("skillName") or "")) != canonical:
            continue
        matched.append(item)
        value = dec(item.get("value"))
        if item.get("effectType") == "damage":
            damage_values.append(value)
        elif item.get("effectType") == "cooldownReduction":
            cooldown_values.append(value)
    # A character normally has at most one damage and one cooldown gem per
    # skill. max() prevents malformed duplicate snapshots from double-counting.
    return {
        "skillName": canonical,
        "damagePercent": max_or_zero(damage_values),
        "cooldownReductionPercent": max_or_zero(cooldown_values),
        "cooldownMultiplier": Decimal("1") - max_or_zero(cooldown_values),
        "matchedEffects": matched,
    }


def normalize_effect_name(name: str) -> str:
    name = canonical_skill(name)
    name = re.sub(r"\s*Lv\.?\s*\d+.*$", "", name)
    name = re.sub(r"\s*[ⅠⅡⅢIVX]+$", "", name)
    return name.strip()


def match_example_effect(text: str) -> str | None:
    for name in EXAMPLE_EFFECT_DB:
        if name in text:
            return name
    return None


def parse_ark_passive(
    body: dict[str, Any] | None,
    warnings: list[str],
    target_skill: str = CANONICAL_SKILL,
) -> dict[str, Any]:
    body = body or {}
    target_skill = canonical_skill(target_skill)
    effects: dict[str, dict[str, Any]] = {}
    sources: list[dict[str, Any]] = []
    fallbacks: list[dict[str, Any]] = []
    evolution_by_name: dict[str, Decimal] = {}
    skill_damage_by_name: dict[str, Decimal] = {}
    critical_rate_by_name: dict[str, Decimal] = {}
    critical_damage_by_name: dict[str, Decimal] = {}
    critical_hit_damage_by_name: dict[str, Decimal] = {}
    additional_damage_by_name: dict[str, Decimal] = {}
    speed_by_name: dict[str, dict[str, Decimal]] = {}

    def record_fallback(
        *, path: str, label: str, value: Decimal, raw: str, note: str
    ) -> None:
        fallbacks.append(
            source(
                source_type="LEGACY_EXAMPLE",
                path=path,
                label=label,
                value=value,
                raw=raw,
                parsed=False,
                note=note,
            )
        )

    for index, effect in enumerate(body.get("Effects") or []):
        raw_name = str(effect.get("Name") or "")
        summary = tooltip_to_text(effect.get("Description"))
        detail = tooltip_to_text(effect.get("ToolTip") or effect.get("Tooltip"))
        description = "\n".join(part for part in (summary, detail) if part)
        summary_name = re.search(
            r"(?:깨달음|진화|도약)\s+\d+티어\s+(.+?)\s+Lv\.?\s*\d+",
            summary,
        )
        normalized = normalize_effect_name(
            summary_name.group(1) if summary_name else raw_name
        )
        matched = match_example_effect(f"{normalized}\n{description}") or normalized
        level_match = re.search(
            r"(?:Lv\.?\s*|레벨\s*)(\d+)", summary + " " + description
        )
        level = int(level_match.group(1)) if level_match else None

        evolution = max_or_zero(
            pct(v)
            for v in find_numbers(
                description,
                rf"진화형\s*피해(?:가|량이)?\s*(?:\+)?{PERCENT}(?:\s*증가)?",
            )
        )
        critical_rate = max_or_zero(
            pct(v)
            for v in find_numbers(
                description,
                rf"치명타\s*적중률(?:이|은)?\s*(?:\+)?{PERCENT}(?:\s*증가)?",
            )
        )
        attack_move_speed = max_or_zero(
            pct(v)
            for v in find_numbers(
                description,
                rf"공격\s*및\s*이동\s*속도(?:가|는)?\s*(?:\+)?{PERCENT}(?:\s*증가)?",
            )
        )
        skill_damage = Decimal("0")
        if matched in {
            "바람의 길",
            "풀려난 힘",
            "단련된 가르기",
            SPACE_CUTTING_SKILL,
        }:
            skill_damage = max_or_zero(
                pct(v)
                for v in find_numbers(
                    description,
                    rf"(?:피해량|주는\s*피해)(?:이|가)?\s*(?:\+)?{PERCENT}(?:\s*증가)?",
                )
            )
        critical_hit_damage = Decimal("0")
        if matched == "회심":
            critical_hit_damage = max_or_zero(
                pct(v)
                for v in find_numbers(
                    description,
                    rf"치명타로\s*적중\s*시[^%\n]{{0,35}}?피해(?:가|량이)?\s*(?:\+)?{PERCENT}",
                )
            )
        additional_damage = Decimal("0")
        if matched == "달인":
            stack_match = re.search(r"최대\s*(\d+)\s*중첩", description)
            stacks = int(stack_match.group(1)) if stack_match else 5
            per_stack_crit = max_or_zero(
                pct(v)
                for v in find_numbers(
                    description, rf"치명타\s*적중률\s*(?:\+)?{PERCENT}"
                )
            )
            per_stack_additional = max_or_zero(
                pct(v)
                for v in find_numbers(
                    description, rf"추가\s*피해\s*(?:\+)?{PERCENT}"
                )
            )
            critical_rate = per_stack_crit * stacks
            additional_damage = per_stack_additional * stacks
        if matched == "기민함":
            # Under the agreed most-favorable state, both "base speed
            # increase" inputs use the 40% cap: 40%*30%, 40%*120%.
            critical_rate = Decimal("0.12")
            critical_damage_by_name[matched] = Decimal("0.48")

        if evolution:
            evolution_by_name[matched] = evolution
        if skill_damage:
            skill_damage_by_name[matched] = skill_damage
        if critical_rate:
            critical_rate_by_name[matched] = critical_rate
        if critical_hit_damage:
            critical_hit_damage_by_name[matched] = critical_hit_damage
        if additional_damage:
            additional_damage_by_name[matched] = additional_damage
        if attack_move_speed:
            speed_by_name[matched] = {
                "attackSpeed": attack_move_speed,
                "moveSpeed": attack_move_speed,
            }

        # Fallback only when the API tooltip does not expose a usable number.
        fallback = EXAMPLE_EFFECT_DB.get(matched, {})
        if not evolution and fallback.get("evolutionDamage"):
            evolution_by_name[matched] = fallback["evolutionDamage"]
            record_fallback(
                path=f"arkPassive.Effects[{index}]",
                label=f"{matched} 진화형 피해",
                value=fallback["evolutionDamage"],
                raw=description,
                note="API 툴팁 수치 파싱 실패로 예시 DB 사용",
            )
            warn_once(
                warnings,
                f"{matched} 현재 수치를 툴팁에서 파싱하지 못해 예시값 "
                f"{fallback['evolutionDamage'] * 100}%를 사용했습니다.",
            )
        if not skill_damage and fallback.get("skillDamage"):
            skill_damage_by_name[matched] = fallback["skillDamage"]
            record_fallback(
                path=f"arkPassive.Effects[{index}]",
                label=f"{matched} 스킬 피해",
                value=fallback["skillDamage"],
                raw=description,
                note="API 툴팁 수치 파싱 실패로 예시 DB 사용",
            )
            warn_once(
                warnings,
                f"{matched} 현재 수치를 툴팁에서 파싱하지 못해 예시값 "
                f"{fallback['skillDamage'] * 100}%를 사용했습니다.",
            )
        if not critical_rate and fallback.get("criticalRate") and matched != "기민함":
            critical_rate_by_name[matched] = fallback["criticalRate"]
            record_fallback(
                path=f"arkPassive.Effects[{index}]",
                label=f"{matched} 치명타 적중률",
                value=fallback["criticalRate"],
                raw=description,
                note="API 툴팁 수치 파싱 실패로 예시 DB 사용",
            )
        if not critical_hit_damage and fallback.get("criticalHitDamage"):
            critical_hit_damage_by_name[matched] = fallback["criticalHitDamage"]
            record_fallback(
                path=f"arkPassive.Effects[{index}]",
                label=f"{matched} 치명타 적중 시 피해",
                value=fallback["criticalHitDamage"],
                raw=description,
                note="API 툴팁 수치 파싱 실패로 예시 DB 사용",
            )
        if not attack_move_speed and (
            fallback.get("attackSpeed") or fallback.get("moveSpeed")
        ):
            speed_by_name[matched] = {
                "attackSpeed": fallback.get("attackSpeed", Decimal("0")),
                "moveSpeed": fallback.get("moveSpeed", Decimal("0")),
            }
            record_fallback(
                path=f"arkPassive.Effects[{index}]",
                label=f"{matched} 공격·이동속도",
                value=max(
                    fallback.get("attackSpeed", Decimal("0")),
                    fallback.get("moveSpeed", Decimal("0")),
                ),
                raw=description,
                note="API 툴팁 수치 파싱 실패로 예시 DB 사용",
            )

        effects[matched] = {
            "name": matched,
            "rawName": raw_name,
            "level": level,
            "description": description,
            "parsed": {
                "evolutionDamage": evolution_by_name.get(matched, Decimal("0")),
                "skillDamage": skill_damage_by_name.get(matched, Decimal("0")),
                "criticalRate": critical_rate_by_name.get(matched, Decimal("0")),
                "criticalDamage": critical_damage_by_name.get(matched, Decimal("0")),
                "criticalHitDamage": critical_hit_damage_by_name.get(
                    matched, Decimal("0")
                ),
                "additionalDamage": additional_damage_by_name.get(
                    matched, Decimal("0")
                ),
                "attackSpeed": speed_by_name.get(matched, {}).get(
                    "attackSpeed", Decimal("0")
                ),
                "moveSpeed": speed_by_name.get(matched, {}).get(
                    "moveSpeed", Decimal("0")
                ),
            },
        }
        parsed_components = effects[matched]["parsed"]
        scoped_skill_damage = dec(parsed_components.get("skillDamage"))
        skill_damage_eligible, skill_scope_reason = (
            ark_passive_skill_damage_scope(matched, target_skill)
            if scoped_skill_damage
            else (False, "")
        )
        universal_component_keys = {
            "evolutionDamage",
            "criticalRate",
            "criticalDamage",
            "criticalHitDamage",
            "additionalDamage",
            "attackSpeed",
            "moveSpeed",
        }
        eligible = (
            matched == "음속 돌파"
            or any(
                dec(parsed_components.get(key)) != 0
                for key in universal_component_keys
            )
            or (scoped_skill_damage != 0 and skill_damage_eligible)
        )
        excluded_reasons = {
            "환기": "자원 회복은 1회 피해에 직접 영향 없음",
            "치명": "최종 프로필 치명 및 치명타율에 이미 반영",
            "신속": "최종 프로필 신속 및 속도 환산값에 이미 반영",
            "잠재력 해방": "초각성 스킬 쿨타임 효과는 로테이션/DPS 대상",
            "즉각적인 주문": "시전 속도·마나 효과는 1회 피해에 직접 배율 없음",
        }
        excluded_reason = (
            ""
            if eligible
            else (
                f"{skill_scope_reason}; 현재 계산 스킬은 {target_skill}"
                if scoped_skill_damage
                else excluded_reasons.get(
                    matched, "현재 단일 시전 피해식에 연결된 컴포넌트 없음"
                )
            )
        )
        sources.append(
            source(
                source_type="API_FIELD",
                path=f"arkPassive.Effects[{index}]",
                label=matched,
                value=level or 0,
                raw=description,
                eligible=eligible,
                applied=eligible,
                excluded_reason=excluded_reason,
            )
        )

    karma_weapon_attack = Decimal("0")
    karma_evolution = Decimal("0")
    points: list[dict[str, Any]] = []
    for index, point in enumerate(body.get("Points") or []):
        name = str(point.get("Name") or "")
        text = tooltip_to_text(point.get("Description") or point.get("Tooltip"))
        level_values = find_numbers(text, r"([0-9]+)\s*레벨")
        karma_level = int(max(level_values)) if level_values else 0
        weapon_values = [
            pct(v)
            for v in find_numbers(
                text, rf"무기\s*공격력(?:이)?[^%\n]{{0,25}}?{PERCENT}"
            )
        ]
        evolution_values = [
            pct(v)
            for v in find_numbers(
                text, rf"진화형\s*피해(?:가|량이)?[^%\n]{{0,25}}?{PERCENT}"
            )
        ]
        if "깨달음" in name or "깨달음" in text:
            if karma_level:
                karma_weapon_attack = (
                    Decimal(karma_level) * Decimal("0.001")
                )
                sources.append(
                    source(
                        source_type="API_FIELD+USER_VERIFIED",
                        path=f"arkPassive.Points[{index}].Description",
                        label="깨달음 카르마 무기 공격력",
                        value=karma_weapon_attack,
                        raw=text,
                        note=(
                            f"깨달음 카르마 {karma_level}레벨 × "
                            "레벨당 무기 공격력 0.1%"
                        ),
                    )
                )
            elif weapon_values:
                karma_weapon_attack = max(weapon_values)
            elif text:
                warn_once(
                    warnings,
                    "깨달음 카르마 레벨과 무기 공격력 수치를 파싱하지 못해 "
                    "무기 공격력 증가를 적용하지 않았습니다.",
                )
        if "진화" in name or "진화" in text:
            if evolution_values:
                karma_evolution = max(evolution_values)
            elif text and ("카르마" in text or "랭크" in text):
                karma_evolution = Decimal("0.06")
                record_fallback(
                    path=f"arkPassive.Points[{index}]",
                    label="진화 카르마 진화형 피해",
                    value=karma_evolution,
                    raw=text,
                    note="랭크·레벨 전체 표가 없어 예시 DB 사용",
                )
                warn_once(
                    warnings,
                    "진화 카르마 수치를 파싱하지 못해 예시값 +6.0%를 사용했습니다.",
                )
        points.append(
            {
                "name": name,
                "value": point.get("Value"),
                "text": text,
                "karmaLevel": karma_level,
            }
        )
        if weapon_values or evolution_values:
            sources.append(
                source(
                    source_type="API_TOOLTIP",
                    path=f"arkPassive.Points[{index}]",
                    label=f"{name} 카르마",
                    value=(max(weapon_values) if weapon_values else max(evolution_values)),
                    raw=text,
                )
            )
    return {
        "effects": effects,
        "targetSkill": target_skill,
        "points": points,
        "karmaWeaponAttackPercent": karma_weapon_attack,
        "karmaEvolutionDamage": karma_evolution,
        "evolutionDamageByName": evolution_by_name,
        "skillDamageByName": skill_damage_by_name,
        "criticalRateByName": critical_rate_by_name,
        "criticalDamageByName": critical_damage_by_name,
        "criticalHitDamageByName": critical_hit_damage_by_name,
        "additionalDamageByName": additional_damage_by_name,
        "speedByName": speed_by_name,
        "sources": sources,
        "fallbacks": fallbacks,
    }


def parse_tripod_damage_effects(text: str) -> dict[str, Any]:
    """Classify one selected tripod's tooltip effects used by one-cast damage.

    Motion coefficients/constants are treated as the unmodified skill body.
    Every damage increase in the selected tripod tooltip therefore remains an
    independent multiplier.  A tooltip-described additional attack is kept as
    a total-damage multiplier when the API provides no separate motion formula.
    """
    damage_effects: list[dict[str, Any]] = []
    patterns = (
        (
            "DAMAGE_INCREASE",
            "피해 증가",
            rf"적에게\s*주는\s*피해(?:가|를|량이)?\s*(?:\+)?{PERCENT}\s*"
            rf"(?:증가|증가시킨다)",
        ),
        (
            "ADDITIONAL_ATTACK",
            "추가 공격 피해",
            rf"(?:적에게\s*)?(?:총\s*)?(?:\+)?{PERCENT}\s*추가\s*피해",
        ),
        (
            "INCREASED_TOTAL_DAMAGE",
            "총 증가 피해",
            rf"총\s*(?:\+)?{PERCENT}\s*(?:의\s*)?증가된\s*피해",
        ),
    )
    for effect_type, label, pattern in patterns:
        for value in dict.fromkeys(find_numbers(text, pattern)):
            damage_effects.append(
                {
                    "type": effect_type,
                    "label": label,
                    "percent": pct(value),
                    "multiplier": Decimal("1") + pct(value),
                }
            )

    critical_damage = sum_unique(
        pct(value)
        for value in find_numbers(
            text,
            rf"치명타\s*피해(?:가|량이)?\s*(?:\+)?{PERCENT}\s*"
            rf"(?:증가|증가시킨다)",
        )
    )
    return {
        "damageEffects": damage_effects,
        "criticalDamagePercent": critical_damage,
    }


def parse_combat_skills(body: list[dict[str, Any]] | None) -> dict[str, Any]:
    selected_tripods: list[dict[str, Any]] = []
    skill_names: list[str] = []
    exposed_weakness = False
    sources: list[dict[str, Any]] = []
    for skill_index, skill in enumerate(body or []):
        skill_name = canonical_skill(str(skill.get("Name") or ""))
        skill_names.append(skill_name)
        for tripod_index, tripod in enumerate(skill.get("Tripods") or []):
            if tripod.get("IsSelected") is True:
                tripod_name = str(tripod.get("Name") or "")
                tripod_text = tooltip_to_text(tripod.get("Tooltip"))
                parsed_damage = parse_tripod_damage_effects(tripod_text)
                damage_percent = Decimal("0")
                if tripod_name == "역류":
                    damage_percent = sum(
                        (
                            item["percent"]
                            for item in parsed_damage["damageEffects"]
                            if item["type"] == "DAMAGE_INCREASE"
                        ),
                        Decimal("0"),
                    )
                selected_tripods.append(
                    {
                        "skill": skill_name,
                        "name": tripod_name,
                        "tier": tripod.get("Tier"),
                        "tooltipText": tripod_text,
                        "damagePercent": damage_percent,
                        "damageEffects": parsed_damage["damageEffects"],
                        "criticalDamagePercent": parsed_damage[
                            "criticalDamagePercent"
                        ],
                    }
                )
                if "급소 노출" in tripod_name:
                    exposed_weakness = True
                    sources.append(
                        source(
                            source_type="API_FIELD+EXAMPLE_DB",
                            path=f"combatSkills[{skill_index}].Tripods[{tripod_index}]",
                            label="급소 노출",
                            value=EXAMPLE_EFFECT_DB["급소 노출"]["criticalRate"],
                            raw=tooltip_to_text(tripod.get("Tooltip")),
                            note="항상 적용 규칙",
                        )
                    )
    return {
        "skillNames": skill_names,
        "selectedTripods": selected_tripods,
        "hasExposedWeakness": exposed_weakness,
        "sources": sources,
    }


def parse_arkgrid_damage_values(text: str) -> dict[str, Decimal]:
    attack_values = [
        pct(v)
        for v in find_numbers(
            text,
            rf"(?<!무기\s)(?<!아군\s)(?:^|\s)공격력(?:이)?\s*"
            rf"(?:\+|증가\s*)?{PERCENT}",
            re.M,
        )
    ]
    additional_values = [
        pct(v)
        for v in find_numbers(
            text, rf"추가\s*피해(?:가|량이)?\s*(?:\+|증가\s*)?{PERCENT}"
        )
    ]
    boss_values = [
        pct(v)
        for v in find_numbers(
            text,
            rf"(?:"
            rf"보스(?:\s*등급\s*이상\s*몬스터)?에게\s*주는\s*피해"
            rf"|보스\s*피해"
            rf")(?:가|량이)?\s*(?:\+|증가\s*)?{PERCENT}",
        )
    ]
    return {
        "attackPowerPercent": max_or_zero(attack_values),
        "additionalDamagePercent": max_or_zero(additional_values),
        "bossDamagePercent": max_or_zero(boss_values),
    }


def extract_arkgrid_core_options(text: str) -> list[dict[str, Any]]:
    """Return [nP] core options, including continuation lines, in tooltip order."""
    options: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_options = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "코어 옵션":
            in_options = True
            continue
        if line in {"코어 옵션 발동 조건", "분해불가"}:
            if current:
                options.append(current)
                current = None
            in_options = False
            continue
        if not in_options:
            continue
        match = re.match(r"\[(\d+)P\]\s*(.*)", line)
        if match:
            if current:
                options.append(current)
            current = {
                "requiredPoints": int(match.group(1)),
                "text": match.group(2).strip(),
            }
        elif current and line:
            current["text"] += "\n" + line
    if current:
        options.append(current)
    return options


def arkgrid_component(
    category: str,
    value: Decimal,
    *,
    scope_kind: str = "ALL",
    scope_value: str | list[str] = "",
    condition: str = "",
    operator: str = "ADD",
) -> dict[str, Any]:
    return {
        "category": category,
        "value": value,
        "scopeKind": scope_kind,
        "scopeValue": scope_value,
        "condition": condition,
        "operator": operator,
    }


ARKGRID_MULTIPLICATIVE_CATEGORIES = {
    "generalDamagePercent",
    "bossDamagePercent",
    "skillDamagePercent",
    "criticalHitDamagePercent",
    "enemyDefenseReductionPercent",
}


def resolve_arkgrid_grade_values(text: str, core_grade: str) -> str:
    """Select relic/ancient values from A/B% core reference text."""
    use_ancient = "고대" in core_grade

    def replace(match: re.Match[str]) -> str:
        selected = match.group(2) if use_ancient else match.group(1)
        suffix = "%" if match.group(3) else ""
        return f"{selected}{suffix}"

    return re.sub(
        (
            r"(?<![0-9.])([0-9]+(?:\.[0-9]+)?)\s*/\s*"
            r"([0-9]+(?:\.[0-9]+)?)(\s*%)?"
        ),
        replace,
        text,
    )


def arkgrid_core_component_scope(
    component: dict[str, Any], skill_name: str
) -> tuple[bool, str]:
    scope_kind = component["scopeKind"]
    scope_value = component.get("scopeValue")
    model = get_skill_model(skill_name)
    if scope_kind == "ALL":
        return True, "모든 공격"
    if scope_kind == "SKILL_TAG":
        eligible = str(scope_value) in model["tags"]
        return eligible, f"{scope_value} 태그 필요"
    if scope_kind == "SKILL_NAMES":
        names = list(scope_value or [])
        eligible = canonical_skill(skill_name) in names
        return eligible, "대상 스킬: " + ", ".join(names)
    if scope_kind == "SINGLE_CAST_EXCLUDED":
        return False, "1회 피해 계산에 직접 반영하지 않는 재사용 대기시간 효과"
    return False, f"지원하지 않는 범위: {scope_kind}"


def parse_arkgrid_core_option_components(
    text: str,
    skill_name: str,
    core_name: str = "",
    core_grade: str = "",
) -> tuple[list[dict[str, Any]], list[str]]:
    """Classify one core option and retain its additive/multiplicative intent."""
    text = resolve_arkgrid_grade_values(text, core_grade)
    components: list[dict[str, Any]] = []
    notes: list[str] = []
    condition = ""
    if "기류 보호막" in text:
        condition = "기류 보호막 보유(최대 유리 조건)"
    elif "여우비 상태" in text:
        condition = "여우비 상태(최대 유리 조건)"
    elif "'운명" in text or "운명:" in text:
        condition = "운명 효과 활성(최대 유리 조건)"

    def add_percent(
        category: str,
        pattern: str,
        *,
        scope_kind: str = "ALL",
        scope_value: str | list[str] = "",
        source_text: str | None = None,
        multiplicative: bool = False,
    ) -> None:
        target = text if source_text is None else source_text
        for match in re.finditer(pattern, target):
            tail = target[match.end() : match.end() + 24]
            operator = "ADD"
            if multiplicative:
                operator = (
                    "ADD_TO_PREVIOUS"
                    if re.match(r"\s*추가로\s*증가", tail)
                    else "MULTIPLY"
                )
            components.append(
                arkgrid_component(
                    category,
                    pct(match.group(1)),
                    scope_kind=scope_kind,
                    scope_value=scope_value,
                    condition=condition,
                    operator=operator,
                )
            )

    # Skill-scoped damage. The API core tooltip has already resolved ancient
    # versus relic values, so this parser never guesses between A/B values.
    add_percent(
        "skillDamagePercent",
        rf"우산\s*스킬의\s*피해량이\s*{PERCENT}",
        scope_kind="SKILL_TAG",
        scope_value="UMBRELLA_SKILL",
        multiplicative=True,
    )
    add_percent(
        "skillDamagePercent",
        rf"기상\s*스킬의\s*피해량이\s*{PERCENT}",
        scope_kind="SKILL_TAG",
        scope_value="WEATHER_SKILL",
        multiplicative=True,
    )
    for damage_match in re.finditer(
        rf"([^.\n]+?)의\s*피해량이\s*{PERCENT}", text
    ):
        prefix = damage_match.group(1)
        value = pct(damage_match.group(2))
        tail = text[damage_match.end() : damage_match.end() + 24]
        operator = (
            "ADD_TO_PREVIOUS"
            if re.match(r"\s*추가로\s*증가", tail)
            else "MULTIPLY"
        )
        if "우산 스킬" in prefix or "기상 스킬" in prefix:
            continue
        names = [name for name in ARKGRID_SKILL_NAMES if name in prefix]
        # "여우비 기본 공격" is more specific than "여우비".
        if "여우비 기본 공격" in names and "여우비" in names:
            names.remove("여우비")
        if names:
            components.append(
                arkgrid_component(
                    "skillDamagePercent",
                    value,
                    scope_kind="SKILL_NAMES",
                    scope_value=names,
                    condition=condition,
                    operator=operator,
                )
            )

    replacement_targets = {
        "바람의 칼날": ["칼바람"],
        "해와 바람": ["싹쓸바람"],
    }
    replacement_match = re.search(
        rf"피해\s*증가량을\s*{PERCENT}\s*(?:로)?\s*변경", text
    )
    if replacement_match:
        names = next(
            (
                targets
                for core_key, targets in replacement_targets.items()
                if core_key in core_name
            ),
            [],
        )
        if names:
            components.append(
                arkgrid_component(
                    "skillDamagePercent",
                    pct(replacement_match.group(1)),
                    scope_kind="SKILL_NAMES",
                    scope_value=names,
                    condition=condition,
                    operator="REPLACE",
                )
            )
        else:
            notes.append("피해 증가량 변경 대상 스킬을 코어 이름에서 결정하지 못함")

    # Mutually exclusive "damage to enemy" families are removed from a
    # scratch copy before the general-damage expression is parsed.
    general_text = text
    critical_pattern = (
        rf"치명타(?:로)?(?:\s*적중)?\s*시\s*적에게\s*주는\s*피해"
        rf"(?:가|량이)?\s*{PERCENT}"
    )
    add_percent(
        "criticalHitDamagePercent",
        critical_pattern,
        multiplicative=True,
    )
    general_text = re.sub(critical_pattern, "", general_text)
    boss_pattern = (
        rf"보스(?:\s*등급)?\s*이상\s*적에게\s*주는\s*피해"
        rf"(?:가|량이)?\s*{PERCENT}"
    )
    add_percent("bossDamagePercent", boss_pattern, multiplicative=True)
    general_text = re.sub(boss_pattern, "", general_text)
    add_percent(
        "generalDamagePercent",
        rf"적에게\s*주는\s*피해(?:가|량이)?\s*{PERCENT}",
        source_text=general_text,
        multiplicative=True,
    )
    add_percent(
        "additionalDamagePercent",
        rf"추가\s*피해(?:가|량이)?\s*{PERCENT}",
    )
    add_percent(
        "criticalRate",
        rf"치명타\s*적중률(?:이)?\s*{PERCENT}",
    )
    add_percent(
        "criticalDamage",
        rf"(?<!입는\s)치명타\s*피해(?:가|량이)?\s*{PERCENT}",
    )
    add_percent(
        "criticalHitDamagePercent",
        rf"입는\s*치명타\s*피해량을\s*{PERCENT}",
        multiplicative=True,
    )
    add_percent("attackSpeed", rf"공격\s*속도(?:가|는)?\s*{PERCENT}")
    add_percent("moveSpeed", rf"이동\s*속도(?:가|는)?\s*{PERCENT}")
    for value in find_numbers(
        text, rf"공격\s*및\s*이동\s*속도(?:가|는)?\s*{PERCENT}"
    ):
        components.append(arkgrid_component("attackSpeed", pct(value)))
        components.append(arkgrid_component("moveSpeed", pct(value)))
    add_percent(
        "enemyDefenseReductionPercent",
        rf"모든\s*방어력을\s*{PERCENT}\s*감소",
        multiplicative=True,
    )

    # Attack and weapon-attack effects can contain a percent and a flat value
    # in the same threshold option.
    add_percent(
        "weaponAttackPercent",
        rf"무기\s*공격력이\s*{PERCENT}",
    )
    weapon_flat_text = re.sub(PERCENT, "", text)
    for value in find_numbers(
        weapon_flat_text,
        rf"무기\s*공격력이\s*{NUMBER}\s*(?:추가로\s*)?증가",
    ):
        components.append(arkgrid_component("weaponAttackFlat", value))
    if "무기 공격력" in text:
        for value in find_numbers(
            weapon_flat_text, rf"추가로\s*{NUMBER}\s*증가"
        ):
            components.append(arkgrid_component("weaponAttackFlat", value))
    attack_text = re.sub(r"무기\s*공격력", "", text)
    add_percent(
        "attackPowerPercent",
        rf"(?<!아군\s)공격력이\s*{PERCENT}",
        source_text=attack_text,
    )
    attack_flat_text = re.sub(PERCENT, "", attack_text)
    for value in find_numbers(
        attack_flat_text,
        rf"(?<!아군\s)공격력이\s*{NUMBER}\s*(?:추가로\s*)?증가",
    ):
        components.append(arkgrid_component("attackPowerFlat", value))
    if "무기 공격력" not in text and "공격력" in text:
        for value in find_numbers(
            attack_flat_text, rf"추가로\s*{NUMBER}\s*증가"
        ):
            components.append(arkgrid_component("attackPowerFlat", value))

    # Cooldown is retained structurally for rotation/DPS consumers, but a
    # single-cast damage estimate does not apply it.
    for value in find_numbers(
        text,
        rf"재사용\s*대기시간이\s*{PERCENT}\s*(?:추가로\s*)?감소",
    ):
        components.append(
            arkgrid_component(
                "cooldownReductionPercent",
                pct(value),
                scope_kind="SINGLE_CAST_EXCLUDED",
                condition=condition,
            )
        )
    for value in find_numbers(
        text,
        rf"재사용\s*대기시간이\s*([0-9]+(?:\.[0-9]+)?)\s*초\s*감소",
    ):
        components.append(
            arkgrid_component(
                "cooldownReductionSeconds",
                value,
                scope_kind="SINGLE_CAST_EXCLUDED",
                condition=condition,
            )
        )
    for value in find_numbers(
        text,
        rf"재사용\s*대기시간이\s*([0-9]+(?:\.[0-9]+)?)\s*초\s*증가",
    ):
        components.append(
            arkgrid_component(
                "cooldownReductionSeconds",
                -value,
                scope_kind="SINGLE_CAST_EXCLUDED",
                condition=condition,
            )
        )

    for component in components:
        eligible, reason = arkgrid_core_component_scope(component, skill_name)
        component["eligible"] = eligible
        component["applied"] = eligible and component["category"] in (
            set(ARKGRID_CORE_TOTAL_KEYS) | {"skillDamagePercent"}
        )
        component["scopeReason"] = reason
    if not components:
        if any(
            term in text
            for term in (
                "피해",
                "공격",
                "치명타",
                "재사용 대기시간",
                "방어력",
            )
        ):
            notes.append("수치화 가능한 개인 단일 피해 효과 없음 또는 미지원 효과")
        else:
            notes.append("개인 단일 피해와 무관한 유틸리티·방어·지원 효과")
    return components, notes


def parse_ark_grid(
    body: dict[str, Any] | None,
    warnings: list[str],
    target_skill: str = CANONICAL_SKILL,
) -> dict[str, Any]:
    body = body or {}
    target_skill = canonical_skill(target_skill)
    gem_totals = {
        "attackPowerPercent": Decimal("0"),
        "additionalDamagePercent": Decimal("0"),
        "bossDamagePercent": Decimal("0"),
    }
    point_totals = {
        "attackPowerPercent": Decimal("0"),
        "additionalDamagePercent": Decimal("0"),
        "bossDamagePercent": Decimal("0"),
    }
    core_totals = {
        key: Decimal("0") for key in ARKGRID_CORE_TOTAL_KEYS
    }
    core_totals["skillDamagePercent"] = Decimal("0")
    active: list[dict[str, Any]] = []
    active_point_effects: list[dict[str, Any]] = []
    aggregate_effect_categories: set[str] = set()
    cores: list[dict[str, Any]] = []
    core_damage_factors: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for slot_index, slot in enumerate(body.get("Slots") or []):
        core_path = f"arkGrid.Slots[{slot_index}]"
        core_name = str(slot.get("Name") or "이름 없는 아크그리드 코어")
        core_point = int(slot.get("Point") or 0)
        core_grade = str(slot.get("Grade") or "")
        core_text = tooltip_to_text(slot.get("Tooltip"))
        core_options: list[dict[str, Any]] = []
        for option_index, option in enumerate(
            extract_arkgrid_core_options(core_text)
        ):
            required = option["requiredPoints"]
            option_text = option["text"]
            activated = core_point >= required
            option_path = f"{core_path}.Tooltip.options[{option_index}]"
            option_result = {
                "path": option_path,
                "requiredPoints": required,
                "currentPoints": core_point,
                "activated": activated,
                "text": option_text,
                "resolvedText": resolve_arkgrid_grade_values(
                    option_text, core_grade
                ),
                "components": [],
                "notes": [],
            }
            if activated:
                components, notes = parse_arkgrid_core_option_components(
                    option_text, target_skill, core_name, core_grade
                )
                option_result["components"] = components
                option_result["notes"] = notes
                for component in components:
                    category = component["category"]
                    value = component["value"]
                    if component["applied"]:
                        operator = component.get("operator", "ADD")
                        matching_factors = [
                            factor
                            for factor in core_damage_factors
                            if factor["corePath"] == core_path
                            and factor["category"] == category
                            and factor["scopeKind"] == component["scopeKind"]
                            and factor.get("scopeValue")
                            == component.get("scopeValue")
                        ]
                        if category in ARKGRID_MULTIPLICATIVE_CATEGORIES:
                            if operator == "ADD_TO_PREVIOUS" and matching_factors:
                                factor = matching_factors[-1]
                                factor["value"] += value
                                factor["contributions"].append(
                                    {
                                        "path": option_path,
                                        "requiredPoints": required,
                                        "value": value,
                                        "operator": operator,
                                    }
                                )
                            elif operator == "REPLACE" and matching_factors:
                                same_condition = [
                                    factor
                                    for factor in matching_factors
                                    if factor.get("condition") == component["condition"]
                                ]
                                factor = (same_condition or matching_factors)[-1]
                                core_totals[category] -= factor["value"]
                                factor["value"] = value
                                factor["contributions"].append(
                                    {
                                        "path": option_path,
                                        "requiredPoints": required,
                                        "value": value,
                                        "operator": operator,
                                    }
                                )
                            else:
                                factor = {
                                    "factorId": (
                                        f"{core_path}:{category}:"
                                        f"{len(core_damage_factors) + 1}"
                                    ),
                                    "corePath": core_path,
                                    "coreName": core_name,
                                    "coreGrade": core_grade,
                                    "category": category,
                                    "value": value,
                                    "scopeKind": component["scopeKind"],
                                    "scopeValue": component.get("scopeValue"),
                                    "condition": component["condition"],
                                    "contributions": [
                                        {
                                            "path": option_path,
                                            "requiredPoints": required,
                                            "value": value,
                                            "operator": operator,
                                        }
                                    ],
                                }
                                core_damage_factors.append(factor)
                            component["factorId"] = factor["factorId"]
                            component["factorValue"] = factor["value"]
                        core_totals[category] += value
                    sources.append(
                        source(
                            source_type="OFFICIAL_TOOLTIP+DERIVED",
                            path=option_path,
                            label=(
                                f"아크그리드 코어 {core_name} "
                                f"{required}P {category}"
                            ),
                            value=value,
                            raw=option_text,
                            eligible=component["eligible"],
                            applied=component["applied"],
                            excluded_reason=(
                                ""
                                if component["applied"]
                                else component["scopeReason"]
                            ),
                            note=(
                                f"현재 {core_point}P/{core_grade}; "
                                f"연산자={component['operator']}; "
                                f"{component['scopeReason']}"
                                + (
                                    f"; {component['condition']}"
                                    if component["condition"]
                                    else ""
                                )
                            ),
                        )
                    )
                if not components:
                    excluded.append(
                        source(
                            source_type="OFFICIAL_TOOLTIP",
                            path=option_path,
                            label=f"아크그리드 코어 {core_name} {required}P",
                            value=0,
                            raw=option_text,
                            parsed=False,
                            eligible=False,
                            applied=False,
                            excluded_reason="; ".join(notes),
                        )
                    )
            core_options.append(option_result)
        if core_text and not core_options:
            warn_once(
                warnings,
                f"{core_path} '{core_name}' 툴팁에서 [nP] 코어 옵션을 찾지 못했습니다.",
            )
        cores.append(
            {
                "path": core_path,
                "slotIndex": slot.get("Index"),
                "name": core_name,
                "grade": core_grade,
                "point": core_point,
                "tooltipText": core_text,
                "options": core_options,
            }
        )
        for gem_index, gem in enumerate(slot.get("Gems") or []):
            path = f"arkGrid.Slots[{slot_index}].Gems[{gem_index}]"
            text = tooltip_to_text(gem.get("Tooltip"))
            is_active = gem.get("IsActive") is True
            base = {
                "path": path,
                "slotIndex": slot.get("Index"),
                "gemIndex": gem.get("Index"),
                "grade": gem.get("Grade"),
                "isActive": is_active,
                "tooltipText": text,
            }
            if not is_active:
                excluded.append(
                    source(
                        source_type="API_FIELD",
                        path=path,
                        label="비활성 아크그리드 젬",
                        value=0,
                        raw=text,
                        applied=False,
                        note="IsActive=false",
                    )
                )
                continue
            support_hits = [term for term in SUPPORT_ARKGRID_TERMS if term in text]
            for term in support_hits:
                excluded.append(
                    source(
                        source_type="API_TOOLTIP",
                        path=f"{path}.Tooltip",
                        label=term,
                        value=0,
                        raw=text,
                        applied=False,
                        note="서포터 옵션은 딜러 개인 피해에서 제외",
                    )
                )
            scrubbed = text
            for term in SUPPORT_ARKGRID_TERMS:
                scrubbed = "\n".join(line for line in scrubbed.splitlines() if term not in line)
            base["values"] = parse_arkgrid_damage_values(scrubbed)
            for key, value in base["values"].items():
                gem_totals[key] += value
            active.append(base)
            for label, value in base["values"].items():
                if value:
                    sources.append(
                        source(
                            source_type="API_TOOLTIP",
                            path=f"{path}.Tooltip",
                            label=f"아크그리드 젬 {label}",
                            value=value,
                            raw=text,
                        )
                    )
            if not any(base["values"].values()) and not support_hits:
                warnings.append(f"{path} 활성 젬의 딜러 추가 효과를 파싱하지 못했습니다.")

    for index, effect in enumerate(body.get("Effects") or []):
        path = f"arkGrid.Effects[{index}]"
        name = str(effect.get("Name") or "아크그리드 누적 효과")
        text = tooltip_to_text(effect.get("Tooltip"))
        support_hits = [
            term
            for term in SUPPORT_ARKGRID_TERMS
            if term in name or term in text
        ]
        if support_hits:
            excluded.append(
                source(
                    source_type="API_TOOLTIP",
                    path=path,
                    label=name,
                    value=0,
                    raw=text,
                    eligible=False,
                    applied=False,
                    excluded_reason="서포터 파티 강화 옵션은 딜러 개인 피해에서 제외",
                )
            )
            continue
        values = parse_arkgrid_damage_values(text)
        if not any(values.values()):
            excluded.append(
                source(
                    source_type="API_FIELD",
                    path=path,
                    label=name,
                    value=effect.get("Level") or 0,
                    raw=text,
                    parsed=False,
                    eligible=False,
                    applied=False,
                    excluded_reason="지원하지 않는 아크그리드 누적 효과(Effects[])",
                )
            )
            warn_once(warnings, f"{path} '{name}' 효과의 수치를 분류하지 못했습니다.")
            continue
        for key, value in values.items():
            point_totals[key] += value
            if value:
                aggregate_effect_categories.add(key)
                sources.append(
                    source(
                        source_type="OFFICIAL_TOOLTIP",
                        path=f"{path}.Tooltip",
                        label=f"아크그리드 누적 효과(Effects[]) {name} {key}",
                        value=value,
                        raw=text,
                    )
                )
        active_point_effects.append(
            {
                "path": path,
                "name": name,
                "level": effect.get("Level"),
                "tooltipText": text,
                "values": values,
            }
        )
    effective_base_effects = {
        key: (
            point_totals[key]
            if key in aggregate_effect_categories
            else gem_totals[key]
        )
        for key in gem_totals
    }
    for item in sources:
        if (
            str(item.get("path") or "").startswith("arkGrid.Slots[")
            and str(item.get("label") or "").startswith("아크그리드 젬 ")
        ):
            category = str(item["label"]).removeprefix("아크그리드 젬 ")
            if category in aggregate_effect_categories:
                item["applied"] = False
                item["excludedReason"] = (
                    "동일 젬 효과 레벨의 ArkGrid.Effects[] 통합값 사용"
                )
                item["note"] = "개별 젬 값은 검산·출처용이며 중복 합산하지 않음"
    combined = {
        key: effective_base_effects[key] + core_totals[key]
        for key in gem_totals
    }
    for key in ARKGRID_CORE_TOTAL_KEYS:
        if key not in combined:
            combined[key] = core_totals[key]
    combined["skillDamagePercent"] = core_totals["skillDamagePercent"]
    return {
        **combined,
        "gemEffects": gem_totals,
        "pointEffects": point_totals,
        "aggregateEffects": point_totals,
        "effectiveBaseEffects": effective_base_effects,
        "coreEffects": core_totals,
        "coreDamageFactors": core_damage_factors,
        "cores": cores,
        "activeGems": active,
        "activePointEffects": active_point_effects,
        "sources": sources,
        "excluded": excluded,
    }


def effect_present(name: str, parsed: dict[str, Any]) -> bool:
    if name in parsed["engravings"]["entries"]:
        return True
    if name in parsed["arkPassive"]["effects"]:
        return True
    return any(
        name in str(effect.get("rawName") or "") or name in str(effect.get("description") or "")
        for effect in parsed["arkPassive"]["effects"].values()
    )


def example_value(
    name: str,
    key: str,
    parsed: dict[str, Any],
    assumptions: list[dict[str, Any]],
) -> Decimal:
    if not effect_present(name, parsed):
        return Decimal("0")
    value = EXAMPLE_EFFECT_DB.get(name, {}).get(key, Decimal("0"))
    assumptions.append(
        source(
            source_type="API_FIELD+EXAMPLE_DB",
            path=f"effects.{name}",
            label=f"{name} {key}",
            value=value,
            raw="현재 API에서 효과 존재 확인",
            note="예시 DB 고정값; 최대 조건 적용",
        )
    )
    return value


def resolved_engraving_value(
    name: str,
    key: str,
    parsed: dict[str, Any],
    assumptions: list[dict[str, Any]],
    rules: dict[str, Any],
) -> Decimal:
    if name not in parsed["engravings"]["entries"]:
        return Decimal("0")
    if rules["useLiveEngravingDescriptions"]:
        live = dec(
            parsed["engravings"]["parsedEffects"].get(name, {}).get(
                key, Decimal("0")
            )
        )
        if live:
            assumptions.append(
                source(
                    source_type="API_TOOLTIP",
                    path=f"engravings.entries.{name}.Description",
                    label=f"{name} {key}",
                    value=live,
                    raw=parsed["engravings"]["entries"][name].get(
                        "description", ""
                    ),
                    note="현재 API 설명에서 파싱",
                )
            )
            return live
    fallback = EXAMPLE_EFFECT_DB.get(name, {}).get(key, Decimal("0"))
    if fallback:
        assumptions.append(
            source(
                source_type="API_FIELD+EXAMPLE_DB",
                path=f"effects.{name}",
                label=f"{name} {key}",
                value=fallback,
                raw="현재 API에서 효과 존재 확인",
                note="현재 수치 파싱 실패 또는 레거시 버전이므로 예시 DB 사용",
            )
        )
    return fallback


def sonic_breakthrough_breakdown(
    level: int,
    raw_attack_speed: Decimal,
    raw_move_speed: Decimal,
    rule_version: str = DEFAULT_RULE_VERSION,
) -> dict[str, Any]:
    rules = get_rules(rule_version)
    attack_increase = raw_attack_speed - Decimal("1")
    move_increase = raw_move_speed - Decimal("1")
    cap_increase = Decimal("0.4")
    sonic_rule = rules["sonic"][1 if level <= 1 else 2]
    base_rate = sonic_rule["baseRate"]
    both_bonus = sonic_rule["bothBonus"]
    over_rate = sonic_rule["overRate"]
    maximum = sonic_rule["maximum"]
    base_attack_input = min(attack_increase, cap_increase)
    base_move_input = min(move_increase, cap_increase)
    base = base_rate * (base_attack_input + base_move_input)
    both_exceeded = (
        attack_increase > cap_increase and move_increase > cap_increase
    )
    both = (
        both_bonus
        if both_exceeded
        else Decimal("0")
    )
    attack_over = max(attack_increase - cap_increase, Decimal("0"))
    move_over = max(move_increase - cap_increase, Decimal("0"))
    over = over_rate * (attack_over + move_over)
    uncapped = base + both + over
    final = min(maximum, uncapped)
    return {
        "ruleVersion": rule_version,
        "level": level,
        "attackSpeedIncrease": attack_increase,
        "moveSpeedIncrease": move_increase,
        "baseRate": base_rate,
        "baseAttackInput": base_attack_input,
        "baseMoveInput": base_move_input,
        "baseDamage": base,
        "bothSpeedsExceededCap": both_exceeded,
        "bothExceededBonus": both,
        "overCapRate": over_rate,
        "attackOverCap": attack_over,
        "moveOverCap": move_over,
        "overCapDamage": over,
        "uncappedTotal": uncapped,
        "maximum": maximum,
        "final": final,
        "limitedByMaximum": uncapped > maximum,
    }


def sonic_breakthrough(
    level: int,
    raw_attack_speed: Decimal,
    raw_move_speed: Decimal,
    rule_version: str = DEFAULT_RULE_VERSION,
) -> Decimal:
    return sonic_breakthrough_breakdown(
        level, raw_attack_speed, raw_move_speed, rule_version
    )["final"]


def calculate(
    parsed: dict[str, Any],
    include_arkgrid: bool = True,
    rule_version: str = DEFAULT_RULE_VERSION,
    skill_name: str = CANONICAL_SKILL,
) -> dict[str, Any]:
    rules = get_rules(rule_version)
    skill_name = canonical_skill(skill_name)
    skill_model = get_skill_model(skill_name)
    effective_hits = effective_skill_hits(skill_name, rules)
    warnings = parsed["warnings"]
    assumptions: list[dict[str, Any]] = []
    equipment = parsed["equipment"]
    profile = parsed["profile"]
    engravings = parsed["engravings"]
    ark = parsed["arkPassive"]
    grid = parsed["arkGrid"]

    assumptions.append(
        source(
            source_type=skill_model["source"],
            path=f"skillModels.{skill_name}.hits",
            label=f"{skill_name} 타격 계수·상수",
            value=len(skill_model["hits"]),
            raw="; ".join(
                f"{hit['name']}={hit['coefficient']}×공격력+{hit['constant']}"
                for hit in effective_hits
            ),
            note=(
                (
                    "원본 모션계수에 2026-02-11 피해 상향분 ×1.292를 "
                    "적용하고 모션상수는 변경하지 않음"
                    if skill_name == SPACE_CUTTING_SKILL
                    and effective_hits[0]["coefficientMultiplier"] != 1
                    else
                    "1·2타는 기본 타격, 3타는 공간베기 94.8% 추가 공격의 "
                    "별도 모션식으로 사용"
                    if skill_name == DOWNPOUR_SKILL
                    else "사용자가 제공한 트라이포드 미반영 기본 타격 수치를 사용"
                )
                if skill_model["source"] == "USER_VERIFIED"
                else (
                    "기존 계산기 스킬 모델"
                )
            ),
        )
    )
    selected_skill_tripod_items = [
        item
        for item in parsed["combatSkills"]["selectedTripods"]
        if item["skill"] == skill_name
    ]
    selected_skill_tripods = {
        item["name"]
        for item in selected_skill_tripod_items
    }
    required_tripods = set(skill_model.get("requiredTripods", []))
    missing_tripods = sorted(required_tripods - selected_skill_tripods)
    if required_tripods:
        assumptions.append(
            source(
                source_type="OFFICIAL_API",
                path=f"combatSkills[{skill_name}].Tripods[IsSelected=true]",
                label=f"{skill_name} 선택 트라이포드 확인",
                value=", ".join(sorted(selected_skill_tripods)),
                raw="필수 트라이포드: " + ", ".join(sorted(required_tripods)),
                parsed=not missing_tripods,
                eligible=not missing_tripods,
                applied=not missing_tripods,
                excluded_reason=(
                    "누락: " + ", ".join(missing_tripods)
                    if missing_tripods
                    else ""
                ),
                note=(
                    "선택 조합 확인용이며 모션계수·모션상수에는 포함되지 않음"
                ),
            )
        )
    critical_tripod = skill_model.get("criticalDamageTripod")
    separate_damage_tripod = skill_model.get("separateDamageTripod")
    tripod_critical_damage = Decimal("0")
    tripod_damage_percent = Decimal("0")
    tripod_damage_effects: list[dict[str, Any]] = []
    embedded_tripod_damage_effects: list[dict[str, Any]] = []
    embedded_tripod_names = {
        str(hit.get("tripodSource"))
        for hit in skill_model["hits"]
        if hit.get("tripodSource")
    }
    if rules.get("applyAllSelectedTripodDamage", False):
        tripod_damage_percent = sum(
            (dec(item.get("damagePercent")) for item in selected_skill_tripod_items),
            Decimal("0"),
        )
        for tripod_item in selected_skill_tripod_items:
            item_effects = tripod_item.get("damageEffects", [])
            item_critical_damage = dec(
                tripod_item.get("criticalDamagePercent")
            )
            for effect_index, effect in enumerate(item_effects):
                normalized_effect = {
                    **effect,
                    "tripodName": tripod_item["name"],
                    "tooltipText": tripod_item["tooltipText"],
                }
                is_embedded_hit = (
                    rules.get("deduplicateEmbeddedTripodHits", False)
                    and effect["type"] == "ADDITIONAL_ATTACK"
                    and tripod_item["name"] in embedded_tripod_names
                )
                normalized_effect["applicationMode"] = (
                    "EMBEDDED_MOTION_HIT"
                    if is_embedded_hit
                    else "MULTIPLIER"
                )
                if is_embedded_hit:
                    embedded_tripod_damage_effects.append(normalized_effect)
                else:
                    tripod_damage_effects.append(normalized_effect)
                assumptions.append(
                    source(
                        source_type="OFFICIAL_TOOLTIP",
                        path=(
                            f"combatSkills[{skill_name}].Tripods"
                            f"[{tripod_item['name']}].damageEffects[{effect_index}]"
                        ),
                        label=(
                            f"{skill_name} {tripod_item['name']} "
                            f"{effect['label']}"
                        ),
                        value=effect["percent"],
                        raw=tripod_item["tooltipText"],
                        note=(
                            "제공된 별도 타격 모션식에 이미 반영되어 추가 곱연산하지 않음"
                            if is_embedded_hit
                            else (
                                "트라이포드 미반영 기본 모션식에 독립 곱연산"
                                + (
                                    "; 별도 타격 모션식이 없어 툴팁의 총 추가 피해율로 적용"
                                    if effect["type"] == "ADDITIONAL_ATTACK"
                                    else ""
                                )
                            )
                        ),
                    )
                )
            if item_critical_damage:
                tripod_critical_damage += item_critical_damage
                assumptions.append(
                    source(
                        source_type="OFFICIAL_TOOLTIP",
                        path=(
                            f"combatSkills[{skill_name}].Tripods"
                            f"[{tripod_item['name']}].criticalDamagePercent"
                        ),
                        label=f"{skill_name} {tripod_item['name']} 치명타 피해",
                        value=item_critical_damage,
                        raw=tripod_item["tooltipText"],
                        note="스킬 전용 치명타 피해는 공용 치명타 피해에 합산",
                    )
                )
            if not item_effects and not item_critical_damage:
                assumptions.append(
                    source(
                        source_type="OFFICIAL_TOOLTIP",
                        path=(
                            f"combatSkills[{skill_name}].Tripods"
                            f"[{tripod_item['name']}]"
                        ),
                        label=f"{skill_name} {tripod_item['name']}",
                        value=Decimal("0"),
                        raw=tripod_item["tooltipText"],
                        parsed=True,
                        eligible=False,
                        applied=False,
                        excluded_reason="1회 피해량을 바꾸는 수치 효과 없음",
                        note="공격속도·조작 방식 등 비피해 효과는 1회 피해 계산에서 제외",
                    )
                )
    elif critical_tripod:
        critical_tripod_active = (
            critical_tripod["name"] in selected_skill_tripods
        )
        if critical_tripod_active:
            tripod_critical_damage = critical_tripod["value"]
        assumptions.append(
            source(
                source_type="OFFICIAL_TOOLTIP",
                path=f"combatSkills[{skill_name}].Tripods[{critical_tripod['name']}]",
                label=f"{skill_name} {critical_tripod['name']} 치명타 피해",
                value=critical_tripod["value"],
                raw=f"치명타 피해 {critical_tripod['value'] * 100}% 증가",
                eligible=critical_tripod_active,
                applied=critical_tripod_active,
                excluded_reason=(
                    ""
                    if critical_tripod_active
                    else "해당 트라이포드가 선택되지 않음"
                ),
                note="스킬 전용 치명타 피해는 공용 치명타 피해에 합산",
            )
        )
    if (
        not rules.get("applyAllSelectedTripodDamage", False)
        and separate_damage_tripod
        and rules.get("includeSeparateTripodDamage", False)
    ):
        tripod_name = separate_damage_tripod["name"]
        tripod_item = next(
            (
                item
                for item in parsed["combatSkills"]["selectedTripods"]
                if item["skill"] == skill_name and item["name"] == tripod_name
            ),
            None,
        )
        if tripod_item:
            tripod_damage_percent = dec(tripod_item.get("damagePercent"))
            if not tripod_damage_percent:
                warn_once(
                    warnings,
                    f"{skill_name} {tripod_name} 피해 증가율을 선택 트라이포드 "
                    "툴팁에서 파싱하지 못해 적용하지 않았습니다.",
                )
        assumptions.append(
            source(
                source_type="OFFICIAL_TOOLTIP",
                path=f"combatSkills[{skill_name}].Tripods[{tripod_name}]",
                label=f"{skill_name} {tripod_name} 피해",
                value=tripod_damage_percent,
                raw=(tripod_item or {}).get("tooltipText", ""),
                parsed=bool(tripod_damage_percent),
                eligible=bool(tripod_item),
                applied=bool(tripod_damage_percent),
                excluded_reason=(
                    ""
                    if tripod_damage_percent
                    else (
                        "피해 증가율 파싱 실패"
                        if tripod_item
                        else "해당 트라이포드가 선택되지 않음"
                    )
                ),
                note=(
                    f"모션계수·모션상수에 포함되지 않은 독립 곱연산; "
                    f"{separate_damage_tripod['condition']} 조건을 최대 유리 "
                    "시나리오에서 충족"
                ),
            )
        )
        if tripod_damage_percent:
            tripod_damage_effects.append(
                {
                    "type": "DAMAGE_INCREASE",
                    "label": "피해 증가",
                    "percent": tripod_damage_percent,
                    "multiplier": Decimal("1") + tripod_damage_percent,
                    "tripodName": tripod_name,
                    "tooltipText": (tripod_item or {}).get("tooltipText", ""),
                }
            )
    if skill_model["tagVerification"] != "VERIFIED":
        assumptions.append(
            source(
                source_type="PROVISIONAL",
                path=f"skillModels.{skill_name}.tags",
                label=f"{skill_name} 스킬 태그",
                value=", ".join(sorted(skill_model["tags"])),
                raw="공식 API에 방향성·각성기·우산 스킬 분류 필드가 없음",
                note=(
                    "타격의 대가 및 범위형 아크 패시브의 적용 여부를 판정하기 위한 "
                    "잠정 분류이며 보고서에 명시"
                ),
            )
        )

    for fixed_name, label in (
        ("levelMainStat", "레벨 주스탯"),
        ("expeditionMainStat", "원정대 주스탯"),
        ("collectionMainStat", "카드·내실 주스탯"),
    ):
        assumptions.append(
            source(
                source_type="EXAMPLE_DB",
                path=f"fixed.{fixed_name}",
                label=label,
                value=rules[fixed_name],
                note=f"{rule_version} 규칙의 고정값",
            )
        )
    if profile.get("characterLevel") != 70:
        warn_once(
            warnings,
            f"현재 캐릭터 레벨은 {profile.get('characterLevel')}이지만 레벨 주스탯은 "
            f"{rule_version} 고정값 +{rules['levelMainStat']}을 사용했습니다."
        )
    if profile.get("expeditionLevel") != 272:
        warn_once(
            warnings,
            f"현재 원정대 레벨은 {profile.get('expeditionLevel')}이지만 원정대/물약 주스탯은 "
            f"{rule_version} 고정값 +{rules['expeditionMainStat']}을 사용했습니다."
        )

    base_main_stat = (
        equipment["mainStat"]
        + rules["levelMainStat"]
        + rules["expeditionMainStat"]
        + rules["collectionMainStat"]
    )
    pet_main_stat_percent = (
        FIXED["petMainStatPercent"]
        if rules["includePetMainStat"]
        else Decimal("0")
    )
    avatar_pet_percent = (
        parsed["avatars"]["mainStatPercent"] + pet_main_stat_percent
    )
    final_main_stat_raw = base_main_stat * (
        Decimal("1") + avatar_pet_percent
    )
    final_main_stat = apply_stage_rounding(
        final_main_stat_raw, "mainStat", rules
    )

    weapon_attack_flat = (
        equipment["weaponAttackFlat"]
        if rules["includeFlatWeaponAttack"]
        else Decimal("0")
    )
    if include_arkgrid:
        weapon_attack_flat += grid["weaponAttackFlat"]
    weapon_attack_subtotal = equipment["baseWeaponAttack"] + weapon_attack_flat
    weapon_attack_percent = (
        equipment["weaponAttackPercent"] + ark["karmaWeaponAttackPercent"]
    )
    if include_arkgrid:
        weapon_attack_percent += grid["weaponAttackPercent"]
    final_weapon_attack_raw = weapon_attack_subtotal * (
        Decimal("1") + weapon_attack_percent
    )
    final_weapon_attack = apply_stage_rounding(
        final_weapon_attack_raw, "weaponAttack", rules
    )

    armlet_base_attack_flat = (
        equipment["baseAttackPowerFlat"]
        if rules.get("includeArmletBaseAttack", False)
        else Decimal("0")
    )
    armlet_base_attack_percent = (
        equipment["baseAttackPowerPercent"]
        if rules.get("includeArmletBaseAttack", False)
        else Decimal("0")
    )
    base_attack_percent = (
        parsed["gems"]["baseAttackPercent"]
        + engravings["stoneBaseAttackPercent"]
        + armlet_base_attack_percent
    )
    if final_main_stat < 0 or final_weapon_attack < 0:
        raise CalculationError("주스탯 또는 무기 공격력이 음수입니다.")
    root_attack = (final_main_stat * final_weapon_attack / Decimal("6")).sqrt()
    base_attack_subtotal = root_attack + armlet_base_attack_flat
    root_with_base_attack_percent = base_attack_subtotal * (
        Decimal("1") + base_attack_percent
    )
    attack_power_flat = (
        equipment["attackPowerFlat"]
        if rules["includeFlatAttackPower"]
        else Decimal("0")
    )
    if include_arkgrid:
        attack_power_flat += grid["attackPowerFlat"]
    base_attack = root_with_base_attack_percent + attack_power_flat

    adrenaline_attack = resolved_engraving_value(
        "아드레날린",
        "attackPowerPercent",
        parsed,
        assumptions,
        rules,
    )
    arkgrid_attack = grid["attackPowerPercent"] if include_arkgrid else Decimal("0")
    arkgrid_gem_attack = (
        grid["gemEffects"]["attackPowerPercent"]
        if include_arkgrid
        else Decimal("0")
    )
    arkgrid_point_attack = (
        grid["pointEffects"]["attackPowerPercent"]
        if include_arkgrid
        else Decimal("0")
    )
    arkgrid_core_attack = (
        grid["coreEffects"]["attackPowerPercent"]
        if include_arkgrid
        else Decimal("0")
    )
    attack_power_percent = (
        equipment["attackPowerPercent"] + adrenaline_attack + arkgrid_attack
    )
    final_attack_raw = base_attack * (
        Decimal("1") + attack_power_percent
    )
    final_attack = apply_stage_rounding(
        final_attack_raw, "attackPower", rules
    )
    profile_attack = profile["profileAttackPower"]
    attack_values_match = profile_attack == final_attack
    calculated_attack_override = rules.get(
        "useCalculatedAttackForDamage", False
    )
    use_profile_attack = (
        profile_attack > 0
        and not attack_values_match
        and not calculated_attack_override
    )
    damage_formula_attack = profile_attack if use_profile_attack else final_attack
    if use_profile_attack:
        warn_once(
            warnings,
            "재구성 공격력과 API 프로필 공격력이 불일치하여 재구성 과정은 "
            "검산용으로 표시하고 이후 피해 계산에는 프로필 공격력을 사용했습니다.",
        )
    elif calculated_attack_override and not attack_values_match:
        warn_once(
            warnings,
            "재구성 공격력과 API 프로필 공격력이 불일치하여 공식 "
            "current-v2.7.2 규칙에 따라 이후 피해 계산에는 재구성 "
            "공격력을 사용했습니다.",
        )

    additional_damage_percent = (
        equipment["weaponAdditionalDamage"]
        + equipment["necklaceAdditionalDamage"]
        + equipment["otherAdditionalDamage"]
        + sum(ark["additionalDamageByName"].values(), Decimal("0"))
        + (
            FIXED["petAdditionalDamagePercent"]
            if rules["includePetAdditionalDamage"]
            else Decimal("0")
        )
        + (grid["additionalDamagePercent"] if include_arkgrid else Decimal("0"))
    )
    additional_damage_multiplier = Decimal("1") + additional_damage_percent

    mass_speed = resolved_engraving_value(
        "질량 증가", "attackSpeed", parsed, assumptions, rules
    )
    gale_attack = ark["speedByName"].get("질풍노도", {}).get(
        "attackSpeed", Decimal("0")
    )
    gale_move = ark["speedByName"].get("질풍노도", {}).get(
        "moveSpeed", Decimal("0")
    )
    arkgrid_attack_speed = (
        grid["attackSpeed"] if include_arkgrid else Decimal("0")
    )
    arkgrid_move_speed = (
        grid["moveSpeed"] if include_arkgrid else Decimal("0")
    )
    raw_attack_speed = (
        Decimal("1")
        + profile["attackSpeedFromSwiftness"]
        + mass_speed
        + rules["combatBlessingAttackSpeedPercent"]
        + rules["feastAttackSpeedPercent"]
        + gale_attack
        + arkgrid_attack_speed
    )
    raw_move_speed = (
        Decimal("1")
        + profile["moveSpeedFromSwiftness"]
        + rules["combatBlessingMoveSpeedPercent"]
        + rules["feastMoveSpeedPercent"]
        + gale_move
        + arkgrid_move_speed
    )
    capped_attack_speed = min(raw_attack_speed, FIXED["speedCap"])
    capped_move_speed = min(raw_move_speed, FIXED["speedCap"])

    sonic_level = 0
    for effect in ark["effects"].values():
        if "음속 돌파" in (effect.get("rawName") or "") or "음속 돌파" in (
            effect.get("description") or ""
        ):
            sonic_level = effect.get("level") or 2
            if effect.get("level") is None:
                warn_once(
                    warnings,
                    "음속 돌파 레벨을 파싱하지 못해 예시 레벨 2를 사용했습니다.",
                )
            break
    sonic_detail = (
        sonic_breakthrough_breakdown(
            sonic_level, raw_attack_speed, raw_move_speed, rule_version
        )
        if sonic_level
        else {
            "level": 0,
            "attackSpeedIncrease": raw_attack_speed - Decimal("1"),
            "moveSpeedIncrease": raw_move_speed - Decimal("1"),
            "baseRate": Decimal("0"),
            "baseAttackInput": Decimal("0"),
            "baseMoveInput": Decimal("0"),
            "baseDamage": Decimal("0"),
            "bothSpeedsExceededCap": False,
            "bothExceededBonus": Decimal("0"),
            "overCapRate": Decimal("0"),
            "attackOverCap": Decimal("0"),
            "moveOverCap": Decimal("0"),
            "overCapDamage": Decimal("0"),
            "uncappedTotal": Decimal("0"),
            "maximum": Decimal("0"),
            "final": Decimal("0"),
            "limitedByMaximum": False,
        }
    )
    sonic = sonic_detail["final"]

    evolution_parts: list[tuple[str, Decimal]] = []
    for name, value in ark["evolutionDamageByName"].items():
        if name != "음속 돌파" and value:
            evolution_parts.append((name, value))
    if ark["karmaEvolutionDamage"]:
        evolution_parts.append(("진화 카르마", ark["karmaEvolutionDamage"]))
    if sonic:
        evolution_parts.append((f"음속 돌파 Lv.{sonic_level}", sonic))
    evolution_percent = sum((v for _, v in evolution_parts), Decimal("0"))

    general_engraving_damage: list[tuple[str, Decimal]] = []
    for engraving_name in SUPPORTED_GENERAL_DAMAGE_ENGRAVINGS:
        eligible, scope_reason = engraving_scope(engraving_name, skill_name)
        value = resolved_engraving_value(
            engraving_name,
            "generalDamage",
            parsed,
            assumptions,
            rules,
        )
        if value and eligible:
            general_engraving_damage.append((engraving_name, value))
            if (
                engraving_name == "타격의 대가"
                and skill_model["tagVerification"] != "VERIFIED"
            ):
                assumptions.append(
                    source(
                        source_type="PROVISIONAL",
                        path=f"skillModels.{skill_name}.tags.NON_DIRECTIONAL",
                        label=f"{skill_name} 타격의 대가 범위 판정",
                        value=value,
                        raw=scope_reason,
                        note="비방향성·각성기 제외 스킬로 잠정 분류하여 적용",
                    )
                )
        elif value:
            assumptions.append(
                source(
                    source_type="DERIVED",
                    path=f"effects.{engraving_name}",
                    label=f"{engraving_name} 범위 판정",
                    value=value,
                    raw=scope_reason,
                    eligible=False,
                    applied=False,
                    excluded_reason=f"{skill_name}: {scope_reason} 불충족",
                )
            )
    if rules["useLiveEngravingDescriptions"]:
        for engraving_name, parsed_effect in engravings["parsedEffects"].items():
            if (
                dec(parsed_effect.get("generalDamage")) > 0
                and engraving_name
                not in SUPPORTED_GENERAL_DAMAGE_ENGRAVING_SET
                | {"돌격대장"}
            ):
                warn_once(
                    warnings,
                    f"{engraving_name} 피해 수치는 API에서 읽었지만 {skill_name} 적용 범위가 "
                    "미등록되어 계산에서 제외했습니다.",
                )
    skill_damage_parts: list[tuple[str, Decimal]] = []
    skill_damage_scope: list[dict[str, Any]] = []
    for effect_name, value in ark["skillDamageByName"].items():
        if not value:
            continue
        eligible, scope_reason = ark_passive_skill_damage_scope(
            effect_name, skill_name
        )
        scope_item = {
            "name": effect_name,
            "value": value,
            "eligible": eligible,
            "applied": eligible,
            "reason": scope_reason,
        }
        skill_damage_scope.append(scope_item)
        if eligible:
            skill_damage_parts.append((effect_name, value))
        else:
            assumptions.append(
                source(
                    source_type="DERIVED",
                    path=f"arkPassive.skillDamageByName.{effect_name}",
                    label=f"{effect_name} 스킬 범위 판정",
                    value=value,
                    raw=scope_reason,
                    eligible=False,
                    applied=False,
                    excluded_reason=f"{skill_name}에 적용되는 태그가 아님",
                )
            )
    raid_captain = Decimal("0")
    if effect_present("돌격대장", parsed):
        raid_coefficient = dec(
            engravings["parsedEffects"]
            .get("돌격대장", {})
            .get("raidCaptainCoefficient", Decimal("0"))
        )
        if not rules["useLiveEngravingDescriptions"] or not raid_coefficient:
            raid_coefficient = rules["raidCaptainFallbackCoefficient"]
        raid_captain = max(
            Decimal("0"), capped_move_speed - Decimal("1")
        ) * raid_coefficient
        assumptions.append(
            source(
                source_type="API_FIELD+DERIVED",
                path="effects.돌격대장",
                label="돌격대장 피해",
                value=raid_captain,
                raw=(
                    f"상한 적용 이동속도={capped_move_speed}; "
                    f"이동속도 증가량 계수={raid_coefficient}"
                ),
            )
        )
    master_critical = ark["criticalHitDamageByName"].get("회심", Decimal("0"))
    master_from_ark_passive = bool(master_critical)
    if not master_critical and equipment["hasMasterElixir"]:
        master_critical = EXAMPLE_EFFECT_DB["회심"]["criticalHitDamage"]
    if master_critical:
        master_effect = ark["effects"].get("회심", {})
        assumptions.append(
            source(
                source_type=(
                    "OFFICIAL_TOOLTIP"
                    if master_from_ark_passive
                    else "API_FIELD+EXAMPLE_DB"
                ),
                path=(
                    "arkPassive.Effects[회심]"
                    if master_from_ark_passive
                    else "equipment[*].Tooltip"
                ),
                label="회심 치명타 시 피해",
                value=master_critical,
                raw=(
                    str(master_effect.get("description") or "")
                    if master_from_ark_passive
                    else "회심 문자열 확인"
                ),
                note=(
                    "현재 API 아크 패시브 설명에서 파싱"
                    if master_from_ark_passive
                    else "장비의 회심 문자열만 확인되어 예시 DB 수치 사용"
                ),
            )
        )

    demon_damage = (
        FIXED["petDemonDamagePercent"] + FIXED["collectionDemonDamagePercent"]
    )
    card_damage = parsed["cards"]["damagePercent"]
    boss_damage = (
        grid["gemEffects"]["bossDamagePercent"]
        + grid["pointEffects"]["bossDamagePercent"]
        if include_arkgrid
        else Decimal("0")
    )
    arkgrid_general_damage = (
        grid["generalDamagePercent"] if include_arkgrid else Decimal("0")
    )
    arkgrid_skill_damage = (
        grid["skillDamagePercent"] if include_arkgrid else Decimal("0")
    )
    regular_gem_effect = regular_gem_effect_for_skill(parsed["gems"], skill_name)
    regular_gem_skill_damage = regular_gem_effect["damagePercent"]
    active_core_factors = (
        grid.get("coreDamageFactors", []) if include_arkgrid else []
    )
    core_subtitle_factors = [
        factor
        for factor in active_core_factors
        if factor["category"]
        in {
            "generalDamagePercent",
            "bossDamagePercent",
            "skillDamagePercent",
        }
    ]
    core_subtitle_parts = [
        (
            (
                f"아크그리드 {factor['coreName']} "
                f"{'+'.join(str(item['requiredPoints']) + 'P' for item in factor['contributions'])}"
            ),
            factor["value"],
        )
        for factor in core_subtitle_factors
    ]
    tripod_damage_parts = [
        (
            (
                f"{skill_name} {effect['tripodName']} · {effect['label']}"
                if rules.get("applyAllSelectedTripodDamage", False)
                else f"{skill_name} {effect['tripodName']}"
            ),
            effect["percent"],
        )
        for effect in tripod_damage_effects
    ]
    tripod_damage_multiplier = Decimal("1")
    for effect in tripod_damage_effects:
        tripod_damage_multiplier *= effect["multiplier"]
    subtitle_percentages = [
        *general_engraving_damage,
        ("진화형 피해", evolution_percent),
        ("악마 추가 피해", demon_damage),
        ("카드 피해", card_damage),
        ("돌격대장", raid_captain),
        *skill_damage_parts,
        ("목걸이 적에게 주는 피해", equipment["necklaceDamageToEnemy"]),
        ("팔찌 적에게 주는 피해", equipment["braceletDamageToEnemy"]),
        ("기타 적에게 주는 피해", equipment["otherDamageToEnemy"]),
        ("팔찌 비방향성 피해", equipment["braceletNonDirectionalDamage"]),
        ("아크그리드 보스 피해", boss_damage),
        *core_subtitle_parts,
        *tripod_damage_parts,
        (f"일반 보석 {skill_name} 피해", regular_gem_skill_damage),
    ]
    subtitle_multipliers = [
        (name, Decimal("1") + value) for name, value in subtitle_percentages
    ]
    total_damage_multiplier = Decimal("1")
    for _, multiplier in subtitle_multipliers:
        total_damage_multiplier *= multiplier

    hit_bases = [
        hit["coefficient"] * damage_formula_attack + hit["constant"]
        for hit in effective_hits
    ]
    skill_base = sum(hit_bases, Decimal("0"))
    enemy_defense_reduction = (
        grid["enemyDefenseReductionPercent"]
        if include_arkgrid
        else Decimal("0")
    )
    defense_retention_multiplier = Decimal("1")
    for factor in active_core_factors:
        if factor["category"] == "enemyDefenseReductionPercent":
            defense_retention_multiplier *= Decimal("1") - factor["value"]
    effective_enemy_defense = (
        FIXED["enemyDefense"] * defense_retention_multiplier
    )
    defense_multiplier = FIXED["defenseConstant"] / (
        FIXED["defenseConstant"] + effective_enemy_defense
    )
    common_damage_multiplier = (
        additional_damage_multiplier
        * total_damage_multiplier
        * FIXED["enemyDamageTakenMultiplier"]
        * defense_multiplier
    )
    noncritical_raw = skill_base * common_damage_multiplier

    adrenaline_crit = resolved_engraving_value(
        "아드레날린", "criticalRate", parsed, assumptions, rules
    )
    ark_critical_rate = sum(ark["criticalRateByName"].values(), Decimal("0"))
    exposed = (
        EXAMPLE_EFFECT_DB["급소 노출"]["criticalRate"]
        if parsed["combatSkills"]["hasExposedWeakness"]
        else Decimal("0")
    )
    critical_rate_raw = (
        profile["criticalRateFromStat"]
        + equipment["criticalRate"]
        + adrenaline_crit
        + ark_critical_rate
        + exposed
        + (grid["criticalRate"] if include_arkgrid else Decimal("0"))
    )
    critical_rate = min(Decimal("1"), max(Decimal("0"), critical_rate_raw))
    critical_rate_components = {
        "criticalStat": profile["criticalRateFromStat"],
        "equipment": equipment["criticalRate"],
        "adrenaline": adrenaline_crit,
        "arkPassive": ark_critical_rate,
        "exposedWeakness": exposed,
        "arkGrid": (
            grid["criticalRate"] if include_arkgrid else Decimal("0")
        ),
    }
    ark_passive_critical_damage = sum(
        ark["criticalDamageByName"].values(), Decimal("0")
    )
    arkgrid_critical_damage = (
        grid["criticalDamage"] if include_arkgrid else Decimal("0")
    )
    critical_damage = (
        FIXED["baseCriticalDamage"]
        + equipment["criticalDamage"]
        + ark_passive_critical_damage
        + arkgrid_critical_damage
        + tripod_critical_damage
    )
    critical_damage_components = {
        "base": FIXED["baseCriticalDamage"],
        "equipment": equipment["criticalDamage"],
        "arkPassive": ark_passive_critical_damage,
        "arkGrid": arkgrid_critical_damage,
        "skillTripod": tripod_critical_damage,
    }
    core_critical_hit_multiplier = Decimal("1")
    for factor in active_core_factors:
        if factor["category"] == "criticalHitDamagePercent":
            core_critical_hit_multiplier *= Decimal("1") + factor["value"]
    critical_hit_damage_multiplier = (
        (Decimal("1") + master_critical)
        * (Decimal("1") + equipment["braceletCriticalHitDamage"])
        * core_critical_hit_multiplier
    )
    critical_raw = (
        noncritical_raw * critical_damage * critical_hit_damage_multiplier
    )
    expected_raw = (
        critical_raw * critical_rate
        + noncritical_raw * (Decimal("1") - critical_rate)
    )
    hit_results: list[dict[str, Any]] = []
    for hit, hit_base in zip(effective_hits, hit_bases):
        hit_noncritical = hit_base * common_damage_multiplier
        hit_critical = (
            hit_noncritical
            * critical_damage
            * critical_hit_damage_multiplier
        )
        hit_expected = (
            hit_critical * critical_rate
            + hit_noncritical * (Decimal("1") - critical_rate)
        )
        hit_results.append(
            {
                "name": hit["name"],
                "coefficient": hit["coefficient"],
                "originalCoefficient": hit["originalCoefficient"],
                "coefficientMultiplier": hit["coefficientMultiplier"],
                "constant": hit["constant"],
                "tripodSource": hit.get("tripodSource"),
                "skillBaseRaw": hit_base,
                "nonCriticalRaw": hit_noncritical,
                "criticalRaw": hit_critical,
                "expectedRaw": hit_expected,
                "nonCritical": int(
                    hit_noncritical.to_integral_value(rounding=ROUND_FLOOR)
                ),
                "critical": int(
                    hit_critical.to_integral_value(rounding=ROUND_FLOOR)
                ),
                "expected": int(
                    hit_expected.to_integral_value(rounding=ROUND_FLOOR)
                ),
            }
        )
    # Define the cast total as the exact sum of independently evaluated hits.
    # This avoids a last-place Decimal difference from distributing the common
    # multiplier over a multi-hit skill.
    noncritical_raw = sum(
        (hit["nonCriticalRaw"] for hit in hit_results), Decimal("0")
    )
    critical_raw = sum(
        (hit["criticalRaw"] for hit in hit_results), Decimal("0")
    )
    expected_raw = sum(
        (hit["expectedRaw"] for hit in hit_results), Decimal("0")
    )

    return {
        "calculatorVersion": CALCULATOR_VERSION,
        "parserVersion": PARSER_VERSION,
        "dbRelease": DB_RELEASE,
        "scenarioPresetId": SCENARIO_PRESET_ID,
        "calculationMode": CALCULATION_MODE,
        "skillName": skill_name,
        "skillModel": {
            "variant": skill_model["variant"],
            "hitCount": len(effective_hits),
            "motionCoefficientMultiplier": effective_hits[0][
                "coefficientMultiplier"
            ],
            "tags": sorted(skill_model["tags"]),
            "tagVerification": skill_model["tagVerification"],
            "source": skill_model["source"],
            "requiredTripods": sorted(required_tripods),
            "missingTripods": missing_tripods,
            "tripodCriticalDamage": tripod_critical_damage,
            "separateDamageTripod": separate_damage_tripod,
            "tripodDamagePercent": tripod_damage_percent,
            "selectedTripods": selected_skill_tripod_items,
            "tripodDamageEffects": tripod_damage_effects,
            "embeddedTripodDamageEffects": embedded_tripod_damage_effects,
            "tripodDamageMultiplier": tripod_damage_multiplier,
        },
        "skillScope": skill_damage_scope,
        "ruleVersion": rule_version,
        "ruleLabel": rules["label"],
        "ruleSource": rules["source"],
        "intermediateFloorStages": sorted(rules["intermediateFloorStages"]),
        "includeArkGrid": include_arkgrid,
        "inputs": {
            "equipmentMainStat": equipment["mainStat"],
            "levelMainStat": rules["levelMainStat"],
            "expeditionMainStat": rules["expeditionMainStat"],
            "collectionMainStat": rules["collectionMainStat"],
            "avatarMainStatPercent": parsed["avatars"]["mainStatPercent"],
            "petMainStatPercent": pet_main_stat_percent,
            "baseWeaponAttack": equipment["baseWeaponAttack"],
            "equipmentWeaponAttackFlat": (
                equipment["weaponAttackFlat"]
                if rules["includeFlatWeaponAttack"]
                else Decimal("0")
            ),
            "arkGridCoreWeaponAttackFlat": (
                grid["weaponAttackFlat"] if include_arkgrid else Decimal("0")
            ),
            "equipmentWeaponAttackPercent": equipment["weaponAttackPercent"],
            "karmaWeaponAttackPercent": ark["karmaWeaponAttackPercent"],
            "arkGridCoreWeaponAttackPercent": (
                grid["weaponAttackPercent"]
                if include_arkgrid
                else Decimal("0")
            ),
            "regularGemBaseAttackPercent": parsed["gems"]["baseAttackPercent"],
            "stoneBaseAttackPercent": engravings["stoneBaseAttackPercent"],
            "armletBaseAttackPowerFlat": armlet_base_attack_flat,
            "armletBaseAttackPowerPercent": armlet_base_attack_percent,
            "equipmentAttackPowerFlat": (
                equipment["attackPowerFlat"]
                if rules["includeFlatAttackPower"]
                else Decimal("0")
            ),
            "arkGridCoreAttackPowerFlat": (
                grid["attackPowerFlat"] if include_arkgrid else Decimal("0")
            ),
            "equipmentAttackPowerPercent": equipment["attackPowerPercent"],
            "adrenalineAttackPowerPercent": adrenaline_attack,
            "arkGridAttackPowerPercent": arkgrid_attack,
            "arkGridGemAttackPowerPercent": arkgrid_gem_attack,
            "arkGridPointAttackPowerPercent": arkgrid_point_attack,
            "arkGridCoreAttackPowerPercent": arkgrid_core_attack,
            "arkGridCoreGeneralDamagePercent": arkgrid_general_damage,
            "arkGridCoreSkillDamagePercent": arkgrid_skill_damage,
            "arkGridCoreCriticalRate": (
                grid["criticalRate"] if include_arkgrid else Decimal("0")
            ),
            "arkGridCoreCriticalDamage": (
                grid["criticalDamage"] if include_arkgrid else Decimal("0")
            ),
            "skillTripodCriticalDamage": tripod_critical_damage,
            "skillTripodDamagePercent": tripod_damage_percent,
            "skillTripodDamageMultiplier": tripod_damage_multiplier,
            "arkGridCoreCriticalHitDamagePercent": (
                grid["criticalHitDamagePercent"]
                if include_arkgrid
                else Decimal("0")
            ),
            "arkGridCoreEnemyDefenseReductionPercent": enemy_defense_reduction,
            "regularGemSkillDamagePercent": regular_gem_skill_damage,
            "regularGemCooldownReductionPercent": regular_gem_effect[
                "cooldownReductionPercent"
            ],
            "weaponAdditionalDamage": equipment["weaponAdditionalDamage"],
            "necklaceAdditionalDamage": equipment["necklaceAdditionalDamage"],
            "otherAdditionalDamage": equipment["otherAdditionalDamage"],
            "arkPassiveAdditionalDamage": sum(
                ark["additionalDamageByName"].values(), Decimal("0")
            ),
            "petAdditionalDamage": (
                FIXED["petAdditionalDamagePercent"]
                if rules["includePetAdditionalDamage"]
                else Decimal("0")
            ),
            "arkGridAdditionalDamage": (
                grid["additionalDamagePercent"] if include_arkgrid else Decimal("0")
            ),
        },
        "mainStat": {
            "base": base_main_stat,
            "percent": avatar_pet_percent,
            "rawBeforeStageRounding": final_main_stat_raw,
            "final": final_main_stat,
            "stageRounded": final_main_stat != final_main_stat_raw,
        },
        "weaponAttack": {
            "base": equipment["baseWeaponAttack"],
            "flat": weapon_attack_flat,
            "subtotalBeforePercent": weapon_attack_subtotal,
            "percent": weapon_attack_percent,
            "rawBeforeStageRounding": final_weapon_attack_raw,
            "final": final_weapon_attack,
            "stageRounded": final_weapon_attack != final_weapon_attack_raw,
        },
        "attackPower": {
            "rootBeforeBaseAttackPercent": root_attack,
            "armletBaseAttackFlat": armlet_base_attack_flat,
            "subtotalBeforeBaseAttackPercent": base_attack_subtotal,
            "baseAttackPercent": base_attack_percent,
            "afterBaseAttackPercent": root_with_base_attack_percent,
            "flatAttackPower": attack_power_flat,
            "base": base_attack,
            "finalAttackPercent": attack_power_percent,
            "rawBeforeStageRounding": final_attack_raw,
            "final": final_attack,
            "stageRounded": final_attack != final_attack_raw,
            "profileValueForComparison": profile["profileAttackPower"],
            "differenceFromProfile": final_attack - profile["profileAttackPower"],
            "matchesProfile": attack_values_match,
            "usedForDamage": damage_formula_attack,
            "usedForDamageSource": (
                "API_PROFILE"
                if use_profile_attack
                else (
                    "CALCULATED_OFFICIAL"
                    if calculated_attack_override and not attack_values_match
                    else "CALCULATED"
                )
            ),
        },
        "regularGemSkillEffect": regular_gem_effect,
        "speed": {
            "attackComponents": {
                "base": Decimal("1"),
                "swiftness": profile["attackSpeedFromSwiftness"],
                "massIncrease": mass_speed,
                "combatBlessing": rules[
                    "combatBlessingAttackSpeedPercent"
                ],
                "feast": rules["feastAttackSpeedPercent"],
                "gale": gale_attack,
                "arkGridCore": arkgrid_attack_speed,
            },
            "moveComponents": {
                "base": Decimal("1"),
                "swiftness": profile["moveSpeedFromSwiftness"],
                "combatBlessing": rules[
                    "combatBlessingMoveSpeedPercent"
                ],
                "feast": rules["feastMoveSpeedPercent"],
                "gale": gale_move,
                "arkGridCore": arkgrid_move_speed,
            },
            "rawAttackSpeed": raw_attack_speed,
            "cappedAttackSpeed": capped_attack_speed,
            "rawAttackSpeedIncrease": raw_attack_speed - Decimal("1"),
            "cappedAttackSpeedIncrease": capped_attack_speed - Decimal("1"),
            "rawMoveSpeed": raw_move_speed,
            "cappedMoveSpeed": capped_move_speed,
            "rawMoveSpeedIncrease": raw_move_speed - Decimal("1"),
            "cappedMoveSpeedIncrease": capped_move_speed - Decimal("1"),
            "sonicBreakthroughLevel": sonic_level,
            "sonicBreakthroughEvolutionDamage": sonic,
            "sonicBreakthroughBreakdown": sonic_detail,
        },
        "damageGroups": {
            "engravingParts": [
                {"name": name, "value": value}
                for name, value in general_engraving_damage
            ],
            "additionalDamagePercent": additional_damage_percent,
            "additionalDamageMultiplier": additional_damage_multiplier,
            "evolutionParts": [
                {"name": name, "value": value} for name, value in evolution_parts
            ],
            "skillDamageParts": [
                {"name": name, "value": value}
                for name, value in skill_damage_parts
            ],
            "tripodDamageParts": [
                {"name": name, "value": value}
                for name, value in tripod_damage_parts
            ],
            "tripodDamageEffects": tripod_damage_effects,
            "embeddedTripodDamageEffects": embedded_tripod_damage_effects,
            "tripodDamageMultiplier": tripod_damage_multiplier,
            "subtitles": [
                {"name": name, "percent": percent, "multiplier": Decimal("1") + percent}
                for name, percent in subtitle_percentages
            ],
            "totalSubtitleMultiplier": total_damage_multiplier,
            "arkGridCoreFactors": active_core_factors,
        },
        "critical": {
            "rateRaw": critical_rate_raw,
            "rateCapped": critical_rate,
            "rateComponents": critical_rate_components,
            "damageMultiplier": critical_damage,
            "damageComponents": critical_damage_components,
            "skillTripodCriticalDamage": tripod_critical_damage,
            "criticalHitDamageMultiplier": critical_hit_damage_multiplier,
            "criticalHitDamageFactors": {
                "master": Decimal("1") + master_critical,
                "bracelet": (
                    Decimal("1")
                    + equipment["braceletCriticalHitDamage"]
                ),
                "arkGrid": core_critical_hit_multiplier,
            },
            "arkGridCriticalHitDamageMultiplier": (
                core_critical_hit_multiplier
            ),
        },
        "enemy": {
            "defense": FIXED["enemyDefense"],
            "defenseConstant": FIXED["defenseConstant"],
            "defenseMultiplier": defense_multiplier,
            "damageTakenMultiplier": FIXED["enemyDamageTakenMultiplier"],
            "defenseReductionPercent": enemy_defense_reduction,
            "defenseRetentionMultiplier": defense_retention_multiplier,
            "effectiveDefense": effective_enemy_defense,
            "species": "악마",
        },
        "damage": {
            "attackPowerUsed": damage_formula_attack,
            "hitCount": len(hit_results),
            "hits": hit_results,
            "skillBaseRaw": skill_base,
            "nonCriticalRaw": noncritical_raw,
            "criticalRaw": critical_raw,
            "expectedRaw": expected_raw,
            "nonCritical": int(noncritical_raw.to_integral_value(rounding=ROUND_FLOOR)),
            "critical": int(critical_raw.to_integral_value(rounding=ROUND_FLOOR)),
            "expected": int(expected_raw.to_integral_value(rounding=ROUND_FLOOR)),
        },
        "assumptions": assumptions,
        "provenance": {
            "fallbacks": [
                *parsed.get("fallbacks", []),
                *[
                    item
                    for item in assumptions
                    if "EXAMPLE_DB" in str(item.get("sourceType"))
                    or item.get("sourceType") == "LEGACY_EXAMPLE"
                ],
            ],
            "appliedEffects": [
                item
                for item in [*report_sources(parsed), *assumptions]
                if item.get("applied") is True
            ],
            "excludedEffects": [
                item
                for item in [*report_sources(parsed), *parsed.get("excluded", [])]
                if item.get("applied") is False
            ],
        },
    }


def parse_all(
    responses: dict[str, Any],
    character: str = CHARACTER_NAME,
    skill_name: str = CANONICAL_SKILL,
) -> dict[str, Any]:
    skill_name = canonical_skill(skill_name)
    get_skill_model(skill_name)
    warnings: list[str] = []
    parsed = {
        "schemaVersion": PARSED_SCHEMA_VERSION,
        "calculatorVersion": CALCULATOR_VERSION,
        "parserVersion": PARSER_VERSION,
        "dbRelease": DB_RELEASE,
        "scenarioPresetId": SCENARIO_PRESET_ID,
        "calculationMode": CALCULATION_MODE,
        "availableRuleVersions": list(RULESETS),
        "defaultRuleVersion": DEFAULT_RULE_VERSION,
        "characterName": character,
        "canonicalSkillName": skill_name,
        "aliases": [
            alias
            for alias, canonical in SKILL_ALIASES.items()
            if canonical == skill_name and alias != skill_name
        ],
        "warnings": warnings,
    }
    parsed["profile"] = parse_profile(responses.get("profiles"), warnings)
    parsed["equipment"] = parse_equipment(responses.get("equipment"), warnings)
    parsed["avatars"] = parse_avatars(responses.get("avatars"), warnings)
    parsed["engravings"] = parse_engravings(responses.get("engravings"), warnings)
    parsed["cards"] = parse_cards(responses.get("cards"), warnings)
    parsed["gems"] = parse_gems(responses.get("gems"), warnings, skill_name)
    parsed["arkPassive"] = parse_ark_passive(
        responses.get("arkPassive"), warnings, skill_name
    )
    parsed["combatSkills"] = parse_combat_skills(responses.get("combatSkills"))
    parsed["arkGrid"] = parse_ark_grid(
        responses.get("arkGrid"), warnings, skill_name
    )
    parsed["excluded"] = (
        parsed["equipment"]["excluded"]
        + parsed["avatars"]["excluded"]
        + parsed["arkGrid"]["excluded"]
    )
    fallback_sources: list[dict[str, Any]] = []
    for block_name in (
        "avatars",
        "engravings",
        "combatSkills",
        "arkPassive",
    ):
        block = parsed.get(block_name) or {}
        candidates = [
            *(block.get("sources") or block.get("selected") or []),
            *(block.get("fallbacks") or []),
        ]
        for item in candidates:
            source_type = str(item.get("sourceType") or "")
            try:
                has_effect = dec(item.get("value")) != 0
            except Exception:
                has_effect = bool(item.get("value"))
            if (
                has_effect
                and item.get("applied") is True
                and (
                    "EXAMPLE_DB" in source_type
                    or source_type == "LEGACY_EXAMPLE"
                )
            ):
                fallback_sources.append(item)
    parsed["fallbacks"] = fallback_sources
    return parsed


def fmt(value: Any, places: int = 2) -> str:
    """Format numeric values for Markdown reports only."""
    if isinstance(value, Decimal):
        quantum = Decimal("1").scaleb(-places)
        rounded = value.quantize(quantum, rounding=ROUND_HALF_UP)
        return f"{rounded:,.{places}f}"
    if isinstance(value, int):
        return f"{value:,.{places}f}"
    return str(value)


def pct_fmt(value: Decimal, places: int = 2) -> str:
    quantum = Decimal("1").scaleb(-places)
    rounded = (value * 100).quantize(quantum, rounding=ROUND_HALF_UP)
    return f"{rounded:.{places}f}%"


def category_value_fmt(value: Decimal, category: str) -> str:
    """Format normalized ArkGrid component values without hiding small percents."""
    if category.endswith("Percent") or category in {
        "attackSpeed",
        "criticalDamage",
        "criticalRate",
        "moveSpeed",
    }:
        return pct_fmt(value)
    return fmt(value)


def source_value_fmt(value: Any, label: str) -> str:
    """Format source-table fractions as percents when the label identifies one."""
    percentage_markers = (
        "Percent",
        "additionalDamage",
        "criticalDamage",
        "criticalHitDamage",
        "criticalRate",
        "damageToEnemy",
        "아바타 주스탯",
        "어빌리티 스톤 기본 공격력",
        "일반 보석",
        "깨달음 카르마 무기 공격력",
        "진화 카르마 진화형 피해",
        "급소 노출",
        "세상을 구하는 빛",
    )
    if any(marker in label for marker in percentage_markers):
        return pct_fmt(dec(value))
    return fmt(value)


def report_sources(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for key in (
        "profile",
        "equipment",
        "avatars",
        "engravings",
        "cards",
        "gems",
        "arkPassive",
        "combatSkills",
        "arkGrid",
    ):
        block = parsed.get(key) or {}
        result.extend(block.get("sources") or [])
        result.extend(block.get("selected") or [])
        result.extend(block.get("fallbacks") or [])
    return result


def render_report(
    raw_bundle: dict[str, Any],
    parsed: dict[str, Any],
    without_grid: dict[str, Any],
    with_grid: dict[str, Any],
    raw_path: Path | None,
    parsed_path: Path | None,
) -> str:
    p = parsed
    c = with_grid
    lines: list[str] = [
        f"# {p['profile'].get('characterName') or p['characterName']} "
        f"{c['skillName']} API 파싱·피해 계산 보고서",
        "",
        f"- 캐릭터: `{p['profile'].get('characterName')}` / `{p['profile'].get('className')}`",
        f"- 아이템 레벨: `{p['profile'].get('itemLevel')}`",
        f"- 계산 스킬: `{c['skillName']}` / `{c['skillModel']['variant']}`",
        f"- 계산기 버전: `{c['calculatorVersion']}`",
        f"- 파서 버전: `{c['parserVersion']}`",
        f"- 규칙 버전: `{c['ruleVersion']}` — {c['ruleLabel']}",
        f"- DB 릴리스: `{c['dbRelease']}`",
        f"- 시나리오 프리셋: `{c['scenarioPresetId']}`",
        f"- 계산 모드: `{c['calculationMode']}`",
        f"- 중간 버림 단계: `{', '.join(c['intermediateFloorStages']) or '없음'}`",
        "- 과거 피해값과의 회귀검증은 수행하지 않았습니다.",
        "",
    ]
    source_lines: list[str] = [
        "## 5. API 호출 결과",
        "",
        f"- API 스냅샷: `{raw_bundle.get('capturedAtKst')}`",
        f"- 규칙 출처: `{c['ruleSource']}`",
        (
            f"- 디버그 API 원본: [{raw_path.name}]({raw_path.name})"
            if raw_path is not None
            else "- 디버그 API 원본 JSON: 기본 설정에서는 생성하지 않음"
        ),
        (
            f"- 디버그 파싱 결과: [{parsed_path.name}]({parsed_path.name})"
            if parsed_path is not None
            else "- 디버그 파싱 JSON: 기본 설정에서는 생성하지 않음"
        ),
        "",
        "| 엔드포인트 | HTTP | 호출 시각(KST) | 남은 호출량 |",
        "|---|---:|---|---:|",
    ]
    for key, meta in (raw_bundle.get("endpoints") or {}).items():
        source_lines.append(
            f"| `{key}` | {meta.get('status')} | {meta.get('capturedAtKst')} | "
            f"{(meta.get('rateLimit') or {}).get('remaining')} |"
        )

    source_lines += [
        "",
        (
            "`--emit-debug-json`을 지정한 경우에만 전체 응답 본문을 API 원본 "
            "JSON의 엔드포인트별 `rawBody`와 `responses`로 보존합니다. "
            "Authorization 헤더는 저장하지 않습니다."
        ),
        "",
        "## 6. 파싱 결과와 출처",
        "",
        "| 값 | 정규화 결과 | 출처 | 파싱 | 적용 가능 | 실제 적용 | 제외 사유 |",
        "|---|---:|---|---|---|---|---|",
    ]
    for item in report_sources(parsed):
        raw_short = (
            re.sub(r"\s+", " ", str(item.get("raw") or ""))[:120]
            .replace("|", "\\|")
        )
        label = str(item.get("label") or "").replace("|", "\\|")
        path = str(item.get("path") or "").replace("|", "\\|")
        note = str(item.get("note") or "").replace("|", "\\|")
        parsed_status = "예" if item.get("parsed", True) else "아니오"
        eligible = "예" if item.get("eligible", True) else "아니오"
        applied = "예" if item.get("applied", True) else "아니오"
        excluded_reason = str(item.get("excludedReason") or "").replace("|", "\\|")
        value = item.get("value")
        source_lines.append(
            f"| {label} | `{source_value_fmt(value, label)}` | `{path}`"
            f"{'<br>' + raw_short if raw_short else ''}"
            f"{'<br>' + note if note else ''} | {parsed_status} | {eligible} | "
            f"{applied} | {excluded_reason or '-'} |"
        )

    source_lines += [
        "",
        "### 활성 ArkGrid 코어 임계 효과",
        "",
        "| 코어 | 포인트 | 임계치 | 카테고리 | 값 | 연산 | 적용 | 범위·조건 |",
        "|---|---:|---:|---|---:|---|---|---|",
    ]
    core_row_count = 0
    for core in p["arkGrid"]["cores"]:
        for option in core["options"]:
            if not option["activated"]:
                continue
            for component in option["components"]:
                core_row_count += 1
                condition = component["scopeReason"]
                if component["condition"]:
                    condition += "; " + component["condition"]
                safe_condition = condition.replace("|", "\\|")
                source_lines.append(
                    f"| {core['name']} ({core['grade']}) | {core['point']} | "
                    f"{option['requiredPoints']}P | `{component['category']}` | "
                    f"{category_value_fmt(component['value'], component['category'])} | "
                    f"`{component['operator']}` | "
                    f"{'예' if component['applied'] else '아니오'} | "
                    f"{safe_condition} |"
                )
    if not core_row_count:
        source_lines.append("| - | - | - | - | - | - | - | 활성 수치 효과 없음 |")
    if c["skillName"] == SPACE_CUTTING_SKILL:
        source_lines += [
            "",
            "### 공간 가르기 실측 오차 조사 출처",
            "",
            "- [2026-02 밸런스 패치 후 공간 가르기 피해량 +29.2% 분석]"
            "(https://vortexgaming.io/postdetail/681443)",
            "- [공간 가르기는 피해 보석을 장착할 수 없다는 사용자 논의]"
            "(https://www.inven.co.kr/board/lostark/5862/81961)",
            "- 위 자료는 오차 원인 가설의 근거이며 공식 모션계수 출처는 "
            "아닙니다.",
        ]

    i = c["inputs"]
    ms = c["mainStat"]
    wa = c["weaponAttack"]
    ap = c["attackPower"]
    speed = c["speed"]
    sonic_detail = speed["sonicBreakthroughBreakdown"]
    dg = c["damageGroups"]
    crit = c["critical"]
    enemy = c["enemy"]
    damage = c["damage"]
    regular_gem = c["regularGemSkillEffect"]
    arkgrid_gem_attack_parts = [
        (
            f"슬롯 {gem['slotIndex']}/젬 {gem['gemIndex']} "
            f"{pct_fmt(dec(gem['values']['attackPowerPercent']))}"
        )
        for gem in p["arkGrid"]["activeGems"]
        if dec(gem["values"]["attackPowerPercent"])
    ]
    arkgrid_gem_attack_formula = (
        " + ".join(arkgrid_gem_attack_parts) or "공격력 옵션 없음"
    )

    lines += [
        "",
        "## 1. 계산 과정",
        "",
        (
            "모든 중간값은 소수로 유지했습니다. 아래 세 최종 표시 피해에서만 "
            "`floor`를 적용했습니다."
            if not c["intermediateFloorStages"]
            else "엑셀 원본 호환을 위해 다음 중간 단계에도 `floor`를 적용했습니다: "
            + ", ".join(c["intermediateFloorStages"])
        ),
        "",
        "### 1.1 주스탯",
        "",
        f"`기초 지능 = {fmt(i['equipmentMainStat'])} + {fmt(i['levelMainStat'])} + "
        f"{fmt(i['expeditionMainStat'])} + {fmt(i['collectionMainStat'])} = {fmt(ms['base'])}`",
        "",
        f"`아바타+펫 = {pct_fmt(i['avatarMainStatPercent'])} + "
        f"{pct_fmt(i['petMainStatPercent'])} = {pct_fmt(ms['percent'])}`",
        "",
        f"`최종 지능 원시값 = {fmt(ms['base'])} × (1 + {fmt(ms['percent'])}) = "
        f"{fmt(ms['rawBeforeStageRounding'])}`",
        "",
        f"`규칙 적용 최종 지능 = {fmt(ms['final'])}`",
        "",
        "### 1.2 무기 공격력",
        "",
        f"`무기 공격력 증가 = {pct_fmt(i['equipmentWeaponAttackPercent'])} + "
        f"{pct_fmt(i['karmaWeaponAttackPercent'])} + 아크그리드 코어 "
        f"{pct_fmt(i['arkGridCoreWeaponAttackPercent'])} = {pct_fmt(wa['percent'])}`",
        "",
        f"`무기 공격력 소계 = 기본 {fmt(i['baseWeaponAttack'])} + "
        f"장비 평면 증가 {fmt(i['equipmentWeaponAttackFlat'])} + "
        f"아크그리드 코어 평면 증가 {fmt(i['arkGridCoreWeaponAttackFlat'])} = "
        f"{fmt(wa['subtotalBeforePercent'])}`",
        "",
        f"`최종 무기 공격력 원시값 = {fmt(wa['subtotalBeforePercent'])} × "
        f"(1 + {fmt(wa['percent'])}) = {fmt(wa['rawBeforeStageRounding'])}`",
        "",
        f"`규칙 적용 최종 무기 공격력 = {fmt(wa['final'])}`",
        "",
        "### 1.3 기본 공격력과 최종 공격력",
        "",
        f"`sqrt({fmt(ms['final'])} × {fmt(wa['final'])} ÷ 6) = "
        f"{fmt(ap['rootBeforeBaseAttackPercent'])}`",
        "",
        f"`기본 공격력 증가 = 보석 {pct_fmt(i['regularGemBaseAttackPercent'])} + "
        f"스톤 {pct_fmt(i['stoneBaseAttackPercent'])} + 완갑 "
        f"{pct_fmt(i['armletBaseAttackPowerPercent'])} = "
        f"{pct_fmt(ap['baseAttackPercent'])}`",
        "",
        f"`기본 공격력 소계 = 루트 공격력 {fmt(ap['rootBeforeBaseAttackPercent'])} + "
        f"완갑 평면 증가 {fmt(i['armletBaseAttackPowerFlat'])} = "
        f"{fmt(ap['subtotalBeforeBaseAttackPercent'])}`",
        "",
        f"`기본 공격력 소계 × 기본 공격력% = "
        f"{fmt(ap['subtotalBeforeBaseAttackPercent'])} × "
        f"(1 + {fmt(ap['baseAttackPercent'])}) = "
        f"{fmt(ap['afterBaseAttackPercent'])}`",
        "",
        f"`기본 공격력 단계 = {fmt(ap['afterBaseAttackPercent'])} + "
        f"장비 공격력 평면 증가 {fmt(i['equipmentAttackPowerFlat'])} + "
        f"아크그리드 코어 평면 증가 {fmt(i['arkGridCoreAttackPowerFlat'])} = "
        f"{fmt(ap['base'])}`",
        "",
        f"`공격력 증가 = 장신구 {pct_fmt(i['equipmentAttackPowerPercent'])} + "
        f"아드레날린 {pct_fmt(i['adrenalineAttackPowerPercent'])} + "
        f"아크그리드 누적 효과(Effects[]) "
        f"{pct_fmt(i['arkGridPointAttackPowerPercent'])} + "
        f"아크그리드 코어 {pct_fmt(i['arkGridCoreAttackPowerPercent'])} = "
        f"{pct_fmt(ap['finalAttackPercent'])}`",
        "",
        (
            f"`아크그리드 활성 젬 공격력 상세 = "
            f"{arkgrid_gem_attack_formula} = "
            f"{pct_fmt(i['arkGridGemAttackPowerPercent'])} "
            "(Effects[] 원천 검산값, 중복 합산하지 않음)`"
        ),
        "",
        f"`최종 공격력 원시값 = {fmt(ap['base'])} × "
        f"(1 + {fmt(ap['finalAttackPercent'])}) = "
        f"{fmt(ap['rawBeforeStageRounding'])}`",
        "",
        f"`규칙 적용 최종 공격력 = {fmt(ap['final'])}`",
        "",
        f"API 프로필 공격력은 `{fmt(ap['profileValueForComparison'])}`이며 계산값과의 차이는 "
        f"`{fmt(ap['differenceFromProfile'])}`입니다.",
        "",
        (
            f"두 값이 불일치하므로 위 재구성 값과 계산 과정은 검산용으로 보존하고, "
            f"이후 스킬 피해 계산에는 API 프로필 공격력 "
            f"`{fmt(ap['usedForDamage'])}`을 사용합니다."
            if ap["usedForDamageSource"] == "API_PROFILE"
            else (
                f"두 값은 불일치하지만 공식 current-v2.7.2 규칙에 따라 이후 "
                f"스킬 피해 계산에는 재구성 공격력 "
                f"`{fmt(ap['usedForDamage'])}`을 사용합니다."
                if ap["usedForDamageSource"] == "CALCULATED_OFFICIAL"
                else f"두 값이 일치하거나 프로필 값이 없어 이후 계산에는 "
                f"재구성 공격력 `{fmt(ap['usedForDamage'])}`을 사용합니다."
            )
        ),
        "",
        (
            "아크그리드 공격력은 위 재구성 공격력의 `아크그리드` 항에 분류해 "
            "한 번 반영했습니다. 선택된 공격력 이후 피해 단계에서는 같은 공격력 "
            "효과를 다시 곱하지 않아 중복 적용을 방지합니다."
        ),
        "",
        "### 1.4 공격·이동속도 및 음속 돌파",
        "",
        "공격속도 구성:",
        "",
        f"`1 + 신속 {fmt(speed['attackComponents']['swiftness'])} "
        f"+ 질량 증가 ({fmt(speed['attackComponents']['massIncrease'])}) "
        f"+ 전투 축복 {fmt(speed['attackComponents']['combatBlessing'])} "
        f"+ 만찬 {fmt(speed['attackComponents']['feast'])} "
        f"+ 질풍노도 {fmt(speed['attackComponents']['gale'])} "
        f"+ 아크그리드 코어 {fmt(speed['attackComponents']['arkGridCore'])} "
        f"= {fmt(speed['rawAttackSpeed'])}`",
        "",
        f"- 원시 공격속도 증가량: `{pct_fmt(speed['rawAttackSpeedIncrease'])}`",
        f"- 140% 상한 적용 공격속도: `{fmt(speed['cappedAttackSpeed'])}`",
        f"- 상한 적용 증가량: `{pct_fmt(speed['cappedAttackSpeedIncrease'])}`",
        "",
        "이동속도 구성:",
        "",
        f"`1 + 신속 {fmt(speed['moveComponents']['swiftness'])} "
        f"+ 전투 축복 {fmt(speed['moveComponents']['combatBlessing'])} "
        f"+ 만찬 {fmt(speed['moveComponents']['feast'])} "
        f"+ 질풍노도 {fmt(speed['moveComponents']['gale'])} "
        f"+ 아크그리드 코어 {fmt(speed['moveComponents']['arkGridCore'])} "
        f"= {fmt(speed['rawMoveSpeed'])}`",
        "",
        f"- 원시 이동속도 증가량: `{pct_fmt(speed['rawMoveSpeedIncrease'])}`",
        f"- 140% 상한 적용 이동속도: `{fmt(speed['cappedMoveSpeed'])}`",
        f"- 상한 적용 증가량: `{pct_fmt(speed['cappedMoveSpeedIncrease'])}`",
        "",
        f"음속 돌파 Lv.{sonic_detail['level']} 상세:",
        "",
        f"`기본분 = {fmt(sonic_detail['baseRate'])} × "
        f"[min({fmt(sonic_detail['attackSpeedIncrease'])}, 0.4) + "
        f"min({fmt(sonic_detail['moveSpeedIncrease'])}, 0.4)]`",
        "",
        f"`= {fmt(sonic_detail['baseRate'])} × "
        f"({fmt(sonic_detail['baseAttackInput'])} + "
        f"{fmt(sonic_detail['baseMoveInput'])}) "
        f"= {fmt(sonic_detail['baseDamage'])} "
        f"({pct_fmt(sonic_detail['baseDamage'])})`",
        "",
        f"- 공격·이동속도 모두 상한 초과: "
        f"`{'예' if sonic_detail['bothSpeedsExceededCap'] else '아니오'}`",
        f"- 양쪽 상한 초과 보너스: "
        f"`{pct_fmt(sonic_detail['bothExceededBonus'])}`",
        "",
        f"`초과분 = {fmt(sonic_detail['overCapRate'])} × "
        f"[{fmt(sonic_detail['attackOverCap'])} + "
        f"{fmt(sonic_detail['moveOverCap'])}] "
        f"= {fmt(sonic_detail['overCapDamage'])} "
        f"({pct_fmt(sonic_detail['overCapDamage'])})`",
        "",
        f"`상한 적용 전 합계 = {fmt(sonic_detail['baseDamage'])} + "
        f"{fmt(sonic_detail['bothExceededBonus'])} + "
        f"{fmt(sonic_detail['overCapDamage'])} "
        f"= {fmt(sonic_detail['uncappedTotal'])}`",
        "",
        f"`최종 음속 돌파 = min({fmt(sonic_detail['uncappedTotal'])}, "
        f"{fmt(sonic_detail['maximum'])}) = {fmt(sonic_detail['final'])} "
        f"({pct_fmt(sonic_detail['final'])})`",
        "",
        f"- 최대값 제한 발동: "
        f"`{'예' if sonic_detail['limitedByMaximum'] else '아니오'}`",
        "",
        "### 1.5 추가 피해",
        "",
        f"`1 + 무기 {fmt(i['weaponAdditionalDamage'])} + 목걸이 "
        f"{fmt(i['necklaceAdditionalDamage'])} + 기타 장비 "
        f"{fmt(i['otherAdditionalDamage'])} + 아크 패시브 "
        f"{fmt(i['arkPassiveAdditionalDamage'])} + 펫 {fmt(i['petAdditionalDamage'])} + "
        f"아크그리드 {fmt(i['arkGridAdditionalDamage'])} = "
        f"{fmt(dg['additionalDamageMultiplier'])}`",
        "",
        "### 1.5.1 일반 보석 스킬 효과",
        "",
        f"- 대상 스킬: `{regular_gem['skillName']}`",
        f"- 스킬 피해 증가: `{pct_fmt(regular_gem['damagePercent'])}` "
        "(아래 독립 피해 소제목에 적용)",
        f"- 재사용 대기시간 감소: "
        f"`{pct_fmt(regular_gem['cooldownReductionPercent'])}`",
        f"- 쿨다운 배율: `{fmt(regular_gem['cooldownMultiplier'])}` "
        "(1회 피해에는 미적용, 로테이션/DPS 입력으로 보존)",
        "",
        "### 1.5.2 선택 트라이포드 효과",
        "",
        "각 모션 타격은 출처를 구분합니다. 기본 타격에 없는 트라이포드 효과는 "
        "별도 배율로 적용하고, 트라이포드로 생성된 타격의 모션식이 제공된 경우 "
        "그 타격 자체로 한 번만 적용합니다.",
        "",
        "| 트라이포드 | 파싱된 효과 | 1회 피해 적용 |",
        "|---|---|---|",
    ]
    selected_tripods = c["skillModel"].get("selectedTripods", [])
    embedded_effects = c["skillModel"].get(
        "embeddedTripodDamageEffects", []
    )
    if selected_tripods:
        for tripod in selected_tripods:
            effects: list[str] = []
            modes: list[str] = []
            for effect in tripod.get("damageEffects", []):
                is_embedded = any(
                    embedded["tripodName"] == tripod["name"]
                    and embedded["type"] == effect["type"]
                    and embedded["percent"] == effect["percent"]
                    for embedded in embedded_effects
                )
                if is_embedded:
                    effects.append(
                        f"{effect['label']} {pct_fmt(effect['percent'])} "
                        "(별도 모션 타격)"
                    )
                    modes.append("모션식으로 적용")
                else:
                    effects.append(
                        f"{effect['label']} {pct_fmt(effect['percent'])} "
                        f"(`×{fmt(effect['multiplier'])}`)"
                    )
                    modes.append("배율 적용")
            critical_value = dec(tripod.get("criticalDamagePercent"))
            if critical_value:
                effects.append(f"치명타 피해 +{pct_fmt(critical_value)}")
                modes.append("치명타 피해 합산")
            lines.append(
                f"| {tripod['name']} | "
                f"{'; '.join(effects) if effects else '공격속도·조작 등 비피해 효과'} | "
                f"{', '.join(dict.fromkeys(modes)) if modes else '제외'} |"
            )
    else:
        lines.append("| 없음 | 선택 트라이포드 없음 | 해당 없음 |")
    lines += [
        "",
        f"- 트라이포드 피해 배율 합계: "
        f"`×{fmt(c['skillModel']['tripodDamageMultiplier'])}`",
        f"- 트라이포드 치명타 피해 합계: "
        f"`+{pct_fmt(c['skillModel']['tripodCriticalDamage'])}`",
        "- 별도 모션식이 없는 추가 공격만 툴팁의 총 추가 피해율을 스킬 전체에 "
        "곱합니다. 별도 모션 타격이 있으면 추가 배율을 중복 적용하지 않습니다.",
        "",
        "### 1.6 서로 곱하는 피해 소제목",
        "",
        "| 소제목 | 증가율 | 배율 |",
        "|---|---:|---:|",
    ]
    for item in dg["subtitles"]:
        lines.append(
            f"| {item['name']} | {pct_fmt(item['percent'])} | {fmt(item['multiplier'])} |"
        )
    lines += [
        "",
        f"`전체 소제목 배율 = {' × '.join(fmt(x['multiplier']) for x in dg['subtitles'])} "
        f"= {fmt(dg['totalSubtitleMultiplier'])}`",
        "",
        "진화형 피해 내부 합산:",
        "",
    ]
    for part in dg["evolutionParts"]:
        lines.append(f"- {part['name']}: {pct_fmt(part['value'])}")

    lines += [
        "",
        "### 1.7 적 보정",
        "",
        f"`유효 방어력 = {fmt(enemy['defense'])} × "
        f"(1 - {fmt(enemy['defenseReductionPercent'])}) = "
        f"{fmt(enemy['effectiveDefense'])}`",
        "",
        f"`방어력 보정 = {fmt(enemy['defenseConstant'])} ÷ "
        f"({fmt(enemy['defenseConstant'])} + {fmt(enemy['effectiveDefense'])}) = "
        f"{fmt(enemy['defenseMultiplier'])}`",
        "",
        f"`적 받는 피해 배율 = {fmt(enemy['damageTakenMultiplier'])}`",
        "",
        "### 1.8 비치명타",
        "",
        "| 타격 | 모션 계수 | 모션 상수 | 사용 공격력 | 스킬 본체 |",
        "|---|---:|---:|---:|---:|",
    ]
    for hit in damage["hits"]:
        lines.append(
            f"| {hit['name']} | {fmt(hit['coefficient'])} | "
            f"{fmt(hit['constant'])} | {fmt(ap['usedForDamage'])} "
            f"({ap['usedForDamageSource']}) | {fmt(hit['skillBaseRaw'])} |"
        )
    coefficient_multiplier = c["skillModel"]["motionCoefficientMultiplier"]
    if coefficient_multiplier != 1:
        coefficient_changes = ", ".join(
            f"{hit['name']} {fmt(hit['originalCoefficient'])} → "
            f"{fmt(hit['coefficient'])}"
            for hit in damage["hits"]
        )
        lines += [
            "",
            f"- 모션계수 상향: `×{fmt(coefficient_multiplier)}` "
            f"({coefficient_changes}); 모션상수는 유지",
        ]
    lines += [
        "",
        f"`스킬 본체 합계 = {' + '.join(fmt(hit['skillBaseRaw']) for hit in damage['hits'])} "
        f"= {fmt(damage['skillBaseRaw'])}`",
        "",
        f"`비치명타 원시값 = {fmt(damage['skillBaseRaw'])} × "
        f"{fmt(dg['additionalDamageMultiplier'])} × "
        f"{fmt(dg['totalSubtitleMultiplier'])} × "
        f"{fmt(enemy['damageTakenMultiplier'])} × {fmt(enemy['defenseMultiplier'])} "
        f"= {fmt(damage['nonCriticalRaw'])}`",
        "",
        f"`floor({fmt(damage['nonCriticalRaw'])}) = {fmt(damage['nonCritical'])}`",
        "",
        "### 1.9 치명타와 기대 피해",
        "",
        "치명타율 계산:",
        "",
        f"`원시 치명타율 = 치명 스탯 {pct_fmt(crit['rateComponents']['criticalStat'])} + "
        f"장비 {pct_fmt(crit['rateComponents']['equipment'])} + "
        f"아드레날린 {pct_fmt(crit['rateComponents']['adrenaline'])} + "
        f"아크 패시브 {pct_fmt(crit['rateComponents']['arkPassive'])} + "
        f"급소 노출 {pct_fmt(crit['rateComponents']['exposedWeakness'])} + "
        f"아크그리드 {pct_fmt(crit['rateComponents']['arkGrid'])} = "
        f"{pct_fmt(crit['rateRaw'])}`",
        "",
        f"- 원시 치명타율: `{pct_fmt(crit['rateRaw'])}`",
        f"- 상한 적용 치명타율: `{pct_fmt(crit['rateCapped'])}`",
        "",
        "치명타 피해 배율 계산:",
        "",
        f"`치명타 피해 배율 = 기본 {fmt(crit['damageComponents']['base'])} + "
        f"장비 {fmt(crit['damageComponents']['equipment'])} + "
        f"아크 패시브 {fmt(crit['damageComponents']['arkPassive'])} + "
        f"아크그리드 {fmt(crit['damageComponents']['arkGrid'])} + "
        f"스킬 트라이포드 {fmt(crit['damageComponents']['skillTripod'])} = "
        f"{fmt(crit['damageMultiplier'])}`",
        "",
        f"- 스킬 트라이포드 치명타 피해: "
        f"`{pct_fmt(crit['skillTripodCriticalDamage'])}`",
        f"- 치명타 피해 배율: `{fmt(crit['damageMultiplier'])}`",
        f"`치명타 시 피해 증가 배율 = 회심 "
        f"{fmt(crit['criticalHitDamageFactors']['master'])} × 팔찌 "
        f"{fmt(crit['criticalHitDamageFactors']['bracelet'])} × 아크그리드 "
        f"{fmt(crit['criticalHitDamageFactors']['arkGrid'])} = "
        f"{fmt(crit['criticalHitDamageMultiplier'])}`",
        f"- 치명타 시 피해 증가 배율: `{fmt(crit['criticalHitDamageMultiplier'])}`",
        "",
        f"`치명타 원시값 = {fmt(damage['nonCriticalRaw'])} × "
        f"{fmt(crit['damageMultiplier'])} × "
        f"{fmt(crit['criticalHitDamageMultiplier'])} = {fmt(damage['criticalRaw'])}`",
        "",
        f"`기대 피해 원시값 = {fmt(damage['criticalRaw'])} × "
        f"{fmt(crit['rateCapped'])} + {fmt(damage['nonCriticalRaw'])} × "
        f"(1 - {fmt(crit['rateCapped'])}) = {fmt(damage['expectedRaw'])}`",
        "",
        "## 2. 계산 결과",
        "",
        "| 타격 | 비치명타 | 치명타 | 기대 피해 |",
        "|---|---:|---:|---:|",
    ]
    for hit in damage["hits"]:
        lines.append(
            f"| {hit['name']} | {fmt(hit['nonCritical'])} | "
            f"{fmt(hit['critical'])} | {fmt(hit['expected'])} |"
        )
    lines += [
        "",
        f"- 비치명타 피해: **{fmt(damage['nonCritical'])}**",
        f"- 치명타 피해: **{fmt(damage['critical'])}**",
        f"- 기대 피해: **{fmt(damage['expected'])}**",
        f"- 치명타율: **{pct_fmt(crit['rateCapped'])}**",
    ]

    lines += [
        "",
        "### 스킬 범위 판정",
        "",
        f"- 스킬 태그: `{', '.join(c['skillModel']['tags'])}` "
        f"({c['skillModel']['tagVerification']})",
    ]
    if "NON_DIRECTIONAL" in c["skillModel"]["tags"]:
        lines.append(
            "- `NON_DIRECTIONAL` 태그가 있으므로 비방향성 스킬로 "
            "확정하여 계산했습니다."
        )
    if c["skillScope"]:
        for item in c["skillScope"]:
            status = "적용" if item["applied"] else "제외"
            lines.append(
                f"- {item['name']} {pct_fmt(item['value'])}: **{status}** "
                f"({item['reason']})"
            )
    else:
        lines.append("- 판정할 스킬 전용 아크 패시브 효과 없음")
    if c["skillName"] == SPACE_CUTTING_SKILL:
        lines += [
            "- `공간 가르기` 피해 +200%는 1타와 2타에 동일하게 적용했습니다.",
            "- `풀려난 힘`, `단련된 가르기`는 현재 스킬의 전용 범위가 "
            "아니어서 제외했습니다.",
        ]
        if any(
            item["name"] == "타격의 대가"
            for item in dg["engravingParts"]
        ):
            lines.append(
                "- `NON_DIRECTIONAL` 태그에 따라 `타격의 대가`를 "
                "적용했습니다."
            )
        lines += [
            "",
            "### 공간 가르기 실측 오차 반영",
            "",
            "- 다른 스킬과 공통인 공격력·각인·카드·방어력·아크그리드 "
            "계산은 실측과 오차 범위 내에서 맞으므로, 공통 배율보다 "
            "공간 가르기 전용 입력을 우선 의심해야 합니다.",
            "- 공간 가르기에는 피해 보석이 없는 것이 정상이며, 보석 누락은 "
            "원인 후보에서 제외했습니다.",
            "- 2026-02-11 밸런스 패치의 공간 가르기 피해량 +29.20%를 "
            "반영하기 위해 1타·2타 모션계수만 `+29.20%` 했습니다. "
            "모션상수는 기존 값을 유지했습니다.",
            "- 유효 모션계수는 1타 `51.77`, 2타 `120.80`입니다.",
            "- 두 번째 후보는 제공된 1타·2타 모션식에 포함되지 않은 추가 "
            "타격 또는 후속 검풍입니다. 실측에서 1타·2타 피해 숫자를 각각 "
            "기록하면 계수 노후화와 누락 타격을 구분할 수 있습니다.",
            "- `NON_DIRECTIONAL` 태그로 타격의 대가는 이미 적용되므로 "
            "방향성 판정 누락은 원인이 아닙니다.",
            "- 이 보정은 `current-v2.7.2`에 공식 적용했습니다.",
        ]

    lines += [
        "",
        "## 3. 제외 및 경고",
        "",
        "### 제외된 데이터",
        "",
    ]
    if parsed["excluded"]:
        for item in parsed["excluded"]:
            lines.append(
                f"- `{item['path']}` {item['label']}: {item.get('note') or '미적용'}"
            )
    else:
        lines.append("- 없음")
    lines += ["", "### 경고", ""]
    if parsed["warnings"]:
        for warning in parsed["warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("- 없음")
    lines += [
        "",
        "## 4. 검증 결과",
        "",
        "- 과거 스펙의 최종 피해와 회귀 비교하지 않았습니다.",
        "- 원본 API 경로와 각 파싱값을 출처 표로 연결했습니다.",
        "- 초월, 비활성 아크그리드 젬, 서포터 옵션, 미지원 효과는 제외 목록에서 확인할 수 있습니다.",
        "- 아크그리드 활성 젬·누적 효과(Effects[])와 코어별 활성 임계 효과를 구조화해 검증했습니다.",
        "- 출처마다 parsed / eligible / applied / excludedReason 상태를 분리했습니다.",
        "- fallback 사용 내역은 내부 파싱 결과의 `fallbacks`와 계산별 `provenance.fallbacks`에 구조화했습니다.",
        (
            "- `우뢰바람`은 입력 별칭으로만 허용하고 결과에는 `우레바람`을 사용했습니다."
            if c["skillName"] == CANONICAL_SKILL
            else "- `공간가르기` 입력은 결과에서 `공간 가르기`로 정규화했습니다."
        ),
        (
            "- 최종 비치명타·치명타·기대 피해 외에는 버림을 적용하지 않았습니다."
            if not c["intermediateFloorStages"]
            else "- 선택한 엑셀 호환 규칙의 지정 중간 단계와 최종 피해에 버림을 적용했습니다."
        ),
        "",
    ]
    lines += source_lines
    lines.append("")
    return "\n".join(lines)


def validate(parsed: dict[str, Any], without_grid: dict[str, Any], with_grid: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if canonical_skill("우뢰바람") != CANONICAL_SKILL:
        failures.append("스킬 별칭 정규화 실패")
    if with_grid["damage"]["nonCritical"] != int(
        with_grid["damage"]["nonCriticalRaw"].to_integral_value(rounding=ROUND_FLOOR)
    ):
        failures.append("비치명타 최종 버림 검증 실패")
    if with_grid["damage"]["critical"] != int(
        with_grid["damage"]["criticalRaw"].to_integral_value(rounding=ROUND_FLOOR)
    ):
        failures.append("치명타 최종 버림 검증 실패")
    if with_grid["damage"]["expected"] != int(
        with_grid["damage"]["expectedRaw"].to_integral_value(rounding=ROUND_FLOOR)
    ):
        failures.append("기대 피해 최종 버림 검증 실패")
    if with_grid["ruleVersion"] != without_grid["ruleVersion"]:
        failures.append("아크그리드 전후 계산 규칙 버전 불일치")
    rules = get_rules(with_grid["ruleVersion"])
    for stage, block in (
        ("mainStat", with_grid["mainStat"]),
        ("weaponAttack", with_grid["weaponAttack"]),
        ("attackPower", with_grid["attackPower"]),
    ):
        expected = apply_stage_rounding(
            block["rawBeforeStageRounding"], stage, rules
        )
        if block["final"] != expected:
            failures.append(f"{stage} 중간 버림 정책 검증 실패")
    if with_grid["inputs"]["arkGridAttackPowerPercent"] != parsed["arkGrid"]["attackPowerPercent"]:
        failures.append("아크그리드 공격력 연결 실패")
    if parsed["arkGrid"]["attackPowerPercent"] != (
        parsed["arkGrid"]["effectiveBaseEffects"]["attackPowerPercent"]
        + parsed["arkGrid"]["coreEffects"]["attackPowerPercent"]
    ):
        failures.append("아크그리드 권위 기본 효과/코어 공격력 합산 실패")
    if parsed["arkGrid"]["additionalDamagePercent"] != (
        parsed["arkGrid"]["effectiveBaseEffects"]["additionalDamagePercent"]
        + parsed["arkGrid"]["coreEffects"]["additionalDamagePercent"]
    ):
        failures.append("아크그리드 권위 기본 효과/코어 추가 피해 합산 실패")
    if parsed["arkGrid"]["bossDamagePercent"] != (
        parsed["arkGrid"]["effectiveBaseEffects"]["bossDamagePercent"]
        + parsed["arkGrid"]["coreEffects"]["bossDamagePercent"]
    ):
        failures.append("아크그리드 권위 기본 효과/코어 보스 피해 합산 실패")
    for key in ARKGRID_CORE_TOTAL_KEYS:
        if key in {
            "attackPowerPercent",
            "additionalDamagePercent",
            "bossDamagePercent",
        }:
            continue
        if parsed["arkGrid"][key] != parsed["arkGrid"]["coreEffects"][key]:
            failures.append(f"아크그리드 코어 {key} 합산 실패")
    if without_grid["inputs"]["arkGridAttackPowerPercent"] != 0:
        failures.append("아크그리드 미적용 계산에 공격력 효과가 남아 있음")
    if without_grid["inputs"]["arkGridAdditionalDamage"] != 0:
        failures.append("아크그리드 미적용 계산에 추가 피해 효과가 남아 있음")
    for key in (
        "arkGridCoreWeaponAttackFlat",
        "arkGridCoreWeaponAttackPercent",
        "arkGridCoreAttackPowerFlat",
        "arkGridCoreGeneralDamagePercent",
        "arkGridCoreSkillDamagePercent",
        "arkGridCoreCriticalRate",
        "arkGridCoreCriticalDamage",
        "arkGridCoreCriticalHitDamagePercent",
        "arkGridCoreEnemyDefenseReductionPercent",
    ):
        if without_grid["inputs"][key] != 0:
            failures.append(f"아크그리드 미적용 계산에 {key} 효과가 남아 있음")
    profile_attack = parsed["profile"]["profileAttackPower"]
    calculated_attack = with_grid["attackPower"]["final"]
    expected_damage_attack = calculated_attack
    if (
        not rules.get("useCalculatedAttackForDamage", False)
        and profile_attack > 0
        and profile_attack != calculated_attack
    ):
        expected_damage_attack = profile_attack
    if with_grid["damage"]["attackPowerUsed"] != expected_damage_attack:
        failures.append("프로필/재구성 공격력 선택 규칙 검증 실패")
    skill_model = get_skill_model(with_grid["skillName"])
    effective_hits = effective_skill_hits(with_grid["skillName"], rules)
    expected_skill_base = sum(
        (
            hit["coefficient"] * expected_damage_attack + hit["constant"]
            for hit in effective_hits
        ),
        Decimal("0"),
    )
    if with_grid["damage"]["skillBaseRaw"] != expected_skill_base:
        failures.append("선택 공격력의 스킬 본체 연결 실패")
    if with_grid["damage"]["hitCount"] != len(effective_hits):
        failures.append("스킬 타격 수 연결 실패")
    expected_tripod_multiplier = Decimal("1")
    for effect in with_grid["skillModel"].get("tripodDamageEffects", []):
        expected_tripod_multiplier *= Decimal("1") + dec(effect["percent"])
    if (
        with_grid["skillModel"].get("tripodDamageMultiplier")
        != expected_tripod_multiplier
    ):
        failures.append("선택 트라이포드 피해 배율 합산 실패")
    if rules.get("applyAllSelectedTripodDamage", False):
        applied_tripod_values = [
            item["value"]
            for item in with_grid["damageGroups"]["tripodDamageParts"]
        ]
        parsed_tripod_values = [
            item["percent"]
            for item in with_grid["skillModel"].get("tripodDamageEffects", [])
        ]
        if applied_tripod_values != parsed_tripod_values:
            failures.append("선택 트라이포드 전체 피해 효과 연결 실패")
    if rules.get("deduplicateEmbeddedTripodHits", False):
        hit_tripod_sources = {
            hit.get("tripodSource")
            for hit in with_grid["damage"]["hits"]
            if hit.get("tripodSource")
        }
        for effect in with_grid["skillModel"].get(
            "embeddedTripodDamageEffects", []
        ):
            if effect["tripodName"] not in hit_tripod_sources:
                failures.append(
                    f"{effect['tripodName']} 내장 트라이포드 타격 연결 실패"
                )
            if effect in with_grid["skillModel"].get(
                "tripodDamageEffects", []
            ):
                failures.append(
                    f"{effect['tripodName']} 내장 트라이포드 배율 중복 적용"
                )
    for hit_result, hit_model in zip(
        with_grid["damage"]["hits"], effective_hits
    ):
        expected_hit_base = (
            hit_model["coefficient"] * expected_damage_attack
            + hit_model["constant"]
        )
        if hit_result["skillBaseRaw"] != expected_hit_base:
            failures.append(f"{hit_result['name']} 스킬 본체 연결 실패")
        for raw_key, final_key, label in (
            ("nonCriticalRaw", "nonCritical", "비치명타"),
            ("criticalRaw", "critical", "치명타"),
            ("expectedRaw", "expected", "기대 피해"),
        ):
            expected_floor = int(
                hit_result[raw_key].to_integral_value(rounding=ROUND_FLOOR)
            )
            if hit_result[final_key] != expected_floor:
                failures.append(
                    f"{hit_result['name']} {label} 최종 버림 검증 실패"
                )
    for key in ("nonCriticalRaw", "criticalRaw", "expectedRaw"):
        hit_sum = sum(
            (hit[key] for hit in with_grid["damage"]["hits"]),
            Decimal("0"),
        )
        if hit_sum != with_grid["damage"][key]:
            failures.append(f"타격별 {key} 합계 검증 실패")
    for item in parsed["arkGrid"]["excluded"]:
        if item.get("applied") is not False:
            failures.append(f"제외 아크그리드 데이터가 적용됨: {item.get('path')}")
        if item.get("eligible") is not False:
            failures.append(f"제외 아크그리드 데이터가 적용 가능으로 표시됨: {item.get('path')}")
    return failures


def make_paths(
    output_dir: Path,
    character: str,
    rule_version: str,
    skill_name: str = CANONICAL_SKILL,
) -> tuple[Path, Path, Path]:
    safe_character = re.sub(r'[<>:"/\\|?*]', "_", character)
    safe_skill = re.sub(r'[<>:"/\\|?*]', "_", canonical_skill(skill_name))
    safe_version = re.sub(r'[^A-Za-z0-9._-]', "_", rule_version)
    stem = f"{safe_character}_{safe_skill}_{safe_version}"
    return (
        output_dir / f"{stem}_api_raw.json",
        output_dir / f"{stem}_parsed.json",
        output_dir / f"{stem}_계산보고서.md",
    )


def build_rule_manifest() -> dict[str, Any]:
    return {
        "calculatorVersion": CALCULATOR_VERSION,
        "parserVersion": PARSER_VERSION,
        "parsedSchemaVersion": PARSED_SCHEMA_VERSION,
        "defaultRuleVersion": DEFAULT_RULE_VERSION,
        "dbRelease": DB_RELEASE,
        "scenarioPresetId": SCENARIO_PRESET_ID,
        "calculationMode": CALCULATION_MODE,
        "precedence": [
            "explicit_user_rule",
            "live_api_description",
            "workbook_formula",
            "example_fallback_db",
        ],
        "versions": RULESETS,
        "workbookFormulaEvidence": WORKBOOK_FORMULA_EVIDENCE,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--character", default=CHARACTER_NAME)
    parser.add_argument(
        "--skill",
        choices=tuple(SKILL_MODELS),
        default=CANONICAL_SKILL,
        help="계산할 스킬",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument(
        "--rules-version",
        choices=tuple(RULESETS),
        default=DEFAULT_RULE_VERSION,
        help="버전별 계산 규칙 선택",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        help="공식 API 호출 대신 기존 raw bundle JSON을 사용",
    )
    parser.add_argument(
        "--emit-debug-json",
        action="store_true",
        help=(
            "사용자용 보고서와 별도로 *_api_raw.json 및 *_parsed.json "
            "디버그 산출물을 생성"
        ),
    )
    args = parser.parse_args()
    raw_path, parsed_path, report_path = make_paths(
        args.output_dir, args.character, args.rules_version, args.skill
    )
    write_json(
        args.output_dir / "데미지_계산규칙_versions.json",
        build_rule_manifest(),
    )

    if args.snapshot:
        raw_bundle = json.loads(args.snapshot.read_text(encoding="utf-8"))
        responses = response_from_raw_bundle(raw_bundle)
        if args.emit_debug_json:
            write_json(raw_path, raw_bundle)
    else:
        token = os.environ.get("LOSTARK_API_TOKEN", "")
        if not token.strip():
            print(
                "ERROR: LOSTARK_API_TOKEN 환경변수가 없습니다. "
                "토큰은 로그나 파일에 저장되지 않습니다.",
                file=sys.stderr,
            )
            return 2
        raw_bundle, responses = fetch_all(token, args.character)
        if args.emit_debug_json:
            write_json(raw_path, raw_bundle)

    parsed = parse_all(responses, args.character, args.skill)
    without_grid = calculate(
        parsed,
        include_arkgrid=False,
        rule_version=args.rules_version,
        skill_name=args.skill,
    )
    with_grid = calculate(
        parsed,
        include_arkgrid=True,
        rule_version=args.rules_version,
        skill_name=args.skill,
    )
    failures = validate(parsed, without_grid, with_grid)
    parsed["calculations"] = {
        "ruleVersion": args.rules_version,
        "withoutArkGridEffects": without_grid,
        "withArkGridEffects": with_grid,
        "renamedKeys": {
            "withoutArkGridGemEffects": "withoutArkGridEffects",
            "withArkGridGemEffects": "withArkGridEffects",
        },
    }
    parsed["validation"] = {"passed": not failures, "failures": failures}
    if args.emit_debug_json:
        write_json(parsed_path, parsed)
    report = render_report(
        raw_bundle,
        parsed,
        without_grid,
        with_grid,
        raw_path if args.emit_debug_json else None,
        parsed_path if args.emit_debug_json else None,
    )
    report_path.write_text(report, encoding="utf-8", newline="\n")

    if failures:
        print("검증 실패:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    if args.emit_debug_json:
        print(f"디버그 API 원본: {raw_path.resolve()}")
        print(f"디버그 파싱 결과: {parsed_path.resolve()}")
    print(f"계산 보고서: {report_path.resolve()}")
    print(
        "결과: "
        f"비치명타={with_grid['damage']['nonCritical']:,}, "
        f"치명타={with_grid['damage']['critical']:,}, "
        f"기대={with_grid['damage']['expected']:,}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
