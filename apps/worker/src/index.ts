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
  turnstileEnabled: boolean;
  verifyTurnstile?: (token: string) => Promise<boolean>;
  assets?: Fetcher;
  log: (entry: SafeLogEntry) => void;
  inflight?: Map<string, Promise<LoadResult>>;
}

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
    readonly retryAfterSeconds?: number
  ) {
    super(message);
  }
}

function withSecurityHeaders(response: Response): Response {
  const secured = new Response(response.body, response);
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) secured.headers.set(name, value);
  return secured;
}

function json(data: unknown, status = 200, retryAfterSeconds?: number): Response {
  const headers = new Headers(SECURITY_HEADERS);
  if (retryAfterSeconds !== undefined) headers.set('retry-after', String(retryAfterSeconds));
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
  }, error.status, error.retryAfterSeconds);
}

async function readJson(request: Request): Promise<Record<string, unknown>> {
  const contentLength = Number(request.headers.get('content-length') ?? 0);
  if (Number.isFinite(contentLength) && contentLength > MAX_BODY_BYTES) {
    throw new HttpError(413, 'PAYLOAD_TOO_LARGE', 'Request body exceeds 16 KiB');
  }
  if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) {
    throw new HttpError(415, 'UNSUPPORTED_MEDIA_TYPE', 'Content-Type must be application/json');
  }
  const text = await request.text();
  if (new TextEncoder().encode(text).byteLength > MAX_BODY_BYTES) {
    throw new HttpError(413, 'PAYLOAD_TOO_LARGE', 'Request body exceeds 16 KiB');
  }
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
  dependencies: WorkerDependencies
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
    const parsed = Number('retryAfter' in throttled ? throttled.retryAfter ?? 60 : 60);
    const retryAfter = Number.isFinite(parsed) && parsed > 0 ? Math.ceil(parsed) : 60;
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

function createLoader(dependencies: WorkerDependencies) {
  const inflight = dependencies.inflight ?? new Map<string, Promise<LoadResult>>();

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

    const existing = inflight.get(name.key);
    if (existing) return existing;
    const load = (async (): Promise<LoadResult> => {
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
    })();
    inflight.set(name.key, load);
    try {
      return await load;
    } finally {
      if (inflight.get(name.key) === load) inflight.delete(name.key);
    }
  };
}

function validatePatch(patch: BuildPatch): void {
  if (patch.kind === 'reset-section') {
    if (!weatherArtistCatalog.editableSections.some((section) => section.id === patch.sectionId)) {
      throw new HttpError(422, 'INVALID_PATCH', 'Patch references an unknown section');
    }
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
  const simulated = calculateAllSkillDamage(stored.snapshot, {
    directionalSuccessBySkill: directional as Record<string, boolean>
  });
  return success({ snapshotId: body.snapshotId, patches, baseline, simulated }, stored.snapshot.warnings);
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
        } else if (!pathname.startsWith('/api/') && dependencies.assets) {
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

async function digest(value: string): Promise<string> {
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return [...new Uint8Array(bytes)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

const defaultInflight = new Map<string, Promise<LoadResult>>();

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
    randomUUID: crypto.randomUUID,
    turnstileEnabled,
    log: (entry) => console.log(JSON.stringify(entry)),
    inflight: defaultInflight
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
  constructor(private readonly state: DurableObjectState) {}

  async fetch(request: Request): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Not found', { status: 404 });
    }
    const path = new URL(request.url).pathname;
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
      const previous = await transaction.get<{ windowStartedAt: number; endpointCalls: number }>('budget');
      const budget = !previous || now - previous.windowStartedAt >= 60_000
        ? { windowStartedAt: now, endpointCalls: 0 }
        : previous;
      if (budget.endpointCalls + endpointCalls > 90) {
        const retryAfter = Math.max(1, Math.ceil((budget.windowStartedAt + 60_000 - now) / 1000));
        return new Response('Rate limited', { status: 429, headers: { 'retry-after': String(retryAfter) } });
      }
      await transaction.put('budget', { ...budget, endpointCalls: budget.endpointCalls + endpointCalls });
      return new Response(null, { status: 204 });
    });
  }
}

export default defaultWorker;
