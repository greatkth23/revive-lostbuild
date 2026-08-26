import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';
import { buildSnapshotSchema } from '@weather-artist/contracts';
import {
  calculateAttackPower,
  parseBuildSnapshot,
  resolveArkGridGradeValues,
  tooltipToText
} from './index.js';

const rawFixturePath = new URL(
  '../../../api-chatgpt-conversation-6a6309ab-7de4-8342/outputs/봄날꽃씨_우레바람_current-v2.7.2_api_raw.json',
  import.meta.url
);

function loadRawFixture(): unknown {
  return JSON.parse(readFileSync(rawFixturePath, 'utf8'));
}

describe('Weather Artist raw endpoint parser', () => {
  test('uses verified character calculation inputs only for their catalogued character', () => {
    // Break caught: every Weather Artist silently inherits 봄날꽃씨 account and pet bonuses.
    const verified = parseBuildSnapshot(loadRawFixture());
    expect(verified.build.calculationInputs).toEqual({
      accountBonuses: {
        flatMainStat: '2133',
        collectionDemonDamagePercent: '0.065',
        source: 'current-v2.7.2-character-inputs-v1:봄날꽃씨',
        verified: true
      },
      pet: {
        mainStatPercent: '0.01',
        additionalDamagePercent: '0.01',
        demonDamagePercent: '0.005',
        source: 'current-v2.7.2-character-inputs-v1:봄날꽃씨',
        verified: true
      }
    });
    expect(calculateAttackPower(verified).accountMainStatFlat).toBe('2133');

    const raw = structuredClone(loadRawFixture()) as {
      characterName: string;
      responses: { profiles: { CharacterName: string } };
    };
    raw.characterName = '검증되지않은기상술사';
    raw.responses.profiles.CharacterName = '검증되지않은기상술사';
    const unverified = parseBuildSnapshot(raw);
    expect(unverified.build.calculationInputs).toEqual({
      accountBonuses: {
        flatMainStat: '0',
        collectionDemonDamagePercent: '0',
        source: 'no verified character override',
        verified: false
      },
      pet: {
        mainStatPercent: '0',
        additionalDamagePercent: '0',
        demonDamagePercent: '0',
        source: 'no verified character override',
        verified: false
      }
    });
    expect(calculateAttackPower(unverified).accountMainStatFlat).toBe('0');
    expect(unverified.warnings).toEqual(expect.arrayContaining([
      expect.objectContaining({ severity: 'incomplete', path: 'calculationInputs.accountBonuses' }),
      expect.objectContaining({ severity: 'incomplete', path: 'calculationInputs.pet' })
    ]));
  });

  test('records supported skill levels and warns when a verified coefficient level differs', () => {
    // Break caught: level-14 motion coefficients are presented as verified for a differently levelled API skill.
    const verified = parseBuildSnapshot(loadRawFixture());
    expect(verified.build.combatSkills.levelsByName).toMatchObject({
      '우레바람': 1,
      '회오리 걸음': 14,
      '몰아치기': 14,
      '바람송곳': 14,
      '칼바람': 14
    });
    expect(verified.warnings.some((item) => item.path.includes('.Level'))).toBe(false);

    const raw = structuredClone(loadRawFixture()) as {
      responses: { combatSkills: Array<{ Name: string; Level: number }> };
    };
    const wind = raw.responses.combatSkills.find((skill) => skill.Name === '바람송곳')!;
    wind.Level = 13;
    const mismatch = parseBuildSnapshot(raw);
    const index = raw.responses.combatSkills.indexOf(wind);
    expect(mismatch.warnings).toContainEqual(expect.objectContaining({
      code: 'SKILL_LEVEL_COEFFICIENT_MISMATCH',
      severity: 'incomplete',
      path: `combatSkills[${index}].Level`
    }));
    expect(mismatch.warnings.some((item) => item.message.includes('공간 가르기'))).toBe(false);
  });

  test('rejects present-but-null or wrong-shaped endpoint payloads and an empty character name', () => {
    // Break caught: object()/array() coercion silently turning malformed endpoint responses into zero stats.
    const malformed: Array<[string, unknown]> = [
      ['profiles', null],
      ['equipment', {}],
      ['avatars', {}],
      ['combatSkills', {}],
      ['engravings', []],
      ['cards', []],
      ['gems', []],
      ['arkPassive', []],
      ['arkGrid', []]
    ];
    for (const [endpoint, value] of malformed) {
      const raw = structuredClone(loadRawFixture()) as { responses: Record<string, unknown> };
      raw.responses[endpoint] = value;
      expect(() => parseBuildSnapshot(raw), endpoint).toThrow(`responses.${endpoint}`);
    }

    const nameless = structuredClone(loadRawFixture()) as {
      characterName?: string;
      responses: { profiles: { CharacterName?: string } };
    };
    nameless.characterName = '';
    nameless.responses.profiles.CharacterName = '';
    expect(() => parseBuildSnapshot(nameless)).toThrow('profiles.CharacterName');
  });

  test('rejects non-object members from every endpoint array the parser consumes', () => {
    // Break caught: valid containers with null members were normalized into zero-valued records.
    const cases: Array<[string, (responses: Record<string, any>) => void]> = [
      ['responses.profiles.Stats[0]', (responses) => { responses.profiles.Stats[0] = null; }],
      ['responses.equipment[0]', (responses) => { responses.equipment[0] = null; }],
      ['responses.avatars[0]', (responses) => { responses.avatars[0] = null; }],
      ['responses.combatSkills[0]', (responses) => { responses.combatSkills[0] = null; }],
      ['responses.combatSkills[0].Tripods[0]', (responses) => { responses.combatSkills[0].Tripods[0] = null; }],
      ['responses.engravings.ArkPassiveEffects[0]', (responses) => { responses.engravings.ArkPassiveEffects[0] = null; }],
      ['responses.cards.Cards[0]', (responses) => { responses.cards.Cards[0] = null; }],
      ['responses.cards.Effects[0]', (responses) => { responses.cards.Effects[0] = null; }],
      ['responses.cards.Effects[0].Items[0]', (responses) => { responses.cards.Effects[0].Items[0] = null; }],
      ['responses.gems.Gems[0]', (responses) => { responses.gems.Gems[0] = null; }],
      ['responses.arkPassive.Points[0]', (responses) => { responses.arkPassive.Points[0] = null; }],
      ['responses.arkPassive.Effects[0]', (responses) => { responses.arkPassive.Effects[0] = null; }],
      ['responses.arkGrid.Slots[0]', (responses) => { responses.arkGrid.Slots[0] = null; }],
      ['responses.arkGrid.Slots[0].Gems[0]', (responses) => { responses.arkGrid.Slots[0].Gems[0] = null; }],
      ['responses.arkGrid.Effects[0]', (responses) => { responses.arkGrid.Effects[0] = null; }]
    ];

    for (const [path, mutate] of cases) {
      const raw = structuredClone(loadRawFixture()) as { responses: Record<string, any> };
      mutate(raw.responses);
      expect(() => parseBuildSnapshot(raw), path).toThrow(path);
    }
  });

  test('accepts legacy engraving Effects fallback and rejects payloads with neither valid collection', () => {
    // Break caught: validation rejected shapes that parseEngravings intentionally supports.
    for (const arkPassiveShape of ['missing', 'null', 'empty'] as const) {
      const raw = structuredClone(loadRawFixture()) as {
        responses: { engravings: { ArkPassiveEffects?: unknown; Effects?: unknown } };
      };
      const engravings = raw.responses.engravings;
      engravings.Effects = engravings.ArkPassiveEffects;
      if (arkPassiveShape === 'missing') delete engravings.ArkPassiveEffects;
      else engravings.ArkPassiveEffects = arkPassiveShape === 'null' ? null : [];

      expect(parseBuildSnapshot(raw).build.engravings).toMatchObject({
        names: ['돌격대장', '아드레날린', '원한', '질량 증가', '타격의 대가'],
        stoneLevelTotal: 5,
        stoneBaseAttackPercent: '0.015'
      });
    }

    const invalidCases: Array<[unknown, unknown, string]> = [
      [null, null, 'responses.engravings.Effects'],
      [[], undefined, 'responses.engravings.Effects'],
      [null, [null], 'responses.engravings.Effects[0]']
    ];
    for (const [arkPassiveEffects, effects, expectedPath] of invalidCases) {
      const raw = structuredClone(loadRawFixture()) as {
        responses: { engravings: { ArkPassiveEffects?: unknown; Effects?: unknown } };
      };
      raw.responses.engravings.ArkPassiveEffects = arkPassiveEffects;
      raw.responses.engravings.Effects = effects;
      expect(() => parseBuildSnapshot(raw), expectedPath).toThrow(expectedPath);
    }
  });

  test('normalizes all nine endpoint payloads into the versioned snapshot contract', () => {
    // Break caught: omitting one endpoint or leaking numeric values as JS numbers.
    const snapshot = parseBuildSnapshot(loadRawFixture());

    expect(buildSnapshotSchema.safeParse(snapshot).success).toBe(true);
    expect(snapshot.schemaVersion).toBe('1');
    expect(snapshot.characterName).toBe('봄날꽃씨');
    expect(snapshot.build.endpointSources).toEqual([
      'profiles',
      'equipment',
      'avatars',
      'combatSkills',
      'engravings',
      'cards',
      'gems',
      'arkPassive',
      'arkGrid'
    ]);
    expect(snapshot.build.profile.className).toBe('기상술사');
    expect(snapshot.build.equipment.items).toHaveLength(17);
    expect(snapshot.build.avatars.items).toHaveLength(11);
    expect(snapshot.build.gems.items).toHaveLength(11);
    expect((snapshot.build.arkPassive as typeof snapshot.build.arkPassive & { points: unknown[] }).points).toHaveLength(3);
    expect(snapshot.build.combatSkills.skillNames).toHaveLength(22);
    expect(snapshot.build.arkGrid.cores).toHaveLength(6);
    const arkGrid = snapshot.build.arkGrid as typeof snapshot.build.arkGrid & {
      activeGems: Array<{ path: string; values: Record<string, string> }>;
      activeAggregateEffects: Array<{ path: string; name: string; values: Record<string, string> }>;
    };
    expect(arkGrid.activeGems).toHaveLength(24);
    expect(arkGrid.activeGems[0]).toMatchObject({
      path: 'arkGrid.Slots[0].Gems[0]',
      values: { additionalDamagePercent: '0.004' }
    });
    expect(arkGrid.activeAggregateEffects).toHaveLength(3);
    expect(arkGrid.activeAggregateEffects.at(-1)).toMatchObject({
      path: 'arkGrid.Effects[4]',
      name: '보스 피해',
      values: { bossDamagePercent: '0.0425' }
    });
  });

  test('preserves only safe HTTPS API icon URLs for equipment, avatars, and gems', () => {
    // Break caught: UI receives normalized data without official image URLs and must either copy assets or show blank cards.
    const raw = structuredClone(loadRawFixture()) as { responses: { equipment: Array<Record<string, unknown>>; avatars: Array<Record<string, unknown>>; gems: { Gems: Array<Record<string, unknown>> } } };
    raw.responses.equipment[0]!.Icon = 'https://cdn.example.test/equipment.png';
    raw.responses.avatars[0]!.Icon = 'http://unsafe.example.test/avatar.png';
    raw.responses.gems.Gems[0]!.Icon = 'https://cdn.example.test/gem.png';
    const build = parseBuildSnapshot(raw).build as typeof parseBuildSnapshot extends never ? never : {
      equipment: { items: Array<{ iconUrl?: string }> };
      avatars: { items: Array<{ iconUrl?: string }> };
      gems: { items: Array<{ iconUrl?: string }> };
    };

    expect(build.equipment.items[0]?.iconUrl).toBe('https://cdn.example.test/equipment.png');
    expect(build.avatars.items[0]?.iconUrl).toBeUndefined();
    expect(build.gems.items[0]?.iconUrl).toBe('https://cdn.example.test/gem.png');
  });

  test('parses equipment, armlet, accessory, avatar, pet, engraving, stone, and card checkpoints', () => {
    // Break caught: collapsing armlet base attack into final attack or skipping non-skill sections.
    const { build } = parseBuildSnapshot(loadRawFixture());

    expect(build.equipment).toMatchObject({
      mainStat: '747822',
      baseWeaponAttack: '241367',
      weaponAttackFlat: '10969',
      weaponAttackPercent: '0.06',
      baseAttackPowerFlat: '2030',
      attackPowerPercent: '0.019',
      weaponAdditionalDamage: '0.3',
      necklaceAdditionalDamage: '0.026',
      necklaceDamageToEnemy: '0.012',
      criticalRate: '0.073',
      criticalDamage: '0.132',
      braceletCriticalHitDamage: '0.015'
    });
    expect(build.equipment.items.find((item) => item.type === '완갑')?.values.baseAttackPowerFlat).toBe('2030');
    expect(build.equipment.items.some((item) => item.type === '팔찌')).toBe(true);
    expect(build.avatars.mainStatPercent).toBe('0.08');
    expect(build.calculationInputs.pet).toMatchObject({ mainStatPercent: '0.01', additionalDamagePercent: '0.01' });
    expect(build.engravings.stoneLevelTotal).toBe(5);
    expect(build.engravings.stoneBaseAttackPercent).toBe('0.015');
    expect(build.engravings.effects['아드레날린']).toMatchObject({
      attackPowerPercent: '0.1038',
      criticalRate: '0.2'
    });
    expect(build.cards.damagePercent).toBe('0.15');
  });

  test('derives enlightenment karma weapon attack and regular skill gems', () => {
    // Break caught: treating the karma point Value as percent or double-counting duplicate skill gems.
    const { build } = parseBuildSnapshot(loadRawFixture());

    expect(build.arkPassive.karmaWeaponAttackPercent).toBe('0.028');
    expect(build.gems.baseAttackPercent).toBe('0.104');
    expect(build.gems.skillEffects.filter((effect) => effect.skillName === '바람송곳')).toEqual([
      expect.objectContaining({ effectType: 'damage', value: '0.4' }),
      expect.objectContaining({ effectType: 'cooldownReduction', value: '0.22' })
    ]);
  });

  test('warns when a regular gem contains an unclassified skill-damage sentence', () => {
    // Break caught: an unfamiliar regular-gem damage wording silently disappears while the gem remains active.
    const raw = structuredClone(loadRawFixture()) as {
      responses: { gems: { Gems: Array<Record<string, unknown>> } };
    };
    const tooltip = '[바람송곳] 피해량이 77.0%만큼 변한다';
    raw.responses.gems.Gems[0]!.Tooltip = tooltip;

    expect(parseBuildSnapshot(raw).warnings).toContainEqual(expect.objectContaining({
      code: 'UNPARSED_DAMAGE_TOOLTIP',
      severity: 'incomplete',
      path: 'gems.Gems[0].Tooltip',
      rawValue: tooltip
    }));
  });

  test('warns when a regular gem mixes a recognized effect with an unclassified damage clause', () => {
    // Break caught: one parsed gem damage span suppresses a warning for a second unknown damage-bearing span.
    const raw = structuredClone(loadRawFixture()) as {
      responses: { gems: { Gems: Array<Record<string, unknown>> } };
    };
    const tooltip = '바람송곳 피해량이 40.0% 증가한다. 적에게 총 피해량의 77.0%에 해당하는 폭풍 피해를 준다.';
    delete raw.responses.gems.Gems[0]!.Tooltip;
    raw.responses.gems.Gems[0]!.ToolTip = tooltip;

    expect(parseBuildSnapshot(raw).warnings).toContainEqual(expect.objectContaining({
      code: 'UNPARSED_DAMAGE_TOOLTIP',
      severity: 'incomplete',
      path: 'gems.Gems[0].ToolTip',
      rawValue: tooltip
    }));
  });

  test('warns when an Ark Passive effect has an unclassified damage value', () => {
    // Break caught: an unknown active Ark Passive damage node is labelled ineligible instead of incomplete.
    const raw = structuredClone(loadRawFixture()) as {
      responses: { arkPassive: { Effects: Array<Record<string, unknown>> } };
    };
    const tooltip = '적에게 주는 피해량이 7.0%만큼 변한다';
    raw.responses.arkPassive.Effects.push({ Name: '미분류 노드', Description: '진화 2티어 미분류 노드 Lv.1', ToolTip: tooltip });
    const index = raw.responses.arkPassive.Effects.length - 1;

    expect(parseBuildSnapshot(raw).warnings).toContainEqual(expect.objectContaining({
      code: 'UNPARSED_DAMAGE_TOOLTIP',
      severity: 'incomplete',
      path: `arkPassive.Effects[${index}].ToolTip`,
      rawValue: tooltip
    }));
  });

  test('warns on the exact Ark Passive field when parsed and unclassified damage clauses coexist', () => {
    // Break caught: a parsed 바람의 길 value suppresses an unknown clause and the warning always claims ToolTip.
    const raw = structuredClone(loadRawFixture()) as {
      responses: { arkPassive: { Effects: Array<Record<string, unknown>> } };
    };
    const tooltip = '피해량이 2.4% 증가한다. 적에게 총 피해량의 77.0%에 해당하는 폭풍 피해를 준다.';
    raw.responses.arkPassive.Effects.push({
      Name: '바람의 길',
      Description: '깨달음 3티어 바람의 길 Lv.2',
      Tooltip: tooltip
    });
    const index = raw.responses.arkPassive.Effects.length - 1;

    expect(parseBuildSnapshot(raw).warnings).toContainEqual(expect.objectContaining({
      code: 'UNPARSED_DAMAGE_TOOLTIP',
      severity: 'incomplete',
      path: `arkPassive.Effects[${index}].Tooltip`,
      rawValue: tooltip
    }));
  });

  test('uses ArkGrid Effects aggregate values instead of adding the same active-gem effects twice', () => {
    // Break caught: gem + Effects[] double counting raises all three base categories.
    const { arkGrid } = parseBuildSnapshot(loadRawFixture()).build;

    expect(arkGrid.gemEffects).toEqual({
      attackPowerPercent: '0.0139',
      additionalDamagePercent: '0.0416',
      bossDamagePercent: '0.042'
    });
    expect(arkGrid.aggregateEffects).toEqual({
      attackPowerPercent: '0.0143',
      additionalDamagePercent: '0.042',
      bossDamagePercent: '0.0425'
    });
    expect(arkGrid.effectiveBaseEffects).toEqual(arkGrid.aggregateEffects);
    expect(arkGrid.attackPowerPercent).toBe('0.0411');
  });

  test('selects the relic or ancient side of slash values and keeps 18P, 19P, and 20P factors separate', () => {
    // Break caught: choosing the wrong slash branch or summing repeated multiplicative thresholds.
    expect(resolveArkGridGradeValues('피해량이 8 / 18% 증가', '유물')).toBe('피해량이 8% 증가');
    expect(resolveArkGridGradeValues('피해량이 8 / 18% 증가', '고대')).toBe('피해량이 18% 증가');

    const factors = parseBuildSnapshot(loadRawFixture()).build.arkGrid.coreDamageFactors;
    const repeated = factors.filter(
      (factor) => factor.coreName.includes('우산의 춤')
        && factor.category === 'skillDamagePercent'
        && factor.value === '0.002'
    );
    expect(repeated.map((factor) => factor.requiredPoints)).toEqual([18, 19, 20]);
  });

  test('parses calculator-connected Ark Grid speed, flat weapon attack, and incoming critical-hit damage', () => {
    // Break caught: activated core categories present in Python becoming silent zeroes in TypeScript.
    const raw = structuredClone(loadRawFixture()) as { responses: { arkGrid: unknown } };
    raw.responses.arkGrid = {
      Slots: [{
        Index: 0,
        Name: '혼돈의 별 코어 : 회심',
        Grade: '고대',
        Point: 10,
        Tooltip: JSON.stringify({ Element_000: { value: [
          '코어 옵션',
          '[10P] 공격 및 이동 속도가 3.0% 증가한다. 무기 공격력이 2.25% 증가하고, 추가로 1,000 증가한다. 입는 치명타 피해량을 2.0% 증가시킨다.',
          '분해불가'
        ].join('<BR>') } }),
        Gems: []
      }],
      Effects: []
    };

    const { arkGrid } = parseBuildSnapshot(raw).build;
    expect(arkGrid.coreEffects).toMatchObject({
      attackSpeed: '0.03',
      moveSpeed: '0.03',
      weaponAttackFlat: '1000',
      weaponAttackPercent: '0.0225',
      criticalHitDamagePercent: '0.02'
    });
    expect(arkGrid.coreDamageFactors).toContainEqual(expect.objectContaining({
      category: 'criticalHitDamagePercent',
      value: '0.02'
    }));
  });

  test('warns when an activated Ark Grid core damage option has no recognized component', () => {
    // Break caught: [nP] was found, so an unrecognized active damage option disappeared without warning.
    const raw = structuredClone(loadRawFixture()) as { responses: { arkGrid: unknown } };
    raw.responses.arkGrid = {
      Slots: [{
        Index: 0,
        Name: '알 수 없는 코어',
        Grade: '고대',
        Point: 10,
        Tooltip: JSON.stringify({ Element_000: { value: '코어 옵션<BR>[10P] 미지의 공격 피해가 7.0% 증가한다.<BR>분해불가' } }),
        Gems: []
      }],
      Effects: []
    };

    expect(parseBuildSnapshot(raw).warnings).toContainEqual(expect.objectContaining({
      code: 'UNPARSED_DAMAGE_TOOLTIP',
      severity: 'incomplete',
      path: 'arkGrid.Slots[0].Tooltip.options[0]'
    }));
  });

  test('replaces an Ark Grid factor once in both factors and normalized core totals', () => {
    // Break caught: pre-adding the replacement made normalized coreEffects equal 2r while the factor was r.
    const raw = structuredClone(loadRawFixture()) as { responses: { arkGrid: unknown } };
    raw.responses.arkGrid = {
      Slots: [{
        Index: 0,
        Name: '질서의 해 코어 : 바람의 칼날',
        Grade: '고대',
        Point: 14,
        Tooltip: JSON.stringify({ Element_000: { value: [
          '코어 옵션',
          '[10P] 칼바람의 피해량이 10.0% 증가한다.',
          "[14P] '운명: 바람의 칼날' 효과의 피해 증가량을 20.0%로 변경한다.",
          '분해불가'
        ].join('<BR>') } }),
        Gems: []
      }],
      Effects: []
    };

    const { arkGrid } = parseBuildSnapshot(raw).build;
    expect(arkGrid.coreEffects.skillDamagePercent).toBe('0.2');
    expect(arkGrid.coreDamageFactors).toContainEqual(expect.objectContaining({
      category: 'skillDamagePercent',
      scopeValue: ['칼바람'],
      value: '0.2',
      contributionPaths: [
        'arkGrid.Slots[0].Tooltip.options[0]',
        'arkGrid.Slots[0].Tooltip.options[1]'
      ]
    }));
  });

  test('retains selected tripod effects and marks the additional Space Slash hit as embedded provenance', () => {
    // Break caught: dropping the official tooltip or later multiplying the 94.8% embedded hit again.
    const selected = parseBuildSnapshot(loadRawFixture()).build.combatSkills.selectedTripods;
    const spaceSlash = selected.find((tripod) => tripod.skillName === '몰아치기' && tripod.name === '공간베기');

    expect(spaceSlash?.damageEffects).toContainEqual({
      type: 'ADDITIONAL_ATTACK',
      label: '추가 공격 피해',
      percent: '0.948',
      multiplier: '1.948',
      applicationMode: 'EMBEDDED_MOTION_HIT'
    });
  });

  test('warns with the raw selected-tripod tooltip when a damage clause is not classified', () => {
    // Break caught: a selected extra-hit tripod becomes a silent zero when its sentence is outside known multiplier patterns.
    const raw = structuredClone(loadRawFixture()) as {
      responses: { combatSkills: Array<{ Tripods: Array<Record<string, unknown>> }> };
    };
    const skillIndex = 0;
    const tripodIndex = raw.responses.combatSkills[skillIndex]!.Tripods.length;
    const tooltip = '적에게 총 피해량의 77.0%에 해당하는 폭풍 피해를 준다';
    raw.responses.combatSkills[skillIndex]!.Tripods.push({
      Name: '미분류 폭풍',
      Tier: 3,
      IsSelected: true,
      Tooltip: tooltip
    });

    expect(parseBuildSnapshot(raw).warnings).toContainEqual(expect.objectContaining({
      code: 'UNPARSED_DAMAGE_TOOLTIP',
      severity: 'incomplete',
      path: `combatSkills[${skillIndex}].Tripods[${tripodIndex}].Tooltip`,
      rawValue: tooltip
    }));
  });

  test('warns when a selected tripod mixes a recognized multiplier with an unclassified damage clause', () => {
    // Break caught: one parsed tripod multiplier suppresses a warning for a second unknown damage-bearing span.
    const raw = structuredClone(loadRawFixture()) as {
      responses: { combatSkills: Array<{ Tripods: Array<Record<string, unknown>> }> };
    };
    const skillIndex = 0;
    const tripodIndex = raw.responses.combatSkills[skillIndex]!.Tripods.length;
    const tooltip = '적에게 주는 피해가 60.0% 증가한다. 적에게 총 피해량의 77.0%에 해당하는 폭풍 피해를 준다.';
    raw.responses.combatSkills[skillIndex]!.Tripods.push({
      Name: '부분 파싱 폭풍',
      Tier: 3,
      IsSelected: true,
      ToolTip: tooltip
    });

    expect(parseBuildSnapshot(raw).warnings).toContainEqual(expect.objectContaining({
      code: 'UNPARSED_DAMAGE_TOOLTIP',
      severity: 'incomplete',
      path: `combatSkills[${skillIndex}].Tripods[${tripodIndex}].ToolTip`,
      rawValue: tooltip
    }));
  });

  test('returns a path-bearing incomplete warning for an active damage tooltip it cannot classify', () => {
    // Break caught: silently treating an unknown damage tooltip as a zero-valued effect.
    const raw = structuredClone(loadRawFixture()) as {
      responses: { arkGrid: { Slots: Array<{ Gems?: unknown[] }> } };
    };
    raw.responses.arkGrid.Slots[0]!.Gems ??= [];
    raw.responses.arkGrid.Slots[0]!.Gems.push({
      Index: 99,
      IsActive: true,
      Grade: '고대',
      Tooltip: JSON.stringify({ Element_000: { value: '알 수 없는 개인 피해 증폭 효과' } })
    });

    const snapshot = parseBuildSnapshot(raw);
    expect(snapshot.warnings).toContainEqual(expect.objectContaining({
      code: 'UNPARSED_DAMAGE_TOOLTIP',
      severity: 'incomplete',
      path: 'arkGrid.Slots[0].Gems[4].Tooltip'
    }));
  });

  test('preserves fallback and calculated-attack provenance as structured path-bearing warnings', () => {
    // Break caught: dropping Python fallback/mismatch warnings while normalizing the snapshot.
    const parsed = parseBuildSnapshot(loadRawFixture());
    expect(parsed.warnings.map(({ code, path }) => ({ code, path }))).toEqual([
      { code: 'ARK_PASSIVE_EFFECT_FALLBACK', path: 'arkPassive.Effects[2]' },
      { code: 'KARMA_EVOLUTION_FALLBACK', path: 'arkPassive.Points[0]' },
      { code: 'UNPARSED_DAMAGE_TOOLTIP', path: 'combatSkills[14].Tripods[6].Tooltip' },
      { code: 'UNPARSED_DAMAGE_TOOLTIP', path: 'arkGrid.Slots[4].Tooltip.options[0]' },
      { code: 'CALCULATED_ATTACK_POWER_OVERRIDE', path: 'profiles.Stats[공격력]' }
    ]);
    expect(parsed.build.provenance).toContainEqual(expect.objectContaining({
      path: 'arkPassive.Points[1].Description',
      value: '0.028',
      applied: true
    }));
  });

  test('marks ignored Ark Passive nodes ineligible and identifies verified numeric fallbacks', () => {
    // Break caught: all nodes and fallback-derived numbers were attributed as applied official API values.
    const raw = structuredClone(loadRawFixture()) as {
      responses: { arkPassive: { Effects: unknown[] } };
    };
    raw.responses.arkPassive.Effects = [
      { Name: '깨달음', Description: '깨달음 2티어 환기 Lv.3', ToolTip: '' },
      { Name: '진화', Description: '진화 2티어 한계 돌파 Lv.3', ToolTip: '' }
    ];

    const parsed = parseBuildSnapshot(raw);
    expect(parsed.build.provenance).toContainEqual(expect.objectContaining({
      path: 'arkPassive.Effects[0]',
      label: '환기',
      sourceType: 'OFFICIAL_API',
      eligible: false,
      applied: false,
      excludedReason: expect.stringContaining('1회 피해')
    }));
    expect(parsed.warnings).toContainEqual(expect.objectContaining({
      code: 'ARK_PASSIVE_EFFECT_FALLBACK',
      severity: 'warning',
      path: 'arkPassive.Effects[1]'
    }));
    expect(parsed.build.provenance).toContainEqual(expect.objectContaining({
      path: 'arkPassive.Effects[1].fallback.evolutionDamage',
      label: '한계 돌파 evolutionDamage fallback',
      value: '0.3',
      sourceType: 'VERIFIED_FALLBACK',
      parsed: false,
      eligible: true,
      applied: true
    }));

    const currentNodeProvenance = parseBuildSnapshot(loadRawFixture()).build.provenance
      .filter((item) => /^arkPassive\.Effects\[\d+\]$/.test(item.path));
    for (const ignoredName of ['환기', '치명', '신속', '잠재력 해방', '즉각적인 주문']) {
      expect(currentNodeProvenance).toContainEqual(expect.objectContaining({
        label: ignoredName,
        eligible: false,
        applied: false
      }));
    }
  });

  test('flattens official JSON tooltips without repeating adjacent wrapper values', () => {
    // Break caught: parsing JSON syntax or duplicated wrapper strings as game tooltip content.
    const tooltip = JSON.stringify({
      Element_000: { type: 'ItemTitle', value: '공격력 +1.43%' },
      Element_001: { value: '공격력 +1.43%' },
      Element_002: { value: '<FONT>보스 피해 +4.25%</FONT><BR>적용' }
    });

    expect(tooltipToText(tooltip)).toBe('공격력 +1.43%\n보스 피해 +4.25%\n적용');
  });
});
