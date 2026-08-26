// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, test, vi } from 'vitest';
import App from './App.js';

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

const snapshot = {
  schemaVersion: '1', snapshotId: '00000000-0000-4000-8000-000000000001', characterName: '봄날꽃씨', classId: 'weather-artist',
  calculatorVersion: 'current-v2.7.2', parserVersion: 'lostark-api-ts-v1', catalogVersion: 'weather-artist-v0.5', calculatedAttackPower: '123456.789', warnings: [],
  build: { profile: { className: '기상술사', characterLevel: 70, expeditionLevel: 100, criticalStat: '1200', swiftnessStat: '1800', specializationStat: '0', profileAttackPower: '123456.789' }, equipment: { items: [] }, avatars: { items: [] }, gems: { items: [] }, engravings: { names: ['원한'] }, arkPassive: { effects: [] }, combatSkills: { selectedTripods: [] }, arkGrid: { cores: [] }, provenance: [] }
} as const;

function result(skillId: string, expectedDamage = '1000.125'): Record<string, unknown> {
  return { schemaVersion: '1', skillId, nonCriticalDamage: '900.125', criticalDamage: '1800.125', expectedDamage, criticalRate: '0.5', criticalMultiplier: '2', hits: [{ schemaVersion: '1', hitName: '1타', nonCriticalDamage: '900.125', criticalDamage: '1800.125', expectedDamage }], rationale: ['공식 API 장비 수치 적용'] };
}
const baseline = catalog.skills.map((skill) => result(skill.id));

function response(data: unknown): Response {
  return new Response(JSON.stringify({ schemaVersion: '1', ok: true, data, warnings: [] }), { status: 200, headers: { 'content-type': 'application/json' } });
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
  await screen.findByText('기상술사 · Lv.70');
  return user;
}

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe('Weather Artist simulator editor', () => {
  test('loads the character through the Worker envelope and shows the API baseline summary', async () => {
    // Break caught: a client bypasses the versioned Worker route or renders values before a successful API envelope.
    const fetcher = installFetch();
    await loadCharacter();
    expect(screen.getByText('123,456.79')).toBeTruthy();
    const request = fetcher.mock.calls.find(([url]) => String(url).endsWith('/characters/load'));
    expect(request?.[1]).toMatchObject({ method: 'POST', headers: expect.objectContaining({ 'X-Anonymous-Client-Id': expect.stringMatching(/^[A-Za-z0-9_-]{8,128}$/) }) });
  });

  test('sends a catalog-backed section toggle after 250ms and updates the visible candidate value', async () => {
    // Break caught: toggling the editor only changes a local checkbox and never recalculates the candidate.
    const fetcher = installFetch('800.125');
    await loadCharacter();
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole('checkbox', { name: '보석 사용' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(250); });
    expect(fetcher.mock.calls.filter(([url]) => String(url).endsWith('/simulations'))).toHaveLength(1);
    fireEvent.click(screen.getByRole('tab', { name: '스킬 피해 결과' }));
    expect(screen.getAllByText('800.13').length).toBeGreaterThan(0);
  });

  test('keeps numeric controls locked and explains catalog constraints', async () => {
    // Break caught: an unsupported number editor implies the Worker can apply a patch it rejects.
    installFetch();
    await loadCharacter();
    expect(screen.getByLabelText('장비·완갑 레벨')).toHaveProperty('disabled', true);
    expect(screen.getByText('검증된 장비 성장 데이터셋이 없습니다.')).toBeTruthy();
  });

  test('resets one section to its baseline patch state', async () => {
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

  test('rebases only supported saved patches and announces discarded stale patches', async () => {
    // Break caught: a catalog change replays an unknown local patch and produces an opaque server error.
    localStorage.setItem('weather-artist:patches:봄날꽃씨:1:current-v2.7.2:lostark-api-ts-v1:weather-artist-v0.5', JSON.stringify([
      { schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'gems', enabled: false },
      { schemaVersion: '1', kind: 'set-section-enabled', sectionId: 'obsolete', enabled: false }
    ]));
    installFetch();
    await loadCharacter();
    expect(screen.getByRole('status').textContent).toContain('지원하지 않는 저장 조정 1개를 버렸습니다');
    expect(screen.getByRole('checkbox', { name: '보석 사용' })).toHaveProperty('checked', false);
  });

  test('rebases patches from an older catalog key when a new catalog baseline arrives', async () => {
    // Break caught: versioned storage makes every catalog update silently abandon otherwise supported saved section choices.
    localStorage.setItem('weather-artist:patches:봄날꽃씨:1:current-v2.7.2:lostark-api-ts-v1:weather-artist-v0.5', JSON.stringify([
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

  test('expands a result card to disclose individual hits and source rationale', async () => {
    // Break caught: aggregate damage hides the per-hit and provenance information needed to audit a result.
    installFetch();
    await loadCharacter();
    await userEvent.setup().click(screen.getByRole('tab', { name: '스킬 피해 결과' }));
    expect(screen.getAllByRole('article')).toHaveLength(6);
    const card = screen.getByRole('button', { name: /우레바람 상세/ });
    await userEvent.setup().click(card);
    const panel = screen.getByLabelText('우레바람 상세 결과');
    expect(within(panel).getByText('1타')).toBeTruthy();
    expect(within(panel).getByText('공식 API 장비 수치 적용')).toBeTruthy();
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
});
