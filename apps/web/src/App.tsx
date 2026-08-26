import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react';
import { apiEnvelopeSchema, buildPatchSchema, characterLoadDataSchema, simulationDataSchema, weatherArtistCatalogSchema, type BuildPatch } from '@weather-artist/contracts';
import type { z, ZodTypeAny } from 'zod';
import './app.css';

type Warning = { code: string; severity: string; path: string; message: string };
type Result = { skillId: string; nonCriticalDamage: string; criticalDamage: string; expectedDamage: string; criticalRate: string; criticalMultiplier: string; hits: Array<{ hitName: string; nonCriticalDamage: string; criticalDamage: string; expectedDamage: string }>; rationale: string[] };
type Snapshot = { schemaVersion: string; snapshotId: string; characterName: string; calculatorVersion: string; parserVersion: string; catalogVersion: string; calculatedAttackPower: string; warnings: Warning[]; build: { profile: { className: string; characterLevel: number; expeditionLevel: number; criticalStat: string; swiftnessStat: string; specializationStat: string; profileAttackPower: string }; equipment: { items: Array<{ name: string; type: string; iconUrl?: string | undefined }> }; avatars: { items: Array<{ name: string; type: string; iconUrl?: string | undefined }> }; gems: { items: Array<{ name: string; level: number; iconUrl?: string | undefined }> }; engravings: { names: string[] }; arkPassive: { effects: Array<{ name: string; level: number | null }> }; combatSkills: { selectedTripods: Array<{ skillName: string; name: string }> }; arkGrid: { cores: Array<{ name: string; point: number }> }; provenance: Array<{ label: string; value: string; applied: boolean }> } };
type Section = { id: string; label: string; editable: boolean; lockReason?: string | undefined };
type Skill = { id: string; displayName: string; directionTag: 'NON_DIRECTIONAL' | 'FRONTAL_ATTACK' | 'BACK_ATTACK'; hits: Array<{ name: string }> };
type Catalog = { schemaVersion: string; version: string; editableSections: Section[]; skills: Skill[]; equipmentGrowth: { editingLocked: boolean; reason: string; requiredDataset: string } };
type LoadData = { snapshot: Snapshot; baseline: Result[]; cacheHit: boolean };
type SimulationData = { snapshotId: string; patches: BuildPatch[]; baseline: Result[]; candidate: Result[] };
type Envelope<T> = { schemaVersion: string; ok: true; data: T; warnings: Warning[] } | { schemaVersion: string; ok: false; error: { code: string; message: string; requestId: string } };
type PatchEnvelope = { savedAt: string; patches: unknown[] };

const API = '/api/v1';
const CLIENT_ID_KEY = 'weather-artist:anonymous-client-id';
const PATCH_PREFIX = 'weather-artist:patches';

function normalizedName(value: string): string {
  return value.normalize('NFKC').trim().replace(/\s+/g, ' ').toLocaleLowerCase('ko-KR');
}

function clientId(): string {
  const previous = localStorage.getItem(CLIENT_ID_KEY);
  if (previous && /^[A-Za-z0-9_-]{8,128}$/.test(previous)) return previous;
  const generated = typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID().replaceAll('-', '')
    : `${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`;
  localStorage.setItem(CLIENT_ID_KEY, generated);
  return generated;
}

function patchKey(snapshot: Snapshot): string {
  return [PATCH_PREFIX, normalizedName(snapshot.characterName), snapshot.schemaVersion, snapshot.calculatorVersion, snapshot.parserVersion, snapshot.catalogVersion].join(':');
}

function display(value: string | number): string {
  const number = Number(value);
  return Number.isFinite(number) ? new Intl.NumberFormat('ko-KR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(number) : '데이터 없음';
}

function patchSection(patch: BuildPatch): string | null {
  return 'sectionId' in patch ? patch.sectionId : null;
}

function supportedPatches(raw: unknown, sections: Section[]): { patches: BuildPatch[]; discarded: number } {
  if (!Array.isArray(raw)) return { patches: [], discarded: 0 };
  const supported = new Set(sections.filter((section) => section.editable).map((section) => section.id));
  const patches: BuildPatch[] = [];
  let discarded = 0;
  for (const candidate of raw) {
    const parsed = buildPatchSchema.safeParse(candidate);
    if (!parsed.success) { discarded += 1; continue; }
    const patch = parsed.data;
    const sectionId = patchSection(patch);
    if ((patch.kind === 'set-section-enabled' || patch.kind === 'reset-section') && sectionId && supported.has(sectionId)) patches.push(patch);
    else discarded += 1;
  }
  return { patches, discarded };
}

function patchEnvelope(raw: string | null): PatchEnvelope | null {
  if (!raw) return null;
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || !Array.isArray((parsed as PatchEnvelope).patches) || typeof (parsed as PatchEnvelope).savedAt !== 'string' || Number.isNaN(Date.parse((parsed as PatchEnvelope).savedAt))) return null;
    return parsed as PatchEnvelope;
  } catch { return null; }
}

function storedPatchCandidates(snapshot: Snapshot): { raw: unknown[]; discarded: number; rebased: boolean } {
  const directKey = patchKey(snapshot);
  const direct = localStorage.getItem(directKey);
  const exact = patchEnvelope(direct);
  if (exact) return { raw: exact.patches, discarded: 0, rebased: false };
  if (direct !== null) return { raw: [], discarded: 1, rebased: false };
  const expected = [normalizedName(snapshot.characterName), snapshot.schemaVersion, snapshot.calculatorVersion, snapshot.parserVersion];
  const predecessors = Array.from({ length: localStorage.length }, (_, index) => localStorage.key(index)).flatMap((key) => {
    if (!key) return [];
    const parts = key.split(':');
    if (parts.length !== 7 || parts[0] !== 'weather-artist' || parts[1] !== 'patches' || !expected.every((value, index) => parts[index + 2] === value)) return [];
    const envelope = patchEnvelope(localStorage.getItem(key));
    return envelope ? [{ key, envelope }] : [];
  }).sort((left, right) => Date.parse(right.envelope.savedAt) - Date.parse(left.envelope.savedAt) || left.key.localeCompare(right.key));
  const predecessor = predecessors[0];
  return predecessor ? { raw: predecessor.envelope.patches, discarded: 0, rebased: true } : { raw: [], discarded: 0, rebased: false };
}

async function request<T extends ZodTypeAny>(path: string, init: RequestInit | undefined, schema: T): Promise<z.infer<T>> {
  const response = await fetch(`${API}${path}`, init);
  let raw: unknown;
  try { raw = await response.json(); } catch { throw new Error('서버 응답을 읽을 수 없습니다.'); }
  const parsed = apiEnvelopeSchema(schema).safeParse(raw);
  if (!parsed.success) throw new Error('응답 데이터가 완전하지 않습니다.');
  const envelope = parsed.data as Envelope<z.infer<T>>;
  if (envelope.ok === false) throw new Error(envelope.error.message);
  if (!response.ok) throw new Error('요청에 실패했습니다.');
  return envelope.data;
}

function ApiIcon({ url, label }: { url: string | undefined; label: string }) {
  const [failed, setFailed] = useState(false);
  if (!url || !/^https:\/\//.test(url) || failed) return <span className="icon-fallback" aria-label={`${label} 아이콘 없음`}>?</span>;
  return <img className="api-icon" src={url} alt="" onError={() => setFailed(true)} />;
}

function SectionCard({ section, enabled, onToggle, onReset }: { section: Section; enabled: boolean; onToggle: (enabled: boolean) => void; onReset: () => void }) {
  const editable = section.editable;
  return <section className={`section-card ${editable ? '' : 'is-locked'}`} aria-labelledby={`section-${section.id}`}>
    <div className="card-head"><div><h3 id={`section-${section.id}`}>{section.label}</h3><p>{editable ? '검증된 섹션 단위 사용 여부만 조정할 수 있습니다.' : section.lockReason ?? '현재 데이터로는 수정할 수 없습니다.'}</p></div>{editable && <button type="button" className="quiet" onClick={onReset}>{section.label} 초기화</button>}</div>
    <label className="switch"><input type="checkbox" checked={enabled} disabled={!editable} onChange={(event) => onToggle(event.target.checked)} />{section.label} 사용</label>
    <label className="locked-field">{section.label} 레벨<input aria-label={`${section.label} 레벨`} type="number" value="카탈로그 제한" disabled readOnly /></label>
    <p className="lock-note">{editable ? '수치·옵션 편집은 아직 검증된 패치 계약이 없어 잠겨 있습니다.' : `잠김: ${section.lockReason ?? '카탈로그 제한'}`}</p>
  </section>;
}

function ResultCard({ skill, baseline, candidate }: { skill: Skill; baseline: Result | undefined; candidate: Result | undefined }) {
  const [expanded, setExpanded] = useState(false);
  const unavailable = !baseline || !candidate;
  const delta = unavailable ? null : Number(candidate.expectedDamage) - Number(baseline.expectedDamage);
  const metrics: Array<[string, string, string]> = unavailable ? [] : [
    ['비치명', baseline.nonCriticalDamage, candidate.nonCriticalDamage], ['치명', baseline.criticalDamage, candidate.criticalDamage], ['기대', baseline.expectedDamage, candidate.expectedDamage], ['치명 확률', String(Number(baseline.criticalRate) * 100), String(Number(candidate.criticalRate) * 100)], ['치명 배율', baseline.criticalMultiplier, candidate.criticalMultiplier]
  ];
  return <article className="result-card">
    <div className="result-head"><div><h3>{skill.displayName}</h3><p>{skill.directionTag === 'NON_DIRECTIONAL' ? '비방향성 · 방향 보너스 없음' : skill.directionTag}</p></div><label className="direction"><input aria-label={`${skill.displayName} 방향 성공`} type="checkbox" disabled checked={false} />방향 성공 (읽기 전용)</label></div>
    {unavailable ? <p className="unavailable" role="status">결과 데이터 없음</p> : <><dl className="damage-grid">{metrics.flatMap(([label, base, changed]) => [<div key={`${label}-base`}><dt>기준 {label}</dt><dd>{display(base)}{label === '치명 확률' ? '%' : ''}</dd></div>, <div key={`${label}-candidate`}><dt>변경 {label}</dt><dd>{display(changed)}{label === '치명 확률' ? '%' : ''}</dd></div>])}</dl><p className={delta! < 0 ? 'delta negative' : 'delta'}>기대 피해 차이 {delta! >= 0 ? '+' : ''}{display(delta!)}</p></>}
    <button type="button" className="quiet" aria-expanded={expanded} aria-controls={`result-${skill.id}`} aria-label={`${skill.displayName} 상세`} onClick={() => setExpanded((value) => !value)}>타격·근거 {expanded ? '접기' : '펼치기'}</button>
    {expanded && <div id={`result-${skill.id}`} role="region" aria-label={`${skill.displayName} 상세 결과`} className="result-detail"><h4>타격 상세</h4><div className="table-wrap"><table><thead><tr><th>타격</th><th>기준 기대</th><th>변경 기대</th></tr></thead><tbody>{(candidate?.hits ?? []).map((hit) => <tr key={hit.hitName}><td>{hit.hitName}</td><td>{display(baseline?.hits.find((item) => item.hitName === hit.hitName)?.expectedDamage ?? 'not-a-decimal')}</td><td>{display(hit.expectedDamage)}</td></tr>)}</tbody></table></div><h4>계산 근거 비교</h4><div className="rationale-columns"><ul><li><strong>기준</strong></li>{(baseline?.rationale ?? ['근거 데이터 없음']).map((reason) => <li key={`base-${reason}`}>{reason}</li>)}</ul><ul><li><strong>변경</strong></li>{(candidate?.rationale ?? ['근거 데이터 없음']).map((reason) => <li key={`candidate-${reason}`}>{reason}</li>)}</ul></div></div>}
  </article>;
}

export default function App() {
  const [characterName, setCharacterName] = useState('');
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [loaded, setLoaded] = useState<LoadData | null>(null);
  const [patches, setPatches] = useState<BuildPatch[]>([]);
  const [candidate, setCandidate] = useState<Result[] | null>(null);
  const [tab, setTab] = useState<'editor' | 'results'>('editor');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [simulationError, setSimulationError] = useState<string | null>(null);
  const [simulationStatus, setSimulationStatus] = useState<'fresh' | 'pending' | 'failed'>('fresh');
  const [retry, setRetry] = useState(0);
  const [notice, setNotice] = useState('');
  const hasLoadedRef = useRef(false);
  const loadGenerationRef = useRef(0);
  const loadAbortRef = useRef<AbortController | null>(null);
  const generationRef = useRef(0);
  const simulationAbortRef = useRef<AbortController | null>(null);
  const loadedSnapshotRef = useRef<string | null>(null);
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  useEffect(() => { request('/catalog/weather-artist', undefined, weatherArtistCatalogSchema).then((value) => setCatalog(value)).catch((reason: Error) => setError(reason.message)); }, []);
  useEffect(() => {
    if (!loaded || !hasLoadedRef.current) return;
    const generation = ++generationRef.current;
    simulationAbortRef.current?.abort();
    const controller = new AbortController();
    simulationAbortRef.current = controller;
    setSimulationStatus('pending');
    setSimulationError(null);
    const timer = window.setTimeout(() => {
      const snapshot = loaded.snapshot;
      request('/simulations', { method: 'POST', signal: controller.signal, headers: { 'content-type': 'application/json', 'X-Anonymous-Client-Id': clientId() }, body: JSON.stringify({ schemaVersion: '1', snapshotId: snapshot.snapshotId, calculatorVersion: snapshot.calculatorVersion, parserVersion: snapshot.parserVersion, catalogVersion: snapshot.catalogVersion, patches, scenario: { schemaVersion: '1', id: 'default', bossConditionId: 'default', directionalSuccessBySkill: Object.fromEntries((catalog?.skills ?? []).map((skill) => [skill.id, false])) } }) }, simulationDataSchema)
        .then((data) => {
          if (generation !== generationRef.current || data.snapshotId !== snapshot.snapshotId || loadedSnapshotRef.current !== snapshot.snapshotId) return;
          if ((catalog?.skills ?? []).some((skill) => !data.baseline.some((result) => result.skillId === skill.id) || !data.candidate.some((result) => result.skillId === skill.id))) throw new Error('응답에 필요한 스킬 결과가 없습니다.');
          setCandidate(data.candidate); setSimulationStatus('fresh'); setSimulationError(null); setError(null);
        }).catch((reason: Error) => {
          if (controller.signal.aborted || generation !== generationRef.current) return;
          setSimulationStatus('failed'); setSimulationError(reason.message);
        });
    }, 250);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [patches, loaded, catalog, retry]);

  const sections = catalog?.editableSections ?? [];
  const enabledBySection = useMemo(() => Object.fromEntries(sections.map((section) => {
    const last = [...patches].reverse().find((patch) => patchSection(patch) === section.id);
    return [section.id, last?.kind === 'set-section-enabled' ? last.enabled : true];
  })), [patches, sections]);

  async function load(forceRefresh = false) {
    const name = characterName.normalize('NFKC').trim().replace(/\s+/g, ' ');
    if (!name) { setError('캐릭터 이름을 입력하세요.'); return; }
    const loadGeneration = ++loadGenerationRef.current;
    loadAbortRef.current?.abort();
    const controller = new AbortController();
    loadAbortRef.current = controller;
    generationRef.current += 1; simulationAbortRef.current?.abort(); loadedSnapshotRef.current = null;
    setBusy(true); setError(null); setNotice(''); hasLoadedRef.current = false;
    try {
      const [activeCatalog, data] = await Promise.all([catalog ? Promise.resolve(catalog) : request('/catalog/weather-artist', undefined, weatherArtistCatalogSchema), request('/characters/load', { method: 'POST', signal: controller.signal, headers: { 'content-type': 'application/json', 'X-Anonymous-Client-Id': clientId() }, body: JSON.stringify({ characterName: name, forceRefresh }) }, characterLoadDataSchema)]);
      if (controller.signal.aborted || loadGeneration !== loadGenerationRef.current || normalizedName(data.snapshot.characterName) !== normalizedName(name)) return;
      setCatalog(activeCatalog);
      const saved = storedPatchCandidates(data.snapshot);
      const restored = supportedPatches(saved.raw, activeCatalog.editableSections);
      setLoaded(data); setCandidate(data.baseline); setPatches(restored.patches); loadedSnapshotRef.current = data.snapshot.snapshotId; hasLoadedRef.current = true; setSimulationStatus('fresh'); setSimulationError(null);
      const discarded = saved.discarded + restored.discarded;
      if (saved.rebased) setNotice(`저장 조정을 새 카탈로그에 맞게 다시 적용했습니다.${discarded ? ` 지원하지 않는 저장 조정 ${discarded}개를 버렸습니다.` : ''}`);
      else if (discarded) setNotice(`지원하지 않는 저장 조정 ${discarded}개를 버렸습니다.`);
    } catch (reason) {
      if (!controller.signal.aborted && loadGeneration === loadGenerationRef.current) setError(reason instanceof Error ? reason.message : '불러오기에 실패했습니다.');
    } finally { if (loadGeneration === loadGenerationRef.current) setBusy(false); }
  }

  function changeSection(section: Section, enabled: boolean) {
    setPatches((current) => [...current.filter((patch) => patchSection(patch) !== section.id), { schemaVersion: '1', kind: 'set-section-enabled', sectionId: section.id, enabled }]);
  }
  function resetSection(section: Section) {
    setPatches((current) => [...current.filter((patch) => patchSection(patch) !== section.id), { schemaVersion: '1', kind: 'reset-section', sectionId: section.id }]);
  }
  useEffect(() => { if (loaded) localStorage.setItem(patchKey(loaded.snapshot), JSON.stringify({ savedAt: new Date().toISOString(), patches })); }, [patches, loaded]);

  function selectTab(next: 'editor' | 'results', focus = false) {
    setTab(next);
    if (focus) queueMicrotask(() => tabRefs.current[next === 'editor' ? 0 : 1]?.focus());
  }
  function tabKeyDown(event: KeyboardEvent<HTMLButtonElement>, current: number) {
    const next = event.key === 'ArrowRight' ? (current + 1) % 2 : event.key === 'ArrowLeft' ? (current + 1) % 2 : event.key === 'Home' ? 0 : event.key === 'End' ? 1 : null;
    if (next === null) return;
    event.preventDefault(); selectTab(next === 0 ? 'editor' : 'results', true);
  }
  const results = candidate ?? loaded?.baseline ?? [];
  return <main className="app-shell"><header className="topbar"><div><p className="eyebrow">WEATHER ARTIST · VERIFIED MVP</p><h1>기상술사 피해 시뮬레이터</h1><p>공식 API 기준값과 검증된 섹션 단위 조정을 비교합니다.</p></div><form className="search" onSubmit={(event) => { event.preventDefault(); void load(); }}><label>캐릭터 이름<input aria-label="캐릭터 이름" value={characterName} maxLength={24} onChange={(event) => setCharacterName(event.target.value)} placeholder="캐릭터명 입력" /></label><button disabled={busy} type="submit">{busy ? '불러오는 중…' : '불러오기'}</button>{loaded && <button type="button" className="quiet" onClick={() => void load(true)} disabled={busy}>새로고침</button>}</form></header>
    {error && <aside role="alert" className="message error">{error}<button type="button" onClick={() => void load()}>다시 시도</button></aside>}
    {loaded && simulationError && <aside role="alert" className="message error">{simulationError}<button type="button" onClick={() => setRetry((value) => value + 1)}>계산 다시 시도</button></aside>}
    {notice && <p role="status" className="message">{notice}</p>}
    {loaded && simulationStatus !== 'fresh' && <p role="status" className="message">{simulationStatus === 'pending' ? '계산 반영 중' : '이전 결과 표시 중'}</p>}
    {!loaded && !error && <section className="empty"><h2>캐릭터를 불러오세요</h2><p>지원 빌드의 공식 API 스냅샷을 기준으로 계산합니다.</p></section>}
    {loaded && <div className="workspace"><aside className="summary-rail"><section className="summary-card"><p className="eyebrow">API BASELINE {loaded.cacheHit ? '· CACHE' : '· LIVE'}</p><h2>{loaded.snapshot.characterName}</h2><p>{loaded.snapshot.build.profile.className} · Lv.{loaded.snapshot.build.profile.characterLevel}</p><dl><div><dt>계산 공격력</dt><dd>{display(loaded.snapshot.calculatedAttackPower)}</dd></div><div><dt>치명 / 신속</dt><dd>{display(loaded.snapshot.build.profile.criticalStat)} / {display(loaded.snapshot.build.profile.swiftnessStat)}</dd></div><div><dt>원정대</dt><dd>Lv.{loaded.snapshot.build.profile.expeditionLevel}</dd></div></dl></section><section className="summary-card"><h2>데이터 상태</h2><p>스키마 {loaded.snapshot.schemaVersion} · 카탈로그 {loaded.snapshot.catalogVersion}</p>{loaded.snapshot.warnings.length ? <ul>{loaded.snapshot.warnings.map((warning) => <li key={`${warning.code}${warning.path}`}>{warning.message}</li>)}</ul> : <p>현재 경고가 없습니다.</p>}</section></aside>
      <section className="main-panel"><div role="tablist" aria-label="시뮬레이터 보기" className="tabs"><button ref={(node) => { tabRefs.current[0] = node; }} id="tab-editor" role="tab" tabIndex={tab === 'editor' ? 0 : -1} aria-controls="panel-editor" aria-selected={tab === 'editor'} onKeyDown={(event) => tabKeyDown(event, 0)} onClick={() => selectTab('editor')}>세팅 조정</button><button ref={(node) => { tabRefs.current[1] = node; }} id="tab-results" role="tab" tabIndex={tab === 'results' ? 0 : -1} aria-controls="panel-results" aria-selected={tab === 'results'} onKeyDown={(event) => tabKeyDown(event, 1)} onClick={() => selectTab('results')}>스킬 피해 결과</button></div>
      {tab === 'editor' ? <section id="panel-editor" role="tabpanel" aria-labelledby="tab-editor"><div className="panel-heading"><div><h2>세팅 조정</h2><p>현재 MVP에서는 카탈로그가 허용한 섹션 사용 여부만 변경할 수 있습니다.</p></div><button type="button" className="quiet" onClick={() => setPatches([])}>전체 초기화</button></div><div className="section-grid">{sections.map((section) => <SectionCard key={section.id} section={section} enabled={Boolean(enabledBySection[section.id])} onToggle={(enabled) => changeSection(section, enabled)} onReset={() => resetSection(section)} />)}</div><section className="source-card"><h3>API 데이터 요약</h3><div className="source-columns"><p><strong>각인</strong>{loaded.snapshot.build.engravings.names.join(' · ') || '데이터 없음'}</p><p><strong>아크패시브</strong>{loaded.snapshot.build.arkPassive.effects.map((effect) => `${effect.name}${effect.level ? ` Lv.${effect.level}` : ''}`).join(' · ') || '데이터 없음'}</p><p><strong>아크그리드</strong>{loaded.snapshot.build.arkGrid.cores.map((core) => `${core.name} ${core.point}P`).join(' · ') || '데이터 없음'}</p></div><div className="api-items">{loaded.snapshot.build.gems.items.slice(0, 8).map((item, index) => <span key={`gem-${index}`}><ApiIcon url={item.iconUrl} label={item.name} />{item.name}</span>)}{loaded.snapshot.build.equipment.items.slice(0, 4).map((item, index) => <span key={`equipment-${index}`}><ApiIcon url={item.iconUrl} label={item.name} />{item.name}</span>)}{loaded.snapshot.build.avatars.items.slice(0, 4).map((item, index) => <span key={`avatar-${index}`}><ApiIcon url={item.iconUrl} label={item.name} />{item.name}</span>)}</div></section></section> : <section id="panel-results" role="tabpanel" aria-labelledby="tab-results" className={simulationStatus === 'fresh' ? '' : 'results-stale'}><div className="panel-heading"><div><h2>스킬 피해 결과</h2><p>모든 표시는 반올림된 두 자리이며, 계산용 소수 문자열은 변경하지 않습니다.</p></div></div><div className="result-grid">{(catalog?.skills ?? []).map((skill) => <ResultCard key={skill.id} skill={skill} baseline={loaded.baseline.find((item) => item.skillId === skill.id)} candidate={results.find((item) => item.skillId === skill.id)} />)}</div></section>}</section></div>}
  </main>;
}
