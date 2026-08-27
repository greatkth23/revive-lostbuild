import { cp, mkdir, rm, writeFile, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { calculateAllSkillDamage } from '@weather-artist/calculator';

const project = resolve(import.meta.dirname, '..');
const fixture = JSON.parse(await readFile(resolve(project, 'scripts/fixtures/weather-artist-e2e.json'), 'utf8'));
const dist = resolve(project, 'dist');
await rm(dist, { recursive: true, force: true });
await cp(resolve(project, 'apps/web/dist'), dist, { recursive: true });
await mkdir(resolve(dist, 'server'), { recursive: true });
await cp(resolve(project, 'scripts/sites-server.cjs'), resolve(dist, 'server/index.js'));
const data = {
  catalog: fixture.catalog,
  load: { snapshot: fixture.load.snapshot, baseline: calculateAllSkillDamage(fixture.load.snapshot), cacheHit: true }
};
await writeFile(resolve(dist, 'server/data.js'), `export const data = ${JSON.stringify(data)};`);
console.log(`Sites package prepared at ${dist}`);
