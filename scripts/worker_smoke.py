#!/usr/bin/env python3
"""Local Worker smoke: static SPA, catalog envelope/security headers, and safe unconfigured behavior."""
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1] / "apps" / "worker"
with socket.socket() as probe:
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
BASE = f"http://127.0.0.1:{port}"
npx = "npx.cmd" if sys.platform == "win32" else "npx"
worker_env = os.environ.copy()
worker_env.pop("LOSTARK_API_TOKEN", None)
with tempfile.NamedTemporaryFile(prefix="weather-worker-empty-", suffix=".env", delete=False) as empty_env:
    empty_env_path = empty_env.name
popen_options = (
    {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    if sys.platform == "win32"
    else {"start_new_session": True}
)
process = None
try:
    process = subprocess.Popen(
        [npx, "wrangler", "dev", "--local", "--port", str(port), "--env-file", empty_env_path],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=worker_env,
        **popen_options,
    )
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
    request = Request(
        f"{BASE}/api/v1/characters/load",
        data=json.dumps({"characterName": "봄날꽃씨"}).encode("utf-8"),
        method="POST",
        headers={"content-type": "application/json", "x-anonymous-client-id": "smoke-client-0001"},
    )
    try:
        with urlopen(request, timeout=3) as response:
            raise AssertionError(f"unconfigured load unexpectedly returned {response.status}")
    except HTTPError as error:
        assert error.code == 503, error.code
        body = json.loads(error.read().decode("utf-8"))
        assert body["schemaVersion"] == "1"
        assert body["ok"] is False
        assert body["error"]["code"] == "WORKER_NOT_CONFIGURED"
        assert error.headers["content-security-policy"]
        assert error.headers["x-content-type-options"] == "nosniff"
        assert "LOSTARK_API_TOKEN_SENTINEL_NEVER_SHIP" not in json.dumps(body)
    print("worker smoke passed")
finally:
    if process is not None and process.poll() is None:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if sys.platform == "win32":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
    if os.path.exists(empty_env_path):
        os.unlink(empty_env_path)
