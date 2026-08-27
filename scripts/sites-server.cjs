import { data } from './data.js';

function envelope(value) {
  return { schemaVersion: '1', ok: true, data: value, warnings: [] };
}

async function readBody(request) {
  try { return await request.json(); } catch { throw new Error('invalid JSON'); }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === 'GET' && url.pathname === '/api/v1/catalog/weather-artist') {
      return Response.json(envelope(data.catalog), { headers: { 'cache-control': 'no-store' } });
    }
    if (request.method === 'POST' && url.pathname === '/api/v1/characters/load') {
      await readBody(request);
      return Response.json(envelope(data.load), { headers: { 'cache-control': 'no-store' } });
    }
    if (request.method === 'POST' && url.pathname === '/api/v1/simulations') {
      const body = await readBody(request);
      return Response.json(envelope({
        schemaVersion: '1',
        snapshotId: data.load.snapshot.snapshotId,
        patches: Array.isArray(body.patches) ? body.patches : [],
        baseline: data.load.baseline,
        candidate: data.load.baseline
      }), { headers: { 'cache-control': 'no-store' } });
    }
    if (request.method === 'GET' && env?.ASSETS?.fetch) return env.ASSETS.fetch(request);
    return new Response('Not found', { status: 404 });
  }
};
