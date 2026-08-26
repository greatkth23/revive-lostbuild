import {
  calculatorVersion,
  calculateAllSkillDamage,
  ENDPOINT_SOURCES,
  PARSER_VERSION,
  parseBuildSnapshot
} from '@weather-artist/calculator';
import {
  WEATHER_ARTIST_CATALOG_VERSION,
  weatherArtistCatalog
} from '@weather-artist/catalog';
import {
  buildPatchSchema,
  buildSnapshotSchema,
  type BuildPatch,
  type BuildSnapshot
} from '@weather-artist/contracts';
import { applyBuildPatches } from './patches.js';

const SNAPSHOT_TTL_MS = 300_000;
const MAX_BODY_BYTES = 16_384;
const CLIENT_ID_PATTERN = /^[A-Za-z0-9_-]{8,128}$/;
const OFFICIAL_API_BASE = 'https://developer-lostark.game.onstove.com';
const ENDPOINT_PATHS: Record<(typeof ENDPOINT_SOURCES)[number], string> = {
  profiles: 'profiles',
  equipment: 'equipment',
  avatars: 'avatars',
  combatSkills: 'combat-skills',
  engravings: 'engravings',
  cards: 'cards',
  gems: 'gems',
  arkPassive: 'arkpassive',
  arkGrid: 'arkgrid'
};
const SECURITY_HEADERS = {
  'content-security-policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https: data:; connect-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'",
  'permissions-policy': 'camera=(), geolocation=(), microphone=()',
  'referrer-policy': 'no-referrer',
  'x-content-type-options': 'nosniff',
  'x-frame-options': 'DENY'
} as const;

export interface StoredSnapshot {
  snapshot: BuildSnapshot;
  expiresAt: number;
}

export interface SnapshotStorage {
  getCharacterSnapshotId(characterKey: string): Promise<string | null>;
  getSnapshot(snapshotId: string): Promise<StoredSnapshot | null>;
  putSnapshot(characterKey: string, record: StoredSnapshot): Promise<void>;
}

export interface RateLimitResult {
  allowed: boolean;
  retryAfterSeconds: number;
}

export interface RateLimitStore {
  consume(key: string, limit: number, windowMs: number, now: number): Promise<RateLimitResult>;
}

export interface BudgetService {
  grant(endpointCalls: number): Promise<RateLimitResult>;
}

export interface CharacterLoadCoordinator {
  coordinate<T>(
    characterKey: string,
    characterName: string,
    forceRefresh: boolean,
    task: () => Promise<T>
  ): Promise<T>;
}

export interface SafeLogEntry {
  requestId: string;
  route: string;
  status: number;
  durationMs: number;
  cacheHit: boolean | null;
  versions: {
    schema: '1';
    calculator: string;
    parser: string;
    catalog: string;
  };
}

export interface WorkerDependencies {
  storage: SnapshotStorage;
  rateLimits: RateLimitStore;
  budget: BudgetService;
  upstreamFetch: typeof fetch;
  token: string;
  now: () => number;
  randomUUID: () => string;
  characterLoads: CharacterLoadCoordinator;
  turnstileEnabled: boolean;
  verifyTurnstile?: (token: string) => Promise<boolean>;
  assets?: Fetcher;
  log: (entry: SafeLogEntry) => void;
}

type FreshLoadDependencies = Pick<WorkerDependencies,
  'storage' | 'budget' | 'upstreamFetch' | 'token' | 'now' | 'randomUUID'>;

interface LoadResult {
  snapshot: BuildSnapshot;
  baseline: ReturnType<typeof calculateAllSkillDamage>;
  cacheHit: boolean;
}

interface Env {
  SNAPSHOTS: KVNamespace;
  UPSTREAM_BUDGET: DurableObjectNamespace;
  ASSETS?: Fetcher;
  LOSTARK_API_TOKEN: string;
  TURNSTILE_ENABLED?: string;
  TURNSTILE_SECRET?: string;
}

class HttpError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly retryAfter?: number | string
  ) {
    super(message);
  }
}

function withSecurityHeaders(response: Response): Response {
  const secured = new Response(response.body, response);
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) secured.headers.set(name, value);
  return secured;
}

function json(data: unknown, status = 200, retryAfter?: number | string): Response {
  const headers = new Headers(SECURITY_HEADERS);
  if (retryAfter !== undefined) headers.set('retry-after', String(retryAfter));
  return Response.json(data, { status, headers });
}

function success(data: unknown, warnings: BuildSnapshot['warnings'] = []): Response {
  return json({ schemaVersion: '1', ok: true, data, warnings });
}

function failure(error: HttpError, requestId: string): Response {
  return json({
    schemaVersion: '1',
    ok: false,
    error: { code: error.code, message: error.message, requestId }
  }, error.status, error.retryAfter);
}

async function readJson(request: Request): Promise<Record<string, unknown>> {
  const contentLength = Number(request.headers.get('content-length') ?? 0);
  if (Number.isFinite(contentLength) && contentLength > MAX_BODY_BYTES) {
    throw new HttpError(413, 'PAYLOAD_TOO_LARGE', 'Request body exceeds 16 KiB');
  }
  if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) {
    throw new HttpError(415, 'UNSUPPORTED_MEDIA_TYPE', 'Content-Type must be application/json');
  }
  const chunks: Uint8Array[] = [];
  let totalBytes = 0;
  if (request.body) {
    const reader = request.body.getReader();
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        totalBytes += value.byteLength;
        if (totalBytes > MAX_BODY_BYTES) {
          await reader.cancel('Request body exceeds 16 KiB');
          throw new HttpError(413, 'PAYLOAD_TOO_LARGE', 'Request body exceeds 16 KiB');
        }
        chunks.push(value);
      }
    } finally {
      reader.releaseLock();
    }
  }
  const bytes = new Uint8Array(totalBytes);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  const text = new TextDecoder().decode(bytes);
  try {
    const parsed: unknown = JSON.parse(text);
    if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('object required');
    return parsed as Record<string, unknown>;
  } catch {
    throw new HttpError(400, 'INVALID_JSON', 'Request body must be a JSON object');
  }
}

function clientId(request: Request): string {
  const value = request.headers.get('x-anonymous-client-id') ?? '';
  if (!CLIENT_ID_PATTERN.test(value)) {
    throw new HttpError(400, 'INVALID_CLIENT_ID', 'X-Anonymous-Client-Id must be 8-128 URL-safe characters');
  }
  return value;
}

function normalizedCharacterName(value: unknown): { display: string; key: string } {
  if (typeof value !== 'string') throw new HttpError(400, 'INVALID_CHARACTER_NAME', 'characterName is required');
  const display = value.normalize('NFKC').trim().replace(/\s+/g, ' ');
  if (display.length < 1 || display.length > 24 || /[\u0000-\u001f\u007f]/.test(display)) {
    throw new HttpError(400, 'INVALID_CHARACTER_NAME', 'characterName must contain 1-24 printable characters');
  }
  return { display, key: display.toLocaleLowerCase('ko-KR') };
}

async function enforceRateLimit(
  store: RateLimitStore,
  key: string,
  limit: number,
  windowMs: number,
  now: number,
  code: string
): Promise<void> {
  const result = await store.consume(key, limit, windowMs, now);
  if (!result.allowed) throw new HttpError(429, code, 'Request rate limit exceeded', result.retryAfterSeconds);
}

async function verifyTurnstile(body: Record<string, unknown>, dependencies: WorkerDependencies): Promise<void> {
  if (!dependencies.turnstileEnabled) return;
  const token = body.turnstileToken;
  if (typeof token !== 'string' || token.length < 1 || token.length > 2048 || !dependencies.verifyTurnstile) {
    throw new HttpError(403, 'TURNSTILE_REQUIRED', 'Turnstile verification is required');
  }
  if (!await dependencies.verifyTurnstile(token)) {
    throw new HttpError(403, 'TURNSTILE_FAILED', 'Turnstile verification failed');
  }
}

async function fetchOfficialBundle(
  characterName: string,
  dependencies: FreshLoadDependencies
): Promise<Record<string, unknown>> {
  const grant = await dependencies.budget.grant(ENDPOINT_SOURCES.length);
  if (!grant.allowed) {
    throw new HttpError(429, 'GLOBAL_UPSTREAM_RATE_LIMITED', 'Official API budget is temporarily exhausted', grant.retryAfterSeconds);
  }
  const authorization = dependencies.token.startsWith('Bearer ')
    ? dependencies.token
    : `Bearer ${dependencies.token}`;
  const encodedName = encodeURIComponent(characterName);
  const outcomes = await Promise.all(ENDPOINT_SOURCES.map(async (endpoint) => {
    try {
      const response = await dependencies.upstreamFetch(
        `${OFFICIAL_API_BASE}/armories/characters/${encodedName}/${ENDPOINT_PATHS[endpoint]}`,
        { headers: { accept: 'application/json', authorization } }
      );
      if (!response.ok) {
        return { endpoint, status: response.status, retryAfter: response.headers.get('retry-after') } as const;
      }
      try {
        return { endpoint, status: response.status, data: await response.json() } as const;
      } catch {
        return { endpoint, status: 502 } as const;
      }
    } catch {
      return { endpoint, status: 503 } as const;
    }
  }));
  if (outcomes.some((outcome) => outcome.endpoint === 'profiles' && outcome.status === 404)) {
    throw new HttpError(404, 'CHARACTER_NOT_FOUND', 'Character was not found');
  }
  const throttled = outcomes.find((outcome) => outcome.status === 429);
  if (throttled) {
    const rawRetryAfter = 'retryAfter' in throttled ? throttled.retryAfter : null;
    const parsed = Number(rawRetryAfter);
    const retryAfter = Number.isFinite(parsed) && parsed > 0
      ? Math.ceil(parsed)
      : rawRetryAfter && Number.isFinite(Date.parse(rawRetryAfter)) ? rawRetryAfter : 60;
    throw new HttpError(429, 'UPSTREAM_RATE_LIMITED', 'Official API rate limit exceeded', retryAfter);
  }
  if (outcomes.some((outcome) => outcome.status !== 200 || !('data' in outcome))) {
    throw new HttpError(503, 'UPSTREAM_UNAVAILABLE', 'Official API returned a partial failure');
  }
  return Object.fromEntries(outcomes.map((outcome) => [outcome.endpoint, outcome.data]));
}

function validateSupportedSnapshot(snapshot: BuildSnapshot): void {
  if (snapshot.build.profile.className !== '기상술사') {
    throw new HttpError(422, 'UNSUPPORTED_CLASS', 'Only Weather Artist characters are supported');
  }
  if (!snapshot.build.arkPassive.speedByName['질풍노도']) {
    throw new HttpError(422, 'UNSUPPORTED_BUILD', 'Only the supported 질풍노도 build is available');
  }
}

async function loadFresh(
  name: { display: string; key: string },
  dependencies: FreshLoadDependencies
): Promise<LoadResult> {
  const responses = await fetchOfficialBundle(name.display, dependencies);
  let parsed: BuildSnapshot;
  try {
    parsed = parseBuildSnapshot({
      characterName: name.display,
      capturedAtKst: new Date(dependencies.now()).toISOString(),
      responses
    });
  } catch (error) {
    if (error instanceof HttpError) throw error;
    throw new HttpError(503, 'UPSTREAM_INVALID_PAYLOAD', 'Official API response could not be normalized');
  }
  const snapshot: BuildSnapshot = { ...parsed, snapshotId: dependencies.randomUUID() };
  if (!buildSnapshotSchema.safeParse(snapshot).success) {
    throw new HttpError(503, 'UPSTREAM_INVALID_PAYLOAD', 'Normalized snapshot failed contract validation');
  }
  validateSupportedSnapshot(snapshot);
  const baseline = calculateAllSkillDamage(snapshot);
  await dependencies.storage.putSnapshot(name.key, {
    snapshot,
    expiresAt: dependencies.now() + SNAPSHOT_TTL_MS
  });
  return { snapshot, baseline, cacheHit: false };
}

function createLoader(dependencies: WorkerDependencies) {

  return async (body: Record<string, unknown>, anonymousId: string): Promise<LoadResult> => {
    const name = normalizedCharacterName(body.characterName);
    const forceRefresh = body.forceRefresh === true;
    const now = dependencies.now();
    if (body.forceRefresh !== undefined && typeof body.forceRefresh !== 'boolean') {
      throw new HttpError(400, 'INVALID_FORCE_REFRESH', 'forceRefresh must be a boolean');
    }
    await verifyTurnstile(body, dependencies);
    if (forceRefresh) {
      await enforceRateLimit(dependencies.rateLimits, `force:${anonymousId}`, 1, 60_000, now, 'FORCE_REFRESH_RATE_LIMITED');
    } else {
      const cachedId = await dependencies.storage.getCharacterSnapshotId(name.key);
      if (cachedId) {
        const cached = await dependencies.storage.getSnapshot(cachedId);
        if (cached && cached.expiresAt > now) {
          return { snapshot: cached.snapshot, baseline: calculateAllSkillDamage(cached.snapshot), cacheHit: true };
        }
      }
    }
    await enforceRateLimit(dependencies.rateLimits, `miss:${anonymousId}`, 3, 60_000, now, 'CACHE_MISS_RATE_LIMITED');

    return dependencies.characterLoads.coordinate(
      name.key,
      name.display,
      forceRefresh,
      () => loadFresh(name, dependencies)
    );
  };
}

function validatePatch(patch: BuildPatch): void {
  const section = 'sectionId' in patch
    ? weatherArtistCatalog.editableSections.find((candidate) => candidate.id === patch.sectionId)
    : undefined;
  if (patch.kind === 'reset-section') {
    if (!section) {
      throw new HttpError(422, 'INVALID_PATCH', 'Patch references an unknown section');
    }
    return;
  }
  if (patch.kind === 'set-section-enabled') {
    if (!section) throw new HttpError(422, 'INVALID_PATCH', 'Patch references an unknown section');
    if (!section.editable) throw new HttpError(422, 'INVALID_PATCH', 'Patch references a locked section');
    return;
  }
  if ('skillId' in patch && !weatherArtistCatalog.skills.some((skill) => skill.id === patch.skillId)) {
    throw new HttpError(422, 'INVALID_PATCH', 'Patch references an unknown skill');
  }
  throw new HttpError(422, 'INVALID_PATCH', 'Patch operation is not supported by the validated catalog');
}

function validateVersions(body: Record<string, unknown>, snapshot: BuildSnapshot): void {
  if (
    body.schemaVersion !== '1'
    || body.calculatorVersion !== calculatorVersion
    || body.parserVersion !== PARSER_VERSION
    || body.catalogVersion !== WEATHER_ARTIST_CATALOG_VERSION
    || snapshot.schemaVersion !== '1'
    || snapshot.calculatorVersion !== calculatorVersion
    || snapshot.parserVersion !== PARSER_VERSION
    || snapshot.catalogVersion !== WEATHER_ARTIST_CATALOG_VERSION
  ) {
    throw new HttpError(409, 'VERSION_MISMATCH', 'Snapshot, ruleset, parser, or catalog version does not match');
  }
}

async function simulate(body: Record<string, unknown>, dependencies: WorkerDependencies): Promise<Response> {
  if (typeof body.snapshotId !== 'string' || !/^[0-9a-f-]{36}$/i.test(body.snapshotId)) {
    throw new HttpError(400, 'INVALID_SNAPSHOT_ID', 'snapshotId must be an opaque UUID');
  }
  const stored = await dependencies.storage.getSnapshot(body.snapshotId);
  if (!stored || stored.expiresAt <= dependencies.now()) {
    throw new HttpError(410, 'SNAPSHOT_EXPIRED', 'Snapshot is missing or expired; reload the character');
  }
  validateVersions(body, stored.snapshot);
  if (!Array.isArray(body.patches) || body.patches.length > 100) {
    throw new HttpError(400, 'INVALID_PATCH', 'patches must be an array with at most 100 entries');
  }
  const patches = body.patches.map((value) => {
    const parsed = buildPatchSchema.safeParse(value);
    if (!parsed.success) throw new HttpError(422, 'INVALID_PATCH', 'Patch failed contract validation');
    validatePatch(parsed.data);
    return parsed.data;
  });
  const scenario = body.scenario;
  if (scenario === null || typeof scenario !== 'object' || Array.isArray(scenario)) {
    throw new HttpError(400, 'INVALID_SCENARIO', 'scenario must be an object');
  }
  if ((scenario as Record<string, unknown>).schemaVersion !== '1') {
    throw new HttpError(409, 'VERSION_MISMATCH', 'Scenario schema version does not match');
  }
  const directional = (scenario as Record<string, unknown>).directionalSuccessBySkill;
  if (directional === null || typeof directional !== 'object' || Array.isArray(directional)) {
    throw new HttpError(400, 'INVALID_SCENARIO', 'directionalSuccessBySkill must be an object');
  }
  for (const [skillId, enabled] of Object.entries(directional as Record<string, unknown>)) {
    if (!weatherArtistCatalog.skills.some((skill) => skill.id === skillId) || typeof enabled !== 'boolean') {
      throw new HttpError(422, 'INVALID_SCENARIO', 'Scenario references an unknown skill or non-boolean setting');
    }
  }
  const baseline = calculateAllSkillDamage(stored.snapshot);
  const candidateSnapshot = applyBuildPatches(stored.snapshot, patches);
  const candidate = calculateAllSkillDamage(candidateSnapshot, {
    directionalSuccessBySkill: directional as Record<string, boolean>
  });
  return success({ schemaVersion: '1', snapshotId: body.snapshotId, patches, baseline, candidate }, stored.snapshot.warnings);
}

export function createWorkerApp(dependencies: WorkerDependencies): { fetch(request: Request): Promise<Response> } {
  const load = createLoader(dependencies);
  return {
    async fetch(request: Request): Promise<Response> {
      const startedAt = dependencies.now();
      const requestId = dependencies.randomUUID();
      const { pathname } = new URL(request.url);
      let loggedRoute = 'unmatched';
      let status = 500;
      let cacheHit: boolean | null = null;
      let response: Response;
      try {
        if (request.method === 'GET' && pathname === '/api/v1/catalog/weather-artist') {
          loggedRoute = '/api/v1/catalog/weather-artist';
          response = success(weatherArtistCatalog);
        } else if (request.method === 'POST' && pathname === '/api/v1/characters/load') {
          loggedRoute = '/api/v1/characters/load';
          const anonymousId = clientId(request);
          const result = await load(await readJson(request), anonymousId);
          cacheHit = result.cacheHit;
          response = success(result, result.snapshot.warnings);
        } else if (request.method === 'POST' && pathname === '/api/v1/simulations') {
          loggedRoute = '/api/v1/simulations';
          clientId(request);
          response = await simulate(await readJson(request), dependencies);
        } else if (pathname !== '/api' && !pathname.startsWith('/api/') && dependencies.assets) {
          loggedRoute = 'static-assets';
          response = withSecurityHeaders(await dependencies.assets.fetch(request));
        } else {
          throw new HttpError(404, 'NOT_FOUND', 'Route not found');
        }
      } catch (error) {
        const safeError = error instanceof HttpError
          ? error
          : new HttpError(500, 'INTERNAL_ERROR', 'An internal error occurred');
        response = failure(safeError, requestId);
      }
      status = response.status;
      dependencies.log({
        requestId,
        route: loggedRoute,
        status,
        durationMs: Math.max(0, dependencies.now() - startedAt),
        cacheHit,
        versions: {
          schema: '1',
          calculator: calculatorVersion,
          parser: PARSER_VERSION,
          catalog: WEATHER_ARTIST_CATALOG_VERSION
        }
      });
      return withSecurityHeaders(response);
    }
  };
}

class KVSnapshotStorage implements SnapshotStorage {
  constructor(private readonly kv: KVNamespace) {}

  async getCharacterSnapshotId(characterKey: string): Promise<string | null> {
    return this.kv.get(`character:${await digest(characterKey)}`);
  }

  async getSnapshot(snapshotId: string): Promise<StoredSnapshot | null> {
    return this.kv.get<StoredSnapshot>(`snapshot:${snapshotId}`, 'json');
  }

  async putSnapshot(characterKey: string, record: StoredSnapshot): Promise<void> {
    await Promise.all([
      this.kv.put(`snapshot:${record.snapshot.snapshotId}`, JSON.stringify(record), { expirationTtl: 300 }),
      this.kv.put(`character:${await digest(characterKey)}`, record.snapshot.snapshotId, { expirationTtl: 300 })
    ]);
  }
}

class DurableObjectBudgetService implements BudgetService {
  constructor(private readonly namespace: DurableObjectNamespace) {}

  async grant(endpointCalls: number): Promise<RateLimitResult> {
    const stub = this.namespace.get(this.namespace.idFromName('global'));
    const response = await stub.fetch('https://budget.internal/grant', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ endpointCalls })
    });
    const retryAfterSeconds = Number(response.headers.get('retry-after') ?? 0);
    return { allowed: response.ok, retryAfterSeconds };
  }
}

class DurableObjectRateLimitStore implements RateLimitStore {
  constructor(private readonly namespace: DurableObjectNamespace) {}

  async consume(key: string, limit: number, windowMs: number, _now: number): Promise<RateLimitResult> {
    const id = this.namespace.idFromName(`rate:${await digest(key)}`);
    const response = await this.namespace.get(id).fetch('https://budget.internal/consume', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ limit, windowMs })
    });
    return {
      allowed: response.ok,
      retryAfterSeconds: Number(response.headers.get('retry-after') ?? 0)
    };
  }
}

class DurableObjectCharacterLoadCoordinator implements CharacterLoadCoordinator {
  constructor(private readonly namespace: DurableObjectNamespace) {}

  async coordinate<T>(
    characterKey: string,
    characterName: string,
    forceRefresh: boolean,
    _task: () => Promise<T>
  ): Promise<T> {
    const id = this.namespace.idFromName(`character:${await digest(characterKey)}`);
    const response = await this.namespace.get(id).fetch('https://budget.internal/character/load', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ characterName, forceRefresh })
    });
    const body = await response.json() as LoadResult | { error: { code: string; message: string } };
    if (!response.ok) {
      const error = 'error' in body ? body.error : { code: 'INTERNAL_ERROR', message: 'Character load coordination failed' };
      throw new HttpError(response.status, error.code, error.message, response.headers.get('retry-after') ?? undefined);
    }
    return body as T;
  }
}

async function digest(value: string): Promise<string> {
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return [...new Uint8Array(bytes)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

function dependenciesFromEnv(env: Env): WorkerDependencies {
  const storage = new KVSnapshotStorage(env.SNAPSHOTS);
  const turnstileEnabled = env.TURNSTILE_ENABLED === 'true';
  const dependencies: WorkerDependencies = {
    storage,
    rateLimits: new DurableObjectRateLimitStore(env.UPSTREAM_BUDGET),
    budget: new DurableObjectBudgetService(env.UPSTREAM_BUDGET),
    upstreamFetch: fetch,
    token: env.LOSTARK_API_TOKEN,
    now: Date.now,
    randomUUID: () => crypto.randomUUID(),
    characterLoads: new DurableObjectCharacterLoadCoordinator(env.UPSTREAM_BUDGET),
    turnstileEnabled,
    log: (entry) => console.log(JSON.stringify(entry))
  };
  if (env.ASSETS) dependencies.assets = env.ASSETS;
  if (turnstileEnabled && env.TURNSTILE_SECRET) {
    dependencies.verifyTurnstile = async (token) => {
      const form = new FormData();
      form.set('secret', env.TURNSTILE_SECRET!);
      form.set('response', token);
      const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method: 'POST',
        body: form
      });
      const result = await response.json<{ success?: boolean }>();
      return result.success === true;
    };
  }
  return dependencies;
}

const defaultWorker = {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (!env?.SNAPSHOTS || !env.UPSTREAM_BUDGET) {
      const { pathname } = new URL(request.url);
      if (request.method === 'GET' && pathname === '/api/v1/catalog/weather-artist') {
        return withSecurityHeaders(success(weatherArtistCatalog));
      }
      return failure(new HttpError(503, 'WORKER_NOT_CONFIGURED', 'Worker bindings are not configured'), crypto.randomUUID());
    }
    return createWorkerApp(dependenciesFromEnv(env)).fetch(request);
  }
} satisfies ExportedHandler<Env>;

export class UpstreamBudget implements DurableObject {
  private characterInflight: Promise<LoadResult> | undefined;

  constructor(private readonly state: DurableObjectState, private readonly env?: Env) {}

  async fetch(request: Request): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Not found', { status: 404 });
    }
    const path = new URL(request.url).pathname;
    if (path === '/character/load') {
      if (!this.env) return Response.json({ error: { code: 'WORKER_NOT_CONFIGURED', message: 'Worker bindings are not configured' } }, { status: 503 });
      let body: { characterName?: unknown; forceRefresh?: unknown };
      try {
        body = await request.json<typeof body>();
      } catch {
        return Response.json({ error: { code: 'INVALID_JSON', message: 'Invalid internal request' } }, { status: 400 });
      }
      let name: { display: string; key: string };
      try {
        name = normalizedCharacterName(body.characterName);
      } catch (error) {
        const safeError = error instanceof HttpError ? error : new HttpError(400, 'INVALID_CHARACTER_NAME', 'Invalid character name');
        return Response.json({ error: { code: safeError.code, message: safeError.message } }, { status: safeError.status });
      }
      const forceRefresh = body.forceRefresh === true;
      const storage = new KVSnapshotStorage(this.env.SNAPSHOTS);
      if (!forceRefresh) {
        const cachedId = await storage.getCharacterSnapshotId(name.key);
        const cached = cachedId ? await storage.getSnapshot(cachedId) : null;
        if (cached && cached.expiresAt > Date.now()) {
          return Response.json({ snapshot: cached.snapshot, baseline: calculateAllSkillDamage(cached.snapshot), cacheHit: true });
        }
      }
      if (!this.characterInflight) {
        this.characterInflight = loadFresh(name, {
          storage,
          budget: new DurableObjectBudgetService(this.env.UPSTREAM_BUDGET),
          upstreamFetch: fetch,
          token: this.env.LOSTARK_API_TOKEN,
          now: Date.now,
          randomUUID: () => crypto.randomUUID()
        });
      }
      const pending = this.characterInflight;
      try {
        return Response.json(await pending);
      } catch (error) {
        const safeError = error instanceof HttpError ? error : new HttpError(500, 'INTERNAL_ERROR', 'Character load failed');
        const init: ResponseInit = { status: safeError.status };
        if (safeError.retryAfter !== undefined) init.headers = { 'retry-after': String(safeError.retryAfter) };
        return Response.json({ error: { code: safeError.code, message: safeError.message } }, init);
      } finally {
        if (this.characterInflight === pending) this.characterInflight = undefined;
      }
    }
    if (path === '/consume') {
      let limit: number;
      let windowMs: number;
      try {
        const body = await request.json<{ limit?: unknown; windowMs?: unknown }>();
        limit = Number(body.limit);
        windowMs = Number(body.windowMs);
      } catch {
        return new Response('Invalid request', { status: 400 });
      }
      if (!Number.isInteger(limit) || limit < 1 || limit > 100 || !Number.isInteger(windowMs) || windowMs < 1_000 || windowMs > 3_600_000) {
        return new Response('Invalid rate limit window', { status: 400 });
      }
      const now = Date.now();
      return this.state.storage.transaction(async (transaction) => {
        const prior = await transaction.get<number[]>('rate') ?? [];
        const active = prior.filter((time) => time > now - windowMs);
        if (active.length >= limit) {
          const retryAfter = Math.max(1, Math.ceil((active[0]! + windowMs - now) / 1000));
          return new Response('Rate limited', { status: 429, headers: { 'retry-after': String(retryAfter) } });
        }
        active.push(now);
        await transaction.put('rate', active);
        return new Response(null, { status: 204 });
      });
    }
    if (path !== '/grant') return new Response('Not found', { status: 404 });
    let endpointCalls: number;
    try {
      const body = await request.json<{ endpointCalls?: unknown }>();
      endpointCalls = Number(body.endpointCalls);
    } catch {
      return new Response('Invalid request', { status: 400 });
    }
    if (!Number.isInteger(endpointCalls) || endpointCalls < 1 || endpointCalls > 90) {
      return new Response('Invalid endpoint call count', { status: 400 });
    }
    const now = Date.now();
    return this.state.storage.transaction(async (transaction) => {
      const prior = await transaction.get<number[]>('budget') ?? [];
      const active = prior.filter((time) => time > now - 60_000);
      if (active.length + endpointCalls > 90) {
        const callsThatMustExpire = active.length + endpointCalls - 90;
        const retryAt = active[callsThatMustExpire - 1]! + 60_000;
        const retryAfter = Math.max(1, Math.ceil((retryAt - now) / 1000));
        return new Response('Rate limited', { status: 429, headers: { 'retry-after': String(retryAfter) } });
      }
      active.push(...Array.from({ length: endpointCalls }, () => now));
      await transaction.put('budget', active);
      return new Response(null, { status: 204 });
    });
  }
}

export default defaultWorker;
