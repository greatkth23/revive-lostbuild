#!/usr/bin/env python3

import sqlite3
import tempfile
import unittest
from pathlib import Path

import build_damage_db as dut
import lostark_damage_test as calculator


class DamageKnowledgeDatabaseTests(unittest.TestCase):
    def test_seed_builds_with_expected_release_and_scopes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "damage.sqlite3"
            dut.build_database(output)
            connection = sqlite3.connect(output)
            try:
                release = connection.execute(
                    "SELECT db_release FROM db_releases"
                ).fetchone()
                self.assertEqual(release, ("weather-artist-v0.4",))
                self.assertEqual(release, (calculator.DB_RELEASE,))
                core_categories = {
                    row[0]
                    for row in connection.execute(
                        "SELECT category FROM arkgrid_core_effect_categories"
                    )
                }
                self.assertIn("generalDamagePercent", core_categories)
                self.assertIn("skillDamagePercent", core_categories)
                self.assertIn(
                    "enemyDefenseReductionPercent", core_categories
                )
                cooldown_single_cast = connection.execute(
                    """
                    SELECT single_cast_applied
                    FROM arkgrid_core_effect_categories
                    WHERE category = 'cooldownReductionPercent'
                    """
                ).fetchone()
                self.assertEqual(cooldown_single_cast, (0,))
                space_hits = connection.execute(
                    """
                    SELECT hit_index, coefficient, constant_value
                    FROM skill_hits
                    WHERE variant_id = ?
                    ORDER BY hit_index
                    """,
                    ("weather-artist:공간 가르기:two-hit",),
                ).fetchall()
                self.assertEqual(
                    space_hits,
                    [(1, "40.07", "6117"), (2, "93.50", "14283")],
                )
                skill_count = connection.execute(
                    "SELECT COUNT(*) FROM skills"
                ).fetchone()
                self.assertEqual(skill_count, (6,))
                downpour_hits = connection.execute(
                    """
                    SELECT hit_index, coefficient, constant_value
                    FROM skill_hits
                    WHERE variant_id = ?
                    ORDER BY hit_index
                    """,
                    ("weather-artist:몰아치기:역류-우레-공간베기",),
                ).fetchall()
                self.assertEqual(
                    downpour_hits,
                    [
                        (1, "9.72", "1466.7"),
                        (2, "22.65", "3417.1"),
                        (3, "30.69", "4629.8"),
                    ],
                )
                whirlwind_hits = connection.execute(
                    """
                    SELECT hit_index, coefficient, constant_value
                    FROM skill_hits
                    WHERE variant_id = ?
                    ORDER BY hit_index
                    """,
                    (
                        "weather-artist:회오리 걸음:"
                        "재빠른손놀림-역류-초고속회전",
                    ),
                ).fetchall()
                self.assertEqual(
                    whirlwind_hits,
                    [(1, "22.72", "3427.5"), (2, "9.75", "1470.9")],
                )
                effects = {
                    row[0]
                    for row in connection.execute(
                        "SELECT effect_id FROM effects"
                    )
                }
                self.assertIn("arkgrid:attack-power", effects)
                self.assertIn("arkgrid:additional-damage", effects)
                self.assertIn("arkgrid:boss-damage", effects)
                self.assertIn("regular-gem:skill-damage", effects)
                self.assertIn("regular-gem:cooldown", effects)
                self.assertIn("engraving:hit-master", effects)
                scenario = connection.execute(
                    """
                    SELECT calculation_mode
                    FROM scenario_presets
                    WHERE scenario_preset_id = ?
                    """,
                    ("max-favorable-example-boss-v1",),
                ).fetchone()
                self.assertEqual(scenario, ("ESTIMATE_WITH_FALLBACK",))
                self.assertEqual(
                    calculator.SCENARIO_PRESET_ID,
                    "max-favorable-example-boss-v1",
                )
                self.assertEqual(
                    calculator.CALCULATION_MODE,
                    "ESTIMATE_WITH_FALLBACK",
                )
                self.assertFalse(
                    connection.execute("PRAGMA foreign_key_check").fetchall()
                )
            finally:
                connection.close()

    def test_existing_database_requires_explicit_force(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "damage.sqlite3"
            dut.build_database(output)
            with self.assertRaises(FileExistsError):
                dut.build_database(output)
            dut.build_database(output, force=True)


if __name__ == "__main__":
    unittest.main()
