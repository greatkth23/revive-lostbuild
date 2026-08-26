#!/usr/bin/env python3

import unittest
from decimal import Decimal

import arcana_damage as arcana
import lostark_damage_test as base


class ArcanaModelTests(unittest.TestCase):
    def test_user_motion_models_are_registered(self):
        rain = base.get_skill_model("셀레스티얼 레인")
        seren = base.get_skill_model("세렌디피티")
        ruin = base.get_skill_model("4스택 루인")
        self.assertEqual(rain["hits"][0]["coefficient"], Decimal("4.71"))
        self.assertEqual(seren["hits"][1]["constant"], Decimal("436"))
        self.assertEqual(ruin["hits"][0]["coefficient"], Decimal("15.90"))
        self.assertIn("BACK_ATTACK", base.get_skill_model("포카드")["tags"])

    def test_arcana_direction_is_component_specific(self):
        four_of_a_kind = base.directional_attack_bonus(
            base.get_skill_model("포카드")["tags"]
        )
        serendipity = base.directional_attack_bonus(
            base.get_skill_model("세렌디피티")["tags"]
        )
        linked_ruin = base.directional_attack_bonus(
            base.get_skill_model("4스택 루인")["tags"]
        )
        self.assertEqual(four_of_a_kind["damagePercent"], Decimal("0.05"))
        self.assertEqual(four_of_a_kind["criticalRate"], Decimal("0.10"))
        self.assertEqual(serendipity["damagePercent"], Decimal("0.20"))
        self.assertEqual(linked_ruin["tag"], "NON_DIRECTIONAL")
        self.assertFalse(linked_ruin["applied"])

    def test_specialization_ruin_damage_is_parsed(self):
        profile = base.parse_profile(
            {
                "CharacterClassName": "아르카나",
                "Stats": [
                    {
                        "Type": "특화",
                        "Value": "1806",
                        "Tooltip": ["루인 스킬 피해량이 90.42% 증가합니다."],
                    }
                ],
            },
            [],
        )
        self.assertEqual(profile["specializationStat"], Decimal("1806"))
        self.assertEqual(
            profile["ruinDamageFromSpecialization"], Decimal("0.9042")
        )


class ArcanaMechanicTests(unittest.TestCase):
    def setUp(self):
        self.parsed = {
            "profile": {"ruinDamageFromSpecialization": Decimal("0.9042")},
            "arkPassive": {
                "effects": {
                    "황후의 탐욕": {"description": "루인 스킬의 피해량이 0.9% 증가한다."},
                    "황후의 연회": {"description": "4스택 이상의 루인 피해량이 26.0% 증가한다."},
                    "황후의 속삭임": {"description": "루인 스킬의 피해량이 20.0% 증가한다."},
                    "황제의 자비": {"description": "카드 사용 시 적에게 주는 피해가 1.2% 증가한다."},
                    "뭉툭한 가시": {
                        "description": (
                            "치명타가 발생할 확률이 최대 80.0% 로 제한됩니다. "
                            "초과한 모든 치명타가 발생할 확률의 150.0%가 진화형 피해로 "
                            "전환됩니다. 이 노드에 의한 진화형 피해는 최대 75.0%까지 적용됩니다."
                        )
                    },
                }
            },
            "combatSkills": {
                "selectedTripods": [
                    {
                        "skill": "스트림 오브 엣지",
                        "name": "다크니스 엣지",
                        "tooltipText": "적중 시 마다 치명타 적중률이 5.5% 씩 최대 27.6% 까지 증가한다.",
                    },
                    {
                        "skill": "스크래치 딜러",
                        "name": "안전 장치",
                        "tooltipText": "이동속도가 30.0% 증가한다.",
                    },
                    {
                        "skill": "운명의 부름",
                        "name": "어두운 운명",
                        "tooltipText": "적에게 주는 치명타 피해가 77.5% 증가한다.",
                    },
                ]
            },
            "arkGrid": {
                "cores": [
                    {
                        "name": "질서의 해 코어 : 인피니티 덱",
                        "options": [
                            {"activated": True, "resolvedText": "루인 스킬의 피해량이 1.6% 증가한다."},
                            {"activated": True, "resolvedText": "균형 카드 사용 시 30.0초 동안 루인 스킬의 피해량이 2.0% 증가한다."},
                        ],
                    },
                    {
                        "name": "질서의 달 코어 : 엣지 콤보",
                        "options": [
                            {"activated": True, "resolvedText": "스트림 오브 엣지 사용 시 8.0초 동안 루인 스킬의 피해량이 5.0% 증가한다."},
                        ],
                    },
                    {
                        "name": "질서의 별 코어 : 스트림 오브 엣지",
                        "options": [
                            {"activated": True, "resolvedText": "셀레스티얼 레인의 피해량이 8.0% 증가한다."},
                            {"activated": True, "resolvedText": "버프 중첩 당 치명타 피해량이 1.6% 증가한다."},
                            {"activated": True, "resolvedText": "셀레스티얼 레인의 피해량이 0.8% 증가한다."},
                        ],
                    },
                ]
            },
        }

    def test_current_arcana_effects_are_extracted(self):
        effects = arcana.extract_arcana_mechanics(self.parsed)
        self.assertEqual(effects["specializationRuinDamage"], Decimal("0.9042"))
        self.assertEqual(effects["banquetFourStackDamage"], Decimal("0.26"))
        self.assertEqual(effects["balanceConditionalRuinDamage"], Decimal("0.02"))
        self.assertEqual(effects["streamStacks"], 5)
        self.assertEqual(effects["streamCoreCriticalDamage"], Decimal("0.080"))
        self.assertEqual(
            effects["rainCoreDamageFactors"], [Decimal("0.08"), Decimal("0.008")]
        )

    def test_blunt_spike_is_skill_specific(self):
        mechanics = arcana.extract_arcana_mechanics(self.parsed)
        seed = {"critical": {"rateRaw": Decimal("0.5075")}}
        tripod = {"criticalRate": Decimal("0.45")}
        scenario = {**arcana.SCENARIOS["baseline"], "mechanics": mechanics}
        state = arcana.critical_state(seed, mechanics, tripod, scenario)
        self.assertEqual(state["raw"], Decimal("0.9575"))
        self.assertEqual(state["capped"], Decimal("0.8"))
        self.assertEqual(state["convertedEvolution"], Decimal("0.23625"))

    def test_serendipity_four_stack_probability(self):
        self.parsed["combatSkills"]["selectedTripods"].extend(
            [
                {
                    "skill": "세렌디피티",
                    "name": "꿰뚫는 일격",
                    "tooltipText": "50.0% 확률로 적의 모든 방어력을 80.0% 무시한다.",
                },
                {
                    "skill": "세렌디피티",
                    "name": "우연한 일격",
                    "tooltipText": "스택트 중첩당 20.0% 확률로 루인으로 주는 치명타 피해가 504.0% 증가한다.",
                },
                {
                    "skill": "세렌디피티",
                    "name": "연속된 어둠",
                    "tooltipText": "적에게 주는 총 스킬 피해량이 70.8% 증가한다.",
                },
            ]
        )
        effect = arcana.skill_tripod_mechanics(self.parsed, "세렌디피티")
        self.assertEqual(effect["defenseIgnoreChance"], Decimal("0.5"))
        self.assertEqual(effect["defenseIgnoreRate"], Decimal("0.8"))
        self.assertEqual(effect["ruinCriticalBonusChance"], Decimal("0.8"))
        self.assertEqual(effect["ruinCriticalDamageBonus"], Decimal("5.04"))
        self.assertEqual(effect["directFactors"], [("연속된 어둠", Decimal("0.708"))])

    def test_secret_garden_complete_secret_is_ruin_factor(self):
        self.parsed["combatSkills"]["selectedTripods"].extend(
            [
                {
                    "skill": "시크릿 가든",
                    "name": "완전한 비밀",
                    "tooltipText": "4스택인 적에게 적중 시 80.0% 증가된 피해를 준다.",
                },
                {
                    "skill": "시크릿 가든",
                    "name": "시크릿 찬스",
                    "tooltipText": "스택트 피해 효과가 95.0% 증가한다.",
                },
            ]
        )
        effect = arcana.skill_tripod_mechanics(self.parsed, "시크릿 가든")
        self.assertEqual(effect["directFactors"], [])
        self.assertEqual(
            effect["ruinFactors"],
            [
                ("완전한 비밀 4스택", Decimal("0.80")),
                ("시크릿 찬스", Decimal("0.95")),
            ],
        )

    def test_serendipity_critical_proc_is_ruin_only(self):
        self.test_serendipity_four_stack_probability()
        mechanics = arcana.extract_arcana_mechanics(self.parsed)
        effect = arcana.skill_tripod_mechanics(self.parsed, "세렌디피티")
        seed = {
            "skillName": "세렌디피티",
            "damageGroups": {
                "additionalDamageMultiplier": Decimal("1"),
                "evolutionParts": [],
                "subtitles": [],
            },
            "enemy": {
                "defenseMultiplier": Decimal("0.5"),
                "effectiveDefense": Decimal("6500"),
                "defenseConstant": Decimal("6500"),
                "damageTakenMultiplier": Decimal("1"),
            },
            "critical": {
                "rateRaw": Decimal("0.5"),
                "damageMultiplier": Decimal("7.088"),
                "skillTripodCriticalDamage": Decimal("5.04"),
                "criticalHitDamageMultiplier": Decimal("1"),
            },
        }
        parsed = {
            **self.parsed,
            "profile": {
                **self.parsed["profile"],
                "moveSpeedFromSwiftness": Decimal("0"),
            },
            "engravings": {
                "parsedEffects": {
                    "돌격대장": {"raidCaptainCoefficient": Decimal("0")},
                    "마나 효율 증가": {"generalDamage": Decimal("0")},
                }
            },
            "arkGrid": {**self.parsed["arkGrid"], "criticalDamage": Decimal("0")},
        }
        scenario = {**arcana.SCENARIOS["baseline"], "mechanics": mechanics}
        direct = arcana.component_damage(
            name="본체",
            hit_bases=[("본체", Decimal("100"))],
            seed=seed,
            parsed=parsed,
            mechanics=mechanics,
            tripod_data=effect,
            scenario=scenario,
            factors=[],
            defense_ignore_probability=True,
        )
        ruin = arcana.component_damage(
            name="루인",
            hit_bases=[("루인", Decimal("100"))],
            seed=seed,
            parsed=parsed,
            mechanics=mechanics,
            tripod_data=effect,
            scenario=scenario,
            factors=[],
            defense_ignore_probability=True,
            ruin_critical_probability=True,
        )
        guaranteed_pierce = arcana.component_damage(
            name="꿰뚫는 일격 확정",
            hit_bases=[("루인", Decimal("100"))],
            seed=seed,
            parsed=parsed,
            mechanics=mechanics,
            tripod_data=effect,
            scenario=scenario,
            factors=[],
            defense_ignore_probability=True,
            defense_ignore_chance_override=Decimal("1"),
        )
        guaranteed_lucky = arcana.component_damage(
            name="우연한 일격 확정",
            hit_bases=[("루인", Decimal("100"))],
            seed=seed,
            parsed=parsed,
            mechanics=mechanics,
            tripod_data=effect,
            scenario=scenario,
            factors=[],
            ruin_critical_probability=True,
            ruin_critical_chance_override=Decimal("1"),
        )
        self.assertEqual(direct["criticalDamageExpected"], Decimal("2.048"))
        self.assertEqual(ruin["criticalDamageExpected"], Decimal("6.080"))
        self.assertEqual(
            guaranteed_pierce["defenseIgnoreChanceUsed"], Decimal("1")
        )
        self.assertEqual(
            guaranteed_pierce["defenseMultiplierExpected"],
            guaranteed_pierce["defenseMultiplierIgnored"],
        )
        self.assertEqual(
            guaranteed_lucky["ruinCriticalBonusChanceUsed"], Decimal("1")
        )
        self.assertEqual(
            guaranteed_lucky["criticalDamageExpected"], Decimal("7.088")
        )


if __name__ == "__main__":
    unittest.main()
