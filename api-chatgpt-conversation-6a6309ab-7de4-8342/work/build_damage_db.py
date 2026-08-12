#!/usr/bin/env python3
"""Build the versioned Lost Ark damage knowledge SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_SCHEMA = HERE / "db" / "schema.sql"
DEFAULT_SEED = HERE / "db" / "weather-artist-v0.4_seed.json"
DEFAULT_OUTPUT = HERE / "db" / "weather-artist-v0.4.sqlite3"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} root must be an object")
    return value


def seed_database(connection: sqlite3.Connection, seed: dict[str, Any]) -> None:
    release = seed["release"]
    patch_version = release["patch_version"]
    connection.execute(
        "INSERT INTO patch_versions(patch_version, observed_at, notes) VALUES (?, ?, ?)",
        (
            patch_version,
            release["created_at"],
            "Lost Ark Open API snapshot observation",
        ),
    )

    for item in seed.get("sources", []):
        connection.execute(
            """
            INSERT INTO source_documents(
                source_document_id, source_type, source_locator, source_excerpt,
                verification_status, verified_by, verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["source_document_id"],
                item["source_type"],
                item["source_locator"],
                item.get("source_excerpt", ""),
                item["verification_status"],
                item.get("verified_by"),
                item.get("verified_at"),
            ),
        )

    connection.execute(
        "INSERT INTO parser_versions(parser_version, valid_from_patch, notes) VALUES (?, ?, ?)",
        (
            "lostark-api-v2.4.1",
            patch_version,
            "ArkGrid core operator retention and relic/ancient slash resolution",
        ),
    )
    connection.execute(
        """
        INSERT INTO ruleset_versions(
            ruleset_version, valid_from_patch, source_document_id, notes
        ) VALUES (?, ?, ?, ?)
        """,
        (
            "current-v2.4.1",
            patch_version,
            "audit-v2.1.0",
            "Per-core additive/multiplicative threshold arithmetic",
        ),
    )
    connection.execute(
        """
        INSERT INTO db_releases(
            db_release, patch_version, created_at, verification_status, notes
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            release["db_release"],
            patch_version,
            release["created_at"],
            release["verification_status"],
            release.get("notes", ""),
        ),
    )

    for item in seed.get("stacking_groups", []):
        connection.execute(
            """
            INSERT INTO stacking_groups(stacking_group, operator, description)
            VALUES (?, ?, ?)
            """,
            (
                item["stacking_group"],
                item["operator"],
                item["description"],
            ),
        )
    for item in seed.get("scopes", []):
        connection.execute(
            """
            INSERT INTO effect_scopes(
                scope_id, description, required_skill_tag,
                excluded_skill_tag, target_type
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                item["scope_id"],
                item["description"],
                item.get("required_skill_tag"),
                item.get("excluded_skill_tag"),
                item.get("target_type"),
            ),
        )

    for item in seed.get("arkgrid_core_categories", []):
        connection.execute(
            """
            INSERT INTO arkgrid_core_effect_categories(
                category, target_stat, operator, calculation_stage,
                single_cast_applied, source_document_id, verification_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["category"],
                item["target_stat"],
                item["operator"],
                item["calculation_stage"],
                item["single_cast_applied"],
                "weather-artist-arkgrid-core-reference-v1",
                "VERIFIED",
            ),
        )

    for item in seed.get("skills", []):
        connection.execute(
            """
            INSERT INTO skills(
                skill_id, class_id, canonical_name, patch_version,
                verification_status
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                item["skill_id"],
                item["class_id"],
                item["canonical_name"],
                patch_version,
                item["verification_status"],
            ),
        )
        for alias in item.get("aliases", []):
            connection.execute(
                "INSERT INTO skill_aliases(skill_id, alias) VALUES (?, ?)",
                (item["skill_id"], alias),
            )
        for tag in item.get("tags", []):
            tag_source = (
                (item.get("variant") or {}).get("source_document_id")
                or "audit-v2.1.0"
            )
            connection.execute(
                """
                INSERT INTO skill_tags(
                    skill_id, tag, source_document_id, verification_status
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    item["skill_id"],
                    tag,
                    tag_source,
                    item["verification_status"],
                ),
            )
        variant = item.get("variant")
        if variant:
            connection.execute(
                """
                INSERT INTO skill_variants(
                    variant_id, skill_id, coefficient, constant_value, hit_count,
                    skill_category, class_skill_category, direction_type,
                    cast_type, can_critical, max_hold, source_document_id,
                    verification_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    variant["variant_id"],
                    item["skill_id"],
                    variant.get("coefficient"),
                    variant.get("constant_value"),
                    variant.get("hit_count"),
                    variant.get("skill_category"),
                    variant.get("class_skill_category"),
                    variant.get("direction_type"),
                    variant.get("cast_type"),
                    variant.get("can_critical"),
                    variant.get("max_hold"),
                    variant.get("source_document_id"),
                    variant["verification_status"],
                ),
            )
            for hit in variant.get("hits", []):
                connection.execute(
                    """
                    INSERT INTO skill_hits(
                        variant_id, hit_index, coefficient, constant_value
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        variant["variant_id"],
                        hit["hit_index"],
                        hit.get("coefficient"),
                        hit.get("constant_value"),
                    ),
                )

    for item in seed.get("effects", []):
        connection.execute(
            """
            INSERT INTO effects(
                effect_id, canonical_name, system_name, valid_from_patch,
                source_document_id, verification_status
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                item["effect_id"],
                item["canonical_name"],
                item["system_name"],
                patch_version,
                item.get("source_document_id"),
                item["verification_status"],
            ),
        )
        connection.execute(
            """
            INSERT INTO effect_levels(effect_id, level, verification_status)
            VALUES (?, 0, ?)
            """,
            (item["effect_id"], item["verification_status"]),
        )
        for component_index, component in enumerate(item.get("components", [])):
            connection.execute(
                """
                INSERT INTO effect_components(
                    effect_id, level, component_index, target_stat, operator,
                    value, stacking_group, scope_id, condition_id, formula_id
                ) VALUES (?, 0, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["effect_id"],
                    component_index,
                    component["target_stat"],
                    component["operator"],
                    component.get("value"),
                    component.get("stacking_group"),
                    component.get("scope_id"),
                    component.get("condition_id"),
                    component.get("formula_id"),
                ),
            )

    boss = seed["boss"]
    connection.execute(
        """
        INSERT INTO bosses(
            boss_id, canonical_name, species, defense, damage_taken_multiplier,
            patch_version, source_document_id, verification_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            boss["boss_id"],
            boss["canonical_name"],
            boss.get("species"),
            boss.get("defense"),
            boss.get("damage_taken_multiplier"),
            patch_version,
            boss.get("source_document_id"),
            boss["verification_status"],
        ),
    )
    scenario = seed["scenario"]
    connection.execute(
        """
        INSERT INTO scenario_presets(
            scenario_preset_id, boss_id, calculation_mode, payload_json,
            source_document_id, verification_status
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            scenario["scenario_preset_id"],
            scenario["boss_id"],
            scenario["calculation_mode"],
            json.dumps(scenario.get("payload", {}), ensure_ascii=False),
            scenario.get("source_document_id"),
            scenario["verification_status"],
        ),
    )
    for key, value in (
        scenario.get("payload", {}).get("external_buffs", {}).items()
    ):
        connection.execute(
            """
            INSERT INTO external_buffs(
                scenario_preset_id, buff_key, value, source_document_id,
                verification_status
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                scenario["scenario_preset_id"],
                key,
                str(value),
                scenario.get("source_document_id"),
                scenario["verification_status"],
            ),
        )
    connection.execute(
        """
        INSERT INTO rounding_rules(ruleset_version, stage, rounding_mode)
        VALUES (?, ?, ?)
        """,
        ("current-v2.4.1", "final_damage", "FLOOR"),
    )


def build_database(
    output_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
    seed_path: Path = DEFAULT_SEED,
    *,
    force: bool = False,
) -> Path:
    if output_path.exists():
        if not force:
            raise FileExistsError(
                f"{output_path} already exists; pass --force to replace it"
            )
        output_path.unlink()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema = schema_path.read_text(encoding="utf-8")
    seed = load_json(seed_path)
    connection = sqlite3.connect(output_path)
    try:
        connection.executescript(schema)
        with connection:
            seed_database(connection, seed)
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"foreign-key violations: {violations}")
    except Exception:
        connection.close()
        if output_path.exists():
            output_path.unlink()
        raise
    finally:
        try:
            connection.close()
        except Exception:
            pass
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    output = build_database(
        args.output,
        args.schema,
        args.seed,
        force=args.force,
    )
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
