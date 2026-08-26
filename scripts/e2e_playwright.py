import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
fixture = json.loads((root / 'scripts/fixtures/weather-artist-e2e.json').read_text(encoding='utf8'))
base_url = os.environ.get('E2E_BASE_URL', 'http://127.0.0.1:5173')

def envelope(data): return {'schemaVersion':'1','ok':True,'data':data,'warnings':[]}

with sync_playwright() as p:
  browser = p.chromium.launch(headless=True)
  try:
    for name, viewport in {'desktop':{'width':1440,'height':1000},'tablet':{'width':900,'height':1000},'mobile':{'width':390,'height':844}}.items():
      page = browser.new_page(viewport=viewport); errors=[]; loads=[]; simulations=[]
      page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None); page.on('pageerror', lambda e: errors.append(str(e)))
      def api(route):
        request=route.request
        if request.url.endswith('/catalog/weather-artist'): route.fulfill(content_type='application/json',body=json.dumps(envelope(fixture['catalog'])))
        elif request.url.endswith('/characters/load'):
          loads.append(json.loads(request.post_data or '{}')); route.fulfill(content_type='application/json',body=json.dumps(envelope(fixture['load'])))
        elif request.url.endswith('/simulations'):
          body=json.loads(request.post_data or '{}'); simulations.append(body)
          disabled=any(p.get('kind')=='set-section-enabled' and p.get('sectionId')=='gems' and p.get('enabled') is False for p in body['patches'])
          data={**fixture['simulation'],'patches':body['patches'],'candidate':fixture['simulation']['candidate'] if disabled else fixture['simulation']['baseline']}; route.fulfill(content_type='application/json',body=json.dumps(envelope(data)))
        else: route.continue_()
      page.route('**/api/v1/**', api)
      page.goto(base_url,wait_until='networkidle'); page.evaluate('localStorage.clear()')
      page.get_by_label('캐릭터 이름').fill('봄날꽃씨'); page.get_by_role('button',name='불러오기').click()
      page.get_by_text('258,720.50').wait_for(); page.get_by_role('checkbox',name='보석 사용').uncheck(); page.wait_for_timeout(350)
      page.get_by_role('tab',name='스킬 피해 결과').click(); assert page.get_by_text('800.13').count() and page.get_by_text('기대 피해 차이 -200.00').count()
      page.get_by_role('tab',name='세팅 조정').click(); page.get_by_role('button',name='보석 초기화').click(); page.wait_for_timeout(350); assert simulations[-1]['patches']==[{'schemaVersion':'1','kind':'reset-section','sectionId':'gems'}]
      page.get_by_role('button',name='전체 초기화').click(); page.wait_for_timeout(350); assert simulations[-1]['patches']==[]
      page.get_by_role('checkbox',name='보석 사용').uncheck(); page.wait_for_timeout(350)
      page.get_by_role('button',name='새로고침').click(); page.get_by_text('258,720.50').wait_for(); assert any(x.get('forceRefresh') for x in loads)
      page.reload(wait_until='networkidle'); page.get_by_label('캐릭터 이름').fill('봄날꽃씨'); page.get_by_role('button',name='불러오기').click(); page.get_by_text('258,720.50').wait_for(); assert not page.get_by_role('checkbox',name='보석 사용').is_checked()
      page.get_by_role('tab',name='스킬 피해 결과').click(); page.get_by_text('800.13').first.wait_for(); assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'); assert not errors, errors
      page.close(); print(f'{name}: mocked full flow passed')
  finally: browser.close()
