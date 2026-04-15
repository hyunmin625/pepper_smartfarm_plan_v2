# Site Scope Baseline

이 문서는 `1.1 현장 범위 확정`의 기준값을 고정한다. 현재 기준 사이트는 실증 대상 1개 온실이며, 품종은 건고추/고춧가루용 적고추 계열로 좁혀 운영한다.

## 1. 대상 온실

- 대상 온실 수: `1동`
- 시설 형태: `300평 연동형 비닐온실`
- 운영 방식: `대형 온실 1개를 주 설비로 운영`
- 기준 site_id: `gh-01`
- 면적 환산: 약 `991㎡`

논리 zone은 물리적으로는 1개 대형 온실이지만, 수집/제어/평가를 위해 아래처럼 나눈다.

- `gh-01-zone-a`
- `gh-01-zone-b`
- `gh-01-outside`
- `gh-01-nutrient-room`
- `gh-01-dry-room`

## 2. 품종 범위

- 작물 범위: `적고추(건고추, 고춧가루용)`
- 최종 1품종은 종자 공급 가능 여부와 병해 이력 확인 후 결정한다.
- 현재 AI/정책/평가 기준 품종은 아래 shortlist로 둔다.

### 1차 shortlist

1. `왕조`
   - 건조가 쉽고 착색이 빠르며 건고추 품질이 우수한 품종으로 소개됨
   - 탄저병·역병 계통 저항성과 재배 안정성이 강조됨
2. `칼탄열풍`
   - 건고추용 복합내병계 품종으로 소개됨
   - 바이러스, 탄저병, 역병 대응과 높은 착과력이 장점으로 제시됨
3. `조생강탄`
   - 숙기가 빠른 조생 건고추용 품종으로 소개됨
   - 강한 매운맛, 균일한 과형, 건과 품질이 장점으로 제시됨

### 기본 추천

- 기본 기준 품종: `왕조`
- 추천 이유: 건조 용이성, 빠른 착색, 건고추/고춧가루용 적합성, 재배 안정성 설명이 가장 직접적이다.
- 대안:
  - 병해·바이러스 리스크 우선: `칼탄열풍`
  - 조생·강한 매운맛 우선: `조생강탄`

주의:

- `가장 많이 사용되는 품종`에 대한 공인 점유율 통계는 확인하지 못했다.
- 따라서 위 추천은 `2025-01-06`, `2025-01-16`, `2025-12-23` 기준 종자업계 추천 기사와 공식 재배 기준을 바탕으로 한 운영용 shortlist다.

## 3. 재배 환경/배지 기준

- 육묘용 block: `Grodan Delta 6.5`
- 본재배용 slab: `Grodan GT Master`
- 재배 방식: rockwool block/slab 기반 soilless 재배를 기본으로 둔다.
- 운전 전제:
  - 육묘 단계의 수분·온도·묘 소질 판단은 `Grodan Delta 6.5` block 기준으로 본다.
  - 정식 이후의 관수, 배액률, 급배액 EC 차이, 근권 회복 속도 판단은 `Grodan GT Master` slab 기준으로 본다.
  - 근권 센서 설치와 배액 수집 위치는 대표 slab 라인을 기준으로 설계한다.
  - `Delta 6.5`는 정식 전 wet weight와 saturation evidence를 같이 본다. `10x10x6.5cm` block 기준 wet weight `550g` 미만이거나 측정 자체가 없으면 자동 정식 판단 근거로 쓰지 않는다.
  - `GT Master`는 `WC + drain EC + drain timing/volume` 조합을 기본 근거로 쓴다.
  - `GT Master` 해석 기준:
    - `24시간 slab EC 변동폭 0.3~0.8mS/cm`: 대체로 안정권
    - `0.3 미만`: 과급수 또는 refresh 약화 watch
    - `1.0 초과`: 과소급수, refresh 실패, 염류 축적 watch
    - `first drain`이 잡혀도 EC가 안 떨어지면 `direct drainage` 가능성을 먼저 점검한다.

## 4. 낮/밤 운영 기준

공식 재배 자료 기준 운영 기본값은 아래처럼 둔다.

- 공통 생육 기본 목표:
  - 낮 `25~28℃`
  - 밤 `18℃ 전후`
- 허용 운전 밴드:
  - 낮 `25~30℃`
  - 밤 `18~20℃`
- 수정 불량 경계:
  - `30℃ 초과` 또는 `13℃ 이하`에서는 수정 불량과 기형과 위험이 커짐
- 정식기/시설재배 보수 기준:
  - 밤 온도는 `16℃ 이상` 유지
- 육묘 순화 기준:
  - 정식 `7~10일 전` 낮 `22~23℃`, 밤 `14~15℃`

## 5. 계절 운영 메모

- 겨울: 보온커튼 + 난방기로 밤 온도 유지
- 늦은 봄 이후: 환기량을 점진적으로 확대하고 개화/착과기 고온을 우선 억제
- 계절별 세부 운전 범위는 `docs/seasonal_operation_ranges.md`를 기준으로 사용한다.

## 6. 참고 출처

- 농사로 고추 작목 정보: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=101628&menuId=PS03172
- 농사로 시설고추 계절 관리 Q&A: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=205477&menuId=PS00078
- 농사로 고추 양액재배 현장 기술지원: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=259682&menuId=PS00077
- NH농우바이오 2026년 1월 추천품종 기사: https://www.newsam.co.kr/news/article.html?no=41799
- 아시아종묘 2025년 건고추 추천품종 기사: https://www.newsfm.kr/mobile/article.html?no=9677
