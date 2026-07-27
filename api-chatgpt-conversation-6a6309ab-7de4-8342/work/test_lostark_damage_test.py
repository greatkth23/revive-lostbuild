#!/usr/bin/env python3
"""Offline structural tests. These do not compare old and live damage values."""

import json
import copy
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

import lostark_damage_test as dut


def tip(text: str) -> str:
    return json.dumps({"Element_000": {"value": text}}, ensure_ascii=False)


def fixture_responses():
    return {
        "profiles": {
            "CharacterName": "봄날꽃씨",
            "CharacterClassName": "기상술사",
            "CharacterLevel": 70,
            "ExpeditionLevel": 300,
            "ItemAvgLevel": "1,800.00",
            "Stats": [
                {
                    "Type": "치명",
                    "Value": "845",
                    "Tooltip": ["치명타 적중률이 30.24% 증가합니다."],
                },
                {
                    "Type": "신속",
                    "Value": "1631",
                    "Tooltip": [
                        "공격 속도가 28.01% 증가합니다.",
                        "이동 속도가 28.01% 증가합니다.",
                    ],
                },
                {"Type": "공격력", "Value": "210000", "Tooltip": []},
            ],
        },
        "equipment": [
            {
                "Type": "무기",
                "Name": "테스트 무기",
                "Grade": "고대",
                "Tooltip": tip(
                    "기본 효과<br>지능 +100000<br>무기 공격력 +235,480"
                    "<br>추가 피해 +30.00%<br>초월 7단계"
                ),
            },
            {
                "Type": "목걸이",
                "Name": "테스트 목걸이",
                "Grade": "고대",
                "Tooltip": tip("지능 +10000<br>추가 피해 +2.60%<br>적에게 주는 피해 +1.20%"),
            },
            {
                "Type": "귀걸이",
                "Name": "테스트 귀걸이 1",
                "Grade": "고대",
                "Tooltip": tip("지능 +10000<br>무기 공격력 +3.00%<br>공격력 +0.95%"),
            },
            {
                "Type": "귀걸이",
                "Name": "테스트 귀걸이 2",
                "Grade": "고대",
                "Tooltip": tip("지능 +10000<br>무기 공격력 +3.00%<br>공격력 +0.95%"),
            },
            {
                "Type": "반지",
                "Name": "테스트 반지 1",
                "Grade": "고대",
                "Tooltip": tip("지능 +10000<br>치명타 적중률 +1.55%<br>치명타 피해 +2.40%"),
            },
            {
                "Type": "반지",
                "Name": "테스트 반지 2",
                "Grade": "고대",
                "Tooltip": tip("지능 +10000<br>치명타 적중률 +1.55%<br>치명타 피해 +2.40%"),
            },
            {
                "Type": "팔찌",
                "Name": "테스트 팔찌",
                "Grade": "고대",
                "Tooltip": tip(
                    "지능 +13376<br>추가 피해 +3.50%<br>치명타 적중률 +5.00%<br>"
                    "적에게 주는 피해가 4.50% 증가<br>치명타 피해가 6.80% 증가<br>"
                    "공격이 치명타로 적중 시 적에게 주는 피해가 1.50% 증가<br>"
                    "비방향성 공격 피해가 +2.50%"
                ),
            },
            {
                "Type": "어빌리티 스톤",
                "Name": "테스트 스톤",
                "Grade": "고대",
                "Tooltip": tip("기본 공격력 +1.50%"),
            },
            {
                "Type": "투구",
                "Name": "회심 투구",
                "Grade": "고대",
                "Tooltip": tip("지능 +10000<br>회심 (질서)"),
            },
        ],
        "avatars": [
            {
                "Type": "상의",
                "Name": "외부 상의",
                "Grade": "영웅",
                "IsInner": False,
                "Tooltip": "",
            },
            {
                "Type": "상의",
                "Name": "효과 상의",
                "Grade": "전설",
                "IsInner": True,
                "Tooltip": "",
            },
            {
                "Type": "하의",
                "Name": "효과 하의",
                "Grade": "전설",
                "IsInner": True,
                "Tooltip": "",
            },
        ],
        "combatSkills": [
            {
                "Name": "펼치기",
                "Tripods": [
                    {
                        "Name": "급소 노출",
                        "Tier": 1,
                        "IsSelected": True,
                        "Tooltip": "치명타 저항률 10% 감소",
                    }
                ],
            }
        ],
        "engravings": {
            "ArkPassiveEffects": [
                {"Name": "원한", "Level": 0, "AbilityStoneLevel": 2, "Description": ""},
                {
                    "Name": "아드레날린",
                    "Level": 0,
                    "AbilityStoneLevel": 3,
                    "Description": "",
                },
                {"Name": "돌격대장", "Level": 0, "AbilityStoneLevel": 0, "Description": ""},
                {"Name": "질량 증가", "Level": 0, "AbilityStoneLevel": 0, "Description": ""},
                {"Name": "타격의 대가", "Level": 0, "AbilityStoneLevel": 0, "Description": ""},
                {"Name": "질풍노도", "Level": 0, "AbilityStoneLevel": 0, "Description": ""},
            ]
        },
        "cards": {
            "Cards": [{"Name": "테스트 카드"}],
            "Effects": [
                {
                    "Items": [
                        {"Name": "세트 효과", "Description": "적에게 주는 피해가 15.00% 증가"}
                    ]
                }
            ],
        },
        "gems": {
            "Gems": [
                {
                    "Slot": 0,
                    "Name": "9레벨 광휘의 보석",
                    "Level": 9,
                    "Grade": "고대",
                    "Tooltip": tip("추가 효과<br>기본 공격력 1.00% 증가"),
                }
            ]
        },
        "arkPassive": {
            "Points": [
                {"Name": "진화", "Value": 120, "Description": "카르마 진화형 피해가 6.0% 증가"},
                {"Name": "깨달음", "Value": 100, "Description": "무기 공격력이 2.7% 증가"},
            ],
            "Effects": [
                {"Name": "한계 돌파 Lv.3", "Description": ""},
                {"Name": "무한한 마력 Lv.1", "Description": ""},
                {"Name": "혼신의 강타 Lv.1", "Description": ""},
                {"Name": "분쇄 Lv.1", "Description": ""},
                {"Name": "정열의 춤 II", "Description": ""},
                {"Name": "음속 돌파 Lv.2", "Description": ""},
                {"Name": "풀려난 힘 Lv.1", "Description": ""},
                {"Name": "바람의 길 Lv.2", "Description": ""},
                {"Name": "기민함 Lv.3", "Description": ""},
                {"Name": "단련된 가르기 Lv.3", "Description": ""},
            ],
        },
        "arkGrid": {
            "Slots": [
                {
                    "Index": 0,
                    "Point": 20,
                    "Gems": [
                        {
                            "Index": 0,
                            "Grade": "고대",
                            "IsActive": True,
                            "Tooltip": tip(
                                "고유 효과<br>공격력 +1.20%<br>추가 피해 +2.00%<br>"
                                "보스에게 주는 피해 +3.00%"
                            ),
                        },
                        {
                            "Index": 1,
                            "Grade": "고대",
                            "IsActive": False,
                            "Tooltip": tip("공격력 +99.00%"),
                        },
                        {
                            "Index": 2,
                            "Grade": "고대",
                            "IsActive": True,
                            "Tooltip": tip("낙인력 +5.00%<br>아군 공격력 강화 +4.00%"),
                        },
                    ],
                }
            ],
            "Effects": [{"Name": "포인트 효과", "Level": 2, "Tooltip": "피해 증가"}],
        },
    }


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.parsed = dut.parse_all(fixture_responses())

    def test_canonical_name(self):
        self.assertEqual(dut.canonical_skill("우뢰바람"), "우레바람")

    def test_equipment_and_tooltip_values(self):
        equipment = self.parsed["equipment"]
        self.assertEqual(equipment["baseWeaponAttack"], Decimal("235480"))
        self.assertEqual(equipment["weaponAttackPercent"], Decimal("0.06"))
        self.assertEqual(equipment["attackPowerPercent"], Decimal("0.019"))
        self.assertEqual(equipment["weaponAdditionalDamage"], Decimal("0.30"))
        self.assertEqual(equipment["necklaceAdditionalDamage"], Decimal("0.026"))
        self.assertEqual(equipment["otherAdditionalDamage"], Decimal("0.035"))
        self.assertEqual(equipment["criticalRate"], Decimal("0.081"))
        self.assertEqual(equipment["criticalDamage"], Decimal("0.116"))
        self.assertEqual(equipment["braceletCriticalHitDamage"], Decimal("0.015"))
        self.assertEqual(equipment["braceletNonDirectionalDamage"], Decimal("0.025"))
        self.assertEqual(equipment["braceletDamageToEnemy"], Decimal("0.045"))
        self.assertTrue(equipment["hasMasterElixir"])
        self.assertTrue(any(x["label"] == "초월" for x in equipment["excluded"]))
        self.assertEqual(self.parsed["cards"]["damagePercent"], Decimal("0.15"))

    def test_avatar_inner_precedence(self):
        self.assertEqual(self.parsed["avatars"]["mainStatPercent"], Decimal("0.04"))
        selected_names = [x["raw"] for x in self.parsed["avatars"]["selected"]]
        self.assertTrue(any("효과 상의" in name for name in selected_names))
        self.assertFalse(any("외부 상의" in name for name in selected_names))

    def test_arkgrid_inclusion_and_exclusion(self):
        grid = self.parsed["arkGrid"]
        self.assertEqual(grid["attackPowerPercent"], Decimal("0.012"))
        self.assertEqual(grid["additionalDamagePercent"], Decimal("0.02"))
        self.assertEqual(grid["bossDamagePercent"], Decimal("0.03"))
        labels = [x["label"] for x in grid["excluded"]]
        self.assertIn("비활성 아크그리드 젬", labels)
        self.assertIn("낙인력", labels)
        self.assertIn("포인트 효과", labels)

    def test_calculation_toggle_and_floor(self):
        before = dut.calculate(self.parsed, include_arkgrid=False)
        after = dut.calculate(self.parsed, include_arkgrid=True)
        self.assertEqual(before["inputs"]["arkGridAttackPowerPercent"], 0)
        self.assertEqual(before["inputs"]["arkGridAdditionalDamage"], 0)
        self.assertEqual(after["inputs"]["arkGridAttackPowerPercent"], Decimal("0.012"))
        self.assertGreater(after["damage"]["nonCritical"], before["damage"]["nonCritical"])
        self.assertEqual(
            after["damage"]["nonCritical"],
            int(after["damage"]["nonCriticalRaw"].to_integral_value(rounding=dut.ROUND_FLOOR)),
        )
        self.assertFalse(dut.validate(self.parsed, before, after))

    def test_speed_and_sonic_breakdown(self):
        result = dut.calculate(self.parsed, include_arkgrid=True)
        speed = result["speed"]
        self.assertEqual(
            sum(speed["attackComponents"].values(), Decimal("0")),
            speed["rawAttackSpeed"],
        )
        self.assertEqual(
            sum(speed["moveComponents"].values(), Decimal("0")),
            speed["rawMoveSpeed"],
        )
        sonic = speed["sonicBreakthroughBreakdown"]
        self.assertEqual(
            sonic["uncappedTotal"],
            sonic["baseDamage"]
            + sonic["bothExceededBonus"]
            + sonic["overCapDamage"],
        )
        self.assertEqual(
            sonic["final"],
            min(sonic["uncappedTotal"], sonic["maximum"]),
        )

    def test_versioned_rounding_and_sonic_rules(self):
        current = dut.calculate(
            self.parsed,
            include_arkgrid=True,
            rule_version="current-v2.1.0",
        )
        workbook = dut.calculate(
            self.parsed,
            include_arkgrid=True,
            rule_version="season3-xlsx-v2.0.0",
        )
        self.assertEqual(current["intermediateFloorStages"], [])
        self.assertIn("attackPower", workbook["intermediateFloorStages"])
        self.assertEqual(
            workbook["attackPower"]["final"],
            workbook["attackPower"]["rawBeforeStageRounding"].to_integral_value(
                rounding=dut.ROUND_FLOOR
            ),
        )
        current_sonic = dut.sonic_breakthrough_breakdown(
            2, Decimal("1.45"), Decimal("1.50"), "current-v2.1.0"
        )
        workbook_sonic = dut.sonic_breakthrough_breakdown(
            2, Decimal("1.45"), Decimal("1.50"), "season3-xlsx-v2.0.0"
        )
        self.assertEqual(current_sonic["overCapRate"], Decimal("0.30"))
        self.assertEqual(workbook_sonic["overCapRate"], Decimal("0.20"))
        self.assertGreater(current_sonic["final"], workbook_sonic["final"])

    def test_live_engraving_descriptions_override_example_values(self):
        responses = copy.deepcopy(fixture_responses())
        effects = responses["engravings"]["ArkPassiveEffects"]
        by_name = {entry["Name"]: entry for entry in effects}
        by_name["원한"]["Description"] = (
            "보스 및 레이드 몬스터에게 주는 피해가 21.00% 증가한다."
        )
        by_name["아드레날린"]["Description"] = (
            "스킬 사용 후 공격력이 1.50% 증가하며 (최대 6중첩) "
            "최대 중첩 시 치명타 적중률이 추가로 20.00% 증가한다."
        )
        by_name["질량 증가"]["Description"] = (
            "공격속도가 10.00% 감소하지만, 적에게 주는 피해가 19.00% 증가한다."
        )
        by_name["돌격대장"]["Description"] = (
            "이동속도 증가량의 48.00% 만큼 적에게 주는 피해량이 증가한다."
        )
        effects.append(
            {
                "Name": "저주받은 인형",
                "Level": 4,
                "AbilityStoneLevel": 0,
                "Description": "적에게 주는 피해가 22.25% 증가한다.",
            }
        )
        parsed = dut.parse_all(responses)
        result = dut.calculate(
            parsed,
            include_arkgrid=True,
            rule_version="current-v2.1.0",
        )
        self.assertEqual(
            result["inputs"]["adrenalineAttackPowerPercent"],
            Decimal("0.09"),
        )
        engraving_values = {
            item["name"]: item["value"]
            for item in result["damageGroups"]["engravingParts"]
        }
        self.assertEqual(engraving_values["원한"], Decimal("0.21"))
        self.assertEqual(
            engraving_values["저주받은 인형"], Decimal("0.2225")
        )
        self.assertEqual(engraving_values["질량 증가"], Decimal("0.19"))
        raid = next(
            item
            for item in result["damageGroups"]["subtitles"]
            if item["name"] == "돌격대장"
        )
        self.assertEqual(raid["percent"], Decimal("0.192"))

    def test_flat_weapon_and_attack_power_are_parsed(self):
        responses = copy.deepcopy(fixture_responses())
        responses["equipment"].append(
            {
                "Type": "팔찌",
                "Name": "평면 수치 테스트",
                "Grade": "고대",
                "Tooltip": tip("무기 공격력 +123<br>공격력 +456"),
            }
        )
        parsed = dut.parse_all(responses)
        self.assertEqual(
            parsed["equipment"]["weaponAttackFlat"], Decimal("123")
        )
        self.assertEqual(
            parsed["equipment"]["attackPowerFlat"], Decimal("456")
        )
        flat_sources = [
            item
            for item in parsed["equipment"]["sources"]
            if item["label"].endswith("weaponAttackFlat")
        ]
        self.assertEqual(len(flat_sources), 1)

    def test_report_can_be_rendered(self):
        before = dut.calculate(self.parsed, include_arkgrid=False)
        after = dut.calculate(self.parsed, include_arkgrid=True)
        raw = {
            "capturedAtKst": "2026-07-25T00:00:00+09:00",
            "endpoints": {},
            "responses": fixture_responses(),
        }
        report = dut.render_report(
            raw,
            self.parsed,
            before,
            after,
            Path("raw.json"),
            Path("parsed.json"),
        )
        self.assertIn("비치명타 피해", report)
        self.assertIn("과거 스펙의 최종 피해와 회귀 비교하지 않았습니다.", report)


if __name__ == "__main__":
    unittest.main()
