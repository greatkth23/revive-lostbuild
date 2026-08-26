import { createReadStream, existsSync, readFileSync, statSync } from 'node:fs';
import { createServer, type IncomingMessage, type Server, type ServerResponse } from 'node:http';
import { extname, join, resolve, sep } from 'node:path';
import { calculateAllSkillDamage } from '@weather-artist/calculator';
import { buildPatchSchema, type BuildPatch, type BuildSnapshot, type Scenario, type SkillDamageResult } from '@weather-artist/contracts';
import { applyBuildPatches } from '../apps/worker/src/patches.js';

interface LocalPreviewFixture {
  catalog: unknown;
  load: {
    snapshot: BuildSnapshot;
  };
}

interface LocalLoadData {
  snapshot: BuildSnapshot;
  baseline: SkillDamageResult[];
  cacheHit: boolean;
}

interface LocalSimulationData {
  schemaVersion: '1';
  snapshotId: string;
  patches: BuildPatch[];
  baseline: SkillDamageResult[];
  candidate: SkillDamageResult[];
}

export function buildLocalLoadData(fixture: LocalPreviewFixture): LocalLoadData {
  return {
    snapshot: fixture.load.snapshot,
    baseline: calculateAllSkillDamage(fixture.load.snapshot),
    cacheHit: true
  };
}

export function buildLocalSimulationData(
  fixture: LocalPreviewFixture,
  patches: readonly BuildPatch[],
  scenario: Scenario
): LocalSimulationData {
  const options = { directionalSuccessBySkill: scenario.directionalSuccessBySkill };
  return {
    schemaVersion: '1',
    snapshotId: fixture.load.snapshot.snapshotId,
    patches: [...patches],
    baseline: calculateAllSkillDamage(fixture.load.snapshot, options),
    candidate: calculateAllSkillDamage(applyBuildPatches(fixture.load.snapshot, [...patches]), options)
  };
}

interface LocalPreviewServerOptions {
  fixture: LocalPreviewFixture;
  staticRoot: string;
}

const contentTypes: Record<string, string> = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.js': 'text/javascript; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml'
};

function writeJson(response: ServerResponse, data: unknown, status = 200): void {
  response.writeHead(status, {
    'cache-control': 'no-store',
    'content-type': 'application/json; charset=utf-8'
  });
  response.end(JSON.stringify(data));
}

function success(data: unknown): unknown {
  return { schemaVersion: '1', ok: true, data, warnings: [] };
}

async function readJson(request: IncomingMessage): Promise<Record<string, unknown>> {
  let body = '';
  for await (const chunk of request) {
    body += String(chunk);
    if (body.length > 1024 * 1024) throw new Error('request body is too large');
  }
  const parsed = JSON.parse(body || '{}');
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('request body must be an object');
  return parsed as Record<string, unknown>;
}

function serveStatic(response: ServerResponse, staticRoot: string, pathname: string): void {
  const root = resolve(staticRoot);
  const requested = decodeURIComponent(pathname === '/' ? '/index.html' : pathname);
  let file = resolve(root, `.${requested}`);
  const insideRoot = file === root || file.startsWith(`${root}${sep}`);
  if (!insideRoot || !existsSync(file) || statSync(file).isDirectory()) file = join(root, 'index.html');
  response.writeHead(200, {
    'cache-control': 'no-store',
    'content-type': contentTypes[extname(file)] ?? 'application/octet-stream'
  });
  createReadStream(file).pipe(response);
}

export function createLocalPreviewServer({ fixture, staticRoot }: LocalPreviewServerOptions): Server {
  return createServer(async (request, response) => {
    try {
      const url = new URL(request.url ?? '/', 'http://127.0.0.1');
      if (request.method === 'GET' && url.pathname === '/api/v1/catalog/weather-artist') {
        writeJson(response, success(fixture.catalog));
        return;
      }
      if (request.method === 'POST' && url.pathname === '/api/v1/characters/load') {
        await readJson(request);
        writeJson(response, success(buildLocalLoadData(fixture)));
        return;
      }
      if (request.method === 'POST' && url.pathname === '/api/v1/simulations') {
        const body = await readJson(request);
        const patches = buildPatchSchema.array().parse(body.patches ?? []);
        const scenario = body.scenario as Scenario | undefined;
        if (!scenario || scenario.schemaVersion !== '1' || typeof scenario.directionalSuccessBySkill !== 'object') {
          throw new Error('invalid scenario');
        }
        writeJson(response, success(buildLocalSimulationData(fixture, patches, scenario)));
        return;
      }
      if (request.method === 'GET') {
        serveStatic(response, staticRoot, url.pathname);
        return;
      }
      writeJson(response, { schemaVersion: '1', ok: false, error: { code: 'NOT_FOUND', message: 'Not found', requestId: 'local-preview' } }, 404);
    } catch (error) {
      writeJson(response, {
        schemaVersion: '1',
        ok: false,
        error: { code: 'LOCAL_PREVIEW_ERROR', message: error instanceof Error ? error.message : String(error), requestId: 'local-preview' }
      }, 400);
    }
  });
}

export function shouldStartLocalPreview(environment: Record<string, string | undefined>): boolean {
  return !environment.VITEST;
}

if (shouldStartLocalPreview(process.env)) {
  const fixture = JSON.parse(readFileSync(resolve('scripts/fixtures/weather-artist-e2e.json'), 'utf8')) as LocalPreviewFixture;
  const port = Number(process.env.LOCAL_PREVIEW_PORT ?? '8787');
  createLocalPreviewServer({ fixture, staticRoot: resolve('apps/web/dist') })
    .listen(port, '127.0.0.1', () => console.log(`Local simulator preview ready: http://127.0.0.1:${port}/`));
}
