import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { URL } from 'node:url';

const cwd = process.cwd();
const root = fs.existsSync(path.join(cwd, 'server', 'data.json')) ? cwd : path.join(cwd, 'dist');
const here = path.join(root, 'server');
const staticRoot = root;
const data = JSON.parse(fs.readFileSync(path.join(here, 'data.json'), 'utf8'));
const contentTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

function envelope(value) {
  return JSON.stringify({ schemaVersion: '1', ok: true, data: value, warnings: [] });
}

function sendJson(response, value, status = 200) {
  const body = typeof value === 'string' ? value : JSON.stringify(value);
  response.writeHead(status, { 'cache-control': 'no-store', 'content-type': 'application/json; charset=utf-8' });
  response.end(body);
}

function serveStatic(response, pathname) {
  let requested;
  try { requested = decodeURIComponent(pathname === '/' ? '/index.html' : pathname); } catch { requested = '/index.html'; }
  let file = path.resolve(staticRoot, `.${requested}`);
  if (file !== staticRoot && !file.startsWith(`${staticRoot}${path.sep}`)) file = path.join(staticRoot, 'index.html');
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(staticRoot, 'index.html');
  response.writeHead(200, { 'cache-control': 'no-store', 'content-type': contentTypes[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(response);
}

function readBody(request) {
  return new Promise((resolve, reject) => {
    let body = '';
    request.on('data', (chunk) => { body += chunk; if (body.length > 1024 * 1024) reject(new Error('request body is too large')); });
    request.on('end', () => { try { resolve(JSON.parse(body || '{}')); } catch { reject(new Error('invalid JSON')); } });
    request.on('error', reject);
  });
}

const server = http.createServer(async (request, response) => {
  try {
    const url = new URL(request.url || '/', 'http://localhost');
    if (request.method === 'GET' && url.pathname === '/api/v1/catalog/weather-artist') return sendJson(response, envelope(data.catalog));
    if (request.method === 'POST' && url.pathname === '/api/v1/characters/load') { await readBody(request); return sendJson(response, envelope(data.load)); }
    if (request.method === 'POST' && url.pathname === '/api/v1/simulations') {
      const body = await readBody(request);
      return sendJson(response, envelope({ schemaVersion: '1', snapshotId: data.load.snapshot.snapshotId, patches: Array.isArray(body.patches) ? body.patches : [], baseline: data.load.baseline, candidate: data.load.baseline }));
    }
    if (request.method === 'GET') return serveStatic(response, url.pathname);
    return sendJson(response, { schemaVersion: '1', ok: false, error: { code: 'NOT_FOUND', message: 'Not found', requestId: 'sites-static' } }, 404);
  } catch (error) {
    return sendJson(response, { schemaVersion: '1', ok: false, error: { code: 'SITES_STATIC_ERROR', message: error instanceof Error ? error.message : String(error), requestId: 'sites-static' } }, 400);
  }
});

const port = Number(process.env.PORT || 8787);
server.listen(port, '0.0.0.0', () => console.log(`Sites server listening on ${port}`));
