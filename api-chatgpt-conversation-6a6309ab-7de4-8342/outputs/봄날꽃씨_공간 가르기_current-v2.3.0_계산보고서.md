# 봄날꽃씨 공간 가르기 API 파싱·피해 계산 보고서

- API 스냅샷: `2026-07-26T19:29:06.367871+09:00`
- 캐릭터: `봄날꽃씨` / `기상술사`
- 아이템 레벨: `1,785.83`
- 계산 스킬: `공간 가르기` / `1타+2타`
- 계산기 버전: `2.3.0`
- 파서 버전: `lostark-api-v2.3.0`
- 규칙 버전: `current-v2.3.0` — v2.2 감사 산식 + 다중 스킬·다중 타격
- DB 릴리스: `weather-artist-v0.2`
- 시나리오 프리셋: `max-favorable-example-boss-v1`
- 계산 모드: `ESTIMATE_WITH_FALLBACK`
- 규칙 출처: `current-v2.2.0 + user-provided space-cutting hit coefficients + explicit scope assumptions`
- 중간 버림 단계: `없음`
- API 원본: [봄날꽃씨_공간 가르기_current-v2.3.0_api_raw.json](봄날꽃씨_공간 가르기_current-v2.3.0_api_raw.json)
- 파싱 결과: [봄날꽃씨_공간 가르기_current-v2.3.0_parsed.json](봄날꽃씨_공간 가르기_current-v2.3.0_parsed.json)
- 과거 피해값과의 회귀검증은 수행하지 않았습니다.

## 1. API 호출 결과

| 엔드포인트 | HTTP | 호출 시각(KST) | 남은 호출량 |
|---|---:|---|---:|
| `profiles` | 200 | 2026-07-26T19:29:05.282379+09:00 | 99 |
| `equipment` | 200 | 2026-07-26T19:29:05.672113+09:00 | 98 |
| `avatars` | 200 | 2026-07-26T19:29:05.787971+09:00 | 97 |
| `combatSkills` | 200 | 2026-07-26T19:29:05.861953+09:00 | 98 |
| `engravings` | 200 | 2026-07-26T19:29:05.973629+09:00 | 97 |
| `cards` | 200 | 2026-07-26T19:29:06.046089+09:00 | 96 |
| `gems` | 200 | 2026-07-26T19:29:06.107788+09:00 | 93 |
| `arkPassive` | 200 | 2026-07-26T19:29:06.212605+09:00 | 96 |
| `arkGrid` | 200 | 2026-07-26T19:29:06.280871+09:00 | 95 |

전체 응답 본문은 API 원본 JSON에 엔드포인트별 `rawBody`와 파싱된 `responses`로 보존했습니다. Authorization 헤더는 저장하지 않았습니다.

### 핵심 원본 데이터 발췌

```json
{
  "profile": {
    "CharacterName": "봄날꽃씨",
    "CharacterLevel": 70,
    "ExpeditionLevel": 281,
    "CharacterClassName": "기상술사",
    "ItemAvgLevel": "1,785.83",
    "Stats": [
      {
        "Type": "치명",
        "Value": "773",
        "Tooltip": [
          "<textformat indent='-21' leftMargin='10'><font> </font> 치명타 적중률이 <font color='#99ff99'>27.66%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 물약 및 원정대 레벨 보상 효과로 <font color='#99ff99'>32</font>만큼 영구적으로 증가되었습니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 카드 도감 누적 효과가 반영된 값으로 전투정보실에서는 별도 수치를 표기하지 않습니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 카드 도감 누적 효과가 반영된 값으로 전투정보실에서는 별도 수치를 표기하지 않습니다.</textformat>"
        ]
      },
      {
        "Type": "특화",
        "Value": "73",
        "Tooltip": [
          "<textformat indent='-21' leftMargin='10'><font> </font> 기상 스킬 피해량이 <font color='#99ff99'>5.79%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 타격 시 빗방울 게이지 회복량이 <font color='#99ff99'>2.61%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 각성 스킬의 피해량이 <font color='#99ff99'>1.59%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 물약 및 원정대 레벨 보상 효과로 <font color='#99ff99'>32</font>만큼 영구적으로 증가되었습니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 카드 도감 누적 효과가 반영된 값으로 전투정보실에서는 별도 수치를 표기하지 않습니다.</textformat>"
        ]
      },
      {
        "Type": "제압",
        "Value": "77",
        "Tooltip": [
          "<textformat indent='-21' leftMargin='10'><font> </font> 피격이상 및 상태이상 대상에게 주는 피해량이 <font color='#99ff99'>4.72%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 무력화 대상에게 주는 피해량이 <font color='#99ff99'>5.49%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 물약 및 원정대 레벨 보상 효과로 <font color='#99ff99'>36</font>만큼 영구적으로 증가되었습니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 카드 도감 누적 효과가 반영된 값으로 전투정보실에서는 별도 수치를 표기하지 않습니다.</textformat>"
        ]
      },
      {
        "Type": "신속",
        "Value": "1644",
        "Tooltip": [
          "<textformat indent='-21' leftMargin='10'><font> </font> 공격 속도가 <font color='#99ff99'>28.24%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 이동 속도가 <font color='#99ff99'>28.24%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 스킬 재사용 대기시간이 <font color='#99ff99'>35.30%</font> 감소합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 물약 및 원정대 레벨 보상 효과로 <font color='#99ff99'>32</font>만큼 영구적으로 증가되었습니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 카드 도감 누적 효과가 반영된 값으로 전투정보실에서는 별도 수치를 표기하지 않습니다.</textformat>"
        ]
      },
      {
        "Type": "인내",
        "Value": "71",
        "Tooltip": [
          "<textformat indent='-21' leftMargin='10'><font> </font> 물리 방어력이 <font color='#99ff99'>5.80%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 마법 방어력이 <font color='#99ff99'>5.80%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 보호막 효과가 <font color='#99ff99'>1.81%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 생명력 회복 효과가 <font color='#99ff99'>2.54%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 물약 및 원정대 레벨 보상 효과로 <font color='#99ff99'>28</font>만큼 영구적으로 증가되었습니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 카드 도감 누적 효과가 반영된 값으로 전투정보실에서는 별도 수치를 표기하지 않습니다.</textformat>"
        ]
      },
      {
        "Type": "숙련",
        "Value": "172",
        "Tooltip": [
          "<textformat indent='-21' leftMargin='10'><font> </font> 상태이상 공격 지속시간이 <font color='#99ff99'>7.38%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 상태이상 피해 지속시간이 <font color='#99ff99'>6.15%</font> 감소합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 무력화 피해량이 <font color='#99ff99'>4.92%</font> 증가합니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 물약 및 원정대 레벨 보상 효과로 <font color='#99ff99'>28</font>만큼 영구적으로 증가되었습니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 카드 도감 누적 효과가 반영된 값으로 전투정보실에서는 별도 수치를 표기하지 않습니다.</textformat>"
        ]
      },
      {
        "Type": "최대 생명력",
        "Value": "350349",
        "Tooltip": [
          "<textformat indent='-21' leftMargin='10'><font> </font> 캐릭터의 최대 생명력을 나타냅니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><textformat indent='-21' leftMargin='10'><font> </font> 체력으로 최대 생명력이 <font color='#99ff99'>214808</font> 증가되었습니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 생명 활성력으로 최대 생명력이 <font color='#99ff99'>46.69%</font> 증가되었습니다.</textformat>"
        ]
      },
      {
        "Type": "공격력",
        "Value": "217160",
        "Tooltip": [
          "<textformat indent='-21' leftMargin='10'><font> </font> 적에게 주는 피해를 계산할 때 기준이 되는 값입니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 힘, 민첩, 지능과 무기 공격력을 기반으로 증가한 기본 공격력은 <font color='#99ff99'>210325</font> 입니다.</textformat>",
          "<textformat indent='-21' leftMargin='10'><font> </font> 공격력 증감 효과로 공격력이 <font color='#99ff99'>6835</font> 증가되었습니다.</textformat>"
        ]
      }
    ]
  },
  "equipmentCount": 16,
  "gemCount": 11,
  "arkGrid": {
    "Slots": [
      {
        "Index": 0,
        "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_96.png",
        "Name": "질서의 해 코어 : 비연참",
        "Point": 18,
        "Grade": "고대",
        "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#E3C7A1'>질서의 해 코어 : 비연참</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#E3C7A1'>고대 아크 그리드 코어</FONT></FONT>\",\r\n      \"leftStr1\": \"\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 6,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_96.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<FONT SIZE='12'>기상술사 전용</FONT>\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 타입</FONT>\",\r\n      \"Element_001\": \"질서 - 해\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 공급 의지력</FONT>\",\r\n      \"Element_001\": \"<FONT COLOR = '#B7FB00'>17</FONT> 포인트\"\r\n    }\r\n  },\r\n  \"Element_006\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 옵션</FONT>\",\r\n      \"Element_001\": \"<FONT color='#FFD200'>[10P]</FONT> 우산 스킬의 피해량이 <FONT COLOR='#99ff99'>2.0%</FONT> 증가한다. <br><FONT color='#FFD200'>[14P]</FONT> <FONT COLOR='#bf9ef6'>'운명'</FONT> 발동 시 <FONT COLOR='#bf9ef6'>'운명: 비연참'</FONT> 효과를 획득한다.<BR><FONT COLOR='#bf9ef6'>'운명: 비연참'</FONT> : 다음 사용하는 회오리 걸음, 몰아치기, 바람송곳, 칼바람의 피해량이 <FONT COLOR='#99ff99'>5.0%</FONT> 증가한다.<br><FONT color='#FFD200'>[17P]</FONT> <FONT COLOR='#bf9ef6'>'운명'</FONT> 발동 시 <FONT COLOR='#ffff99'>4.0</FONT>초 동안 지속되는 기류 보호막이 생성된다. 우산 스킬의 피해량이 <FONT COLOR='#99ff99'>1.0%</FONT> 증가한다.<br><FONT color='#FFD200'>[18P]</FONT> 우산 스킬의 피해량이 <FONT COLOR='#99ff99'>0.2%</FONT> 증가한다. <br><FONT color='#FFD200'>[19P]</FONT> 우산 스킬의 피해량이 <FONT COLOR='#99ff99'>0.2%</FONT> 증가한다. <br><FONT color='#FFD200'>[20P]</FONT> 우산 스킬의 피해량이 <FONT COLOR='#99ff99'>0.2%</FONT> 증가한다. \"\r\n    }\r\n  },\r\n  \"Element_007\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 옵션 발동 조건</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>질풍노도 전용<br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아크 패시브 4티어 공간 가르기 활성화 필요\"\r\n    }\r\n  },\r\n  \"Element_008\": null,\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<FONT SIZE='12'><FONT COLOR='#C24B46'>분해불가</FONT></FONT>\"\r\n  },\r\n  \"Element_010\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_011\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_012\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[카제로스 레이드] 4막 : 파멸의 성채</font><BR><Font color='#5FD3F1'>[카제로스 레이드] 종막 : 최후의 날</font><BR><Font color='#5FD3F1'>[그림자 레이드] 고통의 마녀, 세르카</font><BR><Font color='#5FD3F1'>그 외에 획득처가 더 존재합니다.</FONT>\"\r\n  }\r\n}",
        "Gems": [
          {
            "Index": 0,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png",
            "IsActive": true,
            "Grade": "고대",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#E3C7A1'>질서의 젬 : 안정</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#E3C7A1'>고대 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 6,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>19</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>3</FONT> (기본 값 8 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>4</FONT><br>[추가 피해] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.40%<br>[아군 피해 강화] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아군 피해량 강화 효과 +0.26%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 1,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png",
            "IsActive": true,
            "Grade": "전설",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#F99200'>질서의 젬 : 안정</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#F99200'>전설 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 4,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>14</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>3</FONT> (기본 값 8 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[추가 피해] <FONT color='#FFD200'>Lv.3</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.24%<br>[낙인력] <FONT color='#FFD200'>Lv.1</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>낙인력 +0.16%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 2,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_203.png",
            "IsActive": true,
            "Grade": "고대",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#E3C7A1'>질서의 젬 : 견고</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#E3C7A1'>고대 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 6,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_203.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>19</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>4</FONT> (기본 값 9 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[아군 공격 강화] <FONT color='#FFD200'>Lv.4</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아군 공격력 강화 효과 +0.52%<br>[공격력] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>공격력 +0.18%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 3,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_203.png",
            "IsActive": true,
            "Grade": "전설",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#F99200'>질서의 젬 : 견고</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#F99200'>전설 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 4,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_203.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>12</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>7</FONT> (기본 값 9 – 의지력 효율 <FONT COLOR = '#FBB29C'>2</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>4</FONT><br>[공격력] <FONT color='#FFD200'>Lv.1</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>공격력 +0.03%<br>[보스 피해] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>보스 등급 이상 몬스터에게 주는 피해 +0.41%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          }
        ]
      },
      {
        "Index": 1,
        "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_97.png",
        "Name": "질서의 달 코어 : 우산의 춤",
        "Point": 18,
        "Grade": "유물",
        "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#FA5D00'>질서의 달 코어 : 우산의 춤</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#FA5D00'>유물 아크 그리드 코어</FONT></FONT>\",\r\n      \"leftStr1\": \"\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 5,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_97.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<FONT SIZE='12'>기상술사 전용</FONT>\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 타입</FONT>\",\r\n      \"Element_001\": \"질서 - 달\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 공급 의지력</FONT>\",\r\n      \"Element_001\": \"<FONT COLOR = '#B7FB00'>15</FONT> 포인트\"\r\n    }\r\n  },\r\n  \"Element_006\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 옵션</FONT>\",\r\n      \"Element_001\": \"<FONT color='#FFD200'>[10P]</FONT> 우산 스킬의 피해량이 <FONT COLOR='#99ff99'>2.0%</FONT> 증가한다. <br><FONT color='#FFD200'>[14P]</FONT> 회오리 걸음, 몰아치기, 바람송곳, 칼바람 사용 시 <FONT COLOR='#bf9ef6'>'운명'</FONT>이 발동한다.<br><FONT color='#FFD200'>[17P]</FONT> 회오리 걸음, 몰아치기의 피해량이 <FONT COLOR='#99ff99'>8.0%</FONT> 증가한다. <br><FONT color='#FFD200'>[18P]</FONT> 우산 스킬의 피해량이 <FONT COLOR='#99ff99'>0.2%</FONT> 증가한다. <br><FONT color='#FFD200'>[19P]</FONT> 우산 스킬의 피해량이 <FONT COLOR='#99ff99'>0.2%</FONT> 증가한다. <br><FONT color='#FFD200'>[20P]</FONT> 우산 스킬의 피해량이 <FONT COLOR='#99ff99'>0.2%</FONT> 증가한다. \"\r\n    }\r\n  },\r\n  \"Element_007\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 옵션 발동 조건</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>질풍노도 전용<br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아크 패시브 4티어 공간 가르기 활성화 필요\"\r\n    }\r\n  },\r\n  \"Element_008\": null,\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<FONT SIZE='12'><FONT COLOR='#C24B46'>분해불가</FONT></FONT>\"\r\n  },\r\n  \"Element_010\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_011\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_012\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[카제로스 레이드] 4막 : 파멸의 성채</font><BR><Font color='#5FD3F1'>[카제로스 레이드] 종막 : 최후의 날</font><BR><Font color='#5FD3F1'>[그림자 레이드] 고통의 마녀, 세르카</font><BR><Font color='#5FD3F1'>그 외에 획득처가 더 존재합니다.</FONT>\"\r\n  }\r\n}",
        "Gems": [
          {
            "Index": 0,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png",
            "IsActive": true,
            "Grade": "전설",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#F99200'>질서의 젬 : 안정</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#F99200'>전설 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 4,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>13</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>3</FONT> (기본 값 8 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[추가 피해] <FONT color='#FFD200'>Lv.2</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.16%<br>[공격력] <FONT color='#FFD200'>Lv.1</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>공격력 +0.03%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 1,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png",
            "IsActive": true,
            "Grade": "유물",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#FA5D00'>질서의 젬 : 안정</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#FA5D00'>유물 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 5,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>16</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>3</FONT> (기본 값 8 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[추가 피해] <FONT color='#FFD200'>Lv.1</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.08%<br>[공격력] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>공격력 +0.18%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 2,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_203.png",
            "IsActive": true,
            "Grade": "유물",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#FA5D00'>질서의 젬 : 견고</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#FA5D00'>유물 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 5,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_203.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>18</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>4</FONT> (기본 값 9 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>4</FONT><br>[보스 피해] <FONT color='#FFD200'>Lv.4</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>보스 등급 이상 몬스터에게 주는 피해 +0.33%<br>[아군 공격 강화] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아군 공격력 강화 효과 +0.65%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 3,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_204.png",
            "IsActive": true,
            "Grade": "유물",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#FA5D00'>질서의 젬 : 불변</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#FA5D00'>유물 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 5,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_204.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>16</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>5</FONT> (기본 값 10 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>4</FONT><br>[추가 피해] <FONT color='#FFD200'>Lv.3</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.24%<br>[보스 피해] <FONT color='#FFD200'>Lv.4</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>보스 등급 이상 몬스터에게 주는 피해 +0.33%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          }
        ]
      },
      {
        "Index": 2,
        "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_98.png",
        "Name": "질서의 별 코어 : 휘몰아치기",
        "Point": 20,
        "Grade": "유물",
        "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#FA5D00'>질서의 별 코어 : 휘몰아치기</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#FA5D00'>유물 아크 그리드 코어</FONT></FONT>\",\r\n      \"leftStr1\": \"\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 5,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_98.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<FONT SIZE='12'>기상술사 전용</FONT>\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 타입</FONT>\",\r\n      \"Element_001\": \"질서 - 별\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 공급 의지력</FONT>\",\r\n      \"Element_001\": \"<FONT COLOR = '#B7FB00'>15</FONT> 포인트\"\r\n    }\r\n  },\r\n  \"Element_006\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 옵션</FONT>\",\r\n      \"Element_001\": \"<FONT color='#FFD200'>[10P]</FONT> 몰아치기, 회오리 걸음의 시전 속도가 <FONT COLOR='#99ff99'>20.0%</FONT> 증가하고, 몰아치기 시전 중 경직에 면역이 된다.<br><FONT color='#FFD200'>[14P]</FONT> 회오리 걸음의 피해량이 <FONT COLOR='#99ff99'>55.0%</FONT> 증가한다. <br><FONT color='#FFD200'>[17P]</FONT> 몰아치기의 피해량이 <FONT COLOR='#99ff99'>12.0%</FONT> 증가한다. <br><FONT color='#FFD200'>[18P]</FONT> 회오리 걸음, 몰아치기의 피해량이 <FONT COLOR='#99ff99'>0.7%</FONT> 증가한다. <br><FONT color='#FFD200'>[19P]</FONT> 회오리 걸음, 몰아치기의 피해량이 <FONT COLOR='#99ff99'>0.7%</FONT> 증가한다. <br><FONT color='#FFD200'>[20P]</FONT> 회오리 걸음, 몰아치기의 피해량이 <FONT COLOR='#99ff99'>0.7%</FONT> 증가한다. \"\r\n    }\r\n  },\r\n  \"Element_007\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 옵션 발동 조건</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>질풍노도 전용<br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아크 패시브 4티어 공간 가르기 활성화 필요\"\r\n    }\r\n  },\r\n  \"Element_008\": null,\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<FONT SIZE='12'><FONT COLOR='#C24B46'>분해불가</FONT></FONT>\"\r\n  },\r\n  \"Element_010\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_011\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_012\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[카제로스 레이드] 4막 : 파멸의 성채</font><BR><Font color='#5FD3F1'>[카제로스 레이드] 종막 : 최후의 날</font><BR><Font color='#5FD3F1'>[그림자 레이드] 고통의 마녀, 세르카</font><BR><Font color='#5FD3F1'>그 외에 획득처가 더 존재합니다.</FONT>\"\r\n  }\r\n}",
        "Gems": [
          {
            "Index": 0,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_203.png",
            "IsActive": true,
            "Grade": "전설",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#F99200'>질서의 젬 : 견고</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#F99200'>전설 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 4,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_203.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>14</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>4</FONT> (기본 값 9 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[아군 피해 강화] <FONT color='#FFD200'>Lv.1</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아군 피해량 강화 효과 +0.05%<br>[보스 피해] <FONT color='#FFD200'>Lv.3</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>보스 등급 이상 몬스터에게 주는 피해 +0.25%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 1,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png",
            "IsActive": true,
            "Grade": "전설",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#F99200'>질서의 젬 : 안정</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#F99200'>전설 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 4,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>13</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>3</FONT> (기본 값 8 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[낙인력] <FONT color='#FFD200'>Lv.1</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>낙인력 +0.16%<br>[공격력] <FONT color='#FFD200'>Lv.2</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>공격력 +0.07%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 2,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_203.png",
            "IsActive": true,
            "Grade": "유물",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#FA5D00'>질서의 젬 : 견고</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#FA5D00'>유물 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 5,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_203.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>17</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>4</FONT> (기본 값 9 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[보스 피해] <FONT color='#FFD200'>Lv.2</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>보스 등급 이상 몬스터에게 주는 피해 +0.16%<br>[아군 피해 강화] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아군 피해량 강화 효과 +0.26%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 3,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png",
            "IsActive": true,
            "Grade": "전설",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#F99200'>질서의 젬 : 안정</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#F99200'>전설 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 4,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_202.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 질서<br>젬 포인트 : <FONT COLOR = '#B7FB00'>14</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>4</FONT> (기본 값 8 – 의지력 효율 <FONT COLOR = '#FBB29C'>4</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>질서 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[추가 피해] <FONT color='#FFD200'>Lv.2</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.16%<br>[공격력] <FONT color='#FFD200'>Lv.3</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>공격력 +0.11%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          }
        ]
      },
      {
        "Index": 3,
        "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_99.png",
        "Name": "혼돈의 해 코어 : 현란한 공격",
        "Point": 19,
        "Grade": "고대",
        "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#E3C7A1'>혼돈의 해 코어 : 현란한 공격</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#E3C7A1'>고대 아크 그리드 코어</FONT></FONT>\",\r\n      \"leftStr1\": \"\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 6,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_99.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 타입</FONT>\",\r\n      \"Element_001\": \"혼돈 - 해\"\r\n    }\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 공급 의지력</FONT>\",\r\n      \"Element_001\": \"<FONT COLOR = '#B7FB00'>17</FONT> 포인트\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 옵션</FONT>\",\r\n      \"Element_001\": \"<FONT color='#FFD200'>[10P]</FONT> 치명타 시 적에게 주는 피해가 <FONT COLOR='#99ff99'>0.55%</FONT> 증가한다. <br><FONT color='#FFD200'>[14P]</FONT> 적에게 주는 피해가 <FONT COLOR='#99ff99'>0.50%</FONT> 증가한다. <br><FONT color='#FFD200'>[17P]</FONT> 적에게 주는 피해가 <FONT COLOR='#99ff99'>1.50%</FONT> 추가로 증가하고, 치명타 시 적에게 주는 피해가 <FONT COLOR='#99ff99'>1.10%</FONT> 추가로 증가한다. <br><FONT color='#FFD200'>[18P]</FONT> 적에게 주는 피해가 <FONT COLOR='#99ff99'>0.16%</FONT> 증가한다. <br><FONT color='#FFD200'>[19P]</FONT> 적에게 주는 피해가 <FONT COLOR='#99ff99'>0.16%</FONT> 증가한다. <br><FONT color='#FFD200'>[20P]</FONT> 적에게 주는 피해가 <FONT COLOR='#99ff99'>0.16%</FONT> 증가한다. \"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<FONT SIZE='12'><FONT COLOR='#C24B46'>분해불가</FONT></FONT>\"\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_010\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[카제로스 레이드] 4막 : 파멸의 성채</font><BR><Font color='#5FD3F1'>[카제로스 레이드] 종막 : 최후의 날</font><BR><Font color='#5FD3F1'>[그림자 레이드] 고통의 마녀, 세르카</font><BR><Font color='#5FD3F1'>그 외에 획득처가 더 존재합니다.</FONT>\"\r\n  }\r\n}",
        "Gems": [
          {
            "Index": 0,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_205.png",
            "IsActive": true,
            "Grade": "전설",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#F99200'>혼돈의 젬 : 침식</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#F99200'>전설 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 4,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_205.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>14</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>4</FONT> (기본 값 8 – 의지력 효율 <FONT COLOR = '#FBB29C'>4</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>4</FONT><br>[추가 피해] <FONT color='#FFD200'>Lv.3</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.24%<br>[공격력] <FONT color='#FFD200'>Lv.3</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>공격력 +0.11%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 1,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_205.png",
            "IsActive": true,
            "Grade": "고대",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#E3C7A1'>혼돈의 젬 : 침식</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#E3C7A1'>고대 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 6,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_205.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>19</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>3</FONT> (기본 값 8 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[추가 피해] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.40%<br>[공격력] <FONT color='#FFD200'>Lv.4</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>공격력 +0.14%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 2,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_205.png",
            "IsActive": true,
            "Grade": "전설",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#F99200'>혼돈의 젬 : 침식</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#F99200'>전설 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 4,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_205.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>14</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>4</FONT> (기본 값 8 – 의지력 효율 <FONT COLOR = '#FBB29C'>4</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[공격력] <FONT color='#FFD200'>Lv.3</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>공격력 +0.11%<br>[추가 피해] <FONT color='#FFD200'>Lv.2</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.16%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 3,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_207.png",
            "IsActive": true,
            "Grade": "유물",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#FA5D00'>혼돈의 젬 : 붕괴</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#FA5D00'>유물 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 5,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_207.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>18</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>6</FONT> (기본 값 10 – 의지력 효율 <FONT COLOR = '#FBB29C'>4</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[추가 피해] <FONT color='#FFD200'>Lv.4</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.32%<br>[보스 피해] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>보스 등급 이상 몬스터에게 주는 피해 +0.41%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          }
        ]
      },
      {
        "Index": 4,
        "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_100.png",
        "Name": "혼돈의 달 코어 : 불타는 일격",
        "Point": 20,
        "Grade": "고대",
        "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#E3C7A1'>혼돈의 달 코어 : 불타는 일격</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#E3C7A1'>고대 아크 그리드 코어</FONT></FONT>\",\r\n      \"leftStr1\": \"\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 6,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_100.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 타입</FONT>\",\r\n      \"Element_001\": \"혼돈 - 달\"\r\n    }\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 공급 의지력</FONT>\",\r\n      \"Element_001\": \"<FONT COLOR = '#B7FB00'>17</FONT> 포인트\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 옵션</FONT>\",\r\n      \"Element_001\": \"<FONT color='#FFD200'>[10P]</FONT> 보스 이상 적에게 공격 적중 시 <FONT COLOR='#ffff99'>6.0</FONT>초 간 화상 상태로 만들어 피해를 입힌다. <br><FONT color='#FFD200'>[14P]</FONT> 보스 이상 적에게 주는 피해가 <FONT COLOR='#99ff99'>0.50%</FONT> 증가한다.<br><FONT color='#FFD200'>[17P]</FONT> 보스 이상 적에게 주는 피해가 <FONT COLOR='#99ff99'>2.00%</FONT> 추가로 증가하고, 화상의 피해량이 <FONT COLOR='#99ff99'>150%</FONT> 증가한다.<br><FONT color='#FFD200'>[18P]</FONT> 보스 이상 적에게 주는 피해가 <FONT COLOR='#99ff99'>0.16%</FONT> 증가한다.<br><FONT color='#FFD200'>[19P]</FONT> 보스 이상 적에게 주는 피해가 <FONT COLOR='#99ff99'>0.16%</FONT> 증가한다.<br><FONT color='#FFD200'>[20P]</FONT> 보스 이상 적에게 주는 피해가 <FONT COLOR='#99ff99'>0.16%</FONT> 증가한다.\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<FONT SIZE='12'><FONT COLOR='#C24B46'>분해불가</FONT></FONT>\"\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_010\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[카제로스 레이드] 4막 : 파멸의 성채</font><BR><Font color='#5FD3F1'>[카제로스 레이드] 종막 : 최후의 날</font><BR><Font color='#5FD3F1'>[그림자 레이드] 고통의 마녀, 세르카</font><BR><Font color='#5FD3F1'>그 외에 획득처가 더 존재합니다.</FONT>\"\r\n  }\r\n}",
        "Gems": [
          {
            "Index": 0,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_205.png",
            "IsActive": true,
            "Grade": "전설",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#F99200'>혼돈의 젬 : 침식</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#F99200'>전설 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 4,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_205.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>15</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>3</FONT> (기본 값 8 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[아군 피해 강화] <FONT color='#FFD200'>Lv.1</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아군 피해량 강화 효과 +0.05%<br>[추가 피해] <FONT color='#FFD200'>Lv.4</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.32%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 1,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_206.png",
            "IsActive": true,
            "Grade": "유물",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#FA5D00'>혼돈의 젬 : 왜곡</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#FA5D00'>유물 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 5,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_206.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>18</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>4</FONT> (기본 값 9 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[공격력] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>공격력 +0.18%<br>[보스 피해] <FONT color='#FFD200'>Lv.3</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>보스 등급 이상 몬스터에게 주는 피해 +0.25%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 2,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_207.png",
            "IsActive": true,
            "Grade": "전설",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#F99200'>혼돈의 젬 : 붕괴</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#F99200'>전설 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 4,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_207.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>15</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>5</FONT> (기본 값 10 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[추가 피해] <FONT color='#FFD200'>Lv.4</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.32%<br>[아군 공격 강화] <FONT color='#FFD200'>Lv.1</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아군 공격력 강화 효과 +0.13%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 3,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_207.png",
            "IsActive": true,
            "Grade": "유물",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#FA5D00'>혼돈의 젬 : 붕괴</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#FA5D00'>유물 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 5,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_207.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>17</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>5</FONT> (기본 값 10 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[보스 피해] <FONT color='#FFD200'>Lv.4</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>보스 등급 이상 몬스터에게 주는 피해 +0.33%<br>[추가 피해] <FONT color='#FFD200'>Lv.3</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.24%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          }
        ]
      },
      {
        "Index": 5,
        "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_101.png",
        "Name": "혼돈의 별 코어 : 무기",
        "Point": 17,
        "Grade": "고대",
        "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#E3C7A1'>혼돈의 별 코어 : 무기</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#E3C7A1'>고대 아크 그리드 코어</FONT></FONT>\",\r\n      \"leftStr1\": \"\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 6,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_101.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 타입</FONT>\",\r\n      \"Element_001\": \"혼돈 - 별\"\r\n    }\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 공급 의지력</FONT>\",\r\n      \"Element_001\": \"<FONT COLOR = '#B7FB00'>17</FONT> 포인트\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>코어 옵션</FONT>\",\r\n      \"Element_001\": \"<FONT color='#FFD200'>[10P]</FONT> 무기 공격력이 <FONT COLOR='#99ff99'>1300</FONT> 증가한다.<br><FONT color='#FFD200'>[14P]</FONT> 무기 공격력이 <FONT COLOR='#99ff99'>0.75%</FONT> 증가한다.<br><FONT color='#FFD200'>[17P]</FONT> 무기 공격력이 <FONT COLOR='#99ff99'>2.25%</FONT> 증가하고, 추가로 <FONT COLOR='#99ff99'>3900</FONT> 증가한다.<br><FONT color='#FFD200'>[18P]</FONT> 무기 공격력이 <FONT COLOR='#99ff99'>0.23%</FONT> 증가한다.<br><FONT color='#FFD200'>[19P]</FONT> 무기 공격력이 <FONT COLOR='#99ff99'>0.23%</FONT> 증가한다.<br><FONT color='#FFD200'>[20P]</FONT> 무기 공격력이 <FONT COLOR='#99ff99'>0.23%</FONT> 증가한다.\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<FONT SIZE='12'><FONT COLOR='#C24B46'>분해불가</FONT></FONT>\"\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_010\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[카제로스 레이드] 4막 : 파멸의 성채</font><BR><Font color='#5FD3F1'>[카제로스 레이드] 종막 : 최후의 날</font><BR><Font color='#5FD3F1'>[그림자 레이드] 고통의 마녀, 세르카</font><BR><Font color='#5FD3F1'>그 외에 획득처가 더 존재합니다.</FONT>\"\r\n  }\r\n}",
        "Gems": [
          {
            "Index": 0,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_205.png",
            "IsActive": true,
            "Grade": "고대",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#E3C7A1'>혼돈의 젬 : 침식</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#E3C7A1'>고대 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 6,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_205.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>20</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>3</FONT> (기본 값 8 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[공격력] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>공격력 +0.18%<br>[추가 피해] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.40%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  }\r\n}"
          },
          {
            "Index": 1,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_206.png",
            "IsActive": true,
            "Grade": "고대",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#E3C7A1'>혼돈의 젬 : 왜곡</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#E3C7A1'>고대 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 6,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_206.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>19</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>4</FONT> (기본 값 9 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>5</FONT><br>[아군 공격 강화] <FONT color='#FFD200'>Lv.4</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아군 공격력 강화 효과 +0.52%<br>[보스 피해] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>보스 등급 이상 몬스터에게 주는 피해 +0.41%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 2,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_206.png",
            "IsActive": true,
            "Grade": "유물",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#FA5D00'>혼돈의 젬 : 왜곡</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#FA5D00'>유물 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 5,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_206.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>18</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>4</FONT> (기본 값 9 – 의지력 효율 <FONT COLOR = '#FBB29C'>5</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>3</FONT><br>[아군 피해 강화] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>아군 피해량 강화 효과 +0.26%<br>[보스 피해] <FONT color='#FFD200'>Lv.5</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>보스 등급 이상 몬스터에게 주는 피해 +0.41%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          },
          {
            "Index": 3,
            "Icon": "https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_207.png",
            "IsActive": true,
            "Grade": "전설",
            "Tooltip": "{\r\n  \"Element_000\": {\r\n    \"type\": \"NameTagBox\",\r\n    \"value\": \"<P ALIGN='CENTER'><FONT COLOR='#F99200'>혼돈의 젬 : 붕괴</FONT></P>\"\r\n  },\r\n  \"Element_001\": {\r\n    \"type\": \"ItemTitle\",\r\n    \"value\": {\r\n      \"bEquip\": 0,\r\n      \"itemIrochiCount\": 0,\r\n      \"leftStr0\": \"<FONT SIZE='12'><FONT COLOR='#F99200'>전설 아크 그리드 젬</FONT></FONT>\",\r\n      \"leftStr2\": \"\",\r\n      \"qualityValue\": -1,\r\n      \"rightStr0\": \"\",\r\n      \"slotData\": {\r\n        \"advBookIcon\": 0,\r\n        \"battleItemTypeIcon\": 0,\r\n        \"blackListIcon\": 0,\r\n        \"cardIcon\": false,\r\n        \"friendship\": 0,\r\n        \"iconGrade\": 4,\r\n        \"iconPath\": \"https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_13_207.png\",\r\n        \"imagePath\": \"\",\r\n        \"islandIcon\": 0,\r\n        \"petBorder\": 0,\r\n        \"rtString\": \"\",\r\n        \"temporary\": 0,\r\n        \"town\": 0,\r\n        \"trash\": 0\r\n      }\r\n    }\r\n  },\r\n  \"Element_002\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"가공 완료\"\r\n  },\r\n  \"Element_003\": {\r\n    \"type\": \"MultiTextBox\",\r\n    \"value\": \"|<font color='#C24B46'>거래 불가</font>\"\r\n  },\r\n  \"Element_004\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 기본 정보</FONT>\",\r\n      \"Element_001\": \"젬 타입 : 혼돈<br>젬 포인트 : <FONT COLOR = '#B7FB00'>15</FONT>\"\r\n    }\r\n  },\r\n  \"Element_005\": {\r\n    \"type\": \"ItemPartBox\",\r\n    \"value\": {\r\n      \"Element_000\": \"<FONT COLOR='#A9D0F5'>젬 효과</FONT>\",\r\n      \"Element_001\": \"<img src='emoticon_arkgrid_willpower' width='20' height='20' vspace='-7'></img>필요 의지력 : <FONT color='#FFD200'>6</FONT> (기본 값 10 – 의지력 효율 <FONT COLOR = '#FBB29C'>4</FONT>)<br><img src='emoticon_arkgrid_corepoint' width='20' height='20' vspace='-7'></img>혼돈 포인트 : <FONT COLOR = '#B7FB00'>4</FONT><br>[추가 피해] <FONT color='#FFD200'>Lv.3</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>추가 피해 +0.24%<br>[보스 피해] <FONT color='#FFD200'>Lv.4</FONT><br><img src='emoticon_sign_greenDot' width='0' height='0' vspace='-3'></img>보스 등급 이상 몬스터에게 주는 피해 +0.33%\"\r\n    }\r\n  },\r\n  \"Element_006\": null,\r\n  \"Element_007\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_008\": {\r\n    \"type\": \"Progress\",\r\n    \"value\": null\r\n  },\r\n  \"Element_009\": {\r\n    \"type\": \"SingleTextBox\",\r\n    \"value\": \"<Font color='#5FD3F1'>[젬 가공] 아크 그리드 젬</font><BR><Font color='#5FD3F1'>[젬 융합] 가공 완료 젬</font>\"\r\n  }\r\n}"
          }
        ]
      }
    ],
    "Effects": [
      {
        "Name": "추가 피해",
        "Level": 49,
        "Tooltip": "추가 피해 <font color='#ffd200'>+3.96%</font>"
      },
      {
        "Name": "아군 피해 강화",
        "Level": 17,
        "Tooltip": "아군 피해량 강화 효과 <font color='#ffd200'>+0.89%</font>"
      },
      {
        "Name": "낙인력",
        "Level": 2,
        "Tooltip": "낙인력 <font color='#ffd200'>+0.33%</font>"
      },
      {
        "Name": "아군 공격 강화",
        "Level": 14,
        "Tooltip": "아군 공격력 강화 효과 <font color='#ffd200'>+1.82%</font>"
      },
      {
        "Name": "공격력",
        "Level": 37,
        "Tooltip": "공격력 <font color='#ffd200'>+1.35%</font>"
      },
      {
        "Name": "보스 피해",
        "Level": 44,
        "Tooltip": "보스 등급 이상 몬스터에게 주는 피해 <font color='#ffd200'>+3.66%</font>"
      }
    ]
  }
}
```

## 2. 파싱 결과와 출처

| 값 | 정규화 결과 | 출처 | 파싱 | 적용 가능 | 실제 적용 | 제외 사유 |
|---|---:|---|---|---|---|---|
| 캐릭터 레벨 | `70` | `profiles.CharacterLevel` | 예 | 예 | 예 | - |
| 원정대 레벨 | `281` | `profiles.ExpeditionLevel` | 예 | 예 | 예 | - |
| 치명 | `773` | `profiles.Stats[치명]`<br>치명타 적중률이 27.66% 증가합니다. 물약 및 원정대 레벨 보상 효과로 32만큼 영구적으로 증가되었습니다. 카드 도감 누적 효과가 반영된 값으로 전투정보실에서는 별도 수치를 표기하지 않습니다. | 예 | 예 | 예 | - |
| 신속 | `1644` | `profiles.Stats[신속]`<br>공격 속도가 28.24% 증가합니다. 이동 속도가 28.24% 증가합니다. 스킬 재사용 대기시간이 35.30% 감소합니다. 물약 및 원정대 레벨 보상 효과로 32만큼 영구적으로 증가되었습니다. 카드 도감 누적 효과가 | 예 | 예 | 예 | - |
| 프로필 공격력(검산용) | `217160` | `profiles.Stats[공격력]` | 예 | 예 | 예 | - |
| 무기 baseWeaponAttack | `241367` | `equipment[0].Tooltip`<br>+25 운명의 전율 우산 고대 우산 품질 아이템 레벨 1800 (티어 4) 장착중 기상술사 전용 캐릭터 귀속됨 \|거래 불가 기본 효과 무기 공격력 +241367 추가 효과 추가 피해 +30.00% 분해불가, 품질 업 | 예 | 예 | 예 | - |
| 무기 additionalDamage | `0.30` | `equipment[0].Tooltip`<br>+25 운명의 전율 우산 고대 우산 품질 아이템 레벨 1800 (티어 4) 장착중 기상술사 전용 캐릭터 귀속됨 \|거래 불가 기본 효과 무기 공격력 +241367 추가 효과 추가 피해 +30.00% 분해불가, 품질 업 | 예 | 예 | 예 | - |
| 투구 mainStat | `129393` | `equipment[1].Tooltip`<br>+22 운명의 전율 머리장식 고대 머리 방어구 품질 아이템 레벨 1785 (티어 4) 장착중 기상술사 전용 캐릭터 귀속됨 \|거래 불가 기본 효과 물리 방어력 +10100 마법 방어력 +11222 지능 +129393  | 예 | 예 | 예 | - |
| 상의 mainStat | `100989` | `equipment[2].Tooltip`<br>+21 운명의 전율 상의 고대 상의 품질 아이템 레벨 1780 (티어 4) 장착중 기상술사 전용 캐릭터 귀속됨 \|거래 불가 기본 효과 물리 방어력 +13302 마법 방어력 +12193 지능 +100989 체력 +15 | 예 | 예 | 예 | - |
| 하의 mainStat | `109104` | `equipment[3].Tooltip`<br>+21 운명의 전율 하의 고대 하의 품질 아이템 레벨 1780 (티어 4) 장착중 기상술사 전용 캐릭터 귀속됨 \|거래 불가 기본 효과 물리 방어력 +12193 마법 방어력 +13302 지능 +109104 체력 +13 | 예 | 예 | 예 | - |
| 장갑 mainStat | `155271` | `equipment[4].Tooltip`<br>+22 운명의 전율 장갑 고대 장갑 품질 아이템 레벨 1785 (티어 4) 장착중 기상술사 전용 캐릭터 귀속됨 \|거래 불가 기본 효과 물리 방어력 +8978 마법 방어력 +8978 지능 +155271 체력 +7937 | 예 | 예 | 예 | - |
| 어깨 mainStat | `137711` | `equipment[5].Tooltip`<br>+22 운명의 전율 어깨장식 고대 어깨 방어구 품질 아이템 레벨 1785 (티어 4) 장착중 기상술사 전용 캐릭터 귀속됨 \|거래 불가 기본 효과 물리 방어력 +11222 마법 방어력 +10100 지능 +137711  | 예 | 예 | 예 | - |
| 목걸이 mainStat | `17750` | `equipment[6].Tooltip`<br>도래한 결전의 목걸이 고대 목걸이 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 1회 가능 \|거래가능 기본 효과 힘 +17750 민첩 +17750 지능 +17750 체력 +3810  | 예 | 예 | 예 | - |
| 목걸이 additionalDamage | `0.026` | `equipment[6].Tooltip`<br>도래한 결전의 목걸이 고대 목걸이 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 1회 가능 \|거래가능 기본 효과 힘 +17750 민첩 +17750 지능 +17750 체력 +3810  | 예 | 예 | 예 | - |
| 목걸이 damageToEnemy | `0.012` | `equipment[6].Tooltip`<br>도래한 결전의 목걸이 고대 목걸이 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 1회 가능 \|거래가능 기본 효과 힘 +17750 민첩 +17750 지능 +17750 체력 +3810  | 예 | 예 | 예 | - |
| 귀걸이 mainStat | `13744` | `equipment[7].Tooltip`<br>도래한 결전의 귀걸이 고대 귀걸이 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 2회 가능 \|거래가능 기본 효과 힘 +13744 민첩 +13744 지능 +13744 체력 +2914  | 예 | 예 | 예 | - |
| 귀걸이 weaponAttackPercent | `0.03` | `equipment[7].Tooltip`<br>도래한 결전의 귀걸이 고대 귀걸이 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 2회 가능 \|거래가능 기본 효과 힘 +13744 민첩 +13744 지능 +13744 체력 +2914  | 예 | 예 | 예 | - |
| 귀걸이 attackPowerPercent | `0.0095` | `equipment[7].Tooltip`<br>도래한 결전의 귀걸이 고대 귀걸이 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 2회 가능 \|거래가능 기본 효과 힘 +13744 민첩 +13744 지능 +13744 체력 +2914  | 예 | 예 | 예 | - |
| 귀걸이 mainStat | `13535` | `equipment[8].Tooltip`<br>도래한 결전의 귀걸이 고대 귀걸이 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 2회 가능 \|거래가능 기본 효과 힘 +13535 민첩 +13535 지능 +13535 체력 +2742  | 예 | 예 | 예 | - |
| 귀걸이 weaponAttackPercent | `0.03` | `equipment[8].Tooltip`<br>도래한 결전의 귀걸이 고대 귀걸이 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 2회 가능 \|거래가능 기본 효과 힘 +13535 민첩 +13535 지능 +13535 체력 +2742  | 예 | 예 | 예 | - |
| 귀걸이 attackPowerPercent | `0.0095` | `equipment[8].Tooltip`<br>도래한 결전의 귀걸이 고대 귀걸이 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 2회 가능 \|거래가능 기본 효과 힘 +13535 민첩 +13535 지능 +13535 체력 +2742  | 예 | 예 | 예 | - |
| 반지 mainStat | `11446` | `equipment[9].Tooltip`<br>도래한 결전의 반지 고대 반지 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 \|거래 불가 기본 효과 힘 +11446 민첩 +11446 지능 +11446 체력 +2160 연마 효과 치명타  | 예 | 예 | 예 | - |
| 반지 criticalRate | `0.0155` | `equipment[9].Tooltip`<br>도래한 결전의 반지 고대 반지 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 \|거래 불가 기본 효과 힘 +11446 민첩 +11446 지능 +11446 체력 +2160 연마 효과 치명타  | 예 | 예 | 예 | - |
| 반지 criticalDamage | `0.024` | `equipment[9].Tooltip`<br>도래한 결전의 반지 고대 반지 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 \|거래 불가 기본 효과 힘 +11446 민첩 +11446 지능 +11446 체력 +2160 연마 효과 치명타  | 예 | 예 | 예 | - |
| 반지 mainStat | `12549` | `equipment[10].Tooltip`<br>도래한 결전의 반지 고대 반지 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 2회 가능 \|거래가능 기본 효과 힘 +12549 민첩 +12549 지능 +12549 체력 +2345 연마 | 예 | 예 | 예 | - |
| 반지 criticalRate | `0.0155` | `equipment[10].Tooltip`<br>도래한 결전의 반지 고대 반지 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 2회 가능 \|거래가능 기본 효과 힘 +12549 민첩 +12549 지능 +12549 체력 +2345 연마 | 예 | 예 | 예 | - |
| 반지 criticalDamage | `0.024` | `equipment[10].Tooltip`<br>도래한 결전의 반지 고대 반지 품질 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 거래 2회 가능 \|거래가능 기본 효과 힘 +12549 민첩 +12549 지능 +12549 체력 +2345 연마 | 예 | 예 | 예 | - |
| 팔찌 additionalDamage | `0.035` | `equipment[12].Tooltip`<br>찬란한 구원자의 팔찌 고대 팔찌 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 \|거래 불가 팔찌 효과 숙련 +102 신속 +107 추가 피해 +3.50% 스킬의 재사용 대기 시간이 2% 증가하 | 예 | 예 | 예 | - |
| 팔찌 damageToEnemy | `0.045` | `equipment[12].Tooltip`<br>찬란한 구원자의 팔찌 고대 팔찌 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 \|거래 불가 팔찌 효과 숙련 +102 신속 +107 추가 피해 +3.50% 스킬의 재사용 대기 시간이 2% 증가하 | 예 | 예 | 예 | - |
| 팔찌 criticalDamage | `0.068` | `equipment[12].Tooltip`<br>찬란한 구원자의 팔찌 고대 팔찌 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 \|거래 불가 팔찌 효과 숙련 +102 신속 +107 추가 피해 +3.50% 스킬의 재사용 대기 시간이 2% 증가하 | 예 | 예 | 예 | - |
| 팔찌 criticalHitDamage | `0.015` | `equipment[12].Tooltip`<br>찬란한 구원자의 팔찌 고대 팔찌 아이템 티어 4 장착중 거래 제한 아이템 레벨 1680 캐릭터 귀속됨 \|거래 불가 팔찌 효과 숙련 +102 신속 +107 추가 피해 +3.50% 스킬의 재사용 대기 시간이 2% 증가하 | 예 | 예 | 예 | - |
| 무기 아바타 아바타 주스탯 | `0.02` | `avatars[0]`<br>수줍은 영원 우산 (귀속) / 전설 / IsInner=True<br>전설 부위당 +2% 예시값 | 예 | 예 | 예 | - |
| 머리 아바타 아바타 주스탯 | `0.02` | `avatars[1]`<br>수줍은 영원 머리 (귀속) / 전설 / IsInner=True<br>전설 부위당 +2% 예시값 | 예 | 예 | 예 | - |
| 상의 아바타 아바타 주스탯 | `0.02` | `avatars[2]`<br>수줍은 영원 상의 (귀속) / 전설 / IsInner=True<br>전설 부위당 +2% 예시값 | 예 | 예 | 예 | - |
| 하의 아바타 아바타 주스탯 | `0.02` | `avatars[3]`<br>수줍은 영원 하의 (귀속) / 전설 / IsInner=True<br>전설 부위당 +2% 예시값 | 예 | 예 | 예 | - |
| 악기 아바타 아바타 주스탯 | `0` | `avatars[4]`<br>천상의 하프 / 영웅 / IsInner=False<br>주스탯 적용 부위가 아니므로 0% | 예 | 예 | 예 | - |
| 얼굴1 아바타 아바타 주스탯 | `0` | `avatars[5]`<br>모던 캠퍼스 얼굴1 / 영웅 / IsInner=False<br>주스탯 적용 부위가 아니므로 0% | 예 | 예 | 예 | - |
| 얼굴2 아바타 아바타 주스탯 | `0` | `avatars[6]`<br>여명의 백린 얼굴2 / 영웅 / IsInner=False<br>주스탯 적용 부위가 아니므로 0% | 예 | 예 | 예 | - |
| 이동 효과 아바타 주스탯 | `0` | `avatars[10]`<br>첨벙 이동 효과 / 영웅 / IsInner=False<br>주스탯 적용 부위가 아니므로 0% | 예 | 예 | 예 | - |
| 원한 | `3` | `engravings.entries[0]`<br>보스 및 레이드 몬스터에게 주는 피해가 24.00% 증가하지만, 받는 피해가 20.00% 증가한다. | 예 | 예 | 예 | - |
| 질량 증가 | `4` | `engravings.entries[1]`<br>공격속도가 10.00% 감소하지만, 적에게 주는 피해가 19.00% 증가한다. | 예 | 예 | 예 | - |
| 돌격대장 | `3` | `engravings.entries[2]`<br>이동속도 증가량의 46.00% 만큼 적에게 주는 피해량이 증가한다. | 예 | 예 | 예 | - |
| 타격의 대가 | `4` | `engravings.entries[3]`<br>공격 타입이 백 어택 및 헤드 어택에 해당되지 않는 공격의 피해가 17.00% 증가한다. 각성기는 해당 효과가 적용되지 않는다. | 예 | 예 | 예 | - |
| 아드레날린 | `4` | `engravings.entries[4]`<br>이동기 및 기본공격을 제외한 스킬 사용 후 6초 동안 공격력이 1.73% 증가하며 (최대 6중첩) 해당 효과가 최대 중첩 도달 시 치명타 적중률이 추가로 20.00% 증가한다. 해당 효과는 스킬 취소에 따른 재사용  | 예 | 예 | 예 | - |
| 어빌리티 스톤 기본 공격력 | `0.015` | `engravings.ArkPassiveEffects[].AbilityStoneLevel`<br>각인 돌 레벨 합계=5<br>예시 임계값 합계 5 이상 → +1.5% | 예 | 예 | 예 | - |
| 세상을 구하는 빛 6세트 (18각성합계) | `0.07` | `cards.Effects[0].Items[4]`<br>성속성 피해 +7.00% | 예 | 예 | 예 | - |
| 세상을 구하는 빛 6세트 (24각성합계) | `0.04` | `cards.Effects[0].Items[5]`<br>성속성 피해 +4.00% | 예 | 예 | 예 | - |
| 세상을 구하는 빛 6세트 (30각성합계) | `0.04` | `cards.Effects[0].Items[6]`<br>성속성 피해 +4.00% | 예 | 예 | 예 | - |
| 일반 보석 몰아치기 재사용 대기시간 감소 | `0.22` | `gems.Gems[0].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 몰아치 | 예 | 아니오 | 아니오 | 1회 피해에는 영향이 없고 로테이션/DPS에서 사용 |
| <P ALIGN='CENTER'><FONT COLOR='#FA5D00'>9레벨 광휘의 보석</FONT></P> 기본 공격력 | `0.01` | `gems.Gems[0].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 몰아치 | 예 | 예 | 예 | - |
| 일반 보석 회오리 걸음 피해 | `0.40` | `gems.Gems[1].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 회오리 | 예 | 아니오 | 아니오 | 현재 계산 스킬은 공간 가르기 |
| <P ALIGN='CENTER'><FONT COLOR='#FA5D00'>9레벨 광휘의 보석</FONT></P> 기본 공격력 | `0.01` | `gems.Gems[1].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 회오리 | 예 | 예 | 예 | - |
| 일반 보석 칼바람 피해 | `0.40` | `gems.Gems[2].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 칼바람 | 예 | 아니오 | 아니오 | 현재 계산 스킬은 공간 가르기 |
| <P ALIGN='CENTER'><FONT COLOR='#FA5D00'>9레벨 광휘의 보석</FONT></P> 기본 공격력 | `0.01` | `gems.Gems[2].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 칼바람 | 예 | 예 | 예 | - |
| 일반 보석 칼바람 재사용 대기시간 감소 | `0.22` | `gems.Gems[3].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 칼바람 | 예 | 아니오 | 아니오 | 1회 피해에는 영향이 없고 로테이션/DPS에서 사용 |
| <P ALIGN='CENTER'><FONT COLOR='#FA5D00'>9레벨 광휘의 보석</FONT></P> 기본 공격력 | `0.01` | `gems.Gems[3].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 칼바람 | 예 | 예 | 예 | - |
| 일반 보석 몰아치기 피해 | `0.40` | `gems.Gems[4].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 몰아치 | 예 | 아니오 | 아니오 | 현재 계산 스킬은 공간 가르기 |
| <P ALIGN='CENTER'><FONT COLOR='#FA5D00'>9레벨 광휘의 보석</FONT></P> 기본 공격력 | `0.01` | `gems.Gems[4].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 몰아치 | 예 | 예 | 예 | - |
| 일반 보석 바람송곳 피해 | `0.40` | `gems.Gems[5].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 바람송 | 예 | 아니오 | 아니오 | 현재 계산 스킬은 공간 가르기 |
| <P ALIGN='CENTER'><FONT COLOR='#FA5D00'>9레벨 광휘의 보석</FONT></P> 기본 공격력 | `0.01` | `gems.Gems[5].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 바람송 | 예 | 예 | 예 | - |
| 일반 보석 회오리 걸음 재사용 대기시간 감소 | `0.22` | `gems.Gems[6].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 회오리 | 예 | 아니오 | 아니오 | 1회 피해에는 영향이 없고 로테이션/DPS에서 사용 |
| <P ALIGN='CENTER'><FONT COLOR='#FA5D00'>9레벨 광휘의 보석</FONT></P> 기본 공격력 | `0.01` | `gems.Gems[6].Tooltip`<br>9레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 9 효과 [기상술사] 회오리 | 예 | 예 | 예 | - |
| 일반 보석 바람송곳 재사용 대기시간 감소 | `0.20` | `gems.Gems[7].Tooltip`<br>8레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 8 효과 [기상술사] 바람송 | 예 | 아니오 | 아니오 | 1회 피해에는 영향이 없고 로테이션/DPS에서 사용 |
| <P ALIGN='CENTER'><FONT COLOR='#FA5D00'>8레벨 광휘의 보석</FONT></P> 기본 공격력 | `0.008` | `gems.Gems[7].Tooltip`<br>8레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 8 효과 [기상술사] 바람송 | 예 | 예 | 예 | - |
| 일반 보석 싹쓸바람 재사용 대기시간 감소 | `0.20` | `gems.Gems[8].Tooltip`<br>8레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 8 효과 [기상술사] 싹쓸바 | 예 | 아니오 | 아니오 | 1회 피해에는 영향이 없고 로테이션/DPS에서 사용 |
| <P ALIGN='CENTER'><FONT COLOR='#FA5D00'>8레벨 광휘의 보석</FONT></P> 기본 공격력 | `0.008` | `gems.Gems[8].Tooltip`<br>8레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 8 효과 [기상술사] 싹쓸바 | 예 | 예 | 예 | - |
| 일반 보석 마주바람 피해 | `0.36` | `gems.Gems[9].Tooltip`<br>8레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 8 효과 [기상술사] 마주바 | 예 | 아니오 | 아니오 | 현재 계산 스킬은 공간 가르기 |
| <P ALIGN='CENTER'><FONT COLOR='#FA5D00'>8레벨 광휘의 보석</FONT></P> 기본 공격력 | `0.008` | `gems.Gems[9].Tooltip`<br>8레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 8 효과 [기상술사] 마주바 | 예 | 예 | 예 | - |
| 일반 보석 싹쓸바람 피해 | `0.36` | `gems.Gems[10].Tooltip`<br>8레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 8 효과 [기상술사] 싹쓸바 | 예 | 아니오 | 아니오 | 현재 계산 스킬은 공간 가르기 |
| <P ALIGN='CENTER'><FONT COLOR='#FA5D00'>8레벨 광휘의 보석</FONT></P> 기본 공격력 | `0.008` | `gems.Gems[10].Tooltip`<br>8레벨 광휘의 보석 유물 보석 아이템 레벨 1640 (티어 4) 장착중 장착, 합성, 조율 가능 아이템 레벨 1640 거래 제한 아이템 레벨 1640 캐릭터 귀속됨 \|거래 불가 보석 레벨 8 효과 [기상술사] 싹쓸바 | 예 | 예 | 예 | - |
| 질풍노도 | `1` | `arkPassive.Effects[0]`<br>깨달음 1티어 질풍노도 Lv.1 질풍노도 아크 패시브 레벨 1 깨달음 여우비가 강화되어 우산 스킬로 적용된다. 여우비 상태 진입 시 30.0초 동안 지속되는 '질풍노도' 버프와 4.0초 동안 지속되는 기류 보호막이  | 예 | 예 | 예 | - |
| 환기 | `3` | `arkPassive.Effects[1]`<br>깨달음 2티어 환기 Lv.3 환기 아크 패시브 레벨 3 깨달음 우산 스킬을 사용하고 4초 이내에 우산 스킬을 사용하면 최대 빗방울 게이지의 12.0%를 회복한다.\|\| | 예 | 아니오 | 아니오 | 자원 회복은 1회 피해에 직접 영향 없음 |
| 기민함 | `3` | `arkPassive.Effects[2]`<br>깨달음 3티어 기민함 Lv.3 기민함 아크 패시브 레벨 3 깨달음 기본 공격 속도 증가량 %의 120.0% 만큼 치명타 피해량이 증가하고 기본 이동 속도 증가량 %의 30.0% 만큼 치명타 적중률이 증가한다.\|\| | 예 | 예 | 예 | - |
| 바람의 길 | `2` | `arkPassive.Effects[3]`<br>깨달음 4티어 바람의 길 Lv.2 바람의 길 아크 패시브 레벨 2 깨달음 여우비 사용 시 30.0초간 바람의 길 효과를 획득한다. 바람의 길 : 우산 스킬의 피해량이 2.4% 증가한다.\|\| | 예 | 아니오 | 아니오 | 우산 스킬 태그 필요; 현재 계산 스킬은 공간 가르기 |
| 공간 가르기 | `3` | `arkPassive.Effects[4]`<br>깨달음 4티어 공간 가르기 Lv.3 공간 가르기 아크 패시브 레벨 3 깨달음 X키를 눌러 공간 가르기를 사용할 수 있게 되고 기본 및 여우비 상태에서 사용할 수 있다. 공간 가르기가 주는 피해가 200.0% 증가한다 | 예 | 예 | 예 | - |
| 치명 | `14` | `arkPassive.Effects[5]`<br>진화 1티어 치명 Lv.14 치명 아크 패시브 레벨 14 진화 치명이 700 증가합니다.\|\| | 예 | 아니오 | 아니오 | 최종 프로필 치명 및 치명타율에 이미 반영 |
| 신속 | `26` | `arkPassive.Effects[6]`<br>진화 1티어 신속 Lv.26 신속 아크 패시브 레벨 26 진화 신속이 1300 증가합니다.\|\| | 예 | 아니오 | 아니오 | 최종 프로필 신속 및 속도 환산값에 이미 반영 |
| 예리한 감각 | `1` | `arkPassive.Effects[7]`<br>진화 2티어 예리한 감각 Lv.1 예리한 감각 아크 패시브 레벨 1 진화 치명타 적중률이 4.0% 증가하고, 진화형 피해가 5.0% 증가합니다.\|\| | 예 | 예 | 예 | - |
| 한계 돌파 | `2` | `arkPassive.Effects[8]`<br>진화 2티어 한계 돌파 Lv.2 한계 돌파 아크 패시브 레벨 2 진화 진화형 피해가 20.0% 증가합니다.\|\| | 예 | 예 | 예 | - |
| 무한한 마력 | `1` | `arkPassive.Effects[9]`<br>진화 3티어 무한한 마력 Lv.1 무한한 마력 아크 패시브 레벨 1 진화 진화형 피해가 8.0% 증가하고, 마나 스킬의 재사용 대기시간이 7.0% 감소, 마나 소모량이 8.0% 감소합니다.\|\| | 예 | 예 | 예 | - |
| 혼신의 강타 | `1` | `arkPassive.Effects[10]`<br>진화 3티어 혼신의 강타 Lv.1 혼신의 강타 아크 패시브 레벨 1 진화 치명타 적중률이 12.0% 증가하고, 진화형 피해가 2.0% 증가합니다.\|\| | 예 | 예 | 예 | - |
| 회심 | `1` | `arkPassive.Effects[11]`<br>진화 4티어 회심 Lv.1 회심 아크 패시브 레벨 1 진화 공격이 치명타로 적중 시 적에게 주는 피해가 12.0% 증가하며, 받는 피해가 4.0% 감소합니다.\|\| | 예 | 예 | 예 | - |
| 달인 | `1` | `arkPassive.Effects[12]`<br>진화 4티어 달인 Lv.1 달인 아크 패시브 레벨 1 진화 받는 피해가 4.0% 감소하며, 이동기 및 기상기를 제외한 스킬 사용시 10초간 '달인' 효과를 얻습니다. 달인 : 치명타 적중률 +1.4% / 추가 피해  | 예 | 예 | 예 | - |
| 음속 돌파 | `2` | `arkPassive.Effects[13]`<br>진화 5티어 음속 돌파 Lv.2 음속 돌파 아크 패시브 레벨 2 진화 공격 적중 시, 공격 속도 및 이동 속도 증가량의 10.0% 만큼 진화형 피해가 증가합니다. 공격 및 이동 속도가 모두 상한을 초과했다면, 진화형 | 예 | 예 | 예 | - |
| 풀려난 힘 | `5` | `arkPassive.Effects[14]`<br>도약 1티어 풀려난 힘 Lv.5 풀려난 힘 아크 패시브 레벨 5 도약 초각성 스킬이 적에게 주는 피해가 15.0% 증가한다.\|\| | 예 | 아니오 | 아니오 | 초각성 스킬 태그 필요; 현재 계산 스킬은 공간 가르기 |
| 잠재력 해방 | `4` | `arkPassive.Effects[15]`<br>도약 1티어 잠재력 해방 Lv.4 잠재력 해방 아크 패시브 레벨 4 도약 초각성 스킬의 재사용 대기 시간이 8.0% 감소한다.\|\| | 예 | 아니오 | 아니오 | 초각성 스킬 쿨타임 효과는 로테이션/DPS 대상 |
| 즉각적인 주문 | `2` | `arkPassive.Effects[16]`<br>도약 1티어 즉각적인 주문 Lv.2 즉각적인 주문 아크 패시브 레벨 2 도약 초각성 스킬의 시전 속도가 8.0% 증가하고, 마나 소모량이 60.0% 감소한다.\|\| | 예 | 아니오 | 아니오 | 시전 속도·마나 효과는 1회 피해에 직접 배율 없음 |
| 단련된 가르기 | `3` | `arkPassive.Effects[17]`<br>도약 2티어 단련된 가르기 Lv.3 단련된 가르기 아크 패시브 레벨 3 도약 우레바람이 일반 조작으로 변경되고, 피해량이 75.0% 증가한다.\|\| | 예 | 아니오 | 아니오 | 우레바람 전용 효과; 현재 계산 스킬은 공간 가르기 |
| 진화 카르마 진화형 피해 | `0.06` | `arkPassive.Points[0]`<br>6랭크 21레벨<br>랭크·레벨 전체 표가 없어 예시 DB 사용 | 아니오 | 예 | 예 | - |
| 깨달음 카르마 무기 공격력 | `0.027` | `arkPassive.Points[1]`<br>6랭크 27레벨<br>랭크·레벨 전체 표가 없어 예시 DB 사용 | 아니오 | 예 | 예 | - |
| 급소 노출 | `0.10` | `combatSkills[4].Tripods[2]`<br>공격 적중 시 대상이 자신 및 파티원에게 받는 치명타 저항률이 12.0초간 10.0% 감소한다.<br>항상 적용 규칙 | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.004` | `arkGrid.Slots[0].Gems[0].Tooltip`<br>질서의 젬 : 안정 고대 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 19 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 질서 포인트 : 4 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0024` | `arkGrid.Slots[0].Gems[1].Tooltip`<br>질서의 젬 : 안정 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 14 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 질서 포인트 : 5 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 attackPowerPercent | `0.0018` | `arkGrid.Slots[0].Gems[2].Tooltip`<br>질서의 젬 : 견고 고대 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 19 젬 효과 필요 의지력 : 4 (기본 값 9 – 의지력 효율 5) 질서 포인트 : 5 [아군 공격 강 | 예 | 예 | 예 | - |
| 아크그리드 젬 attackPowerPercent | `0.0003` | `arkGrid.Slots[0].Gems[3].Tooltip`<br>질서의 젬 : 견고 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 12 젬 효과 필요 의지력 : 7 (기본 값 9 – 의지력 효율 2) 질서 포인트 : 4 [공격력] Lv | 예 | 예 | 예 | - |
| 아크그리드 젬 bossDamagePercent | `0.0041` | `arkGrid.Slots[0].Gems[3].Tooltip`<br>질서의 젬 : 견고 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 12 젬 효과 필요 의지력 : 7 (기본 값 9 – 의지력 효율 2) 질서 포인트 : 4 [공격력] Lv | 예 | 예 | 예 | - |
| 아크그리드 젬 attackPowerPercent | `0.0003` | `arkGrid.Slots[1].Gems[0].Tooltip`<br>질서의 젬 : 안정 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 13 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 질서 포인트 : 5 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0016` | `arkGrid.Slots[1].Gems[0].Tooltip`<br>질서의 젬 : 안정 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 13 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 질서 포인트 : 5 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 attackPowerPercent | `0.0018` | `arkGrid.Slots[1].Gems[1].Tooltip`<br>질서의 젬 : 안정 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 16 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 질서 포인트 : 5 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0008` | `arkGrid.Slots[1].Gems[1].Tooltip`<br>질서의 젬 : 안정 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 16 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 질서 포인트 : 5 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 bossDamagePercent | `0.0033` | `arkGrid.Slots[1].Gems[2].Tooltip`<br>질서의 젬 : 견고 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 18 젬 효과 필요 의지력 : 4 (기본 값 9 – 의지력 효율 5) 질서 포인트 : 4 [보스 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0024` | `arkGrid.Slots[1].Gems[3].Tooltip`<br>질서의 젬 : 불변 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 16 젬 효과 필요 의지력 : 5 (기본 값 10 – 의지력 효율 5) 질서 포인트 : 4 [추가 피해] | 예 | 예 | 예 | - |
| 아크그리드 젬 bossDamagePercent | `0.0033` | `arkGrid.Slots[1].Gems[3].Tooltip`<br>질서의 젬 : 불변 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 16 젬 효과 필요 의지력 : 5 (기본 값 10 – 의지력 효율 5) 질서 포인트 : 4 [추가 피해] | 예 | 예 | 예 | - |
| 아크그리드 젬 bossDamagePercent | `0.0025` | `arkGrid.Slots[2].Gems[0].Tooltip`<br>질서의 젬 : 견고 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 14 젬 효과 필요 의지력 : 4 (기본 값 9 – 의지력 효율 5) 질서 포인트 : 5 [아군 피해 강 | 예 | 예 | 예 | - |
| 아크그리드 젬 attackPowerPercent | `0.0007` | `arkGrid.Slots[2].Gems[1].Tooltip`<br>질서의 젬 : 안정 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 13 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 질서 포인트 : 5 [낙인력] Lv | 예 | 예 | 예 | - |
| 아크그리드 젬 bossDamagePercent | `0.0016` | `arkGrid.Slots[2].Gems[2].Tooltip`<br>질서의 젬 : 견고 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 17 젬 효과 필요 의지력 : 4 (기본 값 9 – 의지력 효율 5) 질서 포인트 : 5 [보스 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 attackPowerPercent | `0.0011` | `arkGrid.Slots[2].Gems[3].Tooltip`<br>질서의 젬 : 안정 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 14 젬 효과 필요 의지력 : 4 (기본 값 8 – 의지력 효율 4) 질서 포인트 : 5 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0016` | `arkGrid.Slots[2].Gems[3].Tooltip`<br>질서의 젬 : 안정 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 질서 젬 포인트 : 14 젬 효과 필요 의지력 : 4 (기본 값 8 – 의지력 효율 4) 질서 포인트 : 5 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 attackPowerPercent | `0.0011` | `arkGrid.Slots[3].Gems[0].Tooltip`<br>혼돈의 젬 : 침식 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 14 젬 효과 필요 의지력 : 4 (기본 값 8 – 의지력 효율 4) 혼돈 포인트 : 4 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0024` | `arkGrid.Slots[3].Gems[0].Tooltip`<br>혼돈의 젬 : 침식 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 14 젬 효과 필요 의지력 : 4 (기본 값 8 – 의지력 효율 4) 혼돈 포인트 : 4 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 attackPowerPercent | `0.0014` | `arkGrid.Slots[3].Gems[1].Tooltip`<br>혼돈의 젬 : 침식 고대 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 19 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 혼돈 포인트 : 5 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.004` | `arkGrid.Slots[3].Gems[1].Tooltip`<br>혼돈의 젬 : 침식 고대 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 19 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 혼돈 포인트 : 5 [추가 피해]  | 예 | 예 | 예 | - |
| 아크그리드 젬 attackPowerPercent | `0.0011` | `arkGrid.Slots[3].Gems[2].Tooltip`<br>혼돈의 젬 : 침식 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 14 젬 효과 필요 의지력 : 4 (기본 값 8 – 의지력 효율 4) 혼돈 포인트 : 5 [공격력] Lv | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0016` | `arkGrid.Slots[3].Gems[2].Tooltip`<br>혼돈의 젬 : 침식 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 14 젬 효과 필요 의지력 : 4 (기본 값 8 – 의지력 효율 4) 혼돈 포인트 : 5 [공격력] Lv | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0032` | `arkGrid.Slots[3].Gems[3].Tooltip`<br>혼돈의 젬 : 붕괴 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 18 젬 효과 필요 의지력 : 6 (기본 값 10 – 의지력 효율 4) 혼돈 포인트 : 5 [추가 피해] | 예 | 예 | 예 | - |
| 아크그리드 젬 bossDamagePercent | `0.0041` | `arkGrid.Slots[3].Gems[3].Tooltip`<br>혼돈의 젬 : 붕괴 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 18 젬 효과 필요 의지력 : 6 (기본 값 10 – 의지력 효율 4) 혼돈 포인트 : 5 [추가 피해] | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0032` | `arkGrid.Slots[4].Gems[0].Tooltip`<br>혼돈의 젬 : 침식 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 15 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 혼돈 포인트 : 5 [아군 피해 강 | 예 | 예 | 예 | - |
| 아크그리드 젬 attackPowerPercent | `0.0018` | `arkGrid.Slots[4].Gems[1].Tooltip`<br>혼돈의 젬 : 왜곡 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 18 젬 효과 필요 의지력 : 4 (기본 값 9 – 의지력 효율 5) 혼돈 포인트 : 5 [공격력] Lv | 예 | 예 | 예 | - |
| 아크그리드 젬 bossDamagePercent | `0.0025` | `arkGrid.Slots[4].Gems[1].Tooltip`<br>혼돈의 젬 : 왜곡 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 18 젬 효과 필요 의지력 : 4 (기본 값 9 – 의지력 효율 5) 혼돈 포인트 : 5 [공격력] Lv | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0032` | `arkGrid.Slots[4].Gems[2].Tooltip`<br>혼돈의 젬 : 붕괴 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 15 젬 효과 필요 의지력 : 5 (기본 값 10 – 의지력 효율 5) 혼돈 포인트 : 5 [추가 피해] | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0024` | `arkGrid.Slots[4].Gems[3].Tooltip`<br>혼돈의 젬 : 붕괴 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 17 젬 효과 필요 의지력 : 5 (기본 값 10 – 의지력 효율 5) 혼돈 포인트 : 5 [보스 피해] | 예 | 예 | 예 | - |
| 아크그리드 젬 bossDamagePercent | `0.0033` | `arkGrid.Slots[4].Gems[3].Tooltip`<br>혼돈의 젬 : 붕괴 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 17 젬 효과 필요 의지력 : 5 (기본 값 10 – 의지력 효율 5) 혼돈 포인트 : 5 [보스 피해] | 예 | 예 | 예 | - |
| 아크그리드 젬 attackPowerPercent | `0.0018` | `arkGrid.Slots[5].Gems[0].Tooltip`<br>혼돈의 젬 : 침식 고대 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 20 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 혼돈 포인트 : 5 [공격력] Lv | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.004` | `arkGrid.Slots[5].Gems[0].Tooltip`<br>혼돈의 젬 : 침식 고대 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 20 젬 효과 필요 의지력 : 3 (기본 값 8 – 의지력 효율 5) 혼돈 포인트 : 5 [공격력] Lv | 예 | 예 | 예 | - |
| 아크그리드 젬 bossDamagePercent | `0.0041` | `arkGrid.Slots[5].Gems[1].Tooltip`<br>혼돈의 젬 : 왜곡 고대 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 19 젬 효과 필요 의지력 : 4 (기본 값 9 – 의지력 효율 5) 혼돈 포인트 : 5 [아군 공격 강 | 예 | 예 | 예 | - |
| 아크그리드 젬 bossDamagePercent | `0.0041` | `arkGrid.Slots[5].Gems[2].Tooltip`<br>혼돈의 젬 : 왜곡 유물 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 18 젬 효과 필요 의지력 : 4 (기본 값 9 – 의지력 효율 5) 혼돈 포인트 : 3 [아군 피해 강 | 예 | 예 | 예 | - |
| 아크그리드 젬 additionalDamagePercent | `0.0024` | `arkGrid.Slots[5].Gems[3].Tooltip`<br>혼돈의 젬 : 붕괴 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 15 젬 효과 필요 의지력 : 6 (기본 값 10 – 의지력 효율 4) 혼돈 포인트 : 4 [추가 피해] | 예 | 예 | 예 | - |
| 아크그리드 젬 bossDamagePercent | `0.0033` | `arkGrid.Slots[5].Gems[3].Tooltip`<br>혼돈의 젬 : 붕괴 전설 아크 그리드 젬 가공 완료 \|거래 불가 젬 기본 정보 젬 타입 : 혼돈 젬 포인트 : 15 젬 효과 필요 의지력 : 6 (기본 값 10 – 의지력 효율 4) 혼돈 포인트 : 4 [추가 피해] | 예 | 예 | 예 | - |
| 아크그리드 포인트 추가 피해 additionalDamagePercent | `0.0396` | `arkGrid.Effects[0].Tooltip`<br>추가 피해 +3.96% | 예 | 예 | 예 | - |
| 아크그리드 포인트 공격력 attackPowerPercent | `0.0135` | `arkGrid.Effects[4].Tooltip`<br>공격력 +1.35% | 예 | 예 | 예 | - |
| 아크그리드 포인트 보스 피해 bossDamagePercent | `0.0366` | `arkGrid.Effects[5].Tooltip`<br>보스 등급 이상 몬스터에게 주는 피해 +3.66% | 예 | 예 | 예 | - |

## 3. 계산 과정

모든 중간값은 소수로 유지했습니다. 아래 세 최종 표시 피해에서만 `floor`를 적용했습니다.

### 3.1 주스탯

`기초 지능 = 701492 + 477 + 680 + 976 = 703625`

`아바타+펫 = 8.0000% + 1.0000% = 9.0000%`

`최종 지능 원시값 = 703625 × (1 + 0.09) = 766951.25`

`규칙 적용 최종 지능 = 766951.25`

### 3.2 무기 공격력

`무기 공격력 증가 = 6.0000% + 2.7000% = 8.7000%`

`무기 공격력 소계 = 기본 241367 + 평면 증가 0 = 241367`

`최종 무기 공격력 원시값 = 241367 × (1 + 0.087) = 262365.929`

`규칙 적용 최종 무기 공격력 = 262365.929`

### 3.3 기본 공격력과 최종 공격력

`sqrt(766951.25 × 262365.929 ÷ 6) = 183131.0447029491001332609376936259758753`

`기본 공격력 증가 = 보석 10.2000% + 스톤 1.5000% = 11.7000%`

`루트 공격력 × 기본 공격력% = 183131.0447029491001332609376936259758753 × (1 + 0.117) = 204557.3769331941448488524674037802150527`

`기본 공격력 단계 = 204557.3769331941448488524674037802150527 + 공격력 평면 증가 0 = 204557.3769331941448488524674037802150527`

`공격력 증가 = 장신구 1.9000% + 아드레날린 10.3800% + 아크그리드 2.6700% = 14.9500%`

`최종 공격력 원시값 = 204557.3769331941448488524674037802150527 × (1 + 0.1495) = 235138.7047847066695037559112806453572031`

`규칙 적용 최종 공격력 = 235138.7047847066695037559112806453572031`

API 프로필 공격력은 `217160`이며 계산값과의 차이는 `17978.7047847066695037559112806453572031`입니다.

두 값이 불일치하므로 위 재구성 값과 계산 과정은 검산용으로 보존하고, 이후 스킬 피해 계산에는 API 프로필 공격력 `217160`을 사용합니다.

아크그리드 공격력은 위 재구성 공격력의 `아크그리드` 항에 분류해 반영했습니다. 프로필 공격력으로 전환한 뒤에는 조회 시점 프로필에 이미 포함된 공격력 효과를 다시 곱하지 않아 중복 적용을 방지합니다.

### 3.4 공격·이동속도 및 음속 돌파

공격속도 구성:

`1 + 신속 0.2824 + 질량 증가 (-0.10) + 전투 축복 0.09 + 만찬 0.05 + 질풍노도 0.12 = 1.4424`

- 원시 공격속도 증가량: `44.2400%`
- 140% 상한 적용 공격속도: `1.4`
- 상한 적용 증가량: `40.0000%`

이동속도 구성:

`1 + 신속 0.2824 + 전투 축복 0.09 + 만찬 0.05 + 질풍노도 0.12 = 1.5424`

- 원시 이동속도 증가량: `54.2400%`
- 140% 상한 적용 이동속도: `1.4`
- 상한 적용 증가량: `40.0000%`

음속 돌파 Lv.2 상세:

`기본분 = 0.10 × [min(0.4424, 0.4) + min(0.5424, 0.4)]`

`= 0.10 × (0.4 + 0.4) = 0.080 (8.0000%)`

- 공격·이동속도 모두 상한 초과: `예`
- 양쪽 상한 초과 보너스: `8.0000%`

`초과분 = 0.30 × [0.0424 + 0.1424] = 0.055440 (5.5440%)`

`상한 적용 전 합계 = 0.080 + 0.08 + 0.055440 = 0.215440`

`최종 음속 돌파 = min(0.215440, 0.24) = 0.215440 (21.5440%)`

- 최대값 제한 발동: `아니오`

### 3.5 추가 피해

`1 + 무기 0.30 + 목걸이 0.026 + 기타 장비 0.035 + 아크 패시브 0.085 + 펫 0.01 + 아크그리드 0.0788 = 1.5348`

### 3.5.1 일반 보석 스킬 효과

- 대상 스킬: `공간 가르기`
- 스킬 피해 증가: `0.0000%` (아래 독립 피해 소제목에 적용)
- 재사용 대기시간 감소: `0.0000%`
- 쿨다운 배율: `1` (1회 피해에는 미적용, 로테이션/DPS 입력으로 보존)

### 3.6 서로 곱하는 피해 소제목

| 소제목 | 증가율 | 배율 |
|---|---:|---:|
| 원한 | 24.0000% | 1.24 |
| 질량 증가 | 19.0000% | 1.19 |
| 타격의 대가 | 17.0000% | 1.17 |
| 진화형 피해 | 62.5440% | 1.625440 |
| 악마 추가 피해 | 7.0000% | 1.070 |
| 카드 피해 | 15.0000% | 1.15 |
| 돌격대장 | 18.4000% | 1.184 |
| 공간 가르기 | 200.0000% | 3.0 |
| 목걸이 적에게 주는 피해 | 1.2000% | 1.012 |
| 팔찌 적에게 주는 피해 | 4.5000% | 1.045 |
| 기타 적에게 주는 피해 | 0.0000% | 1 |
| 팔찌 비방향성 피해 | 0.0000% | 1 |
| 아크그리드 보스 피해 | 7.2800% | 1.0728 |
| 일반 보석 공간 가르기 피해 | 0.0000% | 1 |

`전체 소제목 배율 = 1.24 × 1.19 × 1.17 × 1.625440 × 1.070 × 1.15 × 1.184 × 3.0 × 1.012 × 1.045 × 1 × 1 × 1.0728 × 1 = 13.9153967804656091835349401600000`

진화형 피해 내부 합산:

- 예리한 감각: 5.0000%
- 한계 돌파: 20.0000%
- 무한한 마력: 8.0000%
- 혼신의 강타: 2.0000%
- 진화 카르마: 6.0000%
- 음속 돌파 Lv.2: 21.5440%

### 3.7 적 보정

`방어력 보정 = 6500 ÷ (6500 + 5850) = 0.5263157894736842105263157894736842105263`

`적 받는 피해 배율 = 0.76`

### 3.8 비치명타

| 타격 | 모션 계수 | 모션 상수 | 사용 공격력 | 스킬 본체 |
|---|---:|---:|---:|---:|
| 1타 | 40.07 | 6117 | 217160 (API_PROFILE) | 8707718.20 |
| 2타 | 93.50 | 14283 | 217160 (API_PROFILE) | 20318743.00 |

`스킬 본체 합계 = 8707718.20 + 20318743.00 = 29026461.20`

`비치명타 원시값 = 29026461.20 × 1.5348 × 13.9153967804656091835349401600000 × 0.76 × 0.5263157894736842105263157894736842105263 = 247971327.8067265494669157210611650553446`

`floor(247971327.8067265494669157210611650553446) = 247,971,327`

### 3.9 치명타와 기대 피해

- 원시 치명타율: `95.7600%`
- 상한 적용 치명타율: `95.7600%`
- 치명타 피해 배율: `2.596`
- 치명타 시 피해 증가 배율: `1.13680`

`치명타 원시값 = 247971327.8067265494669157210611650553446 × 2.596 × 1.13680 = 731796318.9499827807626374992592550010414`

`기대 피해 원시값 = 731796318.9499827807626374992592550010414 × 0.9576 + 247971327.8067265494669157210611650553446 × (1 - 0.9576) = 711282139.3255087165556988958636559873438`

## 4. 계산 결과

| 타격 | 비치명타 | 치명타 | 기대 피해 |
|---|---:|---:|---:|
| 1타 | 74,389,517 | 219,533,345 | 213,379,246 |
| 2타 | 173,581,810 | 512,262,973 | 497,902,892 |

- 비치명타 피해: **247,971,327**
- 치명타 피해: **731,796,318**
- 기대 피해: **711,282,139**
- 치명타율: **95.7600%**

### 아크그리드 전체 효과 적용 전후

프로필 공격력이 재구성 공격력과 달라 두 계산 모두 프로필 공격력을 사용합니다. 따라서 이 표의 차이는 추가 피해·보스 피해 등 직접 피해 그룹의 영향이며, 아크그리드 공격력의 단독 영향도 비교는 아닙니다.

| 결과 | 미적용 | 적용 | 차이 |
|---|---:|---:|---:|
| 비치명타 | 219,276,599 | 247,971,327 | +28,694,728 |
| 치명타 | 647,114,364 | 731,796,318 | +84,681,954 |
| 기대 피해 | 628,974,043 | 711,282,139 | +82,308,096 |

### 스킬 범위 판정

- 스킬 태그: `ENLIGHTENMENT_X_SKILL, NON_DIRECTIONAL` (PROVISIONAL)
- 바람의 길 2.4000%: **제외** (우산 스킬 태그 필요)
- 공간 가르기 200.0000%: **적용** (공간 가르기 전용 아크 패시브)
- 풀려난 힘 15.0000%: **제외** (초각성 스킬 태그 필요)
- 단련된 가르기 75.0000%: **제외** (우레바람 전용 효과)
- `공간 가르기` 피해 +200%는 1타와 2타에 동일하게 적용했습니다.
- `바람의 길`, `풀려난 힘`, `단련된 가르기`는 현재 스킬 태그와 전용 범위가 맞지 않아 제외했습니다.
- 공식 API에 방향성 분류가 없어 `타격의 대가` 적용은 비방향성 스킬이라는 잠정 가정입니다.

## 5. 제외 및 경고

### 제외된 데이터

- `avatars[7]` 무기 아바타 중복 아바타: 부위별 효과 아바타 하나만 선택
- `avatars[8]` 상의 아바타 중복 아바타: 부위별 효과 아바타 하나만 선택
- `avatars[9]` 하의 아바타 중복 아바타: 부위별 효과 아바타 하나만 선택
- `arkGrid.Slots[0].Gems[0].Tooltip` 아군 피해량 강화: 서포터 옵션은 딜러 개인 피해에서 제외
- `arkGrid.Slots[0].Gems[1].Tooltip` 낙인력: 서포터 옵션은 딜러 개인 피해에서 제외
- `arkGrid.Slots[0].Gems[2].Tooltip` 아군 공격력 강화: 서포터 옵션은 딜러 개인 피해에서 제외
- `arkGrid.Slots[1].Gems[2].Tooltip` 아군 공격력 강화: 서포터 옵션은 딜러 개인 피해에서 제외
- `arkGrid.Slots[2].Gems[0].Tooltip` 아군 피해량 강화: 서포터 옵션은 딜러 개인 피해에서 제외
- `arkGrid.Slots[2].Gems[1].Tooltip` 낙인력: 서포터 옵션은 딜러 개인 피해에서 제외
- `arkGrid.Slots[2].Gems[2].Tooltip` 아군 피해량 강화: 서포터 옵션은 딜러 개인 피해에서 제외
- `arkGrid.Slots[4].Gems[0].Tooltip` 아군 피해량 강화: 서포터 옵션은 딜러 개인 피해에서 제외
- `arkGrid.Slots[4].Gems[2].Tooltip` 아군 공격력 강화: 서포터 옵션은 딜러 개인 피해에서 제외
- `arkGrid.Slots[5].Gems[1].Tooltip` 아군 공격력 강화: 서포터 옵션은 딜러 개인 피해에서 제외
- `arkGrid.Slots[5].Gems[2].Tooltip` 아군 피해량 강화: 서포터 옵션은 딜러 개인 피해에서 제외
- `arkGrid.Effects[1]` 아군 피해 강화: 미적용
- `arkGrid.Effects[2]` 낙인력: 미적용
- `arkGrid.Effects[3]` 아군 공격 강화: 미적용

### 경고

- 진화 카르마 수치를 파싱하지 못해 예시값 +6.0%를 사용했습니다.
- 깨달음 카르마 수치를 파싱하지 못해 예시값 +2.7%를 사용했습니다.
- 현재 원정대 레벨은 281이지만 원정대/물약 주스탯은 current-v2.3.0 고정값 +680을 사용했습니다.
- 재구성 공격력과 API 프로필 공격력이 불일치하여 재구성 과정은 검산용으로 표시하고 이후 피해 계산에는 프로필 공격력을 사용했습니다.

## 6. 검증 결과

- 과거 스펙의 최종 피해와 회귀 비교하지 않았습니다.
- 원본 API 경로와 각 파싱값을 출처 표로 연결했습니다.
- 초월, 비활성 아크그리드 젬, 서포터 옵션, 미지원 효과는 제외 목록에서 확인할 수 있습니다.
- 아크그리드 활성 젬과 포인트 효과의 적용 전후 계산을 별도로 수행했습니다.
- 출처마다 parsed / eligible / applied / excludedReason 상태를 분리했습니다.
- fallback 사용 내역은 파싱 JSON의 `fallbacks`와 계산별 `provenance.fallbacks`에 구조화했습니다.
- `공간가르기` 입력은 결과에서 `공간 가르기`로 정규화했습니다.
- 최종 비치명타·치명타·기대 피해 외에는 버림을 적용하지 않았습니다.
