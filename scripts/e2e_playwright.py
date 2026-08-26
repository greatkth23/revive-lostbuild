import json
import os
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
fixture = json.loads((root / 'scripts/fixtures/weather-artist-e2e.json').read_text(encoding='utf8'))
base_url = os.environ.get('E2E_BASE_URL', 'http://127.0.0.1:5173')
baseline_text = '1,000,000,000.13'


def envelope(data):
    return {'schemaVersion': '1', 'ok': True, 'data': data, 'warnings': []}


def wait_for_request(requests, previous_count, label, page, timeout_ms=7000):
    deadline = time.monotonic() + timeout_ms / 1000
    while len(requests) <= previous_count and time.monotonic() < deadline:
        page.wait_for_timeout(25)
    if len(requests) <= previous_count:
        raise AssertionError(f'timed out waiting for {label}')
    return requests[-1]


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    try:
        viewports = {
            'desktop': {'width': 1440, 'height': 1000},
            'tablet': {'width': 900, 'height': 1000},
            'mobile': {'width': 390, 'height': 844},
        }
        for name, viewport in viewports.items():
            page = browser.new_page(viewport=viewport)
            errors = []
            loads = []
            simulations = []
            anonymous_client_ids = []
            page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
            page.on('pageerror', lambda error: errors.append(str(error)))

            def api(route):
                request = route.request
                if request.url.endswith('/catalog/weather-artist'):
                    assert request.method == 'GET'
                    route.fulfill(content_type='application/json', body=json.dumps(envelope(fixture['catalog'])))
                    return
                if request.url.endswith('/characters/load'):
                    assert request.method == 'POST'
                    headers = {key.lower(): value for key, value in request.headers.items()}
                    assert headers.get('content-type') == 'application/json', headers
                    anonymous_client_id = headers.get('x-anonymous-client-id', '')
                    assert re.fullmatch(r'[A-Za-z0-9_-]{8,128}', anonymous_client_id), headers
                    if anonymous_client_ids:
                        assert anonymous_client_id == anonymous_client_ids[0]
                    else:
                        anonymous_client_ids.append(anonymous_client_id)
                    body = json.loads(request.post_data or '{}')
                    assert set(body) == {'characterName', 'forceRefresh'}
                    assert body['characterName'] == '봄날꽃씨'
                    assert isinstance(body['forceRefresh'], bool)
                    loads.append(body)
                    route.fulfill(content_type='application/json', body=json.dumps(envelope(fixture['load'])))
                    return
                if request.url.endswith('/simulations'):
                    simulations.append(json.loads(request.post_data or '{}'))
                    route.fulfill(status=500, content_type='application/json', body='{}')
                    return
                raise AssertionError(f'unexpected API route or method: {request.method} {request.url}')

            try:
                page.route('**/api/v1/**', api)
                page.goto(base_url, wait_until='networkidle')
                page.evaluate('localStorage.clear()')

                load_before = len(loads)
                page.get_by_label('캐릭터 이름').fill('봄날꽃씨')
                page.get_by_role('button', name='불러오기').click()
                first_load = wait_for_request(loads, load_before, 'initial character load', page)
                assert first_load == {'characterName': '봄날꽃씨', 'forceRefresh': False}
                page.get_by_role('heading', name='봄날꽃씨').wait_for()

                page.get_by_text('카제로스', exact=True).first.wait_for()
                page.get_by_text('기부천사', exact=True).first.wait_for()
                page.get_by_text('1,785.83', exact=True).first.wait_for()
                page.get_by_text(re.compile(r'길드 꽃가게')).wait_for()
                for heading in [
                    '전투 특성', '각인', '카드·보조 장비', '데이터 상태', '보석', '장비',
                    '액세서리', '아크패시브', '아크그리드', '아바타·펫', '스킬·트라이포드',
                ]:
                    page.get_by_role('heading', name=heading, exact=True).wait_for()
                assert page.get_by_role('tab', name='현재 세팅').get_attribute('aria-selected') == 'true'
                assert page.get_by_role('tab', name='세팅 조정').count() == 0
                assert page.get_by_role('checkbox').count() == 0
                assert len(simulations) == 0

                damage_tab = page.get_by_role('tab', name='스킬 피해')
                damage_tab.click()
                page.get_by_text(baseline_text, exact=True).first.wait_for()
                assert page.get_by_text('기대 피해 차이').count() == 0
                assert page.get_by_text('기준 비치명').count() == 0
                page.get_by_role('button', name='우레바람 상세').click()
                detail = page.get_by_role('region', name='우레바람 상세 결과')
                detail.wait_for()
                for heading in [
                    '타격별 피해', '계산 공격력', '치명타율', '치명타 피해 배율',
                    '트라이포드', '일반 보석·방향성', '아크패시브·아크그리드', '계산 근거',
                ]:
                    detail.get_by_text(heading, exact=True).wait_for()
                for column in ['타격', '비치명', '치명타', '기대']:
                    detail.get_by_role('columnheader', name=column, exact=True).wait_for()

                damage_tab.press('Home')
                setup_tab = page.get_by_role('tab', name='현재 세팅')
                assert setup_tab.get_attribute('aria-selected') == 'true'
                setup_tab.press('End')
                assert damage_tab.get_attribute('aria-selected') == 'true'

                load_before = len(loads)
                page.get_by_role('button', name='API 새로고침').click()
                refreshed = wait_for_request(loads, load_before, 'force refresh load', page)
                assert refreshed == {'characterName': '봄날꽃씨', 'forceRefresh': True}
                page.get_by_role('heading', name='봄날꽃씨').wait_for()
                page.wait_for_timeout(350)
                assert len(simulations) == 0
                assert page.locator('.eyebrow').count() == 0
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                assert not errors, errors
                print(f'{name}: read-only setup and damage tabs passed')
            finally:
                page.close()
    finally:
        browser.close()
