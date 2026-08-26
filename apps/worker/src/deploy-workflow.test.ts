import { readFileSync } from 'node:fs';
import { parse } from 'yaml';
import { describe, expect, test } from 'vitest';

const workflow = parse(readFileSync(new URL('../../../.github/workflows/deploy.yml', import.meta.url), 'utf8')) as {
  jobs: Record<string, { needs?: string | string[]; steps?: Array<{ name?: string; if?: string; run?: string }> }>;
};

describe('manual deployment gate', () => {
  test('runs the complete release verification before deployment', () => {
    // Break caught: workflow_dispatch bypasses goldens, Python parity, smoke, secret scan, or real Chromium E2E.
    const verify = workflow.jobs.verify;
    expect(verify).toBeTruthy();
    if (!verify) throw new Error('verify job is required');
    const commands = (verify.steps ?? []).map((step) => step.run ?? '').join('\n');
    for (const required of [
      'npm run types:check', 'npm run typecheck', 'npm test',
      'python -m unittest discover', 'npm run build', 'npm run secret:scan',
      'npm run smoke:worker', 'python scripts/e2e_playwright.py'
    ]) expect(commands).toContain(required);
    expect([workflow.jobs.deploy?.needs].flat()).toContain('verify');
  });

  test('hard-fails a production target outside the main branch while allowing preview verification', () => {
    // Break caught: a manually selected production environment deploys an arbitrary feature ref.
    const gate = (workflow.jobs.verify?.steps ?? []).find((step) => step.name === 'Reject production deployment outside main');
    expect(gate?.if).toContain("inputs.target == 'production'");
    expect(gate?.if).toContain("github.ref != 'refs/heads/main'");
    expect(gate?.run).toMatch(/exit\s+1/);
  });
});
