import { readFileSync } from 'node:fs';
import { describe, expect, test, vi } from 'vitest';
import worker, {
  createWorkerApp,
  UpstreamBudget,
  type BudgetService,
  type RateLimitStore,
  type SafeLogEntry,
  type SnapshotStorage,
  type StoredSnapshot,
  type WorkerDependencies
} from './index.js';

const rawFixturePath = new URL(
  '../../../api-chatgpt-conversation-6a6309ab-7de4-8342/outputs/봄날꽃씨_우레바람_current-v2.7.2_api_raw.json',
  import.meta.url
);

type RawBundle = { responses: Record<string, unknown> };

function loadRawFixture(): RawBundle {
  return JSON.parse(readFileSync(rawFixturePath, 'utf8')) as RawBundle;
}

class MemoryStorage implements SnapshotStorage {
  readonly characters = new Map<string, string>();
  readonly snapshots = new Map<string, StoredSnapshot>();

  async getCharacterSnapshotId(characterKey: string): Promise<string | null> {
    return this.characters.get(characterKey) ?? null;
  }

  async getSnapshot(snapshotId: string): Promise<StoredSnapshot | null> {
    return this.snapshots.get(snapshotId) ?? null;
  }

  async putSnapshot(characterKey: string, record: StoredSnapshot): Promise<void> {
    this.characters.set(characterKey, record.snapshot.snapshotId);
    this.snapshots.set(record.snapshot.snapshotId, structuredClone(record));
  }
}

class MemoryRateLimits implements RateLimitStore {
  readonly entries = new Map<string, number[]>();

  async consume(key: string, limit: number, windowMs: number, now: number) {
    const active = (this.entries.get(key) ?? []).filter((time) => time > now - windowMs);
    if (active.length >= limit) {
      return { allowed: false as const, retryAfterSeconds: Math.max(1, Math.ceil((active[0]! + windowMs - now) / 1000)) };
    }
    active.push(now);
    this.entries.set(key, active);
    return { allowed: true as const, retryAfterSeconds: 0 };
  }
}

interface HarnessOptions {
  mutate?: (raw: RawBundle) => void;
  endpointStatus?: Partial<Record<string, number>>;
  endpointRetryAfter?: Partial<Record<string, string>>;
  endpointDelay?: Partial<Record<string, number>>;
  budget?: BudgetService;
  assets?: Fetcher;
}

function makeHarness(options: HarnessOptions = {}) {
  const raw = loadRawFixture();
  options.mutate?.(raw);
  const storage = new MemoryStorage();
  const rateLimits = new MemoryRateLimits();
  const calls: Array<{ endpoint: string; authorization: string | null }> = [];
  const logs: SafeLogEntry[] = [];
  let now = Date.UTC(2026, 7, 25, 10, 0, 0);
  let sequence = 0;
  let activeFetches = 0;
  let maximumConcurrentFetches = 0;
  const endpointByPath: Record<string, string> = {
    profiles: 'profiles',
    equipment: 'equipment',
    avatars: 'avatars',
    'combat-skills': 'combatSkills',
    engravings: 'engravings',
    cards: 'cards',
    gems: 'gems',
    arkpassive: 'arkPassive',
    arkgrid: 'arkGrid'
  };
  const upstreamFetch: typeof fetch = async (input, init) => {
    const url = new URL(typeof input === 'string' ? input : input instanceof URL ? input.href : input.url);
    const endpoint = endpointByPath[url.pathname.split('/').at(-1)!]!;
    calls.push({ endpoint, authorization: new Headers(init?.headers).get('authorization') });
    activeFetches += 1;
    maximumConcurrentFetches = Math.max(maximumConcurrentFetches, activeFetches);
    await new Promise((resolve) => setTimeout(resolve, options.endpointDelay?.[endpoint] ?? 1));
    activeFetches -= 1;
    const status = options.endpointStatus?.[endpoint] ?? 200;
    const responseInit: ResponseInit = { status };
    if (options.endpointRetryAfter?.[endpoint]) {
      responseInit.headers = { 'retry-after': options.endpointRetryAfter[endpoint]! };
    }
    return Response.json(status === 200 ? raw.responses[endpoint] : { message: 'upstream failure' }, responseInit);
  };
  const dependencies: WorkerDependencies = {
    storage,
    rateLimits,
    budget: options.budget ?? { grant: async () => ({ allowed: true, retryAfterSeconds: 0 }) },
    upstreamFetch,
    token: 'Bearer secret-jwt-value',
    now: () => now,
    randomUUID: () => `00000000-0000-4000-8000-${String(++sequence).padStart(12, '0')}`,
    turnstileEnabled: false,
    log: (entry) => { logs.push(entry); }
  };
  if (options.assets) dependencies.assets = options.assets;
  return {
    app: createWorkerApp(dependencies),
    calls,
    logs,
    storage,
    get maximumConcurrentFetches() { return maximumConcurrentFetches; },
    advance(milliseconds: number) { now += milliseconds; }
  };
}

function loadRequest(characterName = '봄날꽃씨', overrides: Record<string, unknown> = {}, clientId = 'client_12345678') {
  return new Request('https://example.test/api/v1/characters/load', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-anonymous-client-id': clientId },
    body: JSON.stringify({ characterName, ...overrides })
  });
}

function simulationRequest(snapshotId: string, overrides: Record<string, unknown> = {}) {
  return new Request('https://example.test/api/v1/simulations', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-anonymous-client-id': 'client_12345678' },
    body: JSON.stringify({
      schemaVersion: '1',
      snapshotId,
      calculatorVersion: 'current-v2.7.2',
      parserVersion: 'lostark-api-ts-v1',
      catalogVersion: 'weather-artist-v0.4',
      patches: [],
      scenario: { schemaVersion: '1', id: 'best', bossConditionId: 'boss', directionalSuccessBySkill: {} },
      ...overrides
    })
  });
}

describe('Weather Artist Worker routes', () => {
  test('serves the versioned Weather Artist catalog with security headers', async () => {
    // Break caught: the fixed catalog route falls through to a placeholder/static response.
    const response = await worker.fetch(
      new Request('https://example.test/api/v1/catalog/weather-artist'),
      {} as never
    );

    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toContain('application/json');
    expect(response.headers.get('x-content-type-options')).toBe('nosniff');
    expect(await response.json()).toMatchObject({
      schemaVersion: '1',
      ok: true,
      data: {
        schemaVersion: '1',
        version: 'weather-artist-v0.4',
        equipmentGrowth: { editingLocked: true }
      }
    });
  });

  test('serves static assets with a CSP that permits the same-origin application bundle', async () => {
    // Break caught: an API-only default-src 'none' policy prevents the configured Vite bundle from running.
    const assets = { fetch: async () => new Response('<script src="/assets/app.js"></script>', {
      headers: { 'content-type': 'text/html' }
    }) } as unknown as Fetcher;
    const response = await makeHarness({ assets }).app.fetch(new Request('https://example.test/'));

    expect(response.status).toBe(200);
    expect(response.headers.get('content-security-policy')).toContain("script-src 'self'");
    expect(await response.text()).toContain('/assets/app.js');
  });

  test('loads nine official endpoints concurrently and stores an opaque normalized snapshot', async () => {
    // Break caught: serial fetching, secret exposure, or storing the parser's name-bearing fixture ID.
    const harness = makeHarness();
    const response = await harness.app.fetch(loadRequest());
    const body = await response.json() as any;

    expect(response.status).toBe(200);
    expect(harness.calls.map((call) => call.endpoint).sort()).toEqual([
      'arkGrid', 'arkPassive', 'avatars', 'cards', 'combatSkills', 'engravings', 'equipment', 'gems', 'profiles'
    ]);
    expect(harness.maximumConcurrentFetches).toBe(9);
    expect(harness.calls.every((call) => call.authorization === 'Bearer secret-jwt-value')).toBe(true);
    expect(JSON.stringify(body)).not.toContain('secret-jwt-value');
    expect(body).toMatchObject({
      schemaVersion: '1',
      ok: true,
      data: {
        cacheHit: false,
        snapshot: { classId: 'weather-artist', characterName: '봄날꽃씨' }
      }
    });
    expect(body.data.snapshot.snapshotId).toMatch(/^[0-9a-f-]{36}$/);
    expect(body.data.baseline).toHaveLength(6);
    expect(harness.storage.snapshots.get(body.data.snapshot.snapshotId)?.expiresAt).toBe(Date.UTC(2026, 7, 25, 10, 5, 0));
  });

  test('emits only privacy-safe structured request metadata', async () => {
    // Break caught: logs accidentally include character names, request settings, tooltips, or the JWT.
    const harness = makeHarness();
    await harness.app.fetch(loadRequest());

    expect(harness.logs).toHaveLength(1);
    expect(harness.logs[0]).toEqual({
      requestId: '00000000-0000-4000-8000-000000000001',
      route: '/api/v1/characters/load',
      status: 200,
      durationMs: 0,
      cacheHit: false,
      versions: {
        schema: '1',
        calculator: 'current-v2.7.2',
        parser: 'lostark-api-ts-v1',
        catalog: 'weather-artist-v0.4'
      }
    });
    const unknown = await harness.app.fetch(new Request('https://example.test/api/봄날꽃씨/private'));
    expect(unknown.status).toBe(404);
    expect(harness.logs).toHaveLength(2);
    expect(harness.logs[1]?.route).toBe('unmatched');
    expect(JSON.stringify(harness.logs)).not.toMatch(/봄날꽃씨|secret-jwt-value|Tooltip|settings/i);
  });

  test('serves normalized-name cache hits without consuming upstream or miss budget', async () => {
    // Break caught: checking the limiter/fetch before the character cache.
    const harness = makeHarness();
    const first = await harness.app.fetch(loadRequest('봄날꽃씨'));
    const second = await harness.app.fetch(loadRequest('  봄날꽃씨  '));
    const body = await second.json() as any;

    expect(first.status).toBe(200);
    expect(second.status).toBe(200);
    expect(body.data.cacheHit).toBe(true);
    expect(harness.calls).toHaveLength(9);
  });

  test('coalesces concurrent same-character misses into one nine-endpoint fetch', async () => {
    // Break caught: an in-flight cache miss fan-outs duplicate official API calls.
    const harness = makeHarness();
    const [first, second] = await Promise.all([
      harness.app.fetch(loadRequest()),
      harness.app.fetch(loadRequest())
    ]);

    expect(first.status).toBe(200);
    expect(second.status).toBe(200);
    expect(harness.calls).toHaveLength(9);
    expect((await first.json() as any).data.snapshot.snapshotId).toBe((await second.json() as any).data.snapshot.snapshotId);
  });

  test('rejects unsupported classes, missing characters, upstream throttles, and partial failure', async () => {
    // Break caught: malformed/unsupported upstream states being cached as usable snapshots.
    const cases: Array<[ReturnType<typeof makeHarness>, number, string, string | null]> = [
      [makeHarness({ mutate: (raw) => { (raw.responses.profiles as any).CharacterClassName = '바드'; } }), 422, 'UNSUPPORTED_CLASS', null],
      [makeHarness({ mutate: (raw) => {
        const arkPassive = raw.responses.arkPassive as { Effects: Array<{ Description: string }> };
        arkPassive.Effects = arkPassive.Effects.filter((effect) => !effect.Description.includes('질풍노도'));
      } }), 422, 'UNSUPPORTED_BUILD', null],
      [makeHarness({
        endpointStatus: { profiles: 404, equipment: 404, avatars: 404, combatSkills: 404, engravings: 404, cards: 404, gems: 404, arkPassive: 404, arkGrid: 404 },
        endpointDelay: { profiles: 8 }
      }), 404, 'CHARACTER_NOT_FOUND', null],
      [makeHarness({
        endpointStatus: { cards: 500, gems: 429 },
        endpointRetryAfter: { gems: '23' },
        endpointDelay: { gems: 8 }
      }), 429, 'UPSTREAM_RATE_LIMITED', '23'],
      [makeHarness({ endpointStatus: { cards: 500 } }), 503, 'UPSTREAM_UNAVAILABLE', null]
    ];
    for (const [harness, status, code, retryAfter] of cases) {
      const response = await harness.app.fetch(loadRequest());
      expect(response.status, code).toBe(status);
      expect((await response.json() as any).error.code, code).toBe(code);
      expect(response.headers.get('retry-after'), code).toBe(retryAfter);
      expect(harness.storage.snapshots.size, code).toBe(0);
    }
  });

  test('enforces required bounded client IDs, payload limits, miss limits, and force-refresh limits', async () => {
    // Break caught: callers can bypass anonymous abuse controls or spend upstream quota on oversized bodies.
    const missingHeader = loadRequest();
    missingHeader.headers.delete('x-anonymous-client-id');
    expect((await makeHarness().app.fetch(missingHeader)).status).toBe(400);

    expect((await makeHarness().app.fetch(loadRequest('봄날꽃씨', {}, 'x'))).status).toBe(400);

    const oversized = loadRequest('봄날꽃씨', { padding: 'x'.repeat(17_000) });
    expect((await makeHarness().app.fetch(oversized)).status).toBe(413);

    const missHarness = makeHarness();
    for (const name of ['첫번째이름', '두번째이름', '세번째이름']) {
      expect((await missHarness.app.fetch(loadRequest(name))).status).toBe(200);
    }
    const limited = await missHarness.app.fetch(loadRequest('네번째이름'));
    expect(limited.status).toBe(429);
    expect((await limited.json() as any).error.code).toBe('CACHE_MISS_RATE_LIMITED');
    expect(missHarness.calls).toHaveLength(27);

    const refreshHarness = makeHarness();
    expect((await refreshHarness.app.fetch(loadRequest())).status).toBe(200);
    expect((await refreshHarness.app.fetch(loadRequest('봄날꽃씨', { forceRefresh: true }))).status).toBe(200);
    const refreshLimited = await refreshHarness.app.fetch(loadRequest('봄날꽃씨', { forceRefresh: true }));
    expect(refreshLimited.status).toBe(429);
    expect((await refreshLimited.json() as any).error.code).toBe('FORCE_REFRESH_RATE_LIMITED');
    expect(refreshHarness.calls).toHaveLength(18);
  });

  test('propagates global upstream-budget retry information before making endpoint calls', async () => {
    // Break caught: all nine calls launch before the Durable Object budget grant.
    const harness = makeHarness({ budget: { grant: async () => ({ allowed: false, retryAfterSeconds: 41 }) } });
    const response = await harness.app.fetch(loadRequest());

    expect(response.status).toBe(429);
    expect(response.headers.get('retry-after')).toBe('41');
    expect((await response.json() as any).error.code).toBe('GLOBAL_UPSTREAM_RATE_LIMITED');
    expect(harness.calls).toHaveLength(0);
  });

  test('simulates a live snapshot and rejects expiry, version mismatch, and invalid patches', async () => {
    // Break caught: simulations trust client versions/IDs or calculate from expired snapshots.
    const harness = makeHarness();
    const loaded = await harness.app.fetch(loadRequest());
    const snapshotId = (await loaded.json() as any).data.snapshot.snapshotId as string;

    const simulated = await harness.app.fetch(simulationRequest(snapshotId));
    expect(simulated.status).toBe(200);
    expect((await simulated.json() as any).data).toMatchObject({ snapshotId, patches: [] });

    const reset = { schemaVersion: '1', kind: 'reset-section', sectionId: 'gems' };
    const resetSimulation = await harness.app.fetch(simulationRequest(snapshotId, { patches: [reset] }));
    expect(resetSimulation.status).toBe(200);
    expect((await resetSimulation.json() as any).data.patches).toEqual([reset]);

    const mismatch = await harness.app.fetch(simulationRequest(snapshotId, { catalogVersion: 'old-catalog' }));
    expect(mismatch.status).toBe(409);
    expect((await mismatch.json() as any).error.code).toBe('VERSION_MISMATCH');

    const scenarioMismatch = await harness.app.fetch(simulationRequest(snapshotId, {
      scenario: { schemaVersion: '2', id: 'best', bossConditionId: 'boss', directionalSuccessBySkill: {} }
    }));
    expect(scenarioMismatch.status).toBe(409);
    expect((await scenarioMismatch.json() as any).error.code).toBe('VERSION_MISMATCH');

    const invalidPatch = await harness.app.fetch(simulationRequest(snapshotId, {
      patches: [{ schemaVersion: '1', kind: 'set-skill-level', skillId: 'not-a-skill', level: 12 }]
    }));
    expect(invalidPatch.status).toBe(422);
    expect((await invalidPatch.json() as any).error.code).toBe('INVALID_PATCH');

    harness.advance(300_001);
    const expired = await harness.app.fetch(simulationRequest(snapshotId));
    expect(expired.status).toBe(410);
    expect((await expired.json() as any).error.code).toBe('SNAPSHOT_EXPIRED');
  });

  test('the global Durable Object grants at most 90 endpoint calls per minute', async () => {
    // Break caught: the budget counts character loads rather than their nine official endpoint calls.
    const values = new Map<string, unknown>();
    const transaction = {
      get: async <T>(key: string) => values.get(key) as T | undefined,
      put: async (key: string, value: unknown) => { values.set(key, value); }
    };
    const state = {
      storage: {
        transaction: async (callback: (storage: typeof transaction) => Promise<Response>) => callback(transaction)
      }
    } as unknown as DurableObjectState;
    const budget = new UpstreamBudget(state);
    let now = Date.UTC(2026, 7, 25, 10, 0, 0);
    vi.spyOn(Date, 'now').mockImplementation(() => now);
    const request = () => new Request('https://budget.internal/grant', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ endpointCalls: 9 })
    });

    for (let index = 0; index < 10; index += 1) {
      expect((await budget.fetch(request())).status, `grant ${index + 1}`).toBe(204);
    }
    const limited = await budget.fetch(request());
    expect(limited.status).toBe(429);
    expect(limited.headers.get('retry-after')).toBe('60');

    now += 60_000;
    expect((await budget.fetch(request())).status).toBe(204);
    vi.restoreAllMocks();
  });

  test('the Durable Object serializes anonymous-client window limits', async () => {
    // Break caught: eventually consistent KV increments allow concurrent abuse-limit bypasses.
    const values = new Map<string, unknown>();
    const transaction = {
      get: async <T>(key: string) => values.get(key) as T | undefined,
      put: async (key: string, value: unknown) => { values.set(key, value); }
    };
    const state = {
      storage: {
        transaction: async (callback: (storage: typeof transaction) => Promise<Response>) => callback(transaction)
      }
    } as unknown as DurableObjectState;
    const limiter = new UpstreamBudget(state);
    vi.spyOn(Date, 'now').mockReturnValue(Date.UTC(2026, 7, 25, 10, 0, 0));
    const request = () => new Request('https://budget.internal/consume', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ limit: 3, windowMs: 60_000 })
    });

    for (let index = 0; index < 3; index += 1) {
      expect((await limiter.fetch(request())).status).toBe(204);
    }
    const limited = await limiter.fetch(request());
    expect(limited.status).toBe(429);
    expect(limited.headers.get('retry-after')).toBe('60');
    vi.restoreAllMocks();
  });
});
