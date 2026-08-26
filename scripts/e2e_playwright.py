import json
import os
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
fixture = json.loads((root / 'scripts/fixtures/weather-artist-e2e.json').read_text(encoding='utf8'))
base_url = os.environ.get('E2E_BASE_URL', 'http://127.0.0.1:5173')
snapshot = fixture['load']['snapshot']
snapshot_id = snapshot['snapshotId']
skill_ids = [skill['id'] for skill in fixture['catalog']['skills']]
editable_sections = [section for section in fixture['catalog']['editableSections'] if section['editable']]
baseline_text = '1,000,000,000.13'
candidate_text = '800,000,000.13'


def envelope(data):
    return {'schemaVersion': '1', 'ok': True, 'data': data, 'warnings': []}


def wait_for_request(page, requests, previous_count, label, timeout_ms=7000):
    deadline = time.monotonic() + timeout_ms / 1000
    while len(requests) <= previous_count and time.monotonic() < deadline:
        page.wait_for_timeout(25)
    if len(requests) <= previous_count:
        raise AssertionError(f'timed out waiting for {label}')
    return requests[-1]


def assert_simulation_contract(body):
    expected_keys = {
        'schemaVersion', 'snapshotId', 'calculatorVersion', 'parserVersion',
        'catalogVersion', 'patches', 'scenario',
    }
    assert set(body) == expected_keys, body
    assert body['schemaVersion'] == '1'
    assert body['snapshotId'] == snapshot_id
    assert body['calculatorVersion'] == snapshot['calculatorVersion']
    assert body['parserVersion'] == snapshot['parserVersion']
    assert body['catalogVersion'] == snapshot['catalogVersion']
    assert isinstance(body['patches'], list)
    for patch in body['patches']:
        assert patch.get('schemaVersion') == '1'
        assert patch.get('sectionId') in {section['id'] for section in editable_sections}
        assert patch.get('kind') in {'set-section-enabled', 'reset-section'}
        if patch['kind'] == 'set-section-enabled':
            assert isinstance(patch.get('enabled'), bool)
            assert set(patch) == {'schemaVersion', 'kind', 'sectionId', 'enabled'}
        else:
            assert set(patch) == {'schemaVersion', 'kind', 'sectionId'}
    scenario = body['scenario']
    assert set(scenario) == {'schemaVersion', 'id', 'bossConditionId', 'directionalSuccessBySkill'}
    assert scenario['schemaVersion'] == '1'
    assert scenario['id'] == 'default'
    assert scenario['bossConditionId'] == 'default'
    assert scenario['directionalSuccessBySkill'] == {skill_id: False for skill_id in skill_ids}


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

            def assert_post_headers(request):
                headers = {key.lower(): value for key, value in request.headers.items()}
                assert headers.get('content-type') == 'application/json', headers
                anonymous_client_id = headers.get('x-anonymous-client-id', '')
                assert re.fullmatch(r'[A-Za-z0-9_-]{8,128}', anonymous_client_id), headers
                if anonymous_client_ids:
                    assert anonymous_client_id == anonymous_client_ids[0], (
                        'anonymous client ID changed during one browser flow'
                    )
                else:
                    anonymous_client_ids.append(anonymous_client_id)

            def api(route):
                request = route.request
                if request.url.endswith('/catalog/weather-artist'):
                    assert request.method == 'GET'
                    route.fulfill(content_type='application/json', body=json.dumps(envelope(fixture['catalog'])))
                    return
                if request.url.endswith('/characters/load'):
                    assert request.method == 'POST'
                    assert_post_headers(request)
                    body = json.loads(request.post_data or '{}')
                    assert set(body) == {'characterName', 'forceRefresh'}
                    assert body['characterName'] == '봄날꽃씨'
                    assert isinstance(body['forceRefresh'], bool)
                    loads.append(body)
                    route.fulfill(content_type='application/json', body=json.dumps(envelope(fixture['load'])))
                    return
                if request.url.endswith('/simulations'):
                    assert request.method == 'POST'
                    assert_post_headers(request)
                    body = json.loads(request.post_data or '{}')
                    assert_simulation_contract(body)
                    simulations.append(body)
                    disabled = any(
                        patch['kind'] == 'set-section-enabled' and patch['enabled'] is False
                        for patch in body['patches']
                    )
                    data = {
                        **fixture['simulation'],
                        'patches': body['patches'],
                        'candidate': fixture['simulation']['candidate'] if disabled else fixture['simulation']['baseline'],
                    }
                    route.fulfill(content_type='application/json', body=json.dumps(envelope(data)))
                    return
                raise AssertionError(f'unexpected API route or method: {request.method} {request.url}')

            try:
                page.route('**/api/v1/**', api)
                page.goto(base_url, wait_until='networkidle')
                page.evaluate('localStorage.clear()')

                load_before = len(loads)
                simulation_before = len(simulations)
                page.get_by_label('캐릭터 이름').fill('봄날꽃씨')
                page.get_by_role('button', name='불러오기').click()
                first_load = wait_for_request(page, loads, load_before, 'initial character load')
                assert first_load == {'characterName': '봄날꽃씨', 'forceRefresh': False}
                wait_for_request(page, simulations, simulation_before, 'initial simulation')
                page.get_by_text('258,720.50').wait_for()

                simulation_before = len(simulations)
                page.get_by_role('checkbox', name='보석 사용').uncheck()
                changed = wait_for_request(page, simulations, simulation_before, 'gem disable simulation')
                assert changed['patches'] == [
                    {'schemaVersion': '1', 'kind': 'set-section-enabled', 'sectionId': 'gems', 'enabled': False},
                ]
                page.get_by_role('tab', name='스킬 피해 결과').click()
                page.get_by_text(candidate_text, exact=True).first.wait_for()
                page.get_by_text('기대 피해 차이 -200,000,000.00 (-20.00%)', exact=True).first.wait_for()

                page.get_by_role('tab', name='세팅 조정').click()
                simulation_before = len(simulations)
                page.get_by_role('button', name='보석 초기화').click()
                reset = wait_for_request(page, simulations, simulation_before, 'gem section reset')
                assert reset['patches'] == [{'schemaVersion': '1', 'kind': 'reset-section', 'sectionId': 'gems'}]
                assert page.get_by_role('checkbox', name='보석 사용').is_checked()
                page.get_by_role('tab', name='스킬 피해 결과').click()
                page.get_by_text(baseline_text, exact=True).first.wait_for()
                page.get_by_text('기대 피해 차이 +0.00 (+0.00%)', exact=True).first.wait_for()

                page.get_by_role('tab', name='세팅 조정').click()
                simulation_before = len(simulations)
                page.get_by_role('checkbox', name='각인·어빌리티 스톤 사용').uncheck()
                wait_for_request(page, simulations, simulation_before, 'meaningful pre-reset edit')
                assert not page.get_by_role('checkbox', name='각인·어빌리티 스톤 사용').is_checked()
                simulation_before = len(simulations)
                page.get_by_role('button', name='전체 초기화').click()
                all_reset = wait_for_request(page, simulations, simulation_before, 'all reset')
                assert all_reset['patches'] == []
                for section in editable_sections:
                    assert page.get_by_role('checkbox', name=f"{section['label']} 사용").is_checked()
                page.get_by_role('tab', name='스킬 피해 결과').click()
                page.get_by_text(baseline_text, exact=True).first.wait_for()
                page.get_by_text('기대 피해 차이 +0.00 (+0.00%)', exact=True).first.wait_for()

                page.get_by_role('tab', name='세팅 조정').click()
                simulation_before = len(simulations)
                page.get_by_role('checkbox', name='보석 사용').uncheck()
                wait_for_request(page, simulations, simulation_before, 'restored patch setup')
                load_before = len(loads)
                simulation_before = len(simulations)
                page.get_by_role('button', name='새로고침').click()
                refreshed = wait_for_request(page, loads, load_before, 'force refresh load')
                assert refreshed == {'characterName': '봄날꽃씨', 'forceRefresh': True}
                refreshed_simulation = wait_for_request(page, simulations, simulation_before, 'force refresh simulation')
                assert refreshed_simulation['patches'] == [
                    {'schemaVersion': '1', 'kind': 'set-section-enabled', 'sectionId': 'gems', 'enabled': False},
                ]
                assert not page.get_by_role('checkbox', name='보석 사용').is_checked()
                page.get_by_role('tab', name='스킬 피해 결과').click()
                page.get_by_text(candidate_text, exact=True).first.wait_for()

                load_before = len(loads)
                simulation_before = len(simulations)
                page.reload(wait_until='networkidle')
                page.get_by_label('캐릭터 이름').fill('봄날꽃씨')
                page.get_by_role('button', name='불러오기').click()
                reloaded = wait_for_request(page, loads, load_before, 'post-reload character load')
                assert reloaded == {'characterName': '봄날꽃씨', 'forceRefresh': False}
                reloaded_simulation = wait_for_request(page, simulations, simulation_before, 'post-reload restored simulation')
                assert reloaded_simulation['patches'] == [
                    {'schemaVersion': '1', 'kind': 'set-section-enabled', 'sectionId': 'gems', 'enabled': False},
                ]
                assert not page.get_by_role('checkbox', name='보석 사용').is_checked()
                page.get_by_role('tab', name='스킬 피해 결과').click()
                page.get_by_text(candidate_text, exact=True).first.wait_for()

                page.get_by_role('button', name='우레바람 상세').click()
                detail = page.get_by_role('region', name='우레바람 상세 결과')
                detail.wait_for()
                detail.get_by_role('table').get_by_text(baseline_text, exact=True).first.wait_for()
                detail.get_by_role('table').get_by_text(candidate_text, exact=True).first.wait_for()
                for heading in [
                    '계산 공격력 과정', '치명타율 계산', '치명타 피해 배율 계산',
                    '적용 트라이포드', '일반 보석', '방향성', '아크패시브', '아크그리드',
                ]:
                    detail.get_by_text(heading, exact=True).wait_for()
                for column in [
                    '기준 비치명', '변경 비치명', '기준 치명', '변경 치명',
                    '기준 기대', '변경 기대',
                ]:
                    detail.get_by_role('columnheader', name=column).wait_for()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                assert not errors, errors
                print(f'{name}: mocked full flow passed')
            finally:
                page.close()
    finally:
        browser.close()
