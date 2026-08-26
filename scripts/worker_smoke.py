#!/usr/bin/env python3
"""Local Worker smoke: static SPA, catalog envelope/security headers, and safe unconfigured behavior."""
import json
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1] / "apps" / "worker"
BASE = "http://127.0.0.1:8787"
npx = "npx.cmd" if sys.platform == "win32" else "npx"
process = subprocess.Popen([npx, "wrangler", "dev", "--local", "--port", "8787"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try:
            with urlopen(f"{BASE}/api/v1/catalog/weather-artist", timeout=1) as response:
                catalog = json.load(response)
                assert catalog["ok"] is True
                assert response.headers["content-security-policy"]
                assert response.headers["x-content-type-options"] == "nosniff"
            with urlopen(f"{BASE}/", timeout=1) as response:
                assert b"id=\"root\"" in response.read().lower()
            break
        except Exception:
            time.sleep(0.2)
    else:
        raise AssertionError("wrangler dev did not become ready")
    request = Request(f"{BASE}/api/v1/characters/load", data=b'{', method="POST", headers={"content-type": "application/json", "x-anonymous-client-id": "smoke-client-0001"})
    try:
        urlopen(request, timeout=3)
    except HTTPError as error:
        body = error.read().decode("utf-8")
        assert "LOSTARK_API_TOKEN_SENTINEL_NEVER_SHIP" not in body
        assert error.code in (400, 503)
    print("worker smoke passed")
finally:
    process.terminate()
    process.wait(timeout=10)
