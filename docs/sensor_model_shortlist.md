# Sensor Model Shortlist

이 문서는 `1.2 센서 인벤토리 작성`의 모델 조사 결과를 정리한다. 목표는 최종 발주가 아니라, `gh-01` 300평 연동형 비닐온실에 맞는 1차 shortlist를 만드는 것이다.

## 선정 기준

- 온실 적용 사례 또는 제조사 명시 용도
- 연속 계측 가능 여부
- 통신 적합성 (`RS485/Modbus`, `SDI-12`, `Wi‑Fi/App` 등)
- 유지보수와 보정 난이도
- `sensor-ingestor`와 연결 가능한 현실성

## 1차 shortlist

| 항목 | 1차 추천 | 대안 | 비고 |
|---|---|---|---|
| 온도 센서 | `Vaisala HMP110` | `Vaisala WXT536` 외기 통합 사용 | 실내 존 온습도 기본 후보 |
| 습도 센서 | `Vaisala HMP110` | `Vaisala WXT536` 외기 통합 사용 | 온도와 동일 프로브 사용 |
| CO2 센서 | `Vaisala GMP252` | 동일 계열 + Indigo host | 온실/농업 용도 명시 |
| 광량(PAR) 센서 | `Apogee SQ-522-SS` | `Apogee SQ-422X-SS` | RS-485/Modbus 직접 연동 장점 |
| 배지 함수율 센서 | `METER TEROS 12` | 추가 캘리브레이션 전제 동일 모델 증설 | 함수율+온도+bulk EC 동시 확보 |
| EC 센서 | `Bluelab Guardian Inline Wi‑Fi` | `Bluelab Conductivity Pen` | 연속계측과 휴대형 점검 분리 |
| pH 센서 | `Bluelab Guardian Inline Wi‑Fi` | `Bluelab OnePen` | 연속계측과 휴대형 점검 분리 |
| 외기 센서 | `Vaisala WXT536` | AWS 급 상위 시스템은 추후 검토 | 풍속/풍향/강우/온습도 일체형 |

## 센서별 메모

### 1. 온도/습도

- 추천: `Vaisala HMP110`
- 이유:
  - 온실 적용 용도가 제조사 설명에 포함됨
  - `0~100 %RH`, `-40~+80℃` 범위
  - 내구성과 정확도가 안정적임
- 주의:
  - 실내 존 센서로는 적합하지만, 외기 풍속/강우는 별도 외기 센서가 필요하다.

### 2. CO2

- 추천: `Vaisala GMP252`
- 이유:
  - 제조사가 농업/온실 용도를 직접 명시
  - `0~10,000 ppm`, 필요 시 `30,000 ppm`까지 확장 가능
  - `RS485`와 `Modbus` 지원
- 주의:
  - zone별 1대 이상 배치 시 차광/환기 위치 영향을 같이 봐야 한다.

### 3. 광량(PAR)

- 추천: `Apogee SQ-522-SS`
- 이유:
  - 온실/식물 생장 챔버 용도 직접 명시
  - `RS-485/Modbus RTU` 직접 출력
  - LED 포함 full-spectrum 대응
- 주의:
  - 존별 canopy 상단 대표 위치 선정이 중요하다.

### 4. 배지 함수율

- 추천: `METER TEROS 12`
- 이유:
  - 함수율, 온도, bulk EC 동시 측정
  - soilless media calibration 범위 제공
  - Grodan rockwool block/slab 같은 soilless 배지 환경에 적용 가능한 후보
- 주의:
  - 기본 출력이 `SDI-12` 계열이라 `sensor-ingestor` 연결부에서 protocol adapter가 필요하다.
  - `Grodan Delta 6.5`, `Grodan GT Master` 환경에 맞는 현장 보정 계수는 별도로 관리해야 한다.

### 5. EC / pH

- 추천: `Bluelab Guardian Inline Wi‑Fi`
- 이유:
  - pH, EC, 온도를 연속으로 inline 모니터링 가능
  - nutrient line / reservoir 연속 감시에 적합
  - 알람과 원격 모니터링이 가능
- 대안:
  - `Bluelab OnePen` 또는 `Conductivity Pen`을 휴대형 검교정/spot check 용도로 병행
- 주의:
  - `Wi‑Fi/App` 중심이라 PLC 직결형 Modbus 장비와는 통합 방식이 다르다.
  - nutrient room 연속계측과 현장 점검 장비를 분리하는 구성이 더 현실적이다.

### 6. 외기 센서

- 추천: `Vaisala WXT536`
- 이유:
  - 풍속/풍향/강우/기압/온도/습도를 한 장비로 취득 가능
  - 외기 기준점 `gh-01-outside` 구성에 적합
  - 유지보수와 설치 단순성이 높다
- 주의:
  - 초기 PoC에서는 외기 온습도+일사만 먼저 쓰고, 풍속/강우는 2차 확장으로 줄일 수도 있다.

## 권장 조합

### A안. 통합 안정성 우선

- 존 환경: `HMP110`
- CO2: `GMP252`
- PAR: `SQ-522-SS`
- 배지: `TEROS 12`
- 양액실: `Guardian Inline Wi‑Fi`
- 외기: `WXT536`

### B안. 초기 구축 비용 절감

- 존 환경: `HMP110` 또는 동급 온습도 센서로 단순화
- CO2: `GMP252`
- PAR: 1대만 우선 도입
- 배지: `TEROS 12`를 대표 라인 위주 배치
- 양액실: `Guardian Monitor Wi‑Fi` + 휴대형 `OnePen`
- 외기: `WXT536`는 2차 도입

## 현재 판단

- `sensor-ingestor`와 가장 직접적으로 맞는 것은 `GMP252`, `SQ-522-SS`, `WXT536` 같은 디지털/통합형 장비다.
- `TEROS 12`는 농업 현장 적합성은 높지만 protocol adapter를 별도로 고려해야 한다.
- `Bluelab` 계열은 nutrient room 연속 모니터링에는 강하지만 PLC 직결형이라기보다 별도 모니터링 계층에 가깝다.

즉, 현재 기준 추천 조합은 아래다.

1. 실내 존 온습도: `Vaisala HMP110`
2. 존 CO2: `Vaisala GMP252`
3. 존 PAR: `Apogee SQ-522-SS`
4. 배지 함수율: `METER TEROS 12`
5. 급액/원수 pH·EC: `Bluelab Guardian Inline Wi‑Fi`
6. 외기 기준점: `Vaisala WXT536`

## 참고 출처

- Vaisala HMP110: https://www.vaisala.com/en/products/instruments-sensors-and-other-measurement-devices/instruments-industrial-measurements/hmp110
- Vaisala GMP252: https://www.vaisala.com/en/products/instruments-sensors-and-other-measurement-devices/instruments-industrial-measurements/gmp252
- Apogee SQ-522-SS: https://www.apogeeinstruments.com/sq-522-ss-modbus-digital-output-full-spectrum-quantum-sensor/
- METER TEROS 12: https://metergroup.com/products/teros-12/
- Bluelab Guardian Inline Wi‑Fi: https://bluelab.com/products/bluelab-guardian-monitor-inline-wi-fi
- Bluelab OnePen: https://bluelab.com/products/bluelab-onepen
- Vaisala WXT536 설명: https://www.vaisala.com/en/expert-article/integrated-weather-data-efficient-building-operation
