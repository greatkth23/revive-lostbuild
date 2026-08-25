# Worker API setup

The Worker serves the static web build and the three fixed API routes:

- `POST /api/v1/characters/load`
- `GET /api/v1/catalog/weather-artist`
- `POST /api/v1/simulations`

Every POST request must include `Content-Type: application/json` and an
`X-Anonymous-Client-Id` containing 8–128 URL-safe characters. Request bodies
are limited to 16 KiB.

Create the production KV namespace and place its ID in the deployment-specific
Wrangler configuration (or CI-generated config). The checked-in binding omits
an account-specific ID so local Wrangler uses its local persistence. The
`UPSTREAM_BUDGET` Durable Object and its initial SQLite migration are declared
in `wrangler.jsonc`.

Store credentials only as Worker secrets:

```powershell
npx wrangler secret put LOSTARK_API_TOKEN
```

Do not add the token to `vars`, `.dev.vars`, source files, logs, responses, or
static assets. For local development, an untracked `.dev.vars` may contain
`LOSTARK_API_TOKEN=...`.

Turnstile is off by default. To enable it, set `TURNSTILE_ENABLED` to `true`
and add the secret separately:

```powershell
npx wrangler secret put TURNSTILE_SECRET
```

Build the web assets before a Worker-only dry run:

```powershell
npm run build -w @weather-artist/web
npm run build -w @weather-artist/worker
```

The Worker logs only request ID, route, status, duration, cache status, and
schema/calculator/parser/catalog versions. Character names, request settings,
tooltips, and credentials are deliberately excluded.
