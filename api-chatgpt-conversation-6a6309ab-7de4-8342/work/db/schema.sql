PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS patch_versions (
    patch_version TEXT PRIMARY KEY,
    observed_at TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS source_documents (
    source_document_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL CHECK (source_type IN (
        'OFFICIAL_API', 'OFFICIAL_TOOLTIP', 'USER_VERIFIED',
        'WORKBOOK_FORMULA', 'EXPERIMENTAL_MEASUREMENT',
        'COMMUNITY_REFERENCE', 'LEGACY_EXAMPLE', 'DERIVED'
    )),
    source_locator TEXT NOT NULL,
    source_excerpt TEXT NOT NULL DEFAULT '',
    verification_status TEXT NOT NULL CHECK (verification_status IN (
        'VERIFIED', 'PROVISIONAL', 'DEPRECATED', 'REJECTED'
    )),
    verified_by TEXT,
    verified_at TEXT
);

CREATE TABLE IF NOT EXISTS parser_versions (
    parser_version TEXT PRIMARY KEY,
    valid_from_patch TEXT REFERENCES patch_versions(patch_version),
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS ruleset_versions (
    ruleset_version TEXT PRIMARY KEY,
    valid_from_patch TEXT REFERENCES patch_versions(patch_version),
    source_document_id TEXT REFERENCES source_documents(source_document_id),
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS db_releases (
    db_release TEXT PRIMARY KEY,
    patch_version TEXT NOT NULL REFERENCES patch_versions(patch_version),
    created_at TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id TEXT PRIMARY KEY,
    class_id TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    patch_version TEXT NOT NULL REFERENCES patch_versions(patch_version),
    verification_status TEXT NOT NULL,
    UNIQUE(class_id, canonical_name, patch_version)
);

CREATE TABLE IF NOT EXISTS skill_aliases (
    skill_id TEXT NOT NULL REFERENCES skills(skill_id),
    alias TEXT NOT NULL,
    PRIMARY KEY (skill_id, alias)
);

CREATE TABLE IF NOT EXISTS skill_variants (
    variant_id TEXT PRIMARY KEY,
    skill_id TEXT NOT NULL REFERENCES skills(skill_id),
    coefficient TEXT,
    constant_value TEXT,
    hit_count INTEGER,
    skill_category TEXT,
    class_skill_category TEXT,
    direction_type TEXT,
    cast_type TEXT,
    can_critical INTEGER,
    max_hold INTEGER,
    source_document_id TEXT REFERENCES source_documents(source_document_id),
    verification_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skill_hits (
    variant_id TEXT NOT NULL REFERENCES skill_variants(variant_id),
    hit_index INTEGER NOT NULL,
    coefficient TEXT,
    constant_value TEXT,
    PRIMARY KEY (variant_id, hit_index)
);

CREATE TABLE IF NOT EXISTS skill_tags (
    skill_id TEXT NOT NULL REFERENCES skills(skill_id),
    tag TEXT NOT NULL,
    source_document_id TEXT REFERENCES source_documents(source_document_id),
    verification_status TEXT NOT NULL,
    PRIMARY KEY (skill_id, tag)
);

CREATE TABLE IF NOT EXISTS arkgrid_core_effect_categories (
    category TEXT PRIMARY KEY,
    target_stat TEXT NOT NULL,
    operator TEXT NOT NULL,
    calculation_stage TEXT NOT NULL,
    single_cast_applied INTEGER NOT NULL CHECK (single_cast_applied IN (0, 1)),
    source_document_id TEXT REFERENCES source_documents(source_document_id),
    verification_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS effects (
    effect_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    system_name TEXT NOT NULL,
    valid_from_patch TEXT REFERENCES patch_versions(patch_version),
    valid_to_patch TEXT,
    source_document_id TEXT REFERENCES source_documents(source_document_id),
    verification_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS effect_aliases (
    effect_id TEXT NOT NULL REFERENCES effects(effect_id),
    alias TEXT NOT NULL,
    PRIMARY KEY (effect_id, alias)
);

CREATE TABLE IF NOT EXISTS effect_levels (
    effect_id TEXT NOT NULL REFERENCES effects(effect_id),
    level INTEGER NOT NULL,
    verification_status TEXT NOT NULL,
    PRIMARY KEY (effect_id, level)
);

CREATE TABLE IF NOT EXISTS effect_scopes (
    scope_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    required_skill_tag TEXT,
    excluded_skill_tag TEXT,
    target_type TEXT
);

CREATE TABLE IF NOT EXISTS effect_conditions (
    condition_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    formula_id TEXT
);

CREATE TABLE IF NOT EXISTS stacking_groups (
    stacking_group TEXT PRIMARY KEY,
    operator TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS effect_components (
    effect_id TEXT NOT NULL REFERENCES effects(effect_id),
    level INTEGER NOT NULL,
    component_index INTEGER NOT NULL,
    target_stat TEXT NOT NULL,
    operator TEXT NOT NULL,
    value TEXT,
    stacking_group TEXT REFERENCES stacking_groups(stacking_group),
    scope_id TEXT REFERENCES effect_scopes(scope_id),
    condition_id TEXT REFERENCES effect_conditions(condition_id),
    formula_id TEXT,
    PRIMARY KEY (effect_id, level, component_index),
    FOREIGN KEY (effect_id, level) REFERENCES effect_levels(effect_id, level)
);

CREATE TABLE IF NOT EXISTS system_effect_levels (
    system_name TEXT NOT NULL,
    system_key TEXT NOT NULL,
    level_key TEXT NOT NULL,
    effect_id TEXT REFERENCES effects(effect_id),
    value TEXT,
    source_document_id TEXT REFERENCES source_documents(source_document_id),
    verification_status TEXT NOT NULL,
    PRIMARY KEY (system_name, system_key, level_key)
);

CREATE TABLE IF NOT EXISTS bosses (
    boss_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    species TEXT,
    defense TEXT,
    damage_taken_multiplier TEXT,
    patch_version TEXT REFERENCES patch_versions(patch_version),
    source_document_id TEXT REFERENCES source_documents(source_document_id),
    verification_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS boss_phases (
    boss_id TEXT NOT NULL REFERENCES bosses(boss_id),
    phase_id TEXT NOT NULL,
    defense TEXT,
    damage_taken_multiplier TEXT,
    PRIMARY KEY (boss_id, phase_id)
);

CREATE TABLE IF NOT EXISTS scenario_presets (
    scenario_preset_id TEXT PRIMARY KEY,
    boss_id TEXT REFERENCES bosses(boss_id),
    calculation_mode TEXT NOT NULL CHECK (calculation_mode IN (
        'STRICT_VERIFIED', 'ESTIMATE_WITH_FALLBACK'
    )),
    payload_json TEXT NOT NULL,
    source_document_id TEXT REFERENCES source_documents(source_document_id),
    verification_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS external_buffs (
    scenario_preset_id TEXT NOT NULL REFERENCES scenario_presets(scenario_preset_id),
    buff_key TEXT NOT NULL,
    value TEXT NOT NULL,
    source_document_id TEXT REFERENCES source_documents(source_document_id),
    verification_status TEXT NOT NULL,
    PRIMARY KEY (scenario_preset_id, buff_key)
);

CREATE TABLE IF NOT EXISTS rounding_rules (
    ruleset_version TEXT NOT NULL REFERENCES ruleset_versions(ruleset_version),
    stage TEXT NOT NULL,
    rounding_mode TEXT NOT NULL,
    PRIMARY KEY (ruleset_version, stage)
);

CREATE TABLE IF NOT EXISTS api_snapshots (
    api_snapshot_id TEXT PRIMARY KEY,
    character_name TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    content_sha256 TEXT
);

CREATE TABLE IF NOT EXISTS normalized_facts (
    api_snapshot_id TEXT NOT NULL REFERENCES api_snapshots(api_snapshot_id),
    fact_path TEXT NOT NULL,
    fact_value_json TEXT NOT NULL,
    parser_version TEXT NOT NULL REFERENCES parser_versions(parser_version),
    parsed INTEGER NOT NULL,
    PRIMARY KEY (api_snapshot_id, fact_path, parser_version)
);

CREATE TABLE IF NOT EXISTS calculation_runs (
    calculation_run_id TEXT PRIMARY KEY,
    api_snapshot_id TEXT REFERENCES api_snapshots(api_snapshot_id),
    parser_version TEXT NOT NULL REFERENCES parser_versions(parser_version),
    ruleset_version TEXT NOT NULL REFERENCES ruleset_versions(ruleset_version),
    db_release TEXT NOT NULL REFERENCES db_releases(db_release),
    scenario_preset_id TEXT NOT NULL REFERENCES scenario_presets(scenario_preset_id),
    calculation_engine_commit TEXT,
    created_at TEXT NOT NULL,
    result_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calculation_inputs (
    calculation_run_id TEXT NOT NULL REFERENCES calculation_runs(calculation_run_id),
    input_path TEXT NOT NULL,
    input_value_json TEXT NOT NULL,
    PRIMARY KEY (calculation_run_id, input_path)
);

CREATE TABLE IF NOT EXISTS applied_effects (
    calculation_run_id TEXT NOT NULL REFERENCES calculation_runs(calculation_run_id),
    effect_key TEXT NOT NULL,
    parsed INTEGER NOT NULL,
    eligible INTEGER NOT NULL,
    applied INTEGER NOT NULL,
    source_document_id TEXT REFERENCES source_documents(source_document_id),
    payload_json TEXT NOT NULL,
    PRIMARY KEY (calculation_run_id, effect_key)
);

CREATE TABLE IF NOT EXISTS excluded_effects (
    calculation_run_id TEXT NOT NULL REFERENCES calculation_runs(calculation_run_id),
    effect_key TEXT NOT NULL,
    parsed INTEGER NOT NULL,
    eligible INTEGER NOT NULL,
    applied INTEGER NOT NULL,
    excluded_reason TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    PRIMARY KEY (calculation_run_id, effect_key)
);

CREATE TABLE IF NOT EXISTS validation_cases (
    validation_case_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    api_snapshot_id TEXT REFERENCES api_snapshots(api_snapshot_id),
    patch_version TEXT REFERENCES patch_versions(patch_version),
    verification_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_assertions (
    validation_case_id TEXT NOT NULL REFERENCES validation_cases(validation_case_id),
    assertion_key TEXT NOT NULL,
    expected_value_json TEXT NOT NULL,
    tolerance TEXT,
    PRIMARY KEY (validation_case_id, assertion_key)
);
