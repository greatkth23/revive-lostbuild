#!/usr/bin/env python3
"""Mocked browser flow; starts only after with_server.py has made both services ready."""
import os
import sys

try:
    from playwright.sync_api import sync_playwright
except ModuleNotFoundError:
    print("Playwright is required; install with: python -m pip install -r requirements-e2e.txt")
    raise SystemExit(1)

VIEWPORTS = {"desktop": {"width": 1440, "height": 1000}, "tablet": {"width": 900, "height": 1000}, "mobile": {"width": 390, "height": 844}}
BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:5173")

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    try:
        for name, viewport in VIEWPORTS.items():
            page = browser.new_page(viewport=viewport)
            page.goto(BASE_URL, wait_until="networkidle")
            page.get_by_label("캐릭터 이름").fill("봄날꽃씨")
            page.get_by_role("button", name="불러오기").click()
            page.wait_for_load_state("networkidle")
            page.get_by_role("checkbox", name="보석 사용").uncheck()
            page.wait_for_timeout(300)
            page.get_by_role("tab", name="스킬 피해 결과").click()
            page.get_by_role("article").first.wait_for()
            page.get_by_role("tab", name="세팅 조정").click()
            page.get_by_role("button", name="보석 초기화").click()
            page.get_by_role("button", name="전체 초기화").click()
            page.get_by_role("button", name="새로고침").click()
            page.wait_for_load_state("networkidle")
            page.reload(wait_until="networkidle")
            assert page.get_by_role("checkbox", name="보석 사용").is_checked(), name
            page.close()
            print(f"{name}: mocked full flow passed")
    finally:
        browser.close()
