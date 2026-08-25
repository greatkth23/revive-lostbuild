# Task 1 report — Workspace, contracts, and catalog foundation

## Implementation

- Added an npm workspaces monorepo with a Vite React app (`apps/web`), a Cloudflare Worker (`apps/worker`), and contracts, catalog, and calculator packages (`packages/*`).
- Added shared strict TypeScript settings, Vitest, root `build`, `typecheck`, and `test` scripts, and package-level build/typecheck scripts.
- Defined runtime schemas and exported TypeScript contracts for decimal-string values, warnings, snapshots, discriminated build patches, scenarios, skill/hit results, catalog entries, editable sections, equipment-growth metadata, and success/failure API envelopes.
- Added the six stable Weather Artist skill IDs with Korean display names and per-hit motion data from `current-v2.7.2`.
- Applied the Space Cutting-only `1.292` hit-motion coefficient (the verified +29.2% correction) while preserving the original hit constants.
- Marked all six supported skills `NON_DIRECTIONAL`; their tags preserve the umbrella/hyper-awakening/enlightenment metadata available in the existing calculator.
- Exposed editable section descriptors and permanently locked equipment-growth editing with `NO_VERIFIED_DATASET` metadata. No equipment-growth values were invented.

## Files changed

- `.gitignore`
- `package.json`
- `package-lock.json`
- `tsconfig.base.json`
- `vitest.config.ts`
- `apps/web/{package.json,tsconfig.json,vite.config.ts,index.html,src/main.tsx}`
- `apps/worker/{package.json,tsconfig.json,wrangler.jsonc,src/index.ts}`
- `packages/contracts/{package.json,tsconfig.json,src/index.ts,src/contracts.test.ts}`
- `packages/catalog/{package.json,tsconfig.json,src/index.ts,src/catalog.test.ts}`
- `packages/calculator/{package.json,tsconfig.json,src/index.ts}`

## TDD RED/GREEN evidence

### RED: catalog behavior

Command:

```text
npm test -- packages/catalog/src/catalog.test.ts
```

Output (exit 1):

```text
FAIL  packages/catalog/src/catalog.test.ts [ packages/catalog/src/catalog.test.ts ]
Error: Cannot find module './index.js' imported from '.../packages/catalog/src/catalog.test.ts'
Caused by: Error: Failed to load url ./index.js ... Does the file exist?
Test Files  1 failed (1)
Tests  no tests
```

This failed because the catalog public module did not exist, which is the expected pre-implementation failure.

### RED: contract behavior

Command:

```text
npm test -- packages/contracts/src/contracts.test.ts
```

Output (exit 1):

```text
FAIL  packages/contracts/src/contracts.test.ts [ packages/contracts/src/contracts.test.ts ]
Error: Cannot find module './index.js' imported from '.../packages/contracts/src/contracts.test.ts'
Caused by: Error: Failed to load url ./index.js ... Does the file exist?
Test Files  1 failed (1)
Tests  no tests
```

This failed because the contracts public module did not exist, which is the expected pre-implementation failure.

### GREEN: focused behaviors

Command:

```text
npm test -- packages/catalog/src/catalog.test.ts packages/contracts/src/contracts.test.ts
```

Output (exit 0):

```text
✓ packages/catalog/src/catalog.test.ts (3 tests) 3ms
✓ packages/contracts/src/contracts.test.ts (2 tests) 6ms

Test Files  2 passed (2)
Tests  5 passed (5)
```

The five checks cover the six stable IDs, the `1.292` coefficient, `NON_DIRECTIONAL` tags, valid/malformed discriminated patches, and decimal-string snapshot boundaries.

## Verification commands and output

```text
npm run typecheck
```

Exit 0. Ran `tsc -p tsconfig.json --noEmit` successfully for `@weather-artist/web`, `@weather-artist/worker`, `@weather-artist/calculator`, `@weather-artist/catalog`, and `@weather-artist/contracts`.

```text
npm run build
```

Exit 0. Vite built the React app (26 modules); Wrangler completed the Worker dry-run upload (no bindings); calculator, catalog, and contracts completed `tsc -p tsconfig.json`.

```text
npm test
```

Output (exit 0):

```text
✓ packages/catalog/src/catalog.test.ts (3 tests) 4ms
✓ packages/contracts/src/contracts.test.ts (2 tests) 7ms

Test Files  2 passed (2)
Tests  5 passed (5)
```

## Self-review

- Confirmed package boundaries are explicit and imports use the contracts package name rather than a relative cross-package path.
- Confirmed all calculated values in public result/snapshot boundaries are `DecimalString`, never `number`.
- Confirmed `space-cutting` alone receives the `1.292` motion multiplier and its two source hit constants remain unchanged.
- Confirmed equipment growth has no editable patch operation and is explicitly represented as locked due to the missing verified dataset.
- Confirmed generated directories (`node_modules`, `dist`, `.wrangler`) are ignored; the existing Python calculator tree was not modified.
- No blocking concerns. Task 2 will need to expand `BuildSnapshot` with parser-normalized source data while retaining its exported decimal-string boundary fields.

## Review fix round 1 — versioned serialized contracts

### Implementation

- Made `schemaVersion: '1'` mandatory on every `BuildPatch` variant, so persisted patch arrays can be validated and migrated when their command schema changes.
- Added mandatory version fields to serialized warnings, hit/skill damage results, and both API envelope variants. `BuildSnapshot` now uses the same literal version contract, while `Scenario` is explicitly typed as version `'1'`.
- Added `skillDamageResultSchema`, `hitDamageResultSchema`, and generic `apiEnvelopeSchema(dataSchema)` validators for the externally serialized result/envelope forms.

### TDD RED

Command:

```text
npm test -- packages/contracts/src/contracts.test.ts
```

Output (exit 1):

```text
× build patch contract > requires a contract version on every persisted patch and serialized response type
→ expected { kind: 'set-skill-level', …(2) } to deeply equal { schemaVersion: '1', …(3) }

- Expected
+ Received

  {
    "kind": "set-skill-level",
    "level": 12,
-   "schemaVersion": "1",
    "skillId": "space-cutting",
  }

Test Files  1 failed (1)
Tests  1 failed | 2 passed (3)
```

The current schema silently stripped the supplied version, proving persisted patches could not retain a migration boundary.

### TDD GREEN

Command:

```text
npm test -- packages/contracts/src/contracts.test.ts
```

Output (exit 0):

```text
✓ packages/contracts/src/contracts.test.ts (3 tests) 13ms

Test Files  1 passed (1)
Tests  3 passed (3)
```

### Full verification

```text
npm run typecheck
```

Exit 0 for all five workspaces.

```text
npm run build
```

Exit 0: Vite built 26 modules, Wrangler completed a Worker dry run, and calculator/catalog/contracts completed TypeScript builds.

```text
npm test
```

Output (exit 0):

```text
✓ packages/catalog/src/catalog.test.ts (3 tests) 4ms
✓ packages/contracts/src/contracts.test.ts (3 tests) 7ms

Test Files  2 passed (2)
Tests  6 passed (6)
```

`git diff --check` also exited 0. The separately ledgered TypeScript configuration issue was not changed in this round.
