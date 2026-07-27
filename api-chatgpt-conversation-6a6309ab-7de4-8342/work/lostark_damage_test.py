#!/usr/bin/env python3
"""우레바람 Lost Ark Open API parsing and damage calculation.

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
from decimal import Decimal, ROUND_FLOOR, getcontext
from pathlib import Path
from typing import Any, Iterable


getcontext().prec = 40

API_BASE = "https://developer-lostark.game.onstove.com"
CHARACTER_NAME = "봄날꽃씨"
CANONICAL_SKILL = "우레바람"
SKILL_ALIASES = {"우뢰바람": CANONICAL_SKILL, CANONICAL_SKILL: CANONICAL_SKILL}
CALCULATOR_VERSION = "2.1.0"
PARSED_SCHEMA_VERSION = "2.0.0"
DEFAULT_RULE_VERSION = "current-v2.1.0"

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
    applied: bool = True,
    note: str = "",
) -> dict[str, Any]:
    return {
        "sourceType": source_type,
        "path": path,
        "label": label,
        "value": value,
        "raw": raw,
        "applied": applied,
        "note": note,
    }


def canonical_skill(name: str) -> str:
    return SKILL_ALIASES.get(name, name)


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
                rf"(?:보스\s*및\s*레이드\s*몬스터에게|적에게)\s*주는\s*"
                rf"피해(?:량)?(?:이|가)?\s*(?:\+)?{PERCENT}(?:\s*증가)?",
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


def parse_gems(body: dict[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    body = body or {}
    total_base_attack = Decimal("0")
    sources: list[dict[str, Any]] = []
    gems: list[dict[str, Any]] = []
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
        parsed = {
            "slot": gem.get("Slot"),
            "name": gem.get("Name"),
            "level": gem.get("Level"),
            "grade": gem.get("Grade"),
            "baseAttackPercent": value,
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
    return {"baseAttackPercent": total_base_attack, "gems": gems, "sources": sources}


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


def parse_ark_passive(body: dict[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    body = body or {}
    effects: dict[str, dict[str, Any]] = {}
    sources: list[dict[str, Any]] = []
    evolution_by_name: dict[str, Decimal] = {}
    skill_damage_by_name: dict[str, Decimal] = {}
    critical_rate_by_name: dict[str, Decimal] = {}
    critical_damage_by_name: dict[str, Decimal] = {}
    critical_hit_damage_by_name: dict[str, Decimal] = {}
    additional_damage_by_name: dict[str, Decimal] = {}
    speed_by_name: dict[str, dict[str, Decimal]] = {}

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
        if matched in {"바람의 길", "풀려난 힘", "단련된 가르기"}:
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
            warn_once(
                warnings,
                f"{matched} 현재 수치를 툴팁에서 파싱하지 못해 예시값 "
                f"{fallback['evolutionDamage'] * 100}%를 사용했습니다.",
            )
        if not skill_damage and fallback.get("skillDamage"):
            skill_damage_by_name[matched] = fallback["skillDamage"]
            warn_once(
                warnings,
                f"{matched} 현재 수치를 툴팁에서 파싱하지 못해 예시값 "
                f"{fallback['skillDamage'] * 100}%를 사용했습니다.",
            )
        if not critical_rate and fallback.get("criticalRate") and matched != "기민함":
            critical_rate_by_name[matched] = fallback["criticalRate"]
        if not critical_hit_damage and fallback.get("criticalHitDamage"):
            critical_hit_damage_by_name[matched] = fallback["criticalHitDamage"]
        if not attack_move_speed and (
            fallback.get("attackSpeed") or fallback.get("moveSpeed")
        ):
            speed_by_name[matched] = {
                "attackSpeed": fallback.get("attackSpeed", Decimal("0")),
                "moveSpeed": fallback.get("moveSpeed", Decimal("0")),
            }

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
        sources.append(
            source(
                source_type="API_FIELD",
                path=f"arkPassive.Effects[{index}]",
                label=matched,
                value=level or 0,
                raw=description,
            )
        )

    karma_weapon_attack = Decimal("0")
    karma_evolution = Decimal("0")
    points: list[dict[str, Any]] = []
    for index, point in enumerate(body.get("Points") or []):
        name = str(point.get("Name") or "")
        text = tooltip_to_text(point.get("Description") or point.get("Tooltip"))
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
            if weapon_values:
                karma_weapon_attack = max(weapon_values)
            elif text:
                karma_weapon_attack = Decimal("0.027")
                warn_once(
                    warnings,
                    "깨달음 카르마 수치를 파싱하지 못해 예시값 +2.7%를 사용했습니다.",
                )
        if "진화" in name or "진화" in text:
            if evolution_values:
                karma_evolution = max(evolution_values)
            elif text and ("카르마" in text or "랭크" in text):
                karma_evolution = Decimal("0.06")
                warn_once(
                    warnings,
                    "진화 카르마 수치를 파싱하지 못해 예시값 +6.0%를 사용했습니다.",
                )
        points.append({"name": name, "value": point.get("Value"), "text": text})
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
                selected_tripods.append(
                    {"skill": skill_name, "name": tripod_name, "tier": tripod.get("Tier")}
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


def parse_ark_grid(body: dict[str, Any] | None, warnings: list[str]) -> dict[str, Any]:
    body = body or {}
    attack = Decimal("0")
    additional = Decimal("0")
    boss = Decimal("0")
    active: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for slot_index, slot in enumerate(body.get("Slots") or []):
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
            attack_values = [
                pct(v)
                for v in find_numbers(
                    scrubbed,
                    rf"(?<!무기\s)(?<!아군\s)(?:^|\s)공격력(?:이)?\s*(?:\+|증가\s*)?{PERCENT}",
                    re.M,
                )
            ]
            additional_values = [
                pct(v)
                for v in find_numbers(
                    scrubbed, rf"추가\s*피해(?:가|량이)?\s*(?:\+|증가\s*)?{PERCENT}"
                )
            ]
            boss_values = [
                pct(v)
                for v in find_numbers(
                    scrubbed,
                    rf"(?:보스에게\s*주는\s*피해|보스\s*피해)(?:가|량이)?\s*(?:\+|증가\s*)?{PERCENT}",
                )
            ]
            parsed_attack = max_or_zero(attack_values)
            parsed_additional = max_or_zero(additional_values)
            parsed_boss = max_or_zero(boss_values)
            attack += parsed_attack
            additional += parsed_additional
            boss += parsed_boss
            base["values"] = {
                "attackPowerPercent": parsed_attack,
                "additionalDamagePercent": parsed_additional,
                "bossDamagePercent": parsed_boss,
            }
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
    # Point-based Effects are deliberately preserved only as exclusions.
    for index, effect in enumerate(body.get("Effects") or []):
        excluded.append(
            source(
                source_type="API_FIELD",
                path=f"arkGrid.Effects[{index}]",
                label=str(effect.get("Name") or "아크그리드 포인트 효과"),
                value=effect.get("Level") or 0,
                raw=tooltip_to_text(effect.get("Tooltip")),
                applied=False,
                note="이번 범위에서는 포인트 활성 효과 제외",
            )
        )
    return {
        "attackPowerPercent": attack,
        "additionalDamagePercent": additional,
        "bossDamagePercent": boss,
        "activeGems": active,
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
) -> dict[str, Any]:
    rules = get_rules(rule_version)
    warnings = parsed["warnings"]
    assumptions: list[dict[str, Any]] = []
    equipment = parsed["equipment"]
    profile = parsed["profile"]
    engravings = parsed["engravings"]
    ark = parsed["arkPassive"]
    grid = parsed["arkGrid"]

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
    weapon_attack_subtotal = equipment["baseWeaponAttack"] + weapon_attack_flat
    weapon_attack_percent = (
        equipment["weaponAttackPercent"] + ark["karmaWeaponAttackPercent"]
    )
    final_weapon_attack_raw = weapon_attack_subtotal * (
        Decimal("1") + weapon_attack_percent
    )
    final_weapon_attack = apply_stage_rounding(
        final_weapon_attack_raw, "weaponAttack", rules
    )

    base_attack_percent = (
        parsed["gems"]["baseAttackPercent"] + engravings["stoneBaseAttackPercent"]
    )
    if final_main_stat < 0 or final_weapon_attack < 0:
        raise CalculationError("주스탯 또는 무기 공격력이 음수입니다.")
    root_attack = (final_main_stat * final_weapon_attack / Decimal("6")).sqrt()
    root_with_base_attack_percent = root_attack * (
        Decimal("1") + base_attack_percent
    )
    attack_power_flat = (
        equipment["attackPowerFlat"]
        if rules["includeFlatAttackPower"]
        else Decimal("0")
    )
    base_attack = root_with_base_attack_percent + attack_power_flat

    adrenaline_attack = resolved_engraving_value(
        "아드레날린",
        "attackPowerPercent",
        parsed,
        assumptions,
        rules,
    )
    arkgrid_attack = grid["attackPowerPercent"] if include_arkgrid else Decimal("0")
    attack_power_percent = (
        equipment["attackPowerPercent"] + adrenaline_attack + arkgrid_attack
    )
    final_attack_raw = base_attack * (
        Decimal("1") + attack_power_percent
    )
    final_attack = apply_stage_rounding(
        final_attack_raw, "attackPower", rules
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
    raw_attack_speed = (
        Decimal("1")
        + profile["attackSpeedFromSwiftness"]
        + mass_speed
        + rules["combatBlessingAttackSpeedPercent"]
        + rules["feastAttackSpeedPercent"]
        + gale_attack
    )
    raw_move_speed = (
        Decimal("1")
        + profile["moveSpeedFromSwiftness"]
        + rules["combatBlessingMoveSpeedPercent"]
        + rules["feastMoveSpeedPercent"]
        + gale_move
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
        value = resolved_engraving_value(
            engraving_name,
            "generalDamage",
            parsed,
            assumptions,
            rules,
        )
        if value:
            general_engraving_damage.append((engraving_name, value))
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
                    f"{engraving_name} 피해 수치는 API에서 읽었지만 우레바람 적용 범위가 "
                    "미등록되어 계산에서 제외했습니다.",
                )
    released = ark["skillDamageByName"].get("풀려난 힘", Decimal("0"))
    wind_path = ark["skillDamageByName"].get("바람의 길", Decimal("0"))
    disciplined = ark["skillDamageByName"].get("단련된 가르기", Decimal("0"))
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
    if not master_critical and equipment["hasMasterElixir"]:
        master_critical = EXAMPLE_EFFECT_DB["회심"]["criticalHitDamage"]
    if master_critical:
        assumptions.append(
            source(
                source_type="API_TOOLTIP+EXAMPLE_DB",
                path="equipment[*].Tooltip",
                label="회심 치명타 시 피해",
                value=master_critical,
                raw="회심 문자열 확인",
            )
        )

    demon_damage = (
        FIXED["petDemonDamagePercent"] + FIXED["collectionDemonDamagePercent"]
    )
    card_damage = parsed["cards"]["damagePercent"]
    boss_damage = grid["bossDamagePercent"] if include_arkgrid else Decimal("0")
    subtitle_percentages = [
        *general_engraving_damage,
        ("진화형 피해", evolution_percent),
        ("악마 추가 피해", demon_damage),
        ("카드 피해", card_damage),
        ("돌격대장", raid_captain),
        ("풀려난 힘", released),
        ("바람의 길", wind_path),
        ("목걸이 적에게 주는 피해", equipment["necklaceDamageToEnemy"]),
        ("팔찌 적에게 주는 피해", equipment["braceletDamageToEnemy"]),
        ("기타 적에게 주는 피해", equipment["otherDamageToEnemy"]),
        ("단련된 가르기", disciplined),
        ("팔찌 비방향성 피해", equipment["braceletNonDirectionalDamage"]),
        ("아크그리드 보스 피해", boss_damage),
    ]
    subtitle_multipliers = [
        (name, Decimal("1") + value) for name, value in subtitle_percentages
    ]
    total_damage_multiplier = Decimal("1")
    for _, multiplier in subtitle_multipliers:
        total_damage_multiplier *= multiplier

    skill_base = FIXED["skillCoefficient"] * final_attack + FIXED["skillConstant"]
    defense_multiplier = FIXED["defenseConstant"] / (
        FIXED["defenseConstant"] + FIXED["enemyDefense"]
    )
    noncritical_raw = (
        skill_base
        * additional_damage_multiplier
        * total_damage_multiplier
        * FIXED["enemyDamageTakenMultiplier"]
        * defense_multiplier
    )

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
    )
    critical_rate = min(Decimal("1"), max(Decimal("0"), critical_rate_raw))
    critical_damage = (
        FIXED["baseCriticalDamage"]
        + equipment["criticalDamage"]
        + sum(ark["criticalDamageByName"].values(), Decimal("0"))
    )
    critical_hit_damage_multiplier = (
        Decimal("1") + master_critical
    ) * (Decimal("1") + equipment["braceletCriticalHitDamage"])
    critical_raw = (
        noncritical_raw * critical_damage * critical_hit_damage_multiplier
    )
    expected_raw = (
        critical_raw * critical_rate
        + noncritical_raw * (Decimal("1") - critical_rate)
    )

    return {
        "calculatorVersion": CALCULATOR_VERSION,
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
            "equipmentWeaponAttackFlat": weapon_attack_flat,
            "equipmentWeaponAttackPercent": equipment["weaponAttackPercent"],
            "karmaWeaponAttackPercent": ark["karmaWeaponAttackPercent"],
            "regularGemBaseAttackPercent": parsed["gems"]["baseAttackPercent"],
            "stoneBaseAttackPercent": engravings["stoneBaseAttackPercent"],
            "equipmentAttackPowerFlat": attack_power_flat,
            "equipmentAttackPowerPercent": equipment["attackPowerPercent"],
            "adrenalineAttackPowerPercent": adrenaline_attack,
            "arkGridAttackPowerPercent": arkgrid_attack,
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
        },
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
            },
            "moveComponents": {
                "base": Decimal("1"),
                "swiftness": profile["moveSpeedFromSwiftness"],
                "combatBlessing": rules[
                    "combatBlessingMoveSpeedPercent"
                ],
                "feast": rules["feastMoveSpeedPercent"],
                "gale": gale_move,
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
            "subtitles": [
                {"name": name, "percent": percent, "multiplier": Decimal("1") + percent}
                for name, percent in subtitle_percentages
            ],
            "totalSubtitleMultiplier": total_damage_multiplier,
        },
        "critical": {
            "rateRaw": critical_rate_raw,
            "rateCapped": critical_rate,
            "damageMultiplier": critical_damage,
            "criticalHitDamageMultiplier": critical_hit_damage_multiplier,
        },
        "enemy": {
            "defense": FIXED["enemyDefense"],
            "defenseConstant": FIXED["defenseConstant"],
            "defenseMultiplier": defense_multiplier,
            "damageTakenMultiplier": FIXED["enemyDamageTakenMultiplier"],
            "species": "악마",
        },
        "damage": {
            "skillBaseRaw": skill_base,
            "nonCriticalRaw": noncritical_raw,
            "criticalRaw": critical_raw,
            "expectedRaw": expected_raw,
            "nonCritical": int(noncritical_raw.to_integral_value(rounding=ROUND_FLOOR)),
            "critical": int(critical_raw.to_integral_value(rounding=ROUND_FLOOR)),
            "expected": int(expected_raw.to_integral_value(rounding=ROUND_FLOOR)),
        },
        "assumptions": assumptions,
    }


def parse_all(
    responses: dict[str, Any], character: str = CHARACTER_NAME
) -> dict[str, Any]:
    warnings: list[str] = []
    parsed = {
        "schemaVersion": PARSED_SCHEMA_VERSION,
        "calculatorVersion": CALCULATOR_VERSION,
        "availableRuleVersions": list(RULESETS),
        "defaultRuleVersion": DEFAULT_RULE_VERSION,
        "characterName": character,
        "canonicalSkillName": CANONICAL_SKILL,
        "aliases": ["우뢰바람"],
        "warnings": warnings,
    }
    parsed["profile"] = parse_profile(responses.get("profiles"), warnings)
    parsed["equipment"] = parse_equipment(responses.get("equipment"), warnings)
    parsed["avatars"] = parse_avatars(responses.get("avatars"), warnings)
    parsed["engravings"] = parse_engravings(responses.get("engravings"), warnings)
    parsed["cards"] = parse_cards(responses.get("cards"), warnings)
    parsed["gems"] = parse_gems(responses.get("gems"), warnings)
    parsed["arkPassive"] = parse_ark_passive(responses.get("arkPassive"), warnings)
    parsed["combatSkills"] = parse_combat_skills(responses.get("combatSkills"))
    parsed["arkGrid"] = parse_ark_grid(responses.get("arkGrid"), warnings)
    parsed["excluded"] = (
        parsed["equipment"]["excluded"]
        + parsed["avatars"]["excluded"]
        + parsed["arkGrid"]["excluded"]
    )
    return parsed


def fmt(value: Any, places: int | None = None) -> str:
    if isinstance(value, Decimal):
        if places is not None:
            return f"{value:.{places}f}"
        return format(value, "f")
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def pct_fmt(value: Decimal, places: int = 4) -> str:
    return f"{value * 100:.{places}f}%"


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
        result.extend(block.get("sources") or block.get("selected") or [])
    return result


def render_report(
    raw_bundle: dict[str, Any],
    parsed: dict[str, Any],
    without_grid: dict[str, Any],
    with_grid: dict[str, Any],
    raw_path: Path,
    parsed_path: Path,
) -> str:
    p = parsed
    c = with_grid
    lines: list[str] = [
        f"# {p['profile'].get('characterName') or p['characterName']} 우레바람 API 파싱·피해 계산 보고서",
        "",
        f"- API 스냅샷: `{raw_bundle.get('capturedAtKst')}`",
        f"- 캐릭터: `{p['profile'].get('characterName')}` / `{p['profile'].get('className')}`",
        f"- 아이템 레벨: `{p['profile'].get('itemLevel')}`",
        f"- 계산 스킬: `{CANONICAL_SKILL}` 최대 홀딩",
        f"- 계산기 버전: `{c['calculatorVersion']}`",
        f"- 규칙 버전: `{c['ruleVersion']}` — {c['ruleLabel']}",
        f"- 규칙 출처: `{c['ruleSource']}`",
        f"- 중간 버림 단계: `{', '.join(c['intermediateFloorStages']) or '없음'}`",
        f"- API 원본: [{raw_path.name}]({raw_path.name})",
        f"- 파싱 결과: [{parsed_path.name}]({parsed_path.name})",
        "- 과거 피해값과의 회귀검증은 수행하지 않았습니다.",
        "",
        "## 1. API 호출 결과",
        "",
        "| 엔드포인트 | HTTP | 호출 시각(KST) | 남은 호출량 |",
        "|---|---:|---|---:|",
    ]
    for key, meta in (raw_bundle.get("endpoints") or {}).items():
        lines.append(
            f"| `{key}` | {meta.get('status')} | {meta.get('capturedAtKst')} | "
            f"{(meta.get('rateLimit') or {}).get('remaining')} |"
        )

    lines += [
        "",
        "전체 응답 본문은 API 원본 JSON에 엔드포인트별 `rawBody`와 파싱된 `responses`로 보존했습니다. Authorization 헤더는 저장하지 않았습니다.",
        "",
        "### 핵심 원본 데이터 발췌",
        "",
        "```json",
        json.dumps(
            json_ready(
                {
                    "profile": {
                        "CharacterName": (raw_bundle["responses"].get("profiles") or {}).get(
                            "CharacterName"
                        ),
                        "CharacterLevel": (raw_bundle["responses"].get("profiles") or {}).get(
                            "CharacterLevel"
                        ),
                        "ExpeditionLevel": (
                            raw_bundle["responses"].get("profiles") or {}
                        ).get("ExpeditionLevel"),
                        "CharacterClassName": (
                            raw_bundle["responses"].get("profiles") or {}
                        ).get("CharacterClassName"),
                        "ItemAvgLevel": (
                            raw_bundle["responses"].get("profiles") or {}
                        ).get("ItemAvgLevel"),
                        "Stats": (raw_bundle["responses"].get("profiles") or {}).get(
                            "Stats"
                        ),
                    },
                    "equipmentCount": len(
                        raw_bundle["responses"].get("equipment") or []
                    ),
                    "gemCount": len(
                        (raw_bundle["responses"].get("gems") or {}).get("Gems") or []
                    ),
                    "arkGrid": raw_bundle["responses"].get("arkGrid"),
                }
            ),
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## 2. 파싱 결과와 출처",
        "",
        "| 값 | 정규화 결과 | 출처 | 적용 |",
        "|---|---:|---|---|",
    ]
    for item in report_sources(parsed):
        raw_short = re.sub(r"\s+", " ", str(item.get("raw") or ""))[:120]
        label = str(item.get("label") or "").replace("|", "\\|")
        path = str(item.get("path") or "").replace("|", "\\|")
        note = str(item.get("note") or "")
        applied = "예" if item.get("applied", True) else "아니오"
        value = item.get("value")
        lines.append(
            f"| {label} | `{fmt(value)}` | `{path}`"
            f"{'<br>' + raw_short if raw_short else ''}"
            f"{'<br>' + note if note else ''} | {applied} |"
        )

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

    lines += [
        "",
        "## 3. 계산 과정",
        "",
        (
            "모든 중간값은 소수로 유지했습니다. 아래 세 최종 표시 피해에서만 "
            "`floor`를 적용했습니다."
            if not c["intermediateFloorStages"]
            else "엑셀 원본 호환을 위해 다음 중간 단계에도 `floor`를 적용했습니다: "
            + ", ".join(c["intermediateFloorStages"])
        ),
        "",
        "### 3.1 주스탯",
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
        "### 3.2 무기 공격력",
        "",
        f"`무기 공격력 증가 = {pct_fmt(i['equipmentWeaponAttackPercent'])} + "
        f"{pct_fmt(i['karmaWeaponAttackPercent'])} = {pct_fmt(wa['percent'])}`",
        "",
        f"`무기 공격력 소계 = 기본 {fmt(i['baseWeaponAttack'])} + "
        f"평면 증가 {fmt(i['equipmentWeaponAttackFlat'])} = "
        f"{fmt(wa['subtotalBeforePercent'])}`",
        "",
        f"`최종 무기 공격력 원시값 = {fmt(wa['subtotalBeforePercent'])} × "
        f"(1 + {fmt(wa['percent'])}) = {fmt(wa['rawBeforeStageRounding'])}`",
        "",
        f"`규칙 적용 최종 무기 공격력 = {fmt(wa['final'])}`",
        "",
        "### 3.3 기본 공격력과 최종 공격력",
        "",
        f"`sqrt({fmt(ms['final'])} × {fmt(wa['final'])} ÷ 6) = "
        f"{fmt(ap['rootBeforeBaseAttackPercent'])}`",
        "",
        f"`기본 공격력 증가 = 보석 {pct_fmt(i['regularGemBaseAttackPercent'])} + "
        f"스톤 {pct_fmt(i['stoneBaseAttackPercent'])} = "
        f"{pct_fmt(ap['baseAttackPercent'])}`",
        "",
        f"`루트 공격력 × 기본 공격력% = {fmt(ap['rootBeforeBaseAttackPercent'])} × "
        f"(1 + {fmt(ap['baseAttackPercent'])}) = "
        f"{fmt(ap['afterBaseAttackPercent'])}`",
        "",
        f"`기본 공격력 단계 = {fmt(ap['afterBaseAttackPercent'])} + "
        f"공격력 평면 증가 {fmt(ap['flatAttackPower'])} = {fmt(ap['base'])}`",
        "",
        f"`공격력 증가 = 장신구 {pct_fmt(i['equipmentAttackPowerPercent'])} + "
        f"아드레날린 {pct_fmt(i['adrenalineAttackPowerPercent'])} + "
        f"아크그리드 {pct_fmt(i['arkGridAttackPowerPercent'])} = "
        f"{pct_fmt(ap['finalAttackPercent'])}`",
        "",
        f"`최종 공격력 원시값 = {fmt(ap['base'])} × "
        f"(1 + {fmt(ap['finalAttackPercent'])}) = "
        f"{fmt(ap['rawBeforeStageRounding'])}`",
        "",
        f"`규칙 적용 최종 공격력 = {fmt(ap['final'])}`",
        "",
        f"API 프로필 공격력은 `{fmt(ap['profileValueForComparison'])}`이며 계산값과의 차이는 "
        f"`{fmt(ap['differenceFromProfile'])}`입니다. 이는 고정 예시값·최대 조건을 적용한 이론값과 "
        "조회 시점 프로필 값의 비교일 뿐, 어느 한쪽을 강제로 맞추지 않았습니다.",
        "",
        "### 3.4 공격·이동속도 및 음속 돌파",
        "",
        "공격속도 구성:",
        "",
        f"`1 + 신속 {fmt(speed['attackComponents']['swiftness'])} "
        f"+ 질량 증가 ({fmt(speed['attackComponents']['massIncrease'])}) "
        f"+ 전투 축복 {fmt(speed['attackComponents']['combatBlessing'])} "
        f"+ 만찬 {fmt(speed['attackComponents']['feast'])} "
        f"+ 질풍노도 {fmt(speed['attackComponents']['gale'])} "
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
        "### 3.5 추가 피해",
        "",
        f"`1 + 무기 {fmt(i['weaponAdditionalDamage'])} + 목걸이 "
        f"{fmt(i['necklaceAdditionalDamage'])} + 기타 장비 "
        f"{fmt(i['otherAdditionalDamage'])} + 아크 패시브 "
        f"{fmt(i['arkPassiveAdditionalDamage'])} + 펫 {fmt(i['petAdditionalDamage'])} + "
        f"아크그리드 {fmt(i['arkGridAdditionalDamage'])} = "
        f"{fmt(dg['additionalDamageMultiplier'])}`",
        "",
        "### 3.6 서로 곱하는 피해 소제목",
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
        "### 3.7 적 보정",
        "",
        f"`방어력 보정 = {fmt(enemy['defenseConstant'])} ÷ "
        f"({fmt(enemy['defenseConstant'])} + {fmt(enemy['defense'])}) = "
        f"{fmt(enemy['defenseMultiplier'])}`",
        "",
        f"`적 받는 피해 배율 = {fmt(enemy['damageTakenMultiplier'])}`",
        "",
        "### 3.8 비치명타",
        "",
        f"`스킬 본체 = 351.262 × {fmt(ap['final'])} + 52,583 = "
        f"{fmt(damage['skillBaseRaw'])}`",
        "",
        f"`비치명타 원시값 = {fmt(damage['skillBaseRaw'])} × "
        f"{fmt(dg['additionalDamageMultiplier'])} × "
        f"{fmt(dg['totalSubtitleMultiplier'])} × "
        f"{fmt(enemy['damageTakenMultiplier'])} × {fmt(enemy['defenseMultiplier'])} "
        f"= {fmt(damage['nonCriticalRaw'])}`",
        "",
        f"`floor({fmt(damage['nonCriticalRaw'])}) = {fmt(damage['nonCritical'])}`",
        "",
        "### 3.9 치명타와 기대 피해",
        "",
        f"- 원시 치명타율: `{pct_fmt(crit['rateRaw'])}`",
        f"- 상한 적용 치명타율: `{pct_fmt(crit['rateCapped'])}`",
        f"- 치명타 피해 배율: `{fmt(crit['damageMultiplier'])}`",
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
        "## 4. 계산 결과",
        "",
        f"- 비치명타 피해: **{fmt(damage['nonCritical'])}**",
        f"- 치명타 피해: **{fmt(damage['critical'])}**",
        f"- 기대 피해: **{fmt(damage['expected'])}**",
        f"- 치명타율: **{pct_fmt(crit['rateCapped'])}**",
        "",
        "### 아크그리드 젬 적용 전후",
        "",
        "| 결과 | 미적용 | 적용 | 차이 |",
        "|---|---:|---:|---:|",
    ]
    for key, label in (
        ("nonCritical", "비치명타"),
        ("critical", "치명타"),
        ("expected", "기대 피해"),
    ):
        before = without_grid["damage"][key]
        after = with_grid["damage"][key]
        lines.append(f"| {label} | {before:,} | {after:,} | {after-before:+,} |")

    lines += [
        "",
        "## 5. 제외 및 경고",
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
        "## 6. 검증 결과",
        "",
        "- 과거 스펙의 최종 피해와 회귀 비교하지 않았습니다.",
        "- 원본 API 경로와 각 파싱값을 출처 표로 연결했습니다.",
        "- 초월, 비활성 아크그리드 젬, 서포터 젬 옵션, 포인트 효과는 제외 목록에서 확인할 수 있습니다.",
        "- 아크그리드 적용 전후 계산을 별도로 수행했습니다.",
        "- `우뢰바람`은 입력 별칭으로만 허용하고 결과에는 `우레바람`을 사용했습니다.",
        (
            "- 최종 비치명타·치명타·기대 피해 외에는 버림을 적용하지 않았습니다."
            if not c["intermediateFloorStages"]
            else "- 선택한 엑셀 호환 규칙의 지정 중간 단계와 최종 피해에 버림을 적용했습니다."
        ),
        "",
    ]
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
    if without_grid["inputs"]["arkGridAttackPowerPercent"] != 0:
        failures.append("아크그리드 미적용 계산에 공격력 젬이 남아 있음")
    if without_grid["inputs"]["arkGridAdditionalDamage"] != 0:
        failures.append("아크그리드 미적용 계산에 추가 피해 젬이 남아 있음")
    for item in parsed["arkGrid"]["excluded"]:
        if item.get("applied") is not False:
            failures.append(f"제외 아크그리드 데이터가 적용됨: {item.get('path')}")
    return failures


def make_paths(
    output_dir: Path, character: str, rule_version: str
) -> tuple[Path, Path, Path]:
    safe_character = re.sub(r'[<>:"/\\|?*]', "_", character)
    safe_version = re.sub(r'[^A-Za-z0-9._-]', "_", rule_version)
    stem = f"{safe_character}_우레바람_{safe_version}"
    return (
        output_dir / f"{stem}_api_raw.json",
        output_dir / f"{stem}_parsed.json",
        output_dir / f"{stem}_계산보고서.md",
    )


def build_rule_manifest() -> dict[str, Any]:
    return {
        "calculatorVersion": CALCULATOR_VERSION,
        "parsedSchemaVersion": PARSED_SCHEMA_VERSION,
        "defaultRuleVersion": DEFAULT_RULE_VERSION,
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
    args = parser.parse_args()
    raw_path, parsed_path, report_path = make_paths(
        args.output_dir, args.character, args.rules_version
    )
    write_json(
        args.output_dir / "데미지_계산규칙_versions.json",
        build_rule_manifest(),
    )

    if args.snapshot:
        raw_bundle = json.loads(args.snapshot.read_text(encoding="utf-8"))
        responses = response_from_raw_bundle(raw_bundle)
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
        write_json(raw_path, raw_bundle)

    parsed = parse_all(responses, args.character)
    without_grid = calculate(
        parsed,
        include_arkgrid=False,
        rule_version=args.rules_version,
    )
    with_grid = calculate(
        parsed,
        include_arkgrid=True,
        rule_version=args.rules_version,
    )
    failures = validate(parsed, without_grid, with_grid)
    parsed["calculations"] = {
        "ruleVersion": args.rules_version,
        "withoutArkGridGemEffects": without_grid,
        "withArkGridGemEffects": with_grid,
    }
    parsed["validation"] = {"passed": not failures, "failures": failures}
    write_json(parsed_path, parsed)
    if args.snapshot and not raw_path.exists():
        write_json(raw_path, raw_bundle)
    report = render_report(
        raw_bundle, parsed, without_grid, with_grid, raw_path, parsed_path
    )
    report_path.write_text(report, encoding="utf-8")

    if failures:
        print("검증 실패:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"API 원본: {raw_path.resolve()}")
    print(f"파싱 결과: {parsed_path.resolve()}")
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
