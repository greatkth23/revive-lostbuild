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
                },
                {
                    "Slot": 1,
                    "Name": "9레벨 겁화의 보석",
                    "Level": 9,
                    "Grade": "유물",
                    "Tooltip": tip(
                        "[기상술사] 우레바람 피해 40.00% 증가<br>"
                        "추가 효과<br>기본 공격력 1.00% 증가"
                    ),
                },
                {
                    "Slot": 2,
                    "Name": "9레벨 작열의 보석",
                    "Level": 9,
                    "Grade": "유물",
                    "Tooltip": tip(
                        "[기상술사] 우레바람 재사용 대기시간 22.00% 감소<br>"
                        "추가 효과<br>기본 공격력 1.00% 증가"
                    ),
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
            "Effects": [
                {"Name": "추가 피해", "Level": 49, "Tooltip": "추가 피해 +3.96%"},
                {"Name": "공격력", "Level": 37, "Tooltip": "공격력 +1.35%"},
                {
                    "Name": "보스 피해",
                    "Level": 44,
                    "Tooltip": "보스 등급 이상 몬스터에게 주는 피해 +3.66%",
                },
                {"Name": "아군 피해 강화", "Level": 17, "Tooltip": "아군 피해량 강화 +0.89%"},
                {"Name": "포인트 효과", "Level": 2, "Tooltip": "피해 증가"},
            ],
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
        self.assertEqual(grid["gemEffects"]["attackPowerPercent"], Decimal("0.012"))
        self.assertEqual(grid["gemEffects"]["additionalDamagePercent"], Decimal("0.02"))
        self.assertEqual(grid["gemEffects"]["bossDamagePercent"], Decimal("0.03"))
        self.assertEqual(grid["pointEffects"]["attackPowerPercent"], Decimal("0.0135"))
        self.assertEqual(grid["pointEffects"]["additionalDamagePercent"], Decimal("0.0396"))
        self.assertEqual(grid["pointEffects"]["bossDamagePercent"], Decimal("0.0366"))
        self.assertEqual(grid["attackPowerPercent"], Decimal("0.0135"))
        self.assertEqual(grid["additionalDamagePercent"], Decimal("0.0396"))
        self.assertEqual(grid["bossDamagePercent"], Decimal("0.0366"))
        self.assertEqual(
            grid["effectiveBaseEffects"]["attackPowerPercent"],
            grid["pointEffects"]["attackPowerPercent"],
        )
        gem_attack_sources = [
            item
            for item in grid["sources"]
            if item["label"] == "아크그리드 젬 attackPowerPercent"
        ]
        self.assertTrue(gem_attack_sources)
        self.assertTrue(
            all(item["applied"] is False for item in gem_attack_sources)
        )
        labels = [x["label"] for x in grid["excluded"]]
        self.assertIn("비활성 아크그리드 젬", labels)
        self.assertIn("낙인력", labels)
        self.assertIn("포인트 효과", labels)

    def test_enlightenment_karma_weapon_attack_uses_level(self):
        for level, expected in (
            (10, "0.010"),
            (27, "0.027"),
            (30, "0.030"),
        ):
            with self.subTest(level=level):
                parsed = dut.parse_ark_passive(
                    {
                        "Points": [
                            {
                                "Name": "깨달음",
                                "Value": 101,
                                "Description": f"6랭크 {level}레벨",
                            }
                        ],
                        "Effects": [],
                    },
                    [],
                )
                self.assertEqual(
                    parsed["karmaWeaponAttackPercent"],
                    Decimal(expected),
                )
                self.assertEqual(parsed["points"][0]["karmaLevel"], level)

    def test_arkgrid_core_thresholds_categories_and_skill_scope(self):
        body = {
            "Slots": [
                {
                    "Index": 0,
                    "Name": "혼돈의 해 코어 : 현란한 공격",
                    "Grade": "고대",
                    "Point": 20,
                    "Tooltip": tip(
                        "코어 옵션<br>"
                        "[10P] 치명타 시 적에게 주는 피해가 0.55% 증가한다.<br>"
                        "[14P] 적에게 주는 피해가 0.50% 증가한다.<br>"
                        "[17P] 적에게 주는 피해가 1.50% 추가로 증가하고, "
                        "치명타 시 적에게 주는 피해가 1.10% 추가로 증가한다.<br>"
                        "[18P] 적에게 주는 피해가 0.16% 증가한다.<br>"
                        "[19P] 적에게 주는 피해가 0.16% 증가한다.<br>"
                        "[20P] 적에게 주는 피해가 0.16% 증가한다.<br>분해불가"
                    ),
                    "Gems": [],
                },
                {
                    "Index": 1,
                    "Name": "혼돈의 별 코어 : 공격",
                    "Grade": "고대",
                    "Point": 19,
                    "Tooltip": tip(
                        "코어 옵션<br>"
                        "[10P] 공격력이 900 증가한다.<br>"
                        "[14P] 공격력이 0.55% 증가한다.<br>"
                        "[17P] 공격력이 1.65% 증가하고, 추가로 2700 증가한다.<br>"
                        "[18P] 공격력이 0.16% 증가한다.<br>"
                        "[19P] 공격력이 0.16% 증가한다.<br>"
                        "[20P] 공격력이 0.16% 증가한다.<br>분해불가"
                    ),
                    "Gems": [],
                },
                {
                    "Index": 2,
                    "Name": "질서의 해 코어 : 비연참",
                    "Grade": "고대",
                    "Point": 18,
                    "Tooltip": tip(
                        "코어 옵션<br>"
                        "[10P] 우산 스킬의 피해량이 2.0% 증가한다.<br>"
                        "[14P] '운명' 발동 시 '운명: 비연참' 효과를 획득한다.<br>"
                        "'운명: 비연참' : 다음 사용하는 회오리 걸음, 몰아치기, "
                        "바람송곳, 칼바람의 피해량이 5.0% 증가한다.<br>"
                        "[17P] 기류 보호막이 생성된다. 우산 스킬의 피해량이 "
                        "1.0% 증가한다.<br>"
                        "[18P] 우산 스킬의 피해량이 0.2% 증가한다.<br>"
                        "[19P] 우산 스킬의 피해량이 0.2% 증가한다.<br>분해불가"
                    ),
                    "Gems": [],
                },
            ],
            "Effects": [],
        }
        space = dut.parse_ark_grid(body, [], "공간 가르기")
        self.assertEqual(
            space["coreEffects"]["generalDamagePercent"], Decimal("0.0248")
        )
        self.assertEqual(
            space["coreEffects"]["criticalHitDamagePercent"],
            Decimal("0.0165"),
        )
        self.assertEqual(
            space["coreEffects"]["attackPowerFlat"], Decimal("3600")
        )
        self.assertEqual(
            space["coreEffects"]["attackPowerPercent"], Decimal("0.0252")
        )
        self.assertEqual(
            space["coreEffects"]["skillDamagePercent"], Decimal("0.032")
        )
        general_factors = [
            item["value"]
            for item in space["coreDamageFactors"]
            if item["category"] == "generalDamagePercent"
        ]
        self.assertEqual(
            general_factors,
            [
                Decimal("0.0200"),
                Decimal("0.0016"),
                Decimal("0.0016"),
                Decimal("0.0016"),
            ],
        )
        factor_product = Decimal("1")
        for value in general_factors:
            factor_product *= Decimal("1") + value
        self.assertEqual(
            factor_product,
            Decimal("1.02") * (Decimal("1.0016") ** 3),
        )
        critical_factors = [
            item["value"]
            for item in space["coreDamageFactors"]
            if item["category"] == "criticalHitDamagePercent"
        ]
        self.assertEqual(critical_factors, [Decimal("0.0165")])
        self.assertFalse(
            space["cores"][2]["options"][-1]["activated"],
            "19P option must not activate at 18 points",
        )

        thunder = dut.parse_ark_grid(body, [], "우레바람")
        self.assertEqual(
            thunder["coreEffects"]["skillDamagePercent"], Decimal("0.032")
        )

    def test_arkgrid_core_component_category_coverage(self):
        cases = [
            ("추가 피해가 2.8% 증가한다.", "additionalDamagePercent", "0.028"),
            ("치명타 적중률이 2.6% 증가한다.", "criticalRate", "0.026"),
            (
                "적의 모든 방어력을 0.8% 감소시킨다.",
                "enemyDefenseReductionPercent",
                "0.008",
            ),
            ("무기 공격력이 2.25% 증가한다.", "weaponAttackPercent", "0.0225"),
            ("무기 공격력이 3900 증가한다.", "weaponAttackFlat", "3900"),
            ("공격력이 1.65% 증가한다.", "attackPowerPercent", "0.0165"),
            ("공격력이 2700 증가한다.", "attackPowerFlat", "2700"),
        ]
        for text, category, expected in cases:
            components, _ = dut.parse_arkgrid_core_option_components(
                text, "우레바람"
            )
            values = [
                item["value"]
                for item in components
                if item["category"] == category
            ]
            self.assertIn(Decimal(expected), values, text)

        speed_components, _ = dut.parse_arkgrid_core_option_components(
            "공격 및 이동 속도가 0.3% 증가한다.", "우레바람"
        )
        speed_by_category = {
            item["category"]: item["value"] for item in speed_components
        }
        self.assertEqual(speed_by_category["attackSpeed"], Decimal("0.003"))
        self.assertEqual(speed_by_category["moveSpeed"], Decimal("0.003"))

        cooldown_components, _ = dut.parse_arkgrid_core_option_components(
            "스킬 재사용 대기시간이 1.6% 감소한다.", "우레바람"
        )
        cooldown = next(
            item
            for item in cooldown_components
            if item["category"] == "cooldownReductionPercent"
        )
        self.assertFalse(cooldown["applied"])

        replacement_components, _ = (
            dut.parse_arkgrid_core_option_components(
                "'운명: 바람의 칼날' 효과의 피해 증가량을 "
                "44.0%로 변경한다.",
                "우레바람",
                "질서의 해 코어 : 바람의 칼날",
            )
        )
        replacement = next(
            item
            for item in replacement_components
            if item.get("operator") == "REPLACE"
        )
        self.assertEqual(replacement["value"], Decimal("0.44"))
        self.assertEqual(replacement["scopeValue"], ["칼바람"])

        relic_components, _ = dut.parse_arkgrid_core_option_components(
            "적에게 주는 피해가 1.0/1.5% 추가로 증가한다.",
            "우레바람",
            core_grade="유물",
        )
        ancient_components, _ = dut.parse_arkgrid_core_option_components(
            "적에게 주는 피해가 1.0/1.5% 추가로 증가한다.",
            "우레바람",
            core_grade="고대",
        )
        self.assertEqual(relic_components[0]["value"], Decimal("0.010"))
        self.assertEqual(ancient_components[0]["value"], Decimal("0.015"))
        self.assertEqual(
            relic_components[0]["operator"], "ADD_TO_PREVIOUS"
        )
        relic_flat, _ = dut.parse_arkgrid_core_option_components(
            "공격력이 1.1/1.65% 증가하고, 추가로 1800/2700 증가한다.",
            "우레바람",
            core_grade="유물",
        )
        ancient_flat, _ = dut.parse_arkgrid_core_option_components(
            "공격력이 1.1/1.65% 증가하고, 추가로 1800/2700 증가한다.",
            "우레바람",
            core_grade="고대",
        )
        relic_by_category = {
            item["category"]: item["value"] for item in relic_flat
        }
        ancient_by_category = {
            item["category"]: item["value"] for item in ancient_flat
        }
        self.assertEqual(
            relic_by_category["attackPowerPercent"], Decimal("0.011")
        )
        self.assertEqual(
            ancient_by_category["attackPowerPercent"], Decimal("0.0165")
        )
        self.assertEqual(
            relic_by_category["attackPowerFlat"], Decimal("1800")
        )
        self.assertEqual(
            ancient_by_category["attackPowerFlat"], Decimal("2700")
        )

    def test_calculation_toggle_and_floor(self):
        before = dut.calculate(self.parsed, include_arkgrid=False)
        after = dut.calculate(self.parsed, include_arkgrid=True)
        self.assertEqual(before["inputs"]["arkGridAttackPowerPercent"], 0)
        self.assertEqual(before["inputs"]["arkGridAdditionalDamage"], 0)
        self.assertEqual(after["inputs"]["arkGridAttackPowerPercent"], Decimal("0.0135"))
        self.assertGreater(after["damage"]["nonCritical"], before["damage"]["nonCritical"])
        self.assertEqual(
            after["damage"]["nonCritical"],
            int(after["damage"]["nonCriticalRaw"].to_integral_value(rounding=dut.ROUND_FLOOR)),
        )
        self.assertFalse(dut.validate(self.parsed, before, after))

    def test_profile_attack_is_used_after_reconstruction_mismatch(self):
        result = dut.calculate(self.parsed, include_arkgrid=True)
        attack = result["attackPower"]
        self.assertNotEqual(attack["final"], Decimal("210000"))
        self.assertEqual(attack["usedForDamage"], Decimal("210000"))
        self.assertEqual(attack["usedForDamageSource"], "API_PROFILE")
        self.assertEqual(result["damage"]["attackPowerUsed"], Decimal("210000"))
        self.assertEqual(
            result["damage"]["skillBaseRaw"],
            dut.FIXED["skillCoefficient"] * Decimal("210000")
            + dut.FIXED["skillConstant"],
        )

    def test_regular_gem_skill_damage_and_cooldown_are_parsed(self):
        effect = dut.regular_gem_effect_for_skill(self.parsed["gems"], "우뢰바람")
        self.assertEqual(effect["skillName"], "우레바람")
        self.assertEqual(effect["damagePercent"], Decimal("0.40"))
        self.assertEqual(effect["cooldownReductionPercent"], Decimal("0.22"))
        self.assertEqual(effect["cooldownMultiplier"], Decimal("0.78"))
        result = dut.calculate(self.parsed, include_arkgrid=True)
        gem_subtitle = next(
            item
            for item in result["damageGroups"]["subtitles"]
            if item["name"] == "일반 보석 우레바람 피해"
        )
        self.assertEqual(gem_subtitle["percent"], Decimal("0.40"))

    def test_space_cutting_two_hits_and_scope(self):
        responses = copy.deepcopy(fixture_responses())
        responses["arkPassive"]["Effects"].append(
            {
                "Name": "공간 가르기 Lv.3",
                "Description": "공간 가르기가 주는 피해가 200.0% 증가한다.",
            }
        )
        parsed = dut.parse_all(
            responses,
            skill_name="공간가르기",
        )
        result = dut.calculate(
            parsed,
            include_arkgrid=True,
            skill_name="공간 가르기",
        )
        self.assertEqual(parsed["canonicalSkillName"], "공간 가르기")
        self.assertEqual(result["damage"]["hitCount"], 2)
        self.assertEqual(
            [hit["coefficient"] for hit in result["damage"]["hits"]],
            [Decimal("40.07"), Decimal("93.50")],
        )
        self.assertEqual(
            [hit["constant"] for hit in result["damage"]["hits"]],
            [Decimal("6117"), Decimal("14283")],
        )
        self.assertIn(
            "UMBRELLA_SKILL",
            dut.SKILL_MODELS["공간 가르기"]["tags"],
        )
        skill_parts = {
            item["name"]: item["value"]
            for item in result["damageGroups"]["skillDamageParts"]
        }
        self.assertEqual(skill_parts, {"공간 가르기": Decimal("2.0")})
        subtitle_names = {
            item["name"] for item in result["damageGroups"]["subtitles"]
        }
        self.assertNotIn("풀려난 힘", subtitle_names)
        self.assertNotIn("바람의 길", subtitle_names)
        self.assertNotIn("단련된 가르기", subtitle_names)
        self.assertEqual(
            result["damage"]["skillBaseRaw"],
            sum(
                (
                    hit["coefficient"] * Decimal("210000")
                    + hit["constant"]
                    for hit in dut.SKILL_MODELS["공간 가르기"]["hits"]
                ),
                Decimal("0"),
            ),
        )
        self.assertFalse(
            dut.validate(
                parsed,
                dut.calculate(
                    parsed,
                    include_arkgrid=False,
                    skill_name="공간 가르기",
                ),
                result,
            )
        )

    def test_gale_umbrella_skill_models_for_spring_flower_seed(self):
        snapshot_path = (
            Path(__file__).resolve().parent.parent
            / "outputs"
            / "봄날꽃씨_공간 가르기_current-v2.4.2_api_raw.json"
        )
        bundle = json.loads(snapshot_path.read_text(encoding="utf-8"))
        responses = dut.response_from_raw_bundle(bundle)
        cases = {
            "바람송곳": {
                "coefficients": [Decimal("52.20")],
                "constants": [Decimal("7874")],
                "criticalTripod": Decimal("0"),
            },
            "칼바람": {
                "coefficients": [Decimal("48.98")],
                "constants": [Decimal("7388.5")],
                "criticalTripod": Decimal("2.10"),
            },
            "몰아치기": {
                "coefficients": [
                    Decimal("9.72"),
                    Decimal("22.65"),
                    Decimal("30.69"),
                ],
                "constants": [
                    Decimal("1466.7"),
                    Decimal("3417.1"),
                    Decimal("4629.8"),
                ],
                "criticalTripod": Decimal("1.80"),
            },
            "회오리 걸음": {
                "coefficients": [Decimal("22.72"), Decimal("9.75")],
                "constants": [Decimal("3427.5"), Decimal("1470.9")],
                "criticalTripod": Decimal("0"),
            },
        }
        for skill_name, expected in cases.items():
            with self.subTest(skill=skill_name):
                parsed = dut.parse_all(responses, skill_name=skill_name)
                result = dut.calculate(
                    parsed,
                    include_arkgrid=True,
                    rule_version="current-v2.5.0",
                    skill_name=skill_name,
                )
                self.assertIn(
                    "UMBRELLA_SKILL",
                    dut.SKILL_MODELS[skill_name]["tags"],
                )
                self.assertEqual(result["skillModel"]["missingTripods"], [])
                self.assertEqual(
                    [hit["coefficient"] for hit in result["damage"]["hits"]],
                    expected["coefficients"],
                )
                self.assertEqual(
                    [hit["constant"] for hit in result["damage"]["hits"]],
                    expected["constants"],
                )
                self.assertEqual(
                    result["critical"]["skillTripodCriticalDamage"],
                    expected["criticalTripod"],
                )
                self.assertEqual(
                    result["inputs"]["regularGemSkillDamagePercent"],
                    Decimal("0.40"),
                )
                self.assertGreater(result["damage"]["nonCritical"], 0)
                self.assertGreater(
                    result["damage"]["critical"],
                    result["damage"]["nonCritical"],
                )

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
        by_name["타격의 대가"]["Description"] = (
            "공격 타입이 백 어택 및 헤드 어택에 해당되지 않는 공격의 피해가 "
            "17.00% 증가한다. 각성기는 해당 효과가 적용되지 않는다."
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
        self.assertEqual(engraving_values["타격의 대가"], Decimal("0.17"))
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

    def test_audit_snapshot_regression(self):
        snapshot_path = (
            Path(__file__).resolve().parent.parent
            / "outputs"
            / "봄날꽃씨_우레바람_current-v2.1.0_api_raw.json"
        )
        bundle = json.loads(snapshot_path.read_text(encoding="utf-8"))
        parsed = dut.parse_all(dut.response_from_raw_bundle(bundle))
        grid = parsed["arkGrid"]
        self.assertEqual(grid["gemEffects"]["attackPowerPercent"], Decimal("0.0132"))
        self.assertEqual(grid["gemEffects"]["additionalDamagePercent"], Decimal("0.0392"))
        self.assertEqual(grid["gemEffects"]["bossDamagePercent"], Decimal("0.0362"))
        self.assertEqual(grid["pointEffects"]["attackPowerPercent"], Decimal("0.0135"))
        self.assertEqual(grid["pointEffects"]["additionalDamagePercent"], Decimal("0.0396"))
        self.assertEqual(grid["pointEffects"]["bossDamagePercent"], Decimal("0.0366"))
        self.assertEqual(
            grid["coreEffects"]["generalDamagePercent"], Decimal("0.0232")
        )
        self.assertEqual(
            grid["coreEffects"]["bossDamagePercent"], Decimal("0.0298")
        )
        self.assertEqual(
            grid["coreEffects"]["criticalHitDamagePercent"],
            Decimal("0.0165"),
        )
        self.assertEqual(
            grid["coreEffects"]["weaponAttackFlat"], Decimal("5200")
        )
        self.assertEqual(
            grid["coreEffects"]["weaponAttackPercent"], Decimal("0.0300")
        )
        self.assertEqual(
            parsed["engravings"]["parsedEffects"]["타격의 대가"]["generalDamage"],
            Decimal("0.17"),
        )
        self.assertEqual(
            dut.regular_gem_effect_for_skill(parsed["gems"], "우레바람")[
                "damagePercent"
            ],
            Decimal("0"),
        )
        result = dut.calculate(parsed)
        self.assertEqual(
            result["attackPower"]["usedForDamage"],
            parsed["profile"]["profileAttackPower"],
        )

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
        self.assertNotIn("핵심 원본 데이터 발췌", report)
        self.assertNotIn("아크그리드 전체 효과 적용 전후", report)
        self.assertIn("아크그리드 젬", report)
        self.assertIn("아크그리드 누적 효과(Effects[])", report)
        self.assertIn("아크그리드 코어", report)
        self.assertIn("아크그리드 활성 젬 공격력 상세", report)
        self.assertIn("과거 스펙의 최종 피해와 회귀 비교하지 않았습니다.", report)


if __name__ == "__main__":
    unittest.main()
