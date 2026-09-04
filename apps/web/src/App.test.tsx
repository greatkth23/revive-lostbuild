// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, test, vi } from 'vitest';
import { calculateAllSkillDamage, parseBuildSnapshot } from '@weather-artist/calculator';
import App, { SIMULATOR_UI_ENABLED } from './App.js';

const simulatorTest = SIMULATOR_UI_ENABLED ? test : test.skip;

const catalog = {
  schemaVersion: '1',
  version: 'weather-artist-v0.5',
  equipmentGrowth: { editingLocked: true, reason: 'NO_VERIFIED_DATASET', requiredDataset: '검증표' },
  editableSections: [
    { id: 'gems', label: '보석', editable: true },
    { id: 'equipment', label: '장비·완갑', editable: false, lockReason: '검증된 장비 성장 데이터셋이 없습니다.' }
  ],
  skills: [
    { id: 'thunderstorm', displayName: '우레바람', directionTag: 'NON_DIRECTIONAL', tags: ['NON_DIRECTIONAL'], hitMotionCoefficient: '1', hits: [{ name: '최대 홀딩', coefficient: '1', constant: '1' }] },
    { id: 'space-cutting', displayName: '공간 가르기', directionTag: 'NON_DIRECTIONAL', tags: ['NON_DIRECTIONAL'], hitMotionCoefficient: '1', hits: [{ name: '1타', coefficient: '1', constant: '1' }] },
    { id: 'piercing-wind', displayName: '바람송곳', directionTag: 'NON_DIRECTIONAL', tags: ['NON_DIRECTIONAL'], hitMotionCoefficient: '1', hits: [{ name: '전체 타격', coefficient: '1', constant: '1' }] },
    { id: 'raging-blizzard', displayName: '칼바람', directionTag: 'NON_DIRECTIONAL', tags: ['NON_DIRECTIONAL'], hitMotionCoefficient: '1', hits: [{ name: '전체 타격', coefficient: '1', constant: '1' }] },
    { id: 'sweeping-strike', displayName: '몰아치기', directionTag: 'NON_DIRECTIONAL', tags: ['NON_DIRECTIONAL'], hitMotionCoefficient: '1', hits: [{ name: '1타', coefficient: '1', constant: '1' }] },
    { id: 'tornado-walk', displayName: '회오리 걸음', directionTag: 'NON_DIRECTIONAL', tags: ['NON_DIRECTIONAL'], hitMotionCoefficient: '1', hits: [{ name: '1타', coefficient: '1', constant: '1' }] }
  ]
} as const;

const rawFixturePath = resolve(process.cwd(), 'api-chatgpt-conversation-6a6309ab-7de4-8342/outputs/봄날꽃씨_우레바람_current-v2.7.2_api_raw.json');
const snapshot = parseBuildSnapshot(JSON.parse(readFileSync(rawFixturePath, 'utf8')));

function result(skillId: string, expectedDamage = '1000.125'): Record<string, unknown> {
  return {
    schemaVersion: '1', skillId, nonCriticalDamage: '900.125', criticalDamage: '1800.125', expectedDamage, criticalRate: '0.5', criticalMultiplier: '2',
    hits: [{ schemaVersion: '1', hitName: '1타', nonCriticalDamage: '900.125', criticalDamage: '1800.125', expectedDamage }],
    rationale: ['공식 API 장비 수치 적용'],
    checkpoints: {
      attackPower: {
        equipmentMainStat: '747822', accountMainStatFlat: '2133', baseMainStat: '749955', avatarMainStatPercent: '0.08', petMainStatPercent: '0.01', finalMainStat: '817450.95',
        baseWeaponAttack: '241367', equipmentWeaponAttackFlat: '10969', arkGridWeaponAttackFlat: '0', weaponAttackSubtotal: '252336', equipmentWeaponAttackPercent: '0.06', karmaWeaponAttackPercent: '0.028', arkGridWeaponAttackPercent: '0', weaponAttackPercent: '0.088', finalWeaponAttack: '274541.568',
        rootAttackPower: '193402.4', armletBaseAttackFlat: '2030', gemsBaseAttackPercent: '0.104', stoneBaseAttackPercent: '0.015', equipmentBaseAttackPercent: '0', baseAttackPercent: '0.119', afterBaseAttackPercent: '218688.1',
        equipmentAttackPowerFlat: '0', arkGridAttackPowerFlat: '900', attackPowerFlat: '900', equipmentAttackPowerPercent: '0.019', adrenalineAttackPowerPercent: '0.1038', arkGridAttackPowerPercent: '0.0411', attackPowerPercent: '0.1639',
        profileAttackPower: '236442', final: '258720.5038', usedForDamage: '258720.5038', usedForDamageSource: 'CALCULATED_OFFICIAL'
      },
      motionCoefficients: ['351.262'],
      criticalRate: { components: [{ label: '치명 스탯', value: '0.3' }, { label: '아드레날린', value: '0.2' }], result: '0.5' },
      criticalMultiplier: { additiveComponents: [{ label: '기본 치명타 피해', value: '2' }], additiveResult: '2', multiplicativeComponents: [{ label: '회심', value: '1' }], result: '2' },
      selectedTripods: [{ skillName: '우레바람', name: '우레', tooltipText: '피해가 증가한다', damagePercent: '0.6', criticalDamagePercent: '0', damageEffects: [{ type: 'DAMAGE_INCREASE', label: '피해 증가', percent: '0.6', multiplier: '1.6', applicationMode: 'MULTIPLIER' }] }],
      regularGem: { damagePercent: '0', cooldownReductionPercent: '0' },
      directional: { tag: 'NON_DIRECTIONAL', label: '비방향성', success: false, applied: false, damagePercent: '0', criticalRate: '0' },
      arkPassive: { appliedEffects: [{ name: '바람의 길', category: 'skillDamage', value: '0.1' }] },
      arkGrid: { appliedFactors: [{ factorId: 'umbrella-10', corePath: 'arkGrid.Slots[0]', coreName: '우산의 춤', coreGrade: '고대', category: 'skillDamagePercent', value: '0.02', scopeKind: 'SKILL_TAG', scopeValue: 'UMBRELLA_SKILL', condition: '', requiredPoints: 10, contributionPaths: ['arkGrid.Slots[0].Tooltip.options[0]'] }], repeatedPointMultiplier: '1.006', commonDamageMultiplier: '4.2' },
      tripodDamageMultiplier: '1.6', embeddedTripodEffects: []
    }
  };
}
const baseline = catalog.skills.map((skill) => result(skill.id));

function stored(patches: unknown[], savedAt = '2026-08-25T12:00:00.000Z') {
  return JSON.stringify({ savedAt, patches });
}

function response(data: unknown): Response {
  const completeData = data && typeof data === 'object' && 'snapshotId' in data && 'baseline' in data && 'candidate' in data
    ? { schemaVersion: '1', ...data }
    : data;
  return new Response(JSON.stringify({ schemaVersion: '1', ok: true, data: completeData, warnings: [] }), { status: 200, headers: { 'content-type': 'application/json' } });
}

function normalizedHeaders(init: RequestInit | undefined): Record<string, string> {
  return Object.fromEntries(new Headers(init?.headers).entries());
}

function installFetch(candidateExpected = '800.125') {
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith('/catalog/weather-artist')) return response(catalog);
    if (url.endsWith('/characters/load')) return response({ snapshot, baseline, cacheHit: false });
    if (url.endsWith('/simulations')) return response({ snapshotId: snapshot.snapshotId, patches: JSON.parse(String(init?.body)).patches, baseline, candidate: catalog.skills.map((skill) => result(skill.id, candidateExpected)) });
    throw new Error(`unexpected request ${url}`);
  });
  vi.stubGlobal('fetch', fetcher);
  return fetcher;
}

async function loadCharacter(name = '봄날꽃씨') {
  const user = userEvent.setup();
  render(<App />);
  await user.type(screen.getByLabelText('캐릭터 이름'), name);
  await user.click(screen.getByRole('button', { name: '불러오기' }));
  await screen.findByRole('heading', { name });
  return user;
}

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe('Weather Artist simulator editor', () => {
  test('shows read-only setup and damage tabs without exposing the suspended simulator', async () => {
    const fetcher = installFetch();
    await loadCharacter();

    expect(screen.getByRole('tab', { name: '현재 세팅' }).getAttribute('aria-selected')).toBe('true');
    expect(screen.getByRole('tab', { name: '스킬 피해' })).toBeTruthy();
    expect(screen.queryByRole('tab', { name: '세팅 조정' })).toBeNull();
    expect(screen.queryByRole('checkbox', { name: '보석 사용' })).toBeNull();
    expect(document.querySelector('.eyebrow')).toBeNull();
    expect(screen.queryByText(/WEATHER ARTIST/)).toBeNull();

    await new Promise((resolve) => window.setTimeout(resolve, 300));
    expect(fetcher.mock.calls.some(([url]) => String(url).endsWith('/simulations'))).toBe(false);
  });

  test('lays out the current API setting as profile and equipment cards', async () => {
    installFetch();
    await loadCharacter();

    expect(screen.getByText(/길드 꽃가게/)).toBeTruthy();
    for (const text of ['카제로스', '기부천사', '1,785.83', '보석', '장비', '액세서리', '각인', '아크패시브', '아크그리드', '아바타·펫', '스킬·트라이포드', '데이터 상태']) {
      expect(screen.getAllByText(text).length, text).toBeGreaterThan(0);
    }
  });

  test('renders one API-baseline damage result instead of a comparison', async () => {
    installFetch();
    const user = await loadCharacter();
    await user.click(screen.getByRole('tab', { name: '스킬 피해' }));

    expect(screen.getAllByText('비치명 피해').length).toBeGreaterThan(0);
    expect(screen.getAllByText('치명타 피해').length).toBeGreaterThan(0);
    expect(screen.getAllByText('기대 피해').length).toBeGreaterThan(0);
    expect(screen.queryByText(/기준 비치명/)).toBeNull();
    expect(screen.queryByText(/변경 비치명/)).toBeNull();
    expect(screen.queryByText(/기대 피해 차이/)).toBeNull();
  });

  test('loads the character through the Worker envelope and shows the API baseline summary', async () => {
    // Break caught: a client bypasses the versioned Worker route or renders values before a successful API envelope.
    const fetcher = installFetch();
    await loadCharacter();
    expect(screen.getAllByText('258,720.50').length).toBeGreaterThan(0);
    const request = fetcher.mock.calls.find(([url]) => String(url).endsWith('/characters/load'));
    expect(request?.[0]).toBe('/api/v1/characters/load');
    expect(request?.[1]?.method).toBe('POST');
    expect(normalizedHeaders(request?.[1])).toEqual({ 'content-type': 'application/json', 'x-anonymous-client-id': expect.stringMatching(/^[A-Za-z0-9_-]{8,128}$/) });
    expect(JSON.parse(String(request?.[1]?.body))).toEqual({ characterName: '봄날꽃씨', forceRefresh: false });
  });

  simulatorTest('sends a catalog-backed section toggle after 250ms and updates the visible candidate value', async () => {
    // Break caught: toggling the editor only changes a local checkbox and never recalculates the candidate.
    const fetcher = installFetch('800.125');
    await loadCharacter();
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole('checkbox', { name: '보석 사용' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    const simulations = fetcher.mock.calls.filter(([url]) => String(url).endsWith('/simulations'));
    expect(simulations).toHaveLength(1);
    expect(simulations[0]?.[1]?.headers).toEqual({ 'content-type': 'application/json', 'X-Anonymous-Client-Id': expect.stringMatching(/^[A-Za-z0-9_-]{8,128}$/) });
    expect(JSON.parse(String(simulations[0]?.[1]?.body))).toEqual({
      schemaVersion: '1', snapshotId: snapshot.snapshotId, calculatorVersion: snapshot.calculatorVersion, parserVersion: snapshot.parserVersion, catalogVersion: snapshot.catalogVersion,
      patches: [{ schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: false }],
      scenario: { schemaVersion: '1', id: 'default', bossConditionId: 'default', directionalSuccessBySkill: Object.fromEntries(catalog.skills.map((skill) => [skill.id, false])) }
    });
    fireEvent.click(screen.getByRole('tab', { name: '스킬 피해 결과' }));
    expect(screen.getAllByText('800.13').length).toBeGreaterThan(0);
  });

  simulatorTest('keeps numeric controls locked and explains catalog constraints', async () => {
    // Break caught: an unsupported number editor implies the Worker can apply a patch it rejects.
    installFetch();
    await loadCharacter();
    expect(screen.getByLabelText('장비·완갑 레벨')).toHaveProperty('disabled', true);
    expect(screen.getByText('검증된 장비 성장 데이터셋이 없습니다.')).toBeTruthy();
  });

  simulatorTest('resets one section to its baseline patch state', async () => {
    // Break caught: reset leaves a stale set-section-enabled false patch persisted and simulated.
    const fetcher = installFetch();
    await loadCharacter();
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole('checkbox', { name: '보석 사용' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    fireEvent.click(screen.getByRole('button', { name: '보석 초기화' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    const lastPayload = JSON.parse(String(fetcher.mock.calls.filter(([url]) => String(url).endsWith('/simulations')).at(-1)?.[1]?.body));
    expect(lastPayload.patches).toEqual([{ schemaVersion: '1', kind: 'reset-section', sectionId: 'gems' }]);
  });

  simulatorTest('rebases only supported saved patches and announces discarded stale patches', async () => {
    // Break caught: a catalog change replays an unknown local patch and produces an opaque server error.
    localStorage.setItem('weather-artist:patches:봄날꽃씨:1:current-v2.7.2:lostark-api-ts-v4:weather-artist-v0.5', stored([
      { schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: false },
      { schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'obsolete', enabled: false }
    ]));
    installFetch();
    await loadCharacter();
    expect(screen.getByText(/지원하지 않는 저장 조정 1개를 버렸습니다/)).toBeTruthy();
    expect(screen.getByRole('checkbox', { name: '보석 사용' })).toHaveProperty('checked', false);
  });

  simulatorTest('rebases patches from an older catalog key when a new catalog baseline arrives', async () => {
    // Break caught: versioned storage makes every catalog update silently abandon otherwise supported saved section choices.
    localStorage.setItem('weather-artist:patches:봄날꽃씨:1:current-v2.7.2:lostark-api-ts-v4:weather-artist-v0.5', stored([
      { schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: false }
    ]));
    const newerCatalog = { ...catalog, version: 'weather-artist-v0.6' };
    const newerSnapshot = { ...snapshot, catalogVersion: 'weather-artist-v0.6' };
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith('/catalog/weather-artist')) return response(newerCatalog);
      return response({ snapshot: newerSnapshot, baseline, cacheHit: false });
    }));
    await loadCharacter();
    expect(screen.getByRole('checkbox', { name: '보석 사용' })).toHaveProperty('checked', false);
  });

  simulatorTest('uses the most recent compatible predecessor envelope and announces the catalog rebase', async () => {
    // Break caught: old histories are concatenated or an incompatible ruleset is accidentally replayed.
    localStorage.setItem('weather-artist:patches:봄날꽃씨:1:old-rules:lostark-api-ts-v4:weather-artist-v0.4', stored([{ schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: false }], '2026-08-25T12:00:00.000Z'));
    localStorage.setItem('weather-artist:patches:봄날꽃씨:1:current-v2.7.2:lostark-api-ts-v4:weather-artist-v0.4', stored([{ schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: false }], '2026-08-25T13:00:00.000Z'));
    localStorage.setItem('weather-artist:patches:봄날꽃씨:1:current-v2.7.2:lostark-api-ts-v4:weather-artist-v0.5', stored([{ schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: true }], '2026-08-25T14:00:00.000Z'));
    const newerCatalog = { ...catalog, version: 'weather-artist-v0.6' };
    const newerSnapshot = { ...snapshot, catalogVersion: 'weather-artist-v0.6' };
    vi.stubGlobal('fetch', vi.fn(async (url: string) => url.endsWith('/catalog/weather-artist') ? response(newerCatalog) : response({ snapshot: newerSnapshot, baseline, cacheHit: false })));
    await loadCharacter();
    expect(screen.getByRole('checkbox', { name: '보석 사용' })).toHaveProperty('checked', true);
    expect(screen.getByText(/저장 조정을 새 카탈로그에 맞게 다시 적용했습니다/)).toBeTruthy();
  });

  simulatorTest('discards malformed saved patch envelopes before they reach the simulation API', async () => {
    // Break caught: a malformed persisted boolean becomes an invalid Worker payload instead of a safely discarded local entry.
    localStorage.setItem('weather-artist:patches:봄날꽃씨:1:current-v2.7.2:lostark-api-ts-v4:weather-artist-v0.5', stored([
      { schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: false },
      { schemaVersion: 'wrong', kind: 'set-section-enabled', sectionId: 'gems', enabled: 'false' }
    ]));
    const fetcher = installFetch();
    await loadCharacter();
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole('checkbox', { name: '보석 사용' }));
    fireEvent.click(screen.getByRole('checkbox', { name: '보석 사용' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    const simulation = fetcher.mock.calls.find(([url]) => String(url).endsWith('/simulations'));
    expect(JSON.parse(String(simulation?.[1]?.body)).patches).toEqual([{ schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: false }]);
    expect(screen.getByText(/버렸습니다/)).toBeTruthy();
  });

  test('expands a result card to disclose individual hits and source rationale', async () => {
    // Break caught: aggregate damage hides the per-hit and provenance information needed to audit a result.
    installFetch();
    await loadCharacter();
    await userEvent.setup().click(screen.getByRole('tab', { name: '스킬 피해' }));
    expect(screen.getAllByRole('article')).toHaveLength(6);
    const card = screen.getByRole('button', { name: /우레바람 상세/ });
    await userEvent.setup().click(card);
    const panel = screen.getByLabelText('우레바람 상세 결과');
    expect(within(panel).getByText('1타')).toBeTruthy();
    expect(within(panel).getByText('공식 API 장비 수치 적용')).toBeTruthy();
  });

  test('shows transported calculation checkpoints and all per-hit current-value columns', async () => {
    // Break caught: the read-only UI receives audit data but only renders aggregate expected damage.
    installFetch();
    await loadCharacter();
    fireEvent.click(screen.getByRole('tab', { name: '스킬 피해' }));
    fireEvent.click(screen.getByRole('button', { name: '우레바람 상세' }));
    const panel = screen.getByRole('region', { name: '우레바람 상세 결과' });
    for (const heading of ['타격별 피해', '계산 공격력', '치명타율', '치명타 피해 배율', '트라이포드', '일반 보석·방향성', '아크패시브·아크그리드']) {
      expect(within(panel).getByText(heading)).toBeTruthy();
    }
    const table = within(panel).getByRole('table');
    for (const column of ['타격', '비치명', '치명타', '기대']) {
      expect(within(table).getByRole('columnheader', { name: column })).toBeTruthy();
    }
  });

  test('shows every tripod effect application, aggregate multiplier, embedded hit, and scoped repeat label', async () => {
    // Break caught: the detail view collapses 큰 센바람/집중 공격/공간베기 into misleading top-level zeroes.
    const calculated = calculateAllSkillDamage(snapshot, {
      directionalSuccessBySkill: Object.fromEntries(catalog.skills.map((skill) => [skill.id, false]))
    });
    vi.stubGlobal('fetch', vi.fn(async (url: string) => url.endsWith('/catalog/weather-artist')
      ? response(catalog)
      : response({ snapshot, baseline: calculated, cacheHit: false })));
    await loadCharacter();
    fireEvent.click(screen.getByRole('tab', { name: '스킬 피해' }));

    fireEvent.click(screen.getByRole('button', { name: '바람송곳 상세' }));
    const wind = screen.getByRole('region', { name: '바람송곳 상세 결과' });
    expect(within(wind).getByText('큰 센바람 · 추가 공격 피해 60.00% · 배율 곱연산')).toBeTruthy();
    expect(within(wind).getByText('집중 공격 · 피해 증가 95.00% · 배율 곱연산')).toBeTruthy();
    expect(within(wind).getByText('전체 트라이포드 피해 배율 ×4.99')).toBeTruthy();
    expect(within(wind).getByText(/18–20P 반복 배율 ×1\.01/)).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: '몰아치기 상세' }));
    const sweeping = screen.getByRole('region', { name: '몰아치기 상세 결과' });
    expect(within(sweeping).getByText('공간베기 · 추가 공격 피해 94.80% · 모션 타격 포함')).toBeTruthy();
    expect(within(sweeping).getByText('전체 트라이포드 피해 배율 ×1.60')).toBeTruthy();
    expect(within(sweeping).getByText('공간베기 · 추가 공격 피해 94.80% · 모션 타격에 포함됨')).toBeTruthy();
  });

  test('prominently labels incomplete inputs and describes the baseline as API plus verified inputs', async () => {
    // Break caught: neutral fallback results look like a complete pure-API baseline.
    const incompleteSnapshot = {
      ...snapshot,
      warnings: [...snapshot.warnings, { schemaVersion: '1', code: 'UNVERIFIED_ACCOUNT_BONUSES', severity: 'incomplete', path: 'calculationInputs.accountBonuses', message: '계정 보너스 검증 자료가 없습니다.' }]
    };
    vi.stubGlobal('fetch', vi.fn(async (url: string) => url.endsWith('/catalog/weather-artist')
      ? response(catalog)
      : response({ snapshot: incompleteSnapshot, baseline, cacheHit: false })));
    await loadCharacter();
    expect(screen.getByText('검증 불완전')).toBeTruthy();
    expect(screen.getByText('계정 보너스 검증 자료가 없습니다.')).toBeTruthy();
  });

  test('exposes a keyboard-operable tablist with linked tab panels', async () => {
    // Break caught: tab buttons look selectable but cannot be discovered or operated as tabs by keyboard users.
    installFetch();
    await loadCharacter();
    const editor = screen.getByRole('tab', { name: '현재 세팅' });
    const results = screen.getByRole('tab', { name: '스킬 피해' });
    expect(editor.getAttribute('aria-controls')).toBe('panel-setup');
    fireEvent.keyDown(editor, { key: 'ArrowRight' });
    expect(results.getAttribute('aria-selected')).toBe('true');
    expect(screen.getByRole('tabpanel').getAttribute('aria-labelledby')).toBe('tab-damage');
    fireEvent.keyDown(results, { key: 'Home' });
    expect(editor.getAttribute('aria-selected')).toBe('true');
  });

  simulatorTest('keeps prior candidate visible as stale after a simulation failure and retries without reload', async () => {
    // Break caught: a transient simulation error erases the comparison or forces a fresh character load to recover.
    let simulationAttempts = 0;
    vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/catalog/weather-artist')) return response(catalog);
      if (url.endsWith('/characters/load')) return response({ snapshot, baseline, cacheHit: false });
      simulationAttempts += 1;
      if (simulationAttempts === 1) return new Response(JSON.stringify({ schemaVersion: '1', ok: false, error: { code: 'TEMPORARY', message: '계산 서버 오류', requestId: 's1' } }), { status: 503, headers: { 'content-type': 'application/json' } });
      return response({ snapshotId: snapshot.snapshotId, patches: JSON.parse(String(init?.body)).patches, baseline, candidate: catalog.skills.map((skill) => result(skill.id, '850.125')) });
    }));
    await loadCharacter();
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole('checkbox', { name: '보석 사용' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    expect(screen.getByRole('alert').textContent).toContain('계산 서버 오류');
    expect(screen.getByText('이전 결과 표시 중')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: '계산 다시 시도' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    fireEvent.click(screen.getByRole('tab', { name: '스킬 피해 결과' }));
    expect(screen.getAllByText('850.13').length).toBeGreaterThan(0);
  });

  simulatorTest('ignores an out-of-order older simulation response after a newer patch generation', async () => {
    // Break caught: a slow, aborted request resolves late and overwrites the more recent candidate comparison.
    const responders: Array<(value: Response) => void> = [];
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.endsWith('/catalog/weather-artist')) return Promise.resolve(response(catalog));
      if (url.endsWith('/characters/load')) return Promise.resolve(response({ snapshot, baseline, cacheHit: false }));
      return new Promise<Response>((resolve) => responders.push(resolve));
    }));
    await loadCharacter();
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole('checkbox', { name: '보석 사용' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    fireEvent.click(screen.getByRole('checkbox', { name: '보석 사용' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    responders[1]?.(response({ snapshotId: snapshot.snapshotId, patches: [], baseline, candidate: catalog.skills.map((skill) => result(skill.id, '1200.125')) }));
    await act(async () => { await Promise.resolve(); });
    fireEvent.click(screen.getByRole('tab', { name: '스킬 피해 결과' }));
    expect(screen.getAllByText('1,200.13').length).toBeGreaterThan(0);
    responders[0]?.(response({ snapshotId: snapshot.snapshotId, patches: [], baseline, candidate: catalog.skills.map((skill) => result(skill.id, '800.125')) }));
    await act(async () => { await Promise.resolve(); });
    expect(screen.getAllByText('1,200.13').length).toBeGreaterThan(0);
  });

  simulatorTest('makes refresh supersede an in-flight simulation from the previous snapshot', async () => {
    // Break caught: a late result from snapshot A overwrites the baseline that was just refreshed as snapshot B.
    let loads = 0;
    let respondSimulation: ((value: Response) => void) | undefined;
    const refreshed = { ...snapshot, snapshotId: '00000000-0000-4000-8000-000000000002' };
    const fetcher = vi.fn((url: string, _init?: RequestInit) => {
      if (url.endsWith('/catalog/weather-artist')) return Promise.resolve(response(catalog));
      if (url.endsWith('/characters/load')) return Promise.resolve(response({ snapshot: loads++ === 0 ? snapshot : refreshed, baseline, cacheHit: false }));
      return new Promise<Response>((resolve) => { respondSimulation = resolve; });
    });
    vi.stubGlobal('fetch', fetcher);
    await loadCharacter();
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole('checkbox', { name: '보석 사용' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    fireEvent.click(screen.getByRole('button', { name: '새로고침' }));
    await act(async () => { await Promise.resolve(); });
    const refresh = fetcher.mock.calls.filter(([url]) => url === '/api/v1/characters/load').at(-1);
    expect(refresh?.[0]).toBe('/api/v1/characters/load');
    expect(refresh?.[1]?.method).toBe('POST');
    expect(normalizedHeaders(refresh?.[1])).toEqual({ 'content-type': 'application/json', 'x-anonymous-client-id': expect.stringMatching(/^[A-Za-z0-9_-]{8,128}$/) });
    expect(JSON.parse(String(refresh?.[1]?.body))).toEqual({ characterName: '봄날꽃씨', forceRefresh: true });
    respondSimulation?.(response({ snapshotId: snapshot.snapshotId, patches: [], baseline, candidate: catalog.skills.map((skill) => result(skill.id, '800.125')) }));
    await act(async () => { await Promise.resolve(); });
    fireEvent.click(screen.getByRole('tab', { name: '스킬 피해 결과' }));
    expect(screen.queryByText('800.13')).toBeNull();
    expect(screen.getAllByText('1,000.13').length).toBeGreaterThan(0);
  });

  simulatorTest('clears every patch when all reset is selected', async () => {
    // Break caught: all reset clears checkboxes cosmetically but leaves a section patch in the next simulation payload.
    const fetcher = installFetch();
    await loadCharacter();
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole('checkbox', { name: '보석 사용' }));
    fireEvent.click(screen.getByRole('button', { name: '전체 초기화' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    const simulation = fetcher.mock.calls.filter(([url]) => String(url).endsWith('/simulations')).at(-1);
    expect(JSON.parse(String(simulation?.[1]?.body)).patches).toEqual([]);
  });

  test('marks a response missing a catalog skill unavailable instead of rendering zero damage', async () => {
    // Break caught: partial load output is silently formatted as 0.00 and looks like a valid damage result.
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith('/catalog/weather-artist')) return response(catalog);
      return response({ snapshot, baseline: baseline.slice(0, 5), cacheHit: false });
    }));
    await loadCharacter();
    fireEvent.click(screen.getByRole('tab', { name: '스킬 피해' }));
    expect(screen.getByText('결과 데이터 없음')).toBeTruthy();
    expect(screen.queryByText('0.00')).toBeNull();
  });

  test('renders official equipment icons and an accessible fallback for unavailable avatar icons', async () => {
    // Break caught: UI copies assets or leaves an unlabeled blank square when an official icon is unavailable.
    const withIcons = structuredClone(snapshot) as any;
    withIcons.build.equipment.items = [{ ...withIcons.build.equipment.items[0], name: '장비 아이콘', iconUrl: 'https://cdn.example.test/equipment.png' }];
    const { iconUrl: _iconUrl, ...avatarWithoutIcon } = withIcons.build.avatars.items[0];
    withIcons.build.avatars.items = [{ ...avatarWithoutIcon, name: '아바타 없음' }];
    vi.stubGlobal('fetch', vi.fn(async (url: string) => url.endsWith('/catalog/weather-artist') ? response(catalog) : response({ snapshot: withIcons, baseline, cacheHit: false })));
    await loadCharacter();
    const image = Array.from(document.querySelectorAll('img')).find((element) => element.getAttribute('src') === 'https://cdn.example.test/equipment.png');
    expect(image).toBeTruthy();
    fireEvent.error(image!);
    expect(document.querySelector('img[src="https://cdn.example.test/equipment.png"]')).toBeNull();
    expect(screen.getByLabelText('장비 아이콘 아이콘 없음')).toBeTruthy();
    expect(screen.getByLabelText('아바타 없음 아이콘 없음')).toBeTruthy();
  });

  test('recovers from a failed load without hiding the retryable search control', async () => {
    // Break caught: a Worker failure leaves the application in a permanent loading state.
    vi.stubGlobal('fetch', vi.fn(async (url: string) => url.endsWith('/catalog/weather-artist')
      ? response(catalog)
      : new Response(JSON.stringify({ schemaVersion: '1', ok: false, error: { code: 'UPSTREAM_UNAVAILABLE', message: '잠시 후 다시 시도하세요.', requestId: 'r1' } }), { status: 503, headers: { 'content-type': 'application/json' } })));
    render(<App />);
    fireEvent.change(screen.getByLabelText('캐릭터 이름'), { target: { value: '봄날꽃씨' } });
    fireEvent.click(screen.getByRole('button', { name: '불러오기' }));
    await screen.findByText('잠시 후 다시 시도하세요.');
    expect(screen.getByRole('button', { name: '다시 시도' })).toBeTruthy();
  });

  test('rejects malformed catalog and character-load success envelopes before rendering nested values', async () => {
    // Break caught: a 200 response with malformed catalog/load data crashes during nested rendering or becomes fake zero data.
    vi.stubGlobal('fetch', vi.fn(async (url: string) => url.endsWith('/catalog/weather-artist')
      ? response({ ...catalog, skills: [{ ...catalog.skills[0], hits: [{ name: 'broken' }] }] })
      : response({ snapshot, baseline, cacheHit: false })));
    render(<App />);
    await screen.findByText('응답 데이터가 완전하지 않습니다.');

    cleanup();
    vi.stubGlobal('fetch', vi.fn(async (url: string) => url.endsWith('/catalog/weather-artist')
      ? response(catalog)
      : response({ snapshot: { ...snapshot, warnings: [{}] }, baseline, cacheHit: false })));
    render(<App />);
    fireEvent.change(screen.getByLabelText('캐릭터 이름'), { target: { value: '봄날꽃씨' } });
    fireEvent.click(screen.getByRole('button', { name: '불러오기' }));
    await screen.findByText('응답 데이터가 완전하지 않습니다.');
    expect(screen.queryByText('0.00')).toBeNull();
  });

  simulatorTest('keeps prior valid results and exposes retry when a simulation success envelope is malformed', async () => {
    // Break caught: malformed result decimals are dereferenced and formatted as 0.00 instead of becoming a retryable stale state.
    vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/catalog/weather-artist')) return response(catalog);
      if (url.endsWith('/characters/load')) return response({ snapshot, baseline, cacheHit: false });
      return response({ snapshotId: snapshot.snapshotId, patches: JSON.parse(String(init?.body)).patches, baseline, candidate: baseline.map((item, index) => index === 0 ? { ...item, criticalRate: 'not-a-decimal' } : item) });
    }));
    await loadCharacter();
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole('checkbox', { name: '보석 사용' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    expect(screen.getByRole('alert').textContent).toContain('응답 데이터가 완전하지 않습니다.');
    expect(screen.getByRole('button', { name: '계산 다시 시도' })).toBeTruthy();
    expect(screen.queryByText('0.00')).toBeNull();
  });

  test('does not commit an older overlapping character load after a newer submitted character wins', async () => {
    // Break caught: an ignored AbortSignal still allows an older load response to replace a newer character snapshot.
    const responders: Array<(value: Response) => void> = [];
    const first = { ...snapshot, characterName: '첫번째' };
    const second = { ...snapshot, characterName: '두번째', snapshotId: '00000000-0000-4000-8000-000000000002' };
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.endsWith('/catalog/weather-artist')) return Promise.resolve(response(catalog));
      return new Promise<Response>((resolve) => responders.push(resolve));
    }));
    render(<App />);
    const input = screen.getByLabelText('캐릭터 이름');
    const form = input.closest('form')!;
    fireEvent.change(input, { target: { value: '첫번째' } });
    fireEvent.submit(form);
    fireEvent.change(input, { target: { value: '두번째' } });
    fireEvent.submit(form);
    responders[1]?.(response({ snapshot: second, baseline, cacheHit: false }));
    await screen.findByRole('heading', { name: '두번째' });
    responders[0]?.(response({ snapshot: first, baseline, cacheHit: false }));
    await act(async () => { await Promise.resolve(); });
    expect(screen.getByRole('heading', { name: '두번째' })).toBeTruthy();
    expect(screen.queryByRole('heading', { name: '첫번째' })).toBeNull();
  });

  simulatorTest('announces a pending calculation once when the results tab is open', async () => {
    // Break caught: the same pending/failed state is announced by both the global and results-panel live regions.
    installFetch();
    await loadCharacter();
    fireEvent.click(screen.getByRole('tab', { name: '스킬 피해 결과' }));
    expect(screen.getAllByRole('status').filter((node) => node.textContent === '계산 반영 중')).toHaveLength(1);
  });
});
