# 대시보드 & 웹UI 전면 재설계 의뢰 (Claude Design Brief)

> 이 문서를 Claude(또는 다른 디자인 파트너)에게 그대로 붙여넣어 대시보드 / 웹UI 전체 화면의 디자인을 의뢰하기 위한 브리프입니다. 변경 사항이 생기면 이 파일을 먼저 업데이트하고 다시 전달하세요.

---

## 1. 프로젝트 컨텍스트

- **제품**: `iFarm 통합제어` — 적고추(Capsicum) 온실 스마트팜 통합 운영 대시보드.
- **목적**: 온실 현장 운영자가 ① 현재 환경 상태를 한눈에 보고 ② AI가 제안한 결정을 승인/거절하고 ③ 안전 범위를 넘는 상황에 즉시 대응할 수 있도록 돕는다.
- **백엔드**: FastAPI (ops-api) + TimescaleDB(Postgres) + LLM orchestrator(파인튜닝된 GPT-4.1-mini "ds_v11") + policy_engine + execution_gateway(PLC 어댑터).
- **현재 프런트엔드**: `ops-api/ops_api/app.py` 안에 한 파일로 embed된 HTML + Tailwind CDN + Vanilla JS. 모든 화면을 단일 페이지 + 사이드바 전환 방식으로 구현.

---

## 2. 해결해야 할 문제 (왜 재설계가 필요한가)

현재 UI는 개발자가 디버깅용으로 만든 티가 강해서, **실제 현장 운영자가 쓰기에는 너무 복잡하고 전문적**이다. 구체적으로:

1. **JSON 원문이 그대로 노출됨** — `decision.parsed_output_json`, `payload_json`, `validator_reason_codes_json` 같은 필드가 운영자 화면에 stringified JSON으로 박혀 있음.
2. **기술 용어가 라벨로 그대로 나옴** — `decision_id`, `request_id`, `runtime_mode_gate`, `blocked_validator`, `shadow_mode`, `HSV-01` 같은 내부 식별자가 UI 라벨에 그대로 노출됨.
3. **정보 밀도가 너무 높음** — 한 카드 안에 8~15개의 필드가 나열되고, 강조/위계 구분이 약함.
4. **운영자가 "지금 내가 뭘 해야 하는가"를 즉시 알 수 없음** — 승인 대기 건수, 경고, 이상 징후가 분산되어 있어 action-first가 아님.
5. **전문가 모드와 초보 모드가 섞여 있음** — 고급 필드(파인튜닝 모델 family, prompt_version, grounding_keys 등)와 일반 운영 정보가 동일 비중으로 표시됨.

### 재설계 후 달성해야 할 것
- **핵심 사용자는 개발자가 아니다**: 농업 경험은 있지만 AI/소프트웨어 지식은 적은 온실 관리자(40~60대 포함)가 태블릿으로 현장에서 본다고 가정.
- **"지금 내가 신경 써야 할 일"**을 첫 화면 상단에서 3초 안에 알 수 있어야 한다.
- **기술 세부는 "고급" 패널로 숨긴다** — 필요할 때만 펼쳐 본다.

---

## 3. 사용자 프로필

| 역할 | 주 사용 화면 | 기술 숙련도 | 목표 |
|---|---|---|---|
| **온실 운영자(Primary)** | 대시보드, 구역 모니터링, 알림, AI 어시스턴트 | 낮음 (AI/DB 용어 모름) | 현재 구역이 정상인가? 지금 해야 할 일은? 비정상이면 왜? |
| **승인자/관리자** | 결정/승인, 환경설정(자동화 규칙), 정책 | 중간 | AI 권고를 검토·승인, 규칙 조정, 안전 한계 관리 |
| **시스템 운영자(Secondary)** | Shadow Mode, 시스템 | 높음 | 모델 품질 모니터링, 실행 이력 감사 |

Primary 사용자를 기본 페르소나로 두고 디자인하되, Secondary 정보는 *접어 놓고 필요시 펼치기* 형태로 유지.

---

## 4. 핵심 디자인 원칙

1. **Plain Korean first, jargon-free** — 모든 라벨/상태/버튼 텍스트를 한국어 운영어로 작성. JSON이나 영문 enum은 툴팁/고급 패널에서만 노출.
2. **Action-first layout** — 화면 상단에 "현재 액션 가능한 항목"(승인 대기 N건, 위험 경고 N건)을 강조. 그 아래에 맥락(환경 요약), 맨 아래에 로그/이력.
3. **Progressive disclosure** — 카드 기본은 요약 1~3줄, 클릭하면 상세 모달. 원본 JSON은 접힌 "개발자 뷰" 토글 안에.
4. **Ambient status color** — 녹색/주황/빨강의 3단계 신호등을 일관되게 사용(정상/주의/위험). 카드 좌측 색 띠, 배경 부드러운 tint, 아이콘 함께.
5. **Low-stress visual tone** — 농업 도메인 정체성을 유지하되, 금융 대시보드급 밀도를 피한다. 숫자 하나를 크게 보여주고 컨텍스트는 작게.
6. **Responsive + touch-first** — 태블릿(10~13")에서 현장 사용, 데스크톱(27")에서 사무실 사용 모두 가능해야 함. 버튼 최소 44×44pt.
7. **접근성** — WCAG AA 대비 준수, 컬러블라인드 안전 팔레트, 아이콘 + 텍스트 병기.

---

## 5. 브랜드 / 비주얼 토큰 (현행 유지 희망)

- **Primary (Agricultural Green)**: `#006a26` ~ `#00913a` 그라디언트 (현재 "농경 사령부" 팔레트).
- **Ink (본문)**: 다크 그레이. **Muted**: 중간 그레이.
- **Surface**: 흰색 + `surface-low`(아주 옅은 배경).
- **Status**:
  - OK: 녹색 계열 (primary와 구분 가능하게 blue-green 톤 제안).
  - Warning: 주황 (#f59e0b 계열).
  - Critical: 빨강 (#dc2626 계열).
- **타이포**: Pretendard(기본) + Noto Sans KR(보조) + 영문 heading용 `font-headline`. **숫자 강조 시 tabular-nums 유지**.
- **아이콘**: Material Symbols Outlined (이미 CDN 로드됨).
- **레이아웃 베이스**: Tailwind CDN. **Figma → HTML 변환 시 Tailwind class로 산출 가능하게 작업**.
- 기존 `WebUI/stitch_ui_v1.zip` Stitch 레퍼런스의 hero strip / greenhouse visual 감성은 유지하되 **정보 밀도는 절반 이하로 낮춘다**.

---

## 6. 화면 목록 (10개 view) — 각각에 대해 재설계 필요

사이드바 메뉴 순서대로. 각 화면의 **핵심 사용자 질문**과 **현재 문제**를 함께 기재.

### 6.1 대시보드 (Overview) — 첫 진입 화면
- 사용자 질문: "지금 우리 온실 괜찮아? 내가 뭘 해야 해?"
- 현재 문제: hero strip · 센서 grid 5개 · 그린하우스 비주얼 · 존 상태 · shadow window · 감사 trail · 알림 — **6개 섹션이 동시에 경쟁**.
- **요청**:
  - 최상단 "오늘의 할 일" 카드: **승인 대기 N건 · 위험 알림 N건 · 주의 장치 N건** 3개 숫자만 크게. 각 숫자 클릭 시 해당 화면으로 이동.
  - 그 아래 환경 요약(온·습도·CO₂·EC 등) — 카드 한 줄. 각 수치에 작은 스파크라인.
  - 그린하우스 비주얼은 *3차 순위*로 축소, 아이콘 수준.
  - 하단 "최근 이벤트" 타임라인 4~5개.

### 6.2 구역 모니터링 (Zones)
- 사용자 질문: "A구역 온도 추이가 이상한가? 최근 24시간 어땠나?"
- 현재: 9개 지표 시계열 차트 + 스냅샷 카드. 차트는 괜찮으나 라벨(`substrate_moisture_pct` 등)이 영문.
- **요청**:
  - 지표명을 한국어 + 단위로(예: "근권 수분 (%)"), 작은 영문 id는 tooltip.
  - 각 지표 카드에 "현재값 · 24h 변화폭 · 정상/주의/위험" 3줄 요약.
  - 시계열 차트는 선택한 지표만 크게 보여주는 master/detail 패턴.

### 6.3 결정 / 승인 (Decisions)
- 사용자 질문: "AI가 뭘 하자고 했고, 내가 승인하면 뭐가 일어나?"
- 현재: decision 카드에 `parsed_output_json`, `validated_output_json`, `validator_reason_codes_json` raw가 들어감.
- **요청**:
  - 카드 상단: "AI가 '천장 개폐기를 20%로 닫기'를 권고함" — **자연어 한 문장**.
  - 카드 body: 근거 2~3개(예: "현재 외부 강우 0.8mm/10min, 풍속 4.2m/s, 내부 습도 85%"), 위험 등급 뱃지.
  - 버튼: 승인 · 거절 · 상세(모달).
  - 모달에서만 JSON + validator reason codes + 원시 payload 노출 ("개발자 뷰" 토글).

### 6.4 AI 어시스턴트 (Chat)
- 사용자 질문: "지금 구역 상태 어때? 이번 주 EC 올리는 게 맞아?"
- 현재: 좌측 채팅 + 우측 "Grounding Inspector"(model_label/provider/grounding_keys 등) — **우측 패널이 기술적**.
- **요청**:
  - 좌측 채팅은 유지, 크기 키움. quick prompt 4~6개 버튼.
  - 우측 패널은 "지금 AI가 본 데이터" 요약: **마지막 답변이 참조한 구역/지표/정책 이름만 칩 형태로**. provider/model_id는 숨기고 "파인튜닝된 적고추 전문 AI" 뱃지 한 개.
  - 개발자 토글 시 기존 Grounding Inspector 필드 복원.

### 6.5 알림 (Alerts)
- 사용자 질문: "어떤 경고가 쌓여 있나? 뭐부터 봐야 하나?"
- 현재: `alert_type=automation_dispatch_fault` 같은 내부 enum이 그대로.
- **요청**:
  - 상단 필터 칩: "위험만 · 자동화 실패만 · 정책 위반만" 등 **한국어 프리셋**.
  - 각 행: "자동화 규칙 '강우 시 천장 닫기'가 실패했습니다" 자연어 + 발생 시각 상대표기(3분 전).
  - Severity 좌측 색 띠(녹/주/빨).

### 6.6 로봇 (Robot Tasks / Candidate)
- 사용자 질문: "로봇이 지금 뭐 하고 있나? 다음에 뭐 할 계획인가?"
- **요청**:
  - 좌측: 현재 실행 중 태스크(1건) · 우측: 대기 큐 · 하단: 오늘 완료 이력.
  - 각 태스크에 "수확 작업 · 작업 구역 A · 예상 12분" 자연어 요약.

### 6.7 장치 / 제약 (Devices)
- 사용자 질문: "어떤 장치가 정상이고 어떤 게 고장났나?"
- **요청**:
  - 장치 카드 grid: 아이콘 + 장치명(한국어) + 상태 컬러 + "정상 · 경고 · 장애" + 마지막 통신 시각.
  - 활성 제약은 장치 카드 하단에 뱃지로 붙이되, 영문 safety interlock id는 툴팁으로.

### 6.8 정책 / 이벤트 (Policies)
- 사용자 질문: "지금 어떤 안전 규칙이 켜져 있나? 언제 마지막으로 트리거됐나?"
- **요청**:
  - 규칙별 토글 스위치 + 사람이 읽을 수 있는 이름("근권 EC 상한 안전 규칙") + 상세 설명 1줄.
  - 최근 이벤트 타임라인: "policy_violation: HSV-03" 같은 표기를 "EC 안전 규칙 위반" 같은 자연어로.

### 6.9 환경설정 (Automation Rules) — 최근 추가
- 사용자 질문: "이 센서가 이 값 넘으면 이 장치 어떻게 해달라는 규칙을 내가 만들 수 있나?"
- 현재: Phase O~S 구축된 규칙 목록 + trigger 상세 drawer. **모달 폼 필드가 20개 이상, 일반인에게 과함**.
- **요청**:
  - 규칙 생성 마법사(wizard) 3단계: ① 언제(센서 + 조건) ② 무엇을(장치 + 동작) ③ 안전(runtime mode + cooldown).
  - 각 단계에서 한 번에 2~3 질문만.
  - 규칙 목록은 "비 올 때 천장 닫기 · 켜짐 · 지난 24h 2번 실행" 같은 자연어 카드.
  - Phase S에서 추가된 trigger 상세 drawer(`#automationTriggerDetailDrawer`)의 **linked decision 섹션 JSON/ID를 사람 언어로 치환**(예: `request_id automation-42-…` → "자동 실행 이력 #42").

### 6.10 Shadow Mode (관리자용)
- 사용자 질문: (관리자) "신규 모델 품질이 어때? 운영자 의견과 일치했나?"
- **요청**: 이 화면은 유지해도 괜찮지만, **Primary 사용자에게는 사이드바에서 숨김 or "고급" 그룹으로 이동**. `operator_agreement_rate`, `critical_disagreement_count` 같은 메트릭은 게이지 UI로.

### 6.11 시스템 (Execution History · Runtime · AI Runtime)
- **요청**: 관리자 전용. 사이드바 하단 "고급" 그룹으로. 현행 AI Runtime 카드/Runtime Mode chip은 일반 사용자에게 숨김.

---

## 7. 공통 컴포넌트 요청 (디자인 시스템)

다음 컴포넌트에 대해 기본형 · hover · active · 위험/주의/정상 변형을 정의해 주세요.

1. **Status chip**: 정상 / 주의 / 위험 / 대기 / 꺼짐 — 한국어 + 아이콘 + 배경 tint.
2. **Action card**: 좌측 색 띠 + 아이콘 + 타이틀(자연어 1문장) + 부연 1줄 + 주 액션 버튼 1개 + 보조 버튼 1개.
3. **Metric card (sensor)**: 지표명 + 현재값(large) + 단위 + 24h 스파크라인 + 상태 dot + 변화폭.
4. **Timeline row**: 시간(상대표기) + 아이콘 + 자연어 요약 + 우측 액션(상세 / 닫기).
5. **Approval card**: AI 권고 자연어 한 문장 + 근거 chip 2~3개 + 위험 뱃지 + 승인/거절/상세 버튼.
6. **Wizard stepper**: 3단계 규칙 생성/편집용.
7. **Detail modal (progressive disclosure)**: 사람 요약 영역 + "개발자 뷰" 접힘 토글.
8. **Empty state**: 각 화면의 "아직 데이터 없음" 상태 일러스트 + 1문장 설명 + CTA.
9. **Error / skeleton / loading**: 각각 명시.

---

## 8. 제거 또는 뒤로 숨겨야 할 현재 요소

- 카드 본문의 raw JSON 표시(모든 `*_json` 필드).
- 내부 식별자(`decision_id=3`, `request_id=automation-…`, `trigger_id=#57`)는 제목에서 제거하고 상세 모달에만.
- 상태 enum 영문 표기(`approval_pending`, `blocked_validator`, `dispatch_fault`, `shadow_logged`, `HSV-01` 등) → 한국어로 전환.
- AI Runtime 카드의 `prompt_version sft_v10`, `retriever openai`, `chat_system_prompt_id` 등은 일반 사용자 화면에서 숨김.
- Shadow window의 `operator_agreement_rate 0.92`, `promotion_decision promote` 같은 메트릭은 관리자 탭으로.

---

## 9. 남겨야 할 / 보완해야 할 정보

- **안전 상태**: 3-layer safety pipeline(AI · Validator · Gateway)의 현재 상태를 항상 상단 헤더에 작은 신호등으로.
- **현재 runtime mode**(shadow / approval / execute): 헤더 우측 고정 칩, 색으로 구분.
- **마지막 업데이트 시각**: 각 카드 우측 하단 작은 텍스트로.
- **실시간 연결 상태**: SSE/WebSocket 끊기면 배너로 명시.

---

## 10. 산출물 기대

디자인 파트너가 다음을 순서대로 만들어 주시면 바로 구현 전환이 가능합니다.

1. **Information architecture 다이어그램** — 10개 view의 재정렬(Primary / Secondary / Admin 그룹).
2. **Low-fi 와이어프레임** — 각 view의 섹션 배치(모바일 · 태블릿 · 데스크톱 3단계).
3. **High-fidelity 시안** — 대시보드 · 결정/승인 · 환경설정(마법사) · 알림 4개 화면 최소.
4. **디자인 시스템 페이지** — §7의 공통 컴포넌트 + 컬러 토큰 + 타이포 스케일.
5. **Interaction spec** — 승인 → 실행 플로우, 규칙 생성 마법사, 상세 모달 펼침 애니메이션.
6. **Copy 라이팅 가이드** — 상태 enum → 한국어 대응표, 에러 메시지 톤&매너(침착하고 비난하지 않는 운영어).
7. **Figma 파일 + Tailwind class로 정리된 컴포넌트 export**(가능하면).

---

## 11. 제약 / 주의 사항

- **백엔드 API 형태 변경 불가 가정**. UI가 JSON을 받아 사람 친화적으로 재가공할 뿐, ops-api 응답 스키마는 그대로(필요 시 별도 BFF 레이어 제안은 환영).
- **단일 페이지 Vanilla JS + Tailwind CDN** 현행 스택을 유지하되, 컴포넌트화 리팩터링 제안은 환영(React/Vue 이관 제안은 별도 섹션으로).
- **일체의 이모지 사용 금지** — 아이콘은 Material Symbols만.
- **한국어 우선, 영문 term은 보조**.
- 파인튜닝 모델 이름·prompt version 같은 내부 브랜드 요소는 **관리자에게만** 노출.

---

## 12. 참고 파일 (파트너에게 함께 전달)

- `ops-api/ops_api/app.py` — 현행 단일 파일 프런트엔드(`_dashboard_html` 내부).
- `docs/automation_rules_runtime.md` — 자동화 규칙 도메인 용어집 + 8개 장치 타입, 21개 센서 키, 6개 연산자, 3개 runtime mode 게이트.
- `docs/policy_output_validator_spec.md` — 10개 HSV(Hard Safety Validator) 규칙 정의.
- `docs/glossary.md` — 도메인 용어집.
- `AGENTS.md` — 전체 아키텍처 / 서비스 경계.
- `WebUI/stitch_ui_v1.zip` — 현재 사용 중인 Stitch 레퍼런스(감성 기준점).

---

## 13. 성공 기준 (운영자 피드백 기준)

재설계 후 다음 3가지가 만족되어야 성공으로 본다:

1. **3초 안에 "지금 내가 봐야 할 게 뭔지"** 운영자가 알 수 있다.
2. 결정/승인 화면에서 **AI 권고를 읽고 "왜 그런지"** 기술 용어 없이 이해할 수 있다.
3. 환경설정(자동화 규칙)을 **개발자 도움 없이** 운영자가 혼자 만들고 켤 수 있다.

---

## 14. 구현 진행 상황

- **Phase T-1 ✅** (2026-04-21): Claude Design handoff(`WebUI/pepper smartfarm dashboard ui V1-handoff.zip`)를 `ops-api/ops_api/static/dashboard_v2/` 하위로 이관하고 `/dashboard/v2` 라우트로 병행 배포. React + Babel standalone + Tailwind CDN 구성, index.html + 12개 jsx 모듈(tokens/chrome/dashboard/decisions/rules/alerts/zones/chat/devices/policies_robot/designsystem/app)을 `StaticFiles(mount="/dashboard/v2/src")`로 서빙. 기존 `/dashboard`는 그대로 유지 → 운영자가 두 화면을 비교 가능. 데이터는 아직 MOCK이므로 후속 패스에서 view별로 `/overview/summary`·`/alerts`·`/automation/*`·`/ai/chat` 등과 연결. 회귀 smoke: `scripts/validate_ops_api_dashboard_v2.py` 14 invariant(index HTML + 12 jsx 모듈 reachability + legacy /dashboard 회귀 가드).

- **Phase T-2 (다음)**: MOCK → 실데이터 배선. 우선순위 — Overview(hero-todo + 환경 요약 metrics)를 `/overview/summary` 응답으로 채우고, 승인 카드를 `/decisions?status=approval_pending` 또는 `/automation/triggers?status=approval_pending` 응답으로 연결. 이후 Rules → `/automation/rules`, Alerts → `/alerts`, Chat → `/ai/chat`, Zones → `/zones/{id}/history`.

- **Phase T-3 (다음 다음)**: 기존 `/dashboard` 폐기, `/`의 307 redirect를 `/dashboard/v2`로 전환. 관리자용 Shadow Mode/시스템 view는 Stub 상태이므로 fallback 필요 시 legacy iframe 허용 검토.
