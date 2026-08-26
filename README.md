# revive-lostbuild

- [Damage calculator guide](api-chatgpt-conversation-6a6309ab-7de4-8342/work/DAMAGE_CALCULATOR_README.md)
- Weather Artist calculator: `lostark_damage_test.py` (official rule v2.7.2)
- Arcana adapter: `arcana_damage.py` (v2.8.1; component-specific head/back attack rules)

## Weather Artist local setup and release checks

Install Node 22+ and Python 3.12+, then run `npm ci`, `npm test`, `npm run typecheck`, and `npm run build`. The Python regression suite is intentionally standard-library based: `python -m unittest discover -s api-chatgpt-conversation-6a6309ab-7de4-8342/work -p 'test_*.py'`.

For local Worker development, create an untracked `apps/worker/.dev.vars` with `LOSTARK_API_TOKEN=...` (and optionally `TURNSTILE_SECRET=...`); never put either value in `wrangler.jsonc`, Vite variables, a fixture, a log, or a commit. Run `npm run smoke:worker` to start a local Worker and verify the SPA shell, catalog/security headers, and safe unconfigured-character response. Account IDs, namespace IDs, and API tokens are deliberately not fabricated in this repository.

The manual GitHub Actions deployment uses separate `preview` and `production` environments. Each environment must provide its own `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, and `LOSTARK_API_TOKEN` secrets plus a distinct `KV_NAMESPACE_ID` variable. The selected target renders an untracked `apps/worker/wrangler.<target>.json` with a distinct Worker name, KV binding, and therefore a distinct Durable Object namespace. The workflow writes the Lost Ark token to a mode-0600 temporary JSON file and performs exactly one `wrangler deploy --secrets-file` operation; both temporary files are removed on exit. Invoke the workflow manually only after the target environment secrets, namespace, migration, build, and smoke checks are ready.

Browser release coverage is `scripts/e2e_playwright.py`. Install it with `pip install -r requirements-e2e.txt` and `python -m playwright install chromium`. Start Vite in one terminal with `npm run dev --workspace @weather-artist/web -- --host 127.0.0.1 --port 5173 --strictPort`, then run `python scripts/e2e_playwright.py` in another. The script intercepts all simulator API routes itself with versioned fixtures, so no mock API server or Lost Ark token is needed. It uses native Python Playwright, headless Chromium, accessible roles/labels, and exercises desktop/tablet/mobile load → edit → result → section/all reset → refresh/reload. Missing Playwright, Chromium, Vite, or a failed browser assertion exits nonzero.

This is a noncommercial tool using the Lost Ark Open API. Operators must comply with the current [Lost Ark Open API terms](https://developer-lostark.game.onstove.com/), including applicable attribution, rate, and use restrictions. API data is parsed into a short-lived normalized snapshot with parser/calculator/catalog versions, warnings, and provenance. Official icon URLs are rendered directly; assets are not copied. Equipment-growth controls remain locked until a versioned, attributable, complete verified dataset is added to the catalog and parser with regression coverage—unknown values must not be guessed.
