# revive-lostbuild

- [Damage calculator guide](api-chatgpt-conversation-6a6309ab-7de4-8342/work/DAMAGE_CALCULATOR_README.md)
- Weather Artist calculator: `lostark_damage_test.py` (official rule v2.7.2)
- Arcana adapter: `arcana_damage.py` (v2.8.1; component-specific head/back attack rules)

## Weather Artist local setup and release checks

Install Node 22+ and Python 3.12+, then run `npm ci`, `npm test`, `npm run typecheck`, and `npm run build`. The Python regression suite is intentionally standard-library based: `python -m unittest discover -s api-chatgpt-conversation-6a6309ab-7de4-8342/work -p 'test_*.py'`.

For local Worker development, create an untracked `apps/worker/.dev.vars` with `LOSTARK_API_TOKEN=...` (and optionally `TURNSTILE_SECRET=...`); never put either value in `wrangler.jsonc`, Vite variables, a fixture, a log, or a commit. For a deployed environment run `cd apps/worker && npx wrangler secret put LOSTARK_API_TOKEN --env <target>`. Create a separate KV namespace for preview and production, configure a distinct Worker name and Durable Object namespace for each target, and run the configured migration before deployment. Account IDs, namespace IDs, and API tokens are deliberately not fabricated in this repository.

The release workflow uses separate GitHub `preview` and `production` environments. Each environment must provide `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, and `LOSTARK_API_TOKEN` as secrets, plus its own `KV_NAMESPACE_ID` variable. The manual workflow chooses the target; it does not auto-deploy. Before authorizing it, build the worker and smoke-test `wrangler dev`: verify `/` serves the SPA, `/api/v1/catalog/weather-artist` has the security headers, and an unconfigured `/api/v1/characters/load` returns the structured configured-state error without a token.

Browser release coverage is `scripts/e2e_playwright.py`. It uses native Python Playwright, headless Chromium, accessible roles/labels, `networkidle`, and exercises desktop/tablet/mobile load → edit → result → section/all reset → refresh/reload. Run it through the provided `with_server.py` helper once a mocked API server and Vite server are supplied; install the browser with `python -m playwright install chromium`. It exits successfully with an explicit skip when Playwright is absent, so standard Python unittest discovery remains dependency-free.

This is a noncommercial tool using the Lost Ark Open API. Operators must comply with the current [Lost Ark Open API terms](https://developer-lostark.game.onstove.com/), including applicable attribution, rate, and use restrictions. API data is parsed into a short-lived normalized snapshot with parser/calculator/catalog versions, warnings, and provenance. Official icon URLs are rendered directly; assets are not copied. Equipment-growth controls remain locked until a versioned, attributable, complete verified dataset is added to the catalog and parser with regression coverage—unknown values must not be guessed.
