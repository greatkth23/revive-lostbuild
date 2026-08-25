# Weather Artist Web Simulator Implementation Plan

**Spec:** `docs/superpowers/specs/2026-08-25-weather-artist-web-simulator-design.md`

**Global constraints:** Work test-first. Preserve Python calculator behavior and unrelated user files. Use `current-v2.7.2`, decimal strings at boundaries, calculated attack power, six supported skills only, no cooldown/DPS, and no unverified equipment growth values. Never expose or persist the Lost Ark token.

### Task 1: Workspace, contracts, and catalog foundation

Create the npm workspace, Vite React app, TypeScript Worker package, calculator package, contracts package, and catalog package. Add Vitest and shared strict TypeScript configuration. Define versioned `BuildSnapshot`, `BuildPatch`, `Scenario`, result, warning, catalog, and API envelope types. Add the six-skill catalog with tags, hit motion data, the 29.2% space-cutting coefficient correction, editable section descriptors, and locked equipment-growth metadata. Add failing tests first for catalog identities, corrected coefficient, direction tags, patch schema validation, and decimal-string contracts; then implement until they pass. Add basic build/typecheck/test scripts and commit.

### Task 2: TypeScript parser and damage-calculator parity

Port the Weather Artist parser and calculation domain needed by the six skills from `api-chatgpt-conversation-6a6309ab-7de4-8342/work/lostark_damage_test.py`. Keep precision 40 and explicit rounding. Parse the nine endpoint payloads into `BuildSnapshot`, including equipment/armlet, accessories/bracelet, avatars/pet, engravings/stone, cards, regular gems, Ark Passive, combat-skill tripods, and Ark Grid cores/gems/effects. Implement deduplication and provenance warnings. Implement calculated attack power and one-cast non-critical, critical, expected, and per-hit results. Write failing regression tests before each behavior, using saved `봄날꽃씨` raw fixtures and hand-fixed expectations generated from the existing Python engine. Cover karma weapon attack, Ark Grid gem/effect dedupe, relic/ancient slash selection, 18–20P repeated multiplication, tripod embedded-effect dedupe, regular skill gems, umbrella scope, and directional rules. Commit only after TypeScript results match the Python golden outputs at named checkpoints.

### Task 3: Worker API, snapshots, cache, and abuse protection

Implement the three `/api/v1` endpoints with dependency-injected Lost Ark fetch and storage boundaries. Fetch all nine endpoints concurrently, validate Weather Artist and supported build status, normalize into a snapshot, calculate the baseline, and store opaque snapshots in KV for 300 seconds. Implement an in-flight same-character request coalescer, an anonymous-client cache-miss limiter of 3/minute, force-refresh limiter of 1/60 seconds, and a Durable Object global upstream budget of 90 endpoint calls/minute. Keep Turnstile behind a disabled flag. Validate patches against the catalog before simulation. Add failing route and service tests first for success, unsupported class, missing character, 429, 503, partial failure, expired snapshot, version mismatch, invalid patch, cache hit, and rate-limit behavior. Configure Worker static assets, bindings, secrets documentation, security headers, payload limits, and privacy-safe structured logs. Commit.

### Task 4: Responsive React editor and comparison results

Build the two-tab Korean UI from the approved reference direction without copying proprietary layout/assets. Implement character search, refresh, API baseline summary, section cards, catalog-constrained controls, section/all reset, 250ms debounced simulations, localStorage patch versioning/rebase, warning states, and API-vs-edited comparison. Show six skills with non-critical, critical, expected, crit rate, crit multiplier, delta, per-hit expansion, effect/provenance breakdown, and per-skill directional success controls. Format display values to two decimals only. Use API image URLs with fallbacks. Add failing component tests first for search/load, edits, constraint errors, resets, debounce, local restoration/rebase, result expansion, and error recovery. Add responsive accessible styling for desktop/tablet/mobile and commit.

### Task 5: Integration, deployment, and release verification

Add mocked full-flow integration tests and Playwright desktop/tablet/mobile tests for load → edit → compare → reset → reload. Add checks that secrets never enter client bundles, responses, or logs. Add GitHub Actions for typecheck/test/build and a manually dispatched production Worker deployment with separate preview/production bindings. Document local setup, `wrangler secret put LOSTARK_API_TOKEN`, KV/Durable Object provisioning, Cloudflare/GitHub secrets, smoke testing, noncommercial API notice, data provenance, and the locked equipment-growth workflow. Run the complete Python and npm suites, production build, and local Worker smoke tests. Commit.

### Task 6: Final review and handoff

Generate a whole-branch review package, run the required independent code review, fix all Critical and Important findings, and perform one scoped re-review. Re-run every verification command fresh. Record any remaining external deployment prerequisites without claiming production deployment if credentials are absent. Use the finishing-development-branch procedure and present the branch outcome.
