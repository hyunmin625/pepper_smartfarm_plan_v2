// ==== tokens.jsx ====
// tokens.jsx — shared constants, mock data, small primitives

const STATUS = {
  ok:   { label: "정상", chip: "chip-ok",   dot: "dot-ok",   icon: "check_circle" },
  warn: { label: "주의", chip: "chip-warn", dot: "dot-warn", icon: "warning" },
  crit: { label: "위험", chip: "chip-crit", dot: "dot-crit", icon: "error" },
  wait: { label: "대기", chip: "chip-info", dot: "dot-mute", icon: "schedule" },
  off:  { label: "꺼짐", chip: "chip-mute", dot: "dot-mute", icon: "power_settings_new" },
};

// Korean label dictionary (for toggle)
const LABELS_KO = {
  nav_overview: "대시보드", nav_zones: "구역 모니터링", nav_decisions: "결정 · 승인",
  nav_chat: "AI 어시스턴트", nav_alerts: "알림", nav_robot: "로봇",
  nav_devices: "장치 · 제약", nav_policies: "정책 · 이벤트", nav_automation: "환경설정",
  nav_shadow: "Shadow Mode", nav_system: "시스템",
};
const LABELS_EN = {
  nav_overview: "Overview", nav_zones: "Zones", nav_decisions: "Decisions",
  nav_chat: "AI Assistant", nav_alerts: "Alerts", nav_robot: "Robot",
  nav_devices: "Devices", nav_policies: "Policies", nav_automation: "Automation",
  nav_shadow: "Shadow Mode", nav_system: "System",
};

// ————————————————————————————————————————————
// MOCK DATA — Capsicum greenhouse, rain event in progress
// ————————————————————————————————————————————

const MOCK = {
  greenhouse: { name: "적고추 온실 제2동", zones: ["A구역", "B구역", "C구역", "D구역"] },

  runtimeMode: "approval",  // shadow | approval | execute
  safetyPipeline: { ai: "ok", validator: "ok", gateway: "warn" },
  lastSync: "방금 전",
  connection: "connected", // or "degraded"

  todo: {
    pendingApprovals: 2,
    criticalAlerts: 1,
    warnings: 3,
  },

  metrics: [
    { key: "air_temp",   name: "기온",        unit: "°C",  value: 24.8, delta: -0.6, state: "ok",   range: "22–26" },
    { key: "air_humid",  name: "습도",        unit: "%",   value: 85,   delta: +8,   state: "warn", range: "60–80" },
    { key: "co2",        name: "CO₂",         unit: "ppm", value: 612,  delta: -24,  state: "ok",   range: "500–900" },
    { key: "ec",         name: "근권 EC",     unit: "dS/m",value: 2.4,  delta: +0.1, state: "ok",   range: "1.8–2.8" },
    { key: "moisture",   name: "근권 수분",   unit: "%",   value: 62,   delta: +2,   state: "ok",   range: "55–70" },
    { key: "light",      name: "광량(PAR)",   unit: "μmol",value: 180,  delta: -220, state: "warn", range: "300–800" },
  ],

  // tiny pre-computed sparkline paths (24 points, 0..1 space)
  sparks: {
    air_temp:  [0.50,0.52,0.55,0.58,0.60,0.63,0.66,0.70,0.74,0.76,0.78,0.80,0.82,0.80,0.78,0.74,0.70,0.66,0.62,0.58,0.54,0.52,0.50,0.48],
    air_humid: [0.40,0.42,0.44,0.45,0.47,0.48,0.50,0.52,0.55,0.58,0.60,0.62,0.65,0.68,0.72,0.75,0.78,0.82,0.85,0.88,0.90,0.92,0.94,0.95],
    co2:       [0.70,0.72,0.68,0.65,0.60,0.58,0.55,0.53,0.50,0.48,0.46,0.45,0.47,0.50,0.52,0.54,0.56,0.55,0.54,0.53,0.50,0.48,0.46,0.44],
    ec:        [0.50,0.51,0.50,0.49,0.50,0.52,0.53,0.54,0.55,0.56,0.56,0.57,0.58,0.58,0.59,0.60,0.60,0.61,0.62,0.62,0.63,0.63,0.64,0.64],
    moisture:  [0.48,0.50,0.52,0.54,0.55,0.56,0.58,0.60,0.62,0.63,0.64,0.65,0.66,0.66,0.65,0.64,0.62,0.60,0.58,0.56,0.55,0.54,0.53,0.52],
    light:     [0.10,0.20,0.35,0.50,0.65,0.78,0.88,0.92,0.95,0.92,0.88,0.80,0.70,0.58,0.45,0.35,0.28,0.22,0.18,0.15,0.12,0.10,0.08,0.06],
  },

  zones: [
    { name: "A구역", crop: "적고추 · 수확기", state: "warn",  note: "습도 상승 중",        temp: 24.8, hum: 87 },
    { name: "B구역", crop: "적고추 · 개화기", state: "ok",    note: "안정",                 temp: 24.1, hum: 78 },
    { name: "C구역", crop: "적고추 · 착과기", state: "ok",    note: "안정",                 temp: 23.6, hum: 76 },
    { name: "D구역", crop: "적고추 · 육묘",   state: "crit",  note: "천장 개폐기 응답 지연", temp: 25.4, hum: 89 },
  ],

  pending: [
    {
      id: "dec-3",
      zone: "A구역",
      risk: "warn",
      summary: "A구역 천장 개폐기를 20%로 닫고, 제습팬 단계를 2로 올립니다.",
      reasons: [
        "외부 강우 0.8mm/10min 감지",
        "풍속 4.2 m/s — 안전 범위 내",
        "내부 습도 87% — 목표 상단(80%) 초과",
      ],
      plan: [
        { device: "천장 개폐기 #A1", action: "20%로 닫기", etc: "약 90초" },
        { device: "제습팬 #A-FAN-2", action: "단계 2로 전환", etc: "즉시" },
      ],
      impact: "예상 습도 하강 78% (약 12분 후)",
      createdAt: "2분 전",
      confidence: 0.84,
    },
    {
      id: "dec-4",
      zone: "B구역",
      risk: "ok",
      summary: "B구역 야간 관수를 6분으로 단축합니다. (근권 수분 충분)",
      reasons: [
        "근권 수분 66% — 목표 중앙치",
        "근권 EC 2.4 dS/m — 안정",
        "지난 24h 관수량 누적치 상한 근접",
      ],
      plan: [
        { device: "관수 밸브 #B-IRR-1", action: "08:00 스케줄 6분(기존 10분)", etc: "내일 아침" },
      ],
      impact: "EC 상승 억제 · 물 사용량 −18%",
      createdAt: "11분 전",
      confidence: 0.91,
    },
  ],

  alerts: [
    { id: 1, sev: "crit", title: "천장 개폐기 #D1 응답 지연",  body: "D구역 천장 개폐기가 지난 3회 명령에 응답하지 않습니다. 수동 점검이 필요합니다.", tag: "자동화 실패", time: "3분 전", device: "천장 개폐기 #D1" },
    { id: 2, sev: "warn", title: "A구역 습도 상단 초과",      body: "목표 범위(60–80%)를 3회 연속 벗어났습니다. AI가 습도 조정을 권고했습니다.",          tag: "환경 경고", time: "5분 전", device: "습도 센서 #A-H1" },
    { id: 3, sev: "warn", title: "근권 EC 상한 근접",          body: "B구역 근권 EC가 2.75로, 안전 규칙 상한(2.8) 접근 중입니다.",                         tag: "정책 주의", time: "24분 전", device: "EC 센서 #B-E1" },
    { id: 4, sev: "ok",   title: "야간 저광량 모드 진입",      body: "광량이 200 μmol 이하로 내려가 야간 모드로 자동 전환되었습니다.",                       tag: "시스템",     time: "1시간 전", device: "광 센서 #C-L1" },
    { id: 5, sev: "warn", title: "강우 이벤트 감지",            body: "외부 강우 센서에서 지난 10분간 0.8mm 감지. '강우 시 천장 닫기' 규칙이 대기 중입니다.",  tag: "외부 환경", time: "1시간 전", device: "외부 기상" },
  ],

  timeline: [
    { t: "방금 전",     icon: "water_drop",   text: "외부 강우 0.8mm 감지 — AI가 천장 개폐 조정을 권고했습니다.", state: "warn" },
    { t: "5분 전",      icon: "bolt",         text: "B구역 야간 관수 규칙을 6분으로 단축 권고 (수분 충분)",        state: "ok" },
    { t: "17분 전",     icon: "check_circle", text: "C구역 CO₂ 주입 목표치 도달 — 주입 정지",                     state: "ok" },
    { t: "34분 전",     icon: "person",       text: "이영호 관리자가 '야간 저광량 모드' 규칙을 수정했습니다.",      state: "ok" },
    { t: "1시간 전",    icon: "warning",      text: "D구역 천장 개폐기 응답 지연 — 수동 점검 필요",                 state: "crit" },
  ],

  rules: [
    { id: 1, name: "강우 시 천장 닫기",          enabled: true,  when: "외부 강우 ≥ 0.5 mm/10min", then: "A~D 천장 개폐기 20%로 닫기", mode: "approval", runs24h: 2, last: "3분 전" },
    { id: 2, name: "고온 시 제습팬 가동",        enabled: true,  when: "기온 ≥ 28°C 10분 지속",     then: "제습팬 단계 2",               mode: "execute",  runs24h: 0, last: "어제" },
    { id: 3, name: "야간 저광량 모드",           enabled: true,  when: "광량 ≤ 200 μmol 30분",     then: "보광등 60% + 팬 단계 1",      mode: "execute",  runs24h: 1, last: "1시간 전" },
    { id: 4, name: "근권 EC 상한 안전 규칙",     enabled: true,  when: "EC ≥ 2.8 dS/m",             then: "관수 즉시 정지 + 경고",        mode: "approval", runs24h: 0, last: "3일 전" },
    { id: 5, name: "CO₂ 보충 (주간)",            enabled: false, when: "CO₂ ≤ 500 ppm 주간",       then: "CO₂ 주입 10분",               mode: "shadow",   runs24h: 0, last: "비활성" },
  ],

  sensors: [
    { key: "air_temp", label: "기온" }, { key: "air_humid", label: "습도" },
    { key: "co2", label: "CO₂" }, { key: "ec", label: "근권 EC" },
    { key: "moisture", label: "근권 수분" }, { key: "light", label: "광량(PAR)" },
  ],
  operators: [
    { key: "gte", label: "≥ (이상)" }, { key: "lte", label: "≤ (이하)" },
    { key: "gt",  label: "> (초과)" }, { key: "lt",  label: "< (미만)" },
    { key: "eq",  label: "= (같음)" }, { key: "neq", label: "≠ (다름)" },
  ],
  devices: [
    { key: "vent_roof",   label: "천장 개폐기" },
    { key: "fan_dehum",   label: "제습팬" },
    { key: "irrigation",  label: "관수 밸브" },
    { key: "grow_light",  label: "보광등" },
    { key: "co2_inject",  label: "CO₂ 주입기" },
    { key: "heater",      label: "난방기" },
    { key: "cooler",      label: "냉방기" },
    { key: "shade",       label: "차광막" },
  ],
};

// ————————————————————————————————————————————
// Primitive components
// ————————————————————————————————————————————

function Icon({ name, className = "", style = {} }) {
  return <span className={`ms ${className}`} style={style}>{name}</span>;
}

function Chip({ tone = "mute", icon, children, className = "" }) {
  const cls = `chip chip-${tone} ${className}`;
  return (
    <span className={cls}>
      {icon && <Icon name={icon} />}
      {children}
    </span>
  );
}

function StatusChip({ state, withIcon = true, children }) {
  const s = STATUS[state] || STATUS.off;
  const tone = state === "ok" ? "ok" : state === "warn" ? "warn" : state === "crit" ? "crit" : state === "wait" ? "info" : "mute";
  return (
    <Chip tone={tone} icon={withIcon ? s.icon : null}>
      {children || s.label}
    </Chip>
  );
}

function Dot({ state }) {
  const cls = state === "ok" ? "dot-ok" : state === "warn" ? "dot-warn" : state === "crit" ? "dot-crit" : "dot-mute";
  return <span className={`dot ${cls}`}></span>;
}

// Sparkline SVG from 0..1 array
function Sparkline({ points, tone = "brand", width = 120, height = 34, showArea = true }) {
  if (!points?.length) return null;
  const n = points.length;
  const stepX = width / (n - 1);
  const pts = points.map((v, i) => [i * stepX, height - v * (height - 4) - 2]);
  const d = pts.map((p, i) => (i === 0 ? `M${p[0]},${p[1]}` : `L${p[0]},${p[1]}`)).join(" ");
  const area = `${d} L${width},${height} L0,${height} Z`;
  const color = tone === "warn" ? "var(--warn)" : tone === "crit" ? "var(--crit)" : tone === "ok" ? "var(--ok)" : "var(--brand)";
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {showArea && <path d={area} fill={color} opacity="0.12" />}
      <path d={d} fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ————————————————————————————————————————————
// Extended mock data for Zones, Chat, Devices, Policies, Robot
// ————————————————————————————————————————————

// 72-point detailed series (last 24h, 20min granularity-ish)
function genSeries(base, amp, trend, noise, n = 72) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1);
    const wave = Math.sin(t * Math.PI * 2.2 + base * 0.37) * amp;
    const nz = (Math.sin(i * (0.9 + base * 0.17)) + Math.cos(i * 1.3 + base)) * noise;
    out.push(+(base + wave + trend * t + nz).toFixed(2));
  }
  return out;
}

MOCK.series = {
  air_temp:  genSeries(24.5, 1.8, -0.3, 0.25),
  air_humid: genSeries(72,   7,   14,   2.2),
  co2:       genSeries(680, 120, -80,   22),
  ec:        genSeries(2.3, 0.15, 0.1, 0.03),
  moisture:  genSeries(60,   3,   2,    0.8),
  light:     genSeries(380, 360, -360, 18),
};

MOCK.zonesDetail = [
  { key: "A", name: "A구역", crop: "적고추 · 수확기", state: "warn", note: "습도 상승 — 개폐기 조정 권고" },
  { key: "B", name: "B구역", crop: "적고추 · 개화기", state: "ok",   note: "전반 안정" },
  { key: "C", name: "C구역", crop: "적고추 · 착과기", state: "ok",   note: "전반 안정" },
  { key: "D", name: "D구역", crop: "적고추 · 육묘",   state: "crit", note: "천장 개폐기 응답 지연" },
];

MOCK.devicesList = [
  { id: "A-VENT-01", type: "vent_roof",  name: "A구역 천장 개폐기 #1", zone: "A", state: "ok",   lastSeen: "방금 전",  value: "30% 열림", constraint: "풍속 6m/s 이상 시 강제 닫힘" },
  { id: "A-FAN-02",  type: "fan_dehum",  name: "A구역 제습팬 #2",      zone: "A", state: "warn", lastSeen: "12초 전",  value: "단계 2/3",  constraint: "야간 단계 1 제한" },
  { id: "A-IRR-01",  type: "irrigation", name: "A구역 관수 밸브 #1",  zone: "A", state: "ok",   lastSeen: "2분 전",   value: "대기",      constraint: "EC 2.8 초과 시 자동 정지" },
  { id: "B-LIGHT-01",type: "grow_light", name: "B구역 보광등 #1",      zone: "B", state: "ok",   lastSeen: "방금 전",  value: "60%",       constraint: "야간 12시 이후 소등" },
  { id: "B-CO2-01",  type: "co2_inject", name: "B구역 CO₂ 주입기",    zone: "B", state: "off",  lastSeen: "1시간 전", value: "꺼짐",      constraint: "주간 900ppm 상한" },
  { id: "C-HEAT-01", type: "heater",     name: "C구역 난방기 #1",      zone: "C", state: "ok",   lastSeen: "1분 전",   value: "대기",      constraint: "외기 5°C 이하 기동" },
  { id: "C-SHADE-01",type: "shade",      name: "C구역 차광막",         zone: "C", state: "ok",   lastSeen: "방금 전",  value: "20% 닫힘",  constraint: "PAR 900 초과 시 확장" },
  { id: "D-VENT-01", type: "vent_roof",  name: "D구역 천장 개폐기 #1", zone: "D", state: "crit", lastSeen: "6분 전",   value: "응답 없음", constraint: "수동 점검 필요" },
  { id: "D-FAN-01",  type: "fan_dehum",  name: "D구역 제습팬 #1",      zone: "D", state: "ok",   lastSeen: "1분 전",   value: "단계 1/3",  constraint: null },
  { id: "D-IRR-01",  type: "irrigation", name: "D구역 관수 밸브 #1",  zone: "D", state: "ok",   lastSeen: "방금 전",  value: "대기",      constraint: "EC 2.8 초과 시 자동 정지" },
];

MOCK.policies = [
  { id: "HSV-01", name: "AI 응답 형식 규칙",      desc: "AI 출력이 정의된 스키마를 따르는지 확인합니다.",              enabled: true, state: "ok",   triggers24h: 0 },
  { id: "HSV-03", name: "근권 EC 상한 안전 규칙", desc: "EC가 2.8 dS/m을 넘는 관수 명령을 차단합니다.",               enabled: true, state: "ok",   triggers24h: 1 },
  { id: "HSV-04", name: "풍속 과다 시 천장 닫기", desc: "외부 풍속 ≥ 6 m/s일 때 모든 천장 개폐기를 자동 폐쇄합니다.",  enabled: true, state: "ok",   triggers24h: 0 },
  { id: "HSV-05", name: "야간 관수 금지",         desc: "22시 ~ 04시 사이 관수 명령을 차단합니다.",                    enabled: true, state: "ok",   triggers24h: 0 },
  { id: "HSV-07", name: "장치 쿨다운",            desc: "같은 장치를 5분 이내에 두 번 이상 움직이지 않도록 합니다.",     enabled: true, state: "warn", triggers24h: 3 },
  { id: "HSV-10", name: "화재·고온 비상 정지",     desc: "기온 ≥ 40°C 시 난방·CO₂ 주입·관수를 즉시 중지합니다.",        enabled: true, state: "ok",   triggers24h: 0 },
];

MOCK.policyEvents = [
  { t: "3분 전",    policy: "HSV-07",  title: "장치 쿨다운 발동 — A구역 제습팬",     zone: "A", state: "warn" },
  { t: "24분 전",   policy: "HSV-03",  title: "근권 EC 상한 근접 — B구역 관수 억제", zone: "B", state: "warn" },
  { t: "1시간 전",  policy: "HSV-07",  title: "장치 쿨다운 발동 — D구역 천장",       zone: "D", state: "warn" },
  { t: "3시간 전",  policy: "HSV-04",  title: "풍속 증가 감지, 안전 규칙 대기",      zone: "전체", state: "ok" },
];

MOCK.robotTasks = {
  now: { id: "R-20263", name: "수확 작업", zone: "B구역 2열", eta: "12분", progress: 0.58, robot: "Picker-01", started: "5분 전" },
  queue: [
    { id: "R-20264", name: "잎 제거",   zone: "B구역 2열", eta: "8분",  priority: "보통" },
    { id: "R-20265", name: "수확 작업", zone: "C구역 1열", eta: "18분", priority: "높음" },
    { id: "R-20266", name: "방제 순회", zone: "A~D 전체",  eta: "35분", priority: "낮음" },
  ],
  done: [
    { id: "R-20261", name: "수확 작업", zone: "A구역 3열", ended: "14분 전", result: "완료 · 4.2kg" },
    { id: "R-20260", name: "잎 제거",   zone: "A구역 1열", ended: "56분 전", result: "완료" },
    { id: "R-20259", name: "방제 순회", zone: "B구역",     ended: "2시간 전", result: "완료 · 이상 없음" },
  ],
};

MOCK.chatHistory = [
  { who: "user", text: "A구역 지금 상태 어때?", t: "14:30" },
  { who: "ai",   text: "A구역은 **주의** 상태입니다. 습도가 87%로 목표(60–80%)를 넘었고, 외부 강우가 감지됐어요. 제가 방금 '천장 개폐기 20%로 닫기'를 권고해뒀으니 **결정·승인** 화면에서 확인해주세요. 기온(24.8°C)과 EC(2.4)는 안정 범위입니다.",
    grounds: { zones: ["A구역"], metrics: ["습도", "기온", "EC"], policies: ["HSV-04"] }, t: "14:30" },
  { who: "user", text: "이번 주 EC를 조금 올려볼까 하는데 어때?", t: "14:32" },
  { who: "ai",   text: "현재 B구역 EC는 2.4 dS/m로 정상 범위(1.8–2.8)의 중상단입니다. 수확기인 A·B 구역 기준으로 2.6까지 올려도 안전 규칙(HSV-03, 상한 2.8)에 걸리지 않습니다. 다만 지난 48시간 동안 관수량이 누적 상한에 근접했기 때문에, **관수량을 늘리지 않고 비료 농도만 조정하는 방식**을 권장합니다.",
    grounds: { zones: ["A구역", "B구역"], metrics: ["근권 EC", "관수 누적량"], policies: ["HSV-03"] }, t: "14:32" },
];

MOCK.quickPrompts = [
  "지금 모든 구역 상태 요약해줘",
  "오늘 승인해야 할 권고가 뭐야?",
  "이번 주 습도 추이는 어때?",
  "수확량이 가장 좋은 구역은?",
];

// expose
Object.assign(window, {
  STATUS, LABELS_KO, LABELS_EN, MOCK,
  Icon, Chip, StatusChip, Dot, Sparkline,
});

// ==== chrome.jsx ====
// chrome.jsx — sidebar, topbar, status header, shared layout

function Sidebar({ route, setRoute, labels }) {
  const L = labels;
  const primary = [
    { k: "overview",   icon: "space_dashboard",  label: L.nav_overview },
    { k: "zones",      icon: "grid_view",        label: L.nav_zones },
    { k: "decisions",  icon: "check_circle",     label: L.nav_decisions, badge: MOCK.todo.pendingApprovals },
    { k: "chat",       icon: "forum",            label: L.nav_chat },
    { k: "alerts",     icon: "notifications",    label: L.nav_alerts,    badge: MOCK.todo.criticalAlerts + MOCK.todo.warnings },
  ];
  const control = [
    { k: "robot",      icon: "precision_manufacturing", label: L.nav_robot },
    { k: "devices",    icon: "memory",            label: L.nav_devices },
    { k: "policies",   icon: "shield",            label: L.nav_policies },
    { k: "automation", icon: "tune",              label: L.nav_automation },
  ];
  const admin = [
    { k: "shadow",     icon: "visibility",        label: L.nav_shadow },
    { k: "system",     icon: "build",             label: L.nav_system },
    { k: "designsystem",icon: "palette",          label: "디자인 시스템" },
  ];

  const Item = ({ it }) => (
    <div className={`nav-item ${route === it.k ? "active" : ""}`} onClick={() => setRoute(it.k)}>
      <Icon name={it.icon} style={{ fontSize: 20 }} />
      <span className="flex-1">{it.label}</span>
      {it.badge ? <span className="chip chip-brand" style={{ padding: "1px 7px", fontSize: 11 }}>{it.badge}</span> : null}
    </div>
  );

  return (
    <aside className="flex flex-col shrink-0 resp-sidebar" style={{ width: 232, borderRight: "1px solid var(--line)", background: "#fbfcfb", height: "100vh", position: "sticky", top: 0 }}>
      <div className="flex items-center gap-2 px-4" style={{ height: 64, borderBottom: "1px solid var(--line)" }}>
        <div className="rounded-lg flex items-center justify-center" style={{ width: 32, height: 32, background: "var(--brand)" }}>
          <Icon name="eco" style={{ color: "#fff", fontSize: 20 }} />
        </div>
        <div className="leading-tight">
          <div className="font-display font-semibold" style={{ fontSize: 15 }}>iFarm</div>
          <div className="text-[11px]" style={{ color: "var(--ink-soft)" }}>통합제어</div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto scroll-clean px-2 py-2">
        <div className="nav-group-label">모니터링</div>
        {primary.map(it => <Item key={it.k} it={it} />)}
        <div className="nav-group-label">제어 · 설정</div>
        {control.map(it => <Item key={it.k} it={it} />)}
        <div className="nav-group-label">관리자</div>
        {admin.map(it => <Item key={it.k} it={it} />)}
      </nav>

      <div className="px-3 py-3" style={{ borderTop: "1px solid var(--line)" }}>
        <div className="flex items-center gap-3">
          <div className="rounded-full flex items-center justify-center" style={{ width: 32, height: 32, background: "var(--brand-tint-2)", color: "var(--brand-700)", fontWeight: 700 }}>이</div>
          <div className="leading-tight">
            <div className="text-[13px] font-semibold">이영호</div>
            <div className="text-[11px]" style={{ color: "var(--ink-soft)" }}>온실 관리자</div>
          </div>
          <button className="btn btn-ghost btn-sm ml-auto" title="설정"><Icon name="settings" style={{ fontSize: 18 }} /></button>
        </div>
      </div>
    </aside>
  );
}

function ModeChip({ mode }) {
  const map = {
    shadow:   { label: "섀도우 모드", cls: "mode-shadow",   icon: "visibility" },
    approval: { label: "승인 모드",   cls: "mode-approval", icon: "how_to_reg" },
    execute:  { label: "자동 실행",   cls: "mode-execute",  icon: "bolt" },
  };
  const m = map[mode];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[12px] font-semibold ${m.cls}`}>
      <Icon name={m.icon} style={{ fontSize: 14 }} />
      {m.label}
    </span>
  );
}

function SafetyTrio({ pipeline }) {
  const items = [
    { key: "ai",        label: "AI",      icon: "smart_toy" },
    { key: "validator", label: "검증기",  icon: "verified" },
    { key: "gateway",   label: "게이트웨이", icon: "hub" },
  ];
  return (
    <div className="sig" title="3단 안전 파이프라인: AI → 검증기 → 실행 게이트웨이">
      {items.map((it, i) => (
        <span key={it.key} className="inline-flex items-center gap-1">
          <Dot state={pipeline[it.key]} />
          <span style={{ fontWeight: 600, color: "var(--ink-muted)" }}>{it.label}</span>
          {i < items.length - 1 && <span style={{ color: "#c9d0cb", margin: "0 2px" }}>›</span>}
        </span>
      ))}
    </div>
  );
}

function Topbar({ title, subtitle, route, setRoute, onToggleDev, devViewUnlocked, tweaks, setTweaks }) {
  return (
    <header className="flex items-center gap-4 px-6 resp-topbar-compact" style={{ height: 64, borderBottom: "1px solid var(--line)", background: "rgba(255,255,255,.85)", backdropFilter: "blur(8px)", position: "sticky", top: 0, zIndex: 30 }}>
      <div className="min-w-0">
        <div className="font-display font-semibold truncate" style={{ fontSize: 18 }}>{title}</div>
        {subtitle && <div className="text-[12px] truncate" style={{ color: "var(--ink-soft)" }}>{subtitle}</div>}
      </div>

      <div className="flex-1"></div>

      <SafetyTrio pipeline={MOCK.safetyPipeline} />
      <ModeChip mode={MOCK.runtimeMode} />

      <div className="sig" title="마지막 동기화">
        <Icon name="sync" style={{ fontSize: 14, color: "var(--ok)" }} />
        <span>동기화 {MOCK.lastSync}</span>
      </div>

      <button className="btn btn-sm" onClick={onToggleDev} title="개발자 뷰 토글 (JSON 원문 보기)">
        <Icon name={devViewUnlocked ? "code_off" : "code"} style={{ fontSize: 16 }} />
        {devViewUnlocked ? "개발자 뷰 켜짐" : "개발자 뷰"}
      </button>
    </header>
  );
}

function ConnectionBanner({ connected }) {
  if (connected) return null;
  return (
    <div className="px-6 py-2 flex items-center gap-2" style={{ background: "var(--crit-tint)", borderBottom: "1px solid #f2b8b8", color: "#9b1a1a", fontSize: 13, fontWeight: 500 }}>
      <Icon name="wifi_off" style={{ fontSize: 18 }} />
      실시간 연결이 끊겼습니다. 재연결 시도 중…
    </div>
  );
}

function SectionHeader({ title, sub, right }) {
  return (
    <div className="flex items-end justify-between mb-3">
      <div>
        <h2 className="font-display font-semibold" style={{ fontSize: 16 }}>{title}</h2>
        {sub && <div className="text-[12.5px]" style={{ color: "var(--ink-soft)" }}>{sub}</div>}
      </div>
      {right}
    </div>
  );
}

// Generic modal shell with progressive disclosure dev-view slot
function Modal({ open, onClose, title, subtitle, children, footer, maxWidth = 720, devJson }) {
  if (!open) return null;
  return (
    <div className="backdrop" onClick={onClose}>
      <div className="sheet" style={{ maxWidth, margin: "80px auto 40px", background: "#fff", borderRadius: 16, boxShadow: "var(--shadow-float)", overflow: "hidden" }} onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between px-6 pt-5 pb-4" style={{ borderBottom: "1px solid var(--line)" }}>
          <div>
            <div className="font-display font-semibold" style={{ fontSize: 18 }}>{title}</div>
            {subtitle && <div className="text-[13px] mt-0.5" style={{ color: "var(--ink-soft)" }}>{subtitle}</div>}
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}><Icon name="close" /></button>
        </div>
        <div className="px-6 py-5 max-h-[64vh] overflow-y-auto scroll-clean">
          {children}
          {devJson && (
            <details className="mt-5" style={{ borderTop: "1px dashed var(--line)", paddingTop: 14 }}>
              <summary className="flex items-center gap-2 text-[13px] font-semibold" style={{ color: "var(--ink-muted)" }}>
                <Icon name="code" style={{ fontSize: 16 }} /> 개발자 뷰 · 원본 JSON 펼치기
              </summary>
              <pre className="json mt-3">{JSON.stringify(devJson, null, 2)}</pre>
            </details>
          )}
        </div>
        {footer && <div className="px-6 py-4 flex items-center justify-end gap-2" style={{ borderTop: "1px solid var(--line)", background: "var(--surface-low)" }}>{footer}</div>}
      </div>
    </div>
  );
}

Object.assign(window, { Sidebar, Topbar, ModeChip, SafetyTrio, ConnectionBanner, SectionHeader, Modal });

// ==== dashboard.jsx ====
// dashboard.jsx — Overview (first screen)

function HeroTodo({ todo, onNav, layout }) {
  // layout: "hero-stats" (big numbers) | "sentence" | "trafficlight"
  const items = [
    { k: "approvals", n: todo.pendingApprovals, label: "승인 대기", sub: "AI 권고", tone: "warn", icon: "how_to_reg", nav: "decisions" },
    { k: "critical",  n: todo.criticalAlerts,   label: "위험 경고", sub: "즉시 확인", tone: "crit", icon: "error", nav: "alerts" },
    { k: "warnings",  n: todo.warnings,         label: "주의 장치", sub: "점검 권장", tone: "warn", icon: "report", nav: "devices" },
  ];

  if (layout === "sentence") {
    return (
      <div className="card p-6 rail-warn" style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 24, alignItems: "center" }}>
        <div>
          <div className="text-[13px] font-semibold" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>오늘의 할 일</div>
          <div className="font-display font-semibold mt-2" style={{ fontSize: 26, lineHeight: 1.25, textWrap: "pretty" }}>
            지금 <span style={{ color: "var(--warn)" }}>승인 대기 {todo.pendingApprovals}건</span>과 <span style={{ color: "var(--crit)" }}>위험 경고 {todo.criticalAlerts}건</span>이 있어요. 먼저 검토해주세요.
          </div>
          <div className="text-[13px] mt-1.5" style={{ color: "var(--ink-muted)" }}>주의 장치 {todo.warnings}개 · 적고추 온실 제2동 · 현장 상태 정상</div>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-primary btn-lg" onClick={() => onNav("decisions")}><Icon name="how_to_reg" /> 승인 검토</button>
          <button className="btn btn-lg" onClick={() => onNav("alerts")}><Icon name="notifications" /> 경고 보기</button>
        </div>
      </div>
    );
  }

  // Default: hero-stats — big numbers
  return (
    <div className="grid-auto resp-3col" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
      {items.map(it => (
        <button key={it.k} className={`card text-left p-5 rail-${it.tone === "crit" ? "crit" : "warn"}`}
          style={{ cursor: "pointer" }} onClick={() => onNav(it.nav)}>
          <div className="flex items-start justify-between">
            <div>
              <div className="text-[12.5px] font-semibold" style={{ color: "var(--ink-soft)", letterSpacing: ".03em" }}>{it.label}</div>
              <div className="font-display tnum" style={{ fontSize: 56, lineHeight: 1.0, marginTop: 8, fontWeight: 700, color: it.n > 0 ? (it.tone === "crit" ? "var(--crit)" : "var(--warn)") : "var(--ink)" }}>
                {it.n}
                <span className="text-[16px] ml-1" style={{ color: "var(--ink-soft)" }}>건</span>
              </div>
              <div className="text-[13px] mt-1" style={{ color: "var(--ink-muted)" }}>{it.sub}</div>
            </div>
            <div className="rounded-lg flex items-center justify-center" style={{ width: 40, height: 40, background: it.tone === "crit" ? "var(--crit-tint)" : "var(--warn-tint)" }}>
              <Icon name={it.icon} style={{ fontSize: 22, color: it.tone === "crit" ? "var(--crit)" : "var(--warn)" }} />
            </div>
          </div>
          <div className="hairline mt-4 pt-3 flex items-center justify-between text-[13px]" style={{ color: "var(--ink-muted)" }}>
            <span>자세히 보기</span>
            <Icon name="arrow_forward" style={{ fontSize: 18 }} />
          </div>
        </button>
      ))}
    </div>
  );
}

function MetricCard({ m }) {
  const tone = m.state === "warn" ? "warn" : m.state === "crit" ? "crit" : "brand";
  const deltaTxt = (m.delta > 0 ? "+" : "") + m.delta + " " + m.unit;
  return (
    <div className={`card p-4 rail-${m.state}`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[12.5px] font-semibold" style={{ color: "var(--ink-muted)" }}>{m.name}</div>
          <div className="text-[11px]" style={{ color: "var(--ink-soft)" }}>정상 범위 {m.range}</div>
        </div>
        <StatusChip state={m.state} />
      </div>
      <div className="flex items-end justify-between mt-3">
        <div className="flex items-baseline gap-1.5">
          <div className="font-display tnum" style={{ fontSize: 30, fontWeight: 700, lineHeight: 1 }}>{m.value}</div>
          <div className="text-[13px]" style={{ color: "var(--ink-soft)" }}>{m.unit}</div>
        </div>
        <Sparkline points={MOCK.sparks[m.key]} tone={tone} />
      </div>
      <div className="hairline mt-3 pt-2 flex items-center justify-between text-[12px]" style={{ color: "var(--ink-muted)" }}>
        <span className="flex items-center gap-1">
          <Icon name={m.delta >= 0 ? "north_east" : "south_east"} style={{ fontSize: 14, color: m.state === "warn" ? "var(--warn)" : "var(--ink-soft)" }} />
          24시간 {deltaTxt}
        </span>
        <span>방금 전</span>
      </div>
    </div>
  );
}

function ZoneTile({ z, onClick }) {
  return (
    <button className={`card p-4 text-left rail-${z.state}`} onClick={onClick} style={{ cursor: "pointer" }}>
      <div className="flex items-center justify-between">
        <div className="font-display font-semibold" style={{ fontSize: 15 }}>{z.name}</div>
        <StatusChip state={z.state} />
      </div>
      <div className="text-[12.5px] mt-1" style={{ color: "var(--ink-muted)" }}>{z.crop}</div>
      <div className="flex items-center gap-4 mt-3 tnum">
        <span className="text-[13px]"><span style={{ color: "var(--ink-soft)" }}>온도</span> <b>{z.temp}</b><span style={{ color: "var(--ink-soft)", fontSize: 11 }}>°C</span></span>
        <span className="text-[13px]"><span style={{ color: "var(--ink-soft)" }}>습도</span> <b>{z.hum}</b><span style={{ color: "var(--ink-soft)", fontSize: 11 }}>%</span></span>
      </div>
      <div className="text-[12px] mt-1" style={{ color: z.state === "crit" ? "var(--crit)" : z.state === "warn" ? "var(--warn)" : "var(--ink-soft)" }}>{z.note}</div>
    </button>
  );
}

function TimelineRow({ item }) {
  const iconColor = item.state === "warn" ? "var(--warn)" : item.state === "crit" ? "var(--crit)" : "var(--ok)";
  return (
    <div className="flex items-start gap-3 py-3" style={{ borderBottom: "1px solid var(--line-soft)" }}>
      <div className="rounded-full flex items-center justify-center shrink-0" style={{ width: 30, height: 30, background: "var(--surface-low)", border: "1px solid var(--line)" }}>
        <Icon name={item.icon} style={{ fontSize: 16, color: iconColor }} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[13.5px]" style={{ lineHeight: 1.5 }}>{item.text}</div>
        <div className="text-[11.5px] mt-0.5" style={{ color: "var(--ink-soft)" }}>{item.t}</div>
      </div>
      <button className="btn btn-ghost btn-sm"><Icon name="chevron_right" style={{ fontSize: 18 }} /></button>
    </div>
  );
}

function GreenhouseMini() {
  return (
    <div className="card p-5 gh-glyph" style={{ minHeight: 176, display: "flex", alignItems: "center", gap: 20 }}>
      <svg width="140" height="110" viewBox="0 0 140 110" style={{ filter: "drop-shadow(0 2px 8px rgba(0,106,38,.18))" }}>
        {/* ground */}
        <rect x="6" y="92" width="128" height="12" rx="2" fill="#cfe0d3" />
        {/* greenhouse arch */}
        <path d="M14 92 L14 54 Q70 6 126 54 L126 92 Z" fill="#ffffff" stroke="#9ac4ae" strokeWidth="1.5" />
        <path d="M70 14 L70 92" stroke="#d6e4dc" strokeWidth="1" />
        <path d="M14 54 Q70 6 126 54" fill="none" stroke="#9ac4ae" strokeWidth="1.5" />
        {/* zone dots */}
        <circle cx="34" cy="78" r="5" fill="var(--warn)" />
        <circle cx="58" cy="78" r="5" fill="var(--ok)" />
        <circle cx="82" cy="78" r="5" fill="var(--ok)" />
        <circle cx="106" cy="78" r="5" fill="var(--crit)" />
        {/* rain */}
        <g stroke="#7db0c9" strokeWidth="1.5" strokeLinecap="round" opacity="0.7">
          <line x1="36" y1="4" x2="32" y2="10" />
          <line x1="58" y1="2" x2="54" y2="9" />
          <line x1="88" y1="6" x2="84" y2="12" />
          <line x1="106" y1="2" x2="102" y2="8" />
        </g>
      </svg>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="chip chip-info"><Icon name="water_drop" /> 외부 강우 중</span>
          <span className="chip chip-mute">풍속 4.2 m/s</span>
        </div>
        <div className="font-display font-semibold mt-2" style={{ fontSize: 17 }}>{MOCK.greenhouse.name}</div>
        <div className="text-[12.5px] mt-0.5" style={{ color: "var(--ink-muted)" }}>4개 구역 · 3개 정상 · 1개 경고 · 1개 위험</div>
      </div>
    </div>
  );
}

function Dashboard({ tweaks, setRoute, onOpenApproval }) {
  return (
    <div className="p-6 space-y-6">
      {/* Hero */}
      <section>
        <div className="flex items-baseline justify-between mb-3">
          <div>
            <div className="text-[12px] font-semibold" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>Overview</div>
            <h1 className="font-display font-semibold" style={{ fontSize: 22 }}>안녕하세요, 이영호 님</h1>
          </div>
          <div className="text-[12.5px]" style={{ color: "var(--ink-soft)" }}>2026-04-21 화요일 · 오후 2:34</div>
        </div>
        <HeroTodo todo={MOCK.todo} onNav={setRoute} layout={tweaks.dashboardLayout} />
      </section>

      {/* Metrics */}
      <section>
        <SectionHeader
          title="환경 요약"
          sub="지금 주요 구역의 환경 수치. 주의 이상 상태만 색으로 표시합니다."
          right={
            <div className="flex items-center gap-2">
              <button className="btn btn-sm"><Icon name="grid_view" style={{ fontSize: 16 }} /> A구역</button>
              <button className="btn btn-sm btn-ghost">B구역</button>
              <button className="btn btn-sm btn-ghost">C구역</button>
              <button className="btn btn-sm btn-ghost">D구역</button>
              <span className="hairline-v h-6 mx-1"></span>
              <button className="btn btn-sm" onClick={() => setRoute("zones")}>구역 상세 <Icon name="arrow_forward" style={{ fontSize: 16 }}/></button>
            </div>
          }
        />
        <div className="grid-auto resp-3col" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
          {MOCK.metrics.map(m => <MetricCard key={m.key} m={m} />)}
        </div>
      </section>

      <div className="grid-auto resp-2col" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
        {/* Approvals teaser */}
        <section>
          <SectionHeader title="AI가 권고한 조치" sub="승인하시면 실행됩니다. 상세 근거도 함께 확인하세요." right={
            <button className="btn btn-sm" onClick={() => setRoute("decisions")}>전체 보기 <Icon name="arrow_forward" style={{fontSize:16}}/></button>
          } />
          <div className="space-y-3">
            {MOCK.pending.map(p => (
              <div key={p.id} className={`card p-5 rail-${p.risk}`}>
                <div className="flex items-start gap-3">
                  <div className="rounded-lg flex items-center justify-center shrink-0" style={{ width: 38, height: 38, background: "var(--brand-tint)" }}>
                    <Icon name="smart_toy" style={{ color: "var(--brand)", fontSize: 20 }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="chip chip-brand"><Icon name="place" />{p.zone}</span>
                      <StatusChip state={p.risk === "ok" ? "ok" : "warn"}>{p.risk === "ok" ? "안전" : "주의"}</StatusChip>
                      <span className="text-[11.5px] ml-auto" style={{ color: "var(--ink-soft)" }}>{p.createdAt}</span>
                    </div>
                    <div className="font-display" style={{ fontSize: 16, fontWeight: 600, lineHeight: 1.4, textWrap: "pretty" }}>{p.summary}</div>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {p.reasons.slice(0,2).map((r,i) => <span key={i} className="chip chip-mute">{r}</span>)}
                      {p.reasons.length > 2 && <span className="chip chip-mute">+{p.reasons.length-2}</span>}
                    </div>
                  </div>
                </div>
                <div className="hairline mt-4 pt-3 flex items-center gap-2">
                  <button className="btn btn-primary btn-sm" onClick={() => onOpenApproval(p)}><Icon name="check" style={{fontSize:16}}/> 승인</button>
                  <button className="btn btn-sm"><Icon name="close" style={{fontSize:16}}/> 거절</button>
                  <button className="btn btn-ghost btn-sm ml-auto" onClick={() => onOpenApproval(p)}>상세 근거 <Icon name="arrow_forward" style={{fontSize:16}}/></button>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Zones + Timeline */}
        <section className="space-y-6">
          <div>
            <SectionHeader title="구역" sub="클릭하면 해당 구역의 24시간 추이를 확인합니다." />
            <div className="grid-auto resp-2col" style={{ gridTemplateColumns: "1fr 1fr" }}>
              {MOCK.zones.map(z => <ZoneTile key={z.name} z={z} onClick={() => setRoute("zones")} />)}
            </div>
          </div>

          <GreenhouseMini />

          <div>
            <SectionHeader title="최근 이벤트" sub="지난 1시간 · 자동·수동 이벤트" right={<button className="btn btn-ghost btn-sm">모두 보기</button>} />
            <div className="card px-4">
              {MOCK.timeline.map((t,i) => <TimelineRow key={i} item={t} />)}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

Object.assign(window, { Dashboard, MetricCard, ZoneTile, TimelineRow, GreenhouseMini, HeroTodo });

// ==== decisions.jsx ====
// decisions.jsx — Decisions/Approval queue + detail modal

function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <div style={{ width: 120, height: 6, borderRadius: 999, background: "var(--line-soft)", overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: "linear-gradient(90deg, var(--brand-500), var(--brand-700))" }}></div>
      </div>
      <div className="text-[12.5px] tnum" style={{ color: "var(--ink-muted)", fontWeight: 600 }}>{pct}%</div>
    </div>
  );
}

function DecisionCard({ d, onOpen, onApprove, onReject, style }) {
  // style: "list" | "stack" | "split"
  return (
    <div className={`card p-5 rail-${d.risk === "ok" ? "ok" : "warn"}`}>
      <div className="flex items-start gap-4">
        <div className="rounded-lg flex items-center justify-center shrink-0" style={{ width: 44, height: 44, background: "var(--brand-tint)" }}>
          <Icon name="smart_toy" style={{ color: "var(--brand)", fontSize: 22 }} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="chip chip-brand"><Icon name="place" />{d.zone}</span>
            <StatusChip state={d.risk === "ok" ? "ok" : "warn"}>{d.risk === "ok" ? "안전" : "주의"}</StatusChip>
            <span className="chip chip-mute"><Icon name="schedule" /> {d.createdAt}</span>
            <span className="chip chip-mute" title="AI 신뢰도">
              <Icon name="insights" /> 신뢰도 {Math.round(d.confidence*100)}%
            </span>
          </div>
          <div className="font-display" style={{ fontSize: 17, fontWeight: 600, lineHeight: 1.4, textWrap: "pretty" }}>{d.summary}</div>

          <div className="mt-3">
            <div className="text-[12px] font-semibold mb-1.5" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>근거</div>
            <div className="flex flex-wrap gap-1.5">
              {d.reasons.map((r,i) => <span key={i} className="chip chip-mute" style={{ maxWidth: "100%" }}>{r}</span>)}
            </div>
          </div>

          <div className="mt-4" style={{ background: "var(--surface-low)", border: "1px solid var(--line)", borderRadius: 10, padding: 12 }}>
            <div className="text-[12px] font-semibold mb-1.5" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>승인 시 실행</div>
            <div className="space-y-1.5">
              {d.plan.map((p,i) => (
                <div key={i} className="flex items-center gap-2 text-[13.5px]">
                  <Icon name="arrow_right" style={{ fontSize: 18, color: "var(--brand)" }} />
                  <span style={{ fontWeight: 600 }}>{p.device}</span>
                  <span style={{ color: "var(--ink-muted)" }}>— {p.action}</span>
                  <span className="ml-auto text-[12px]" style={{ color: "var(--ink-soft)" }}>{p.etc}</span>
                </div>
              ))}
            </div>
            <div className="hairline mt-2.5 pt-2.5 text-[12.5px] flex items-center gap-1.5" style={{ color: "var(--ink-muted)" }}>
              <Icon name="auto_graph" style={{ fontSize: 14 }} />
              예상 결과: {d.impact}
            </div>
          </div>
        </div>
      </div>

      <div className="hairline mt-4 pt-3 flex items-center gap-2">
        <button className="btn btn-primary" onClick={() => onApprove(d)}>
          <Icon name="check" style={{ fontSize: 18 }} /> 승인하고 실행
        </button>
        <button className="btn btn-danger" onClick={() => onReject(d)}>
          <Icon name="close" style={{ fontSize: 18 }} /> 거절
        </button>
        <button className="btn btn-ghost ml-auto" onClick={() => onOpen(d)}>
          상세 근거 보기 <Icon name="arrow_forward" style={{ fontSize: 16 }} />
        </button>
      </div>
    </div>
  );
}

function DecisionDetailModal({ d, open, onClose, onApprove, onReject, devViewUnlocked }) {
  if (!d) return null;
  const devJson = devViewUnlocked ? {
    decision_id: d.id === "dec-3" ? 3 : 4,
    request_id: "automation-42-" + d.id,
    runtime_mode_gate: "approval",
    parsed_output_json: {
      action: d.plan.map(p => ({ target: p.device, op: p.action })),
      reasons: d.reasons,
    },
    validator_reason_codes_json: ["HSV-01:pass", "HSV-03:pass", "HSV-07:pass"],
    model_family: "ds_v11", prompt_version: "sft_v10",
    confidence: d.confidence,
  } : null;

  return (
    <Modal
      open={open} onClose={onClose} maxWidth={760}
      title="AI 권고 상세"
      subtitle={d.zone + " · " + d.createdAt}
      footer={
        <>
          <button className="btn" onClick={onClose}>취소</button>
          <button className="btn btn-danger" onClick={() => { onReject(d); onClose(); }}><Icon name="close"/> 거절</button>
          <button className="btn btn-primary" onClick={() => { onApprove(d); onClose(); }}><Icon name="check"/> 승인하고 실행</button>
        </>
      }
      devJson={devJson}
    >
      <div className="card-ghost p-4 rail-warn mb-4">
        <div className="flex items-center gap-2 mb-1">
          <Icon name="smart_toy" style={{ color: "var(--brand)" }} />
          <span className="chip chip-brand">적고추 전문 AI</span>
        </div>
        <div className="font-display" style={{ fontSize: 18, fontWeight: 600, lineHeight: 1.4 }}>{d.summary}</div>
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>왜 이 권고인가</div>
          <ul className="space-y-2">
            {d.reasons.map((r,i) => (
              <li key={i} className="flex items-start gap-2 text-[13.5px]" style={{ lineHeight: 1.5 }}>
                <Icon name="fiber_manual_record" style={{ fontSize: 8, color: "var(--brand)", marginTop: 8 }} />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>안전 검증</div>
          <div className="space-y-2">
            {[
              { lbl: "AI 응답 형식", state: "ok" },
              { lbl: "정책 규칙 (EC/온도/풍속)", state: "ok" },
              { lbl: "장치 잠금 및 쿨다운", state: "ok" },
              { lbl: "실행 권한", state: "ok" },
            ].map((c,i) => (
              <div key={i} className="flex items-center gap-2 text-[13px]" style={{ padding: "6px 10px", background: "var(--ok-tint)", border: "1px solid #bde5d2", borderRadius: 8 }}>
                <Icon name="verified" style={{ color: "var(--ok)", fontSize: 16 }} /> {c.lbl}
              </div>
            ))}
          </div>
          <div className="mt-3 text-[12px]" style={{ color: "var(--ink-muted)" }}>AI 신뢰도</div>
          <div className="mt-1"><ConfidenceBar value={d.confidence} /></div>
        </div>
      </div>

      <div className="hairline mt-5 pt-4">
        <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>실행 계획</div>
        <div className="card-ghost" style={{ padding: 2 }}>
          {d.plan.map((p, i) => (
            <div key={i} className="flex items-center gap-3 px-3 py-2.5" style={{ borderBottom: i < d.plan.length-1 ? "1px solid var(--line-soft)" : "none" }}>
              <div className="rounded-md flex items-center justify-center" style={{ width: 32, height: 32, background: "var(--brand-tint)" }}>
                <Icon name="settings_remote" style={{ color: "var(--brand)", fontSize: 18 }} />
              </div>
              <div className="flex-1">
                <div className="text-[13.5px]" style={{ fontWeight: 600 }}>{p.device}</div>
                <div className="text-[12.5px]" style={{ color: "var(--ink-muted)" }}>{p.action}</div>
              </div>
              <div className="text-[12px]" style={{ color: "var(--ink-soft)" }}>{p.etc}</div>
            </div>
          ))}
        </div>
        <div className="mt-2 text-[13px] flex items-center gap-1.5" style={{ color: "var(--ink-muted)" }}>
          <Icon name="auto_graph" style={{ fontSize: 16 }} />
          예상 결과: <span style={{ color: "var(--ink)" }}>{d.impact}</span>
        </div>
      </div>
    </Modal>
  );
}

function DecisionsPage({ devViewUnlocked, tweaks }) {
  const [openItem, setOpenItem] = React.useState(null);
  const [toast, setToast] = React.useState(null);
  const [filter, setFilter] = React.useState("all");
  const items = MOCK.pending;

  const handle = (action) => (d) => {
    setToast({ kind: action, zone: d.zone });
    setTimeout(() => setToast(null), 2800);
  };

  return (
    <div className="p-6">
      <SectionHeader
        title="결정 · 승인"
        sub="AI가 권고한 조치. 한 문장으로 요약하고, 근거와 실행 계획을 함께 보여줍니다."
        right={
          <div className="flex items-center gap-2">
            {[["all","전체",items.length],["warn","주의",1],["ok","안전",1],["mine","내 담당",2]].map(([k,l,n]) => (
              <button key={k} onClick={()=>setFilter(k)} className={`btn btn-sm ${filter===k ? "" : "btn-ghost"}`}>
                {l} <span className="tnum" style={{ color: "var(--ink-soft)", marginLeft: 4 }}>{n}</span>
              </button>
            ))}
          </div>
        }
      />

      <div className="space-y-3 max-w-[920px]">
        {items.map(d => (
          <DecisionCard key={d.id} d={d}
            onOpen={setOpenItem}
            onApprove={handle("approved")}
            onReject={handle("rejected")}
            style={tweaks.approvalStyle}
          />
        ))}

        <div className="card p-6 text-center" style={{ borderStyle: "dashed", background: "transparent" }}>
          <Icon name="task_alt" style={{ fontSize: 28, color: "var(--ok)" }} />
          <div className="font-display font-semibold mt-2" style={{ fontSize: 15 }}>모든 권고를 확인했습니다</div>
          <div className="text-[13px]" style={{ color: "var(--ink-soft)" }}>새 권고가 도착하면 여기에 표시됩니다.</div>
        </div>
      </div>

      <DecisionDetailModal
        d={openItem} open={!!openItem} onClose={() => setOpenItem(null)}
        onApprove={handle("approved")} onReject={handle("rejected")}
        devViewUnlocked={devViewUnlocked}
      />

      {toast && (
        <div style={{ position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)", zIndex: 60 }}>
          <div className="sheet" style={{ background: toast.kind === "approved" ? "var(--ok)" : "var(--ink)", color: "#fff", padding: "12px 18px", borderRadius: 10, boxShadow: "var(--shadow-float)", display: "flex", alignItems: "center", gap: 10, fontSize: 14, fontWeight: 600 }}>
            <Icon name={toast.kind === "approved" ? "check_circle" : "cancel"} />
            {toast.zone} 권고를 {toast.kind === "approved" ? "승인했습니다. 실행 중…" : "거절했습니다."}
          </div>
        </div>
      )}
    </div>
  );
}

Object.assign(window, { DecisionsPage, DecisionCard, DecisionDetailModal, ConfidenceBar });

// ==== rules.jsx ====
// rules.jsx — Automation rules list + 3-step wizard

function RuleRow({ r, onEdit, onToggle }) {
  // Optimistic toggle: flip locally first, then PATCH; on error revert.
  // Passing onToggle is optional so MOCK-only callers still render.
  const [enabled, setEnabled] = React.useState(r.enabled);
  const [pending, setPending] = React.useState(false);
  React.useEffect(() => { setEnabled(r.enabled); }, [r.enabled]);
  const modeChip = {
    shadow:   <span className="chip chip-mute"><Icon name="visibility"/> 섀도우</span>,
    approval: <span className="chip chip-warn"><Icon name="how_to_reg"/> 승인 필요</span>,
    execute:  <span className="chip chip-ok"><Icon name="bolt"/> 자동 실행</span>,
  }[r.mode];

  const handleToggle = async (e) => {
    const next = e.target.checked;
    if (!onToggle) { setEnabled(next); return; }
    setEnabled(next);
    setPending(true);
    try {
      await onToggle(r.rule_id || r.id, next);
    } catch (err) {
      setEnabled(!next); // revert on failure
      alert("규칙 상태 변경 실패: " + (err.message || err));
    } finally {
      setPending(false);
    }
  };

  return (
    <div className={`card p-4 ${enabled ? "" : "opacity-70"}`}>
      <div className="flex items-center gap-4">
        <label className="relative inline-flex items-center cursor-pointer shrink-0" onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={enabled}
            onChange={handleToggle}
            disabled={pending}
            className="sr-only peer"
          />
          <div className="w-11 h-6 rounded-full transition-colors" style={{ background: enabled ? "var(--brand)" : "#cfd6d1", opacity: pending ? 0.6 : 1 }}>
            <div className="w-5 h-5 rounded-full bg-white shadow-sm transition-transform" style={{ transform: `translate(${enabled ? 22 : 2}px, 2px)` }}></div>
          </div>
        </label>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <div className="font-display font-semibold" style={{ fontSize: 15 }}>{r.name}</div>
            {modeChip}
          </div>
          <div className="text-[13px] flex items-center gap-1.5 flex-wrap" style={{ color: "var(--ink-muted)" }}>
            <Icon name="sensors" style={{ fontSize: 14 }} />
            <span>{r.when}</span>
            <Icon name="arrow_right_alt" style={{ fontSize: 16 }} />
            <Icon name="settings_remote" style={{ fontSize: 14 }} />
            <span>{r.then}</span>
          </div>
        </div>

        <div className="text-right shrink-0">
          <div className="text-[12px] tnum" style={{ color: "var(--ink-soft)" }}>지난 24h</div>
          <div className="font-display tnum" style={{ fontSize: 18, fontWeight: 700 }}>{r.runs24h}<span className="text-[11px] font-normal" style={{ color: "var(--ink-soft)", marginLeft: 2 }}>회 실행</span></div>
          <div className="text-[11.5px]" style={{ color: "var(--ink-soft)" }}>마지막 {r.last}</div>
        </div>

        <button className="btn btn-ghost btn-sm" onClick={() => onEdit(r)}><Icon name="edit" style={{ fontSize: 18 }} /></button>
      </div>
    </div>
  );
}

function WizardStepper({ step, labels }) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {labels.map((l, i) => {
        const n = i + 1;
        const active = step === n;
        const done = step > n;
        return (
          <React.Fragment key={i}>
            <div className="flex items-center gap-2">
              <div className="rounded-full flex items-center justify-center tnum" style={{
                width: 28, height: 28, fontWeight: 700, fontSize: 13,
                background: done ? "var(--brand)" : active ? "var(--brand-tint)" : "var(--surface-low)",
                color: done ? "#fff" : active ? "var(--brand-700)" : "var(--ink-soft)",
                border: `1px solid ${done ? "var(--brand)" : active ? "var(--brand-tint-2)" : "var(--line)"}`,
              }}>
                {done ? <Icon name="check" style={{ fontSize: 16 }} /> : n}
              </div>
              <div className={`text-[13.5px] ${active ? "font-semibold" : ""}`} style={{ color: active ? "var(--ink)" : done ? "var(--brand-700)" : "var(--ink-soft)" }}>{l}</div>
            </div>
            {i < labels.length - 1 && <div style={{ flex: 1, height: 1, background: done ? "var(--brand)" : "var(--line)" }}></div>}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function RuleWizard({ open, onClose, editing }) {
  const [step, setStep] = React.useState(1);
  const [form, setForm] = React.useState({
    name: editing?.name || "",
    sensor: "air_humid", op: "gte", value: 85, duration: 10, zone: "all",
    device: "vent_roof", action: "close", actionValue: 20,
    mode: "approval", cooldown: 15,
  });
  React.useEffect(() => { if (open) setStep(1); }, [open]);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const Summary = () => (
    <div className="card-ghost p-4" style={{ background: "var(--surface-low)" }}>
      <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>요약 미리보기</div>
      <div className="font-display" style={{ fontSize: 15, lineHeight: 1.5, textWrap: "pretty" }}>
        <b>{form.zone === "all" ? "모든 구역" : form.zone + "구역"}</b>에서{" "}
        <span className="chip chip-mute">{MOCK.sensors.find(s=>s.key===form.sensor)?.label}</span>이{" "}
        <span className="chip chip-mute">{MOCK.operators.find(o=>o.key===form.op)?.label} {form.value}</span>{" "}
        상태가 <b>{form.duration}분</b> 지속되면, <span className="chip chip-brand">{MOCK.devices.find(d=>d.key===form.device)?.label}</span>을(를){" "}
        <b>{form.action === "close" ? `${form.actionValue}%로 닫고` : form.action === "open" ? `${form.actionValue}%로 열고` : "작동하고"}</b>
        {" "}그 다음은 <span className="chip chip-warn"><Icon name="how_to_reg"/>{form.mode === "execute" ? "자동 실행" : form.mode === "approval" ? "승인 대기" : "섀도우 기록"}</span>입니다.
      </div>
    </div>
  );

  return (
    <Modal
      open={open} onClose={onClose} maxWidth={780}
      title={editing ? "규칙 편집" : "새 자동화 규칙 만들기"}
      subtitle="3단계로 간단하게. 개발자 도움 없이 직접 만들 수 있어요."
      footer={
        <>
          <button className="btn" onClick={onClose}>취소</button>
          {step > 1 && <button className="btn" onClick={() => setStep(step-1)}><Icon name="arrow_back" style={{ fontSize: 16 }}/> 이전</button>}
          {step < 3
            ? <button className="btn btn-primary" onClick={() => setStep(step+1)}>다음 <Icon name="arrow_forward" style={{ fontSize: 16 }}/></button>
            : <button className="btn btn-primary" onClick={onClose}><Icon name="check"/> 규칙 저장</button>}
        </>
      }
    >
      <WizardStepper step={step} labels={["언제", "무엇을", "안전"]} />

      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="text-[13px] font-semibold">규칙 이름</label>
            <input className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px]" style={{ border: "1px solid var(--line)" }} placeholder="예: 습도 높을 때 제습팬 켜기" value={form.name} onChange={e=>set("name", e.target.value)} />
          </div>
          <div className="grid gap-3" style={{ gridTemplateColumns: "2fr 1fr 1fr" }}>
            <div>
              <label className="text-[13px] font-semibold">어떤 센서를?</label>
              <select className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px]" style={{ border: "1px solid var(--line)" }} value={form.sensor} onChange={e=>set("sensor", e.target.value)}>
                {MOCK.sensors.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[13px] font-semibold">조건</label>
              <select className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px]" style={{ border: "1px solid var(--line)" }} value={form.op} onChange={e=>set("op", e.target.value)}>
                {MOCK.operators.map(o => <option key={o.key} value={o.key}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[13px] font-semibold">값</label>
              <input type="number" className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px] tnum" style={{ border: "1px solid var(--line)" }} value={form.value} onChange={e=>set("value", +e.target.value)} />
            </div>
          </div>
          <div className="grid gap-3" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div>
              <label className="text-[13px] font-semibold">지속 시간 (분)</label>
              <input type="number" className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px] tnum" style={{ border: "1px solid var(--line)" }} value={form.duration} onChange={e=>set("duration", +e.target.value)} />
              <div className="text-[11.5px] mt-1" style={{ color: "var(--ink-soft)" }}>짧은 센서 튐을 거르기 위해 최소 1분 이상 권장</div>
            </div>
            <div>
              <label className="text-[13px] font-semibold">적용 구역</label>
              <select className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px]" style={{ border: "1px solid var(--line)" }} value={form.zone} onChange={e=>set("zone", e.target.value)}>
                <option value="all">모든 구역</option>
                <option value="A">A구역</option><option value="B">B구역</option><option value="C">C구역</option><option value="D">D구역</option>
              </select>
            </div>
          </div>
          <Summary />
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <label className="text-[13px] font-semibold">어떤 장치를 움직일까요?</label>
            <div className="mt-2 grid gap-2" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
              {MOCK.devices.map(d => (
                <button key={d.key} onClick={() => set("device", d.key)}
                  className="card-ghost p-3 text-center"
                  style={{ cursor: "pointer", borderColor: form.device === d.key ? "var(--brand)" : "var(--line)", background: form.device === d.key ? "var(--brand-tint)" : "#fff", borderWidth: form.device === d.key ? 2 : 1 }}>
                  <Icon name={
                    d.key === "vent_roof" ? "unfold_less" :
                    d.key === "fan_dehum" ? "mode_fan" :
                    d.key === "irrigation" ? "water_drop" :
                    d.key === "grow_light" ? "wb_incandescent" :
                    d.key === "co2_inject" ? "co2" :
                    d.key === "heater" ? "local_fire_department" :
                    d.key === "cooler" ? "ac_unit" : "blinds"
                  } style={{ fontSize: 24, color: form.device === d.key ? "var(--brand)" : "var(--ink-muted)" }} />
                  <div className="text-[12.5px] mt-1" style={{ fontWeight: form.device === d.key ? 700 : 500 }}>{d.label}</div>
                </button>
              ))}
            </div>
          </div>
          <div className="grid gap-3" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div>
              <label className="text-[13px] font-semibold">동작</label>
              <select className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px]" style={{ border: "1px solid var(--line)" }} value={form.action} onChange={e=>set("action", e.target.value)}>
                <option value="close">닫기 (%)</option>
                <option value="open">열기 (%)</option>
                <option value="level">단계 설정</option>
                <option value="on">켜기</option>
                <option value="off">끄기</option>
              </select>
            </div>
            <div>
              <label className="text-[13px] font-semibold">값 ({form.action === "level" ? "단계" : "%"})</label>
              <input type="number" className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px] tnum" style={{ border: "1px solid var(--line)" }} value={form.actionValue} onChange={e=>set("actionValue", +e.target.value)} />
            </div>
          </div>
          <Summary />
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <div>
            <label className="text-[13px] font-semibold">실행 방식</label>
            <div className="mt-2 space-y-2">
              {[
                { key: "shadow",   title: "섀도우 기록", desc: "실제로 실행하지 않고 기록만. 신규 규칙 안전 테스트에 권장.", icon: "visibility" },
                { key: "approval", title: "승인 대기",   desc: "조건 충족 시 관리자가 확인 후 승인. 가장 안전.", icon: "how_to_reg" },
                { key: "execute",  title: "자동 실행",   desc: "조건 충족 시 즉시 실행. 검증된 규칙만 사용하세요.", icon: "bolt" },
              ].map(o => (
                <label key={o.key} className="card-ghost p-3 flex items-start gap-3 cursor-pointer"
                  style={{ borderColor: form.mode === o.key ? "var(--brand)" : "var(--line)", background: form.mode === o.key ? "var(--brand-tint)" : "#fff", borderWidth: form.mode === o.key ? 2 : 1 }}>
                  <input type="radio" name="mode" checked={form.mode === o.key} onChange={() => set("mode", o.key)} className="mt-1" style={{ accentColor: "var(--brand)" }} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Icon name={o.icon} style={{ fontSize: 18, color: "var(--brand)" }} />
                      <div className="font-semibold" style={{ fontSize: 14 }}>{o.title}</div>
                    </div>
                    <div className="text-[12.5px] mt-1" style={{ color: "var(--ink-muted)" }}>{o.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="text-[13px] font-semibold">재발 방지 간격 (쿨다운)</label>
            <div className="mt-1.5 flex items-center gap-3">
              <input type="range" min="1" max="60" value={form.cooldown} onChange={e => set("cooldown", +e.target.value)} style={{ flex: 1, accentColor: "var(--brand)" }} />
              <div className="tnum font-display font-semibold" style={{ minWidth: 70, textAlign: "right" }}>{form.cooldown}<span style={{ fontWeight: 400, color: "var(--ink-soft)", fontSize: 13, marginLeft: 3 }}>분</span></div>
            </div>
            <div className="text-[11.5px] mt-1" style={{ color: "var(--ink-soft)" }}>규칙이 한 번 실행된 뒤 재실행까지 대기할 시간</div>
          </div>

          <div className="card-ghost p-3 flex items-start gap-3" style={{ background: "var(--info-tint)", borderColor: "#c4d6ef" }}>
            <Icon name="shield" style={{ color: "var(--info)", fontSize: 20, marginTop: 2 }} />
            <div className="text-[13px]" style={{ color: "#143f7a", lineHeight: 1.5 }}>
              이 규칙은 <b>3단 안전 파이프라인</b>을 거쳐 실행됩니다. AI 형식 검증 → 정책 검증(EC 상한 등 HSV 규칙) → 실행 게이트웨이의 장치 잠금 확인.
            </div>
          </div>

          <Summary />
        </div>
      )}
    </Modal>
  );
}

// Phase T-2b: human-readable label tables so server enums render
// naturally in the "when / then" sentence. Keep them lightweight and
// fall back to the raw key when unseen, since the server catalogue
// (21 sensors × 8 device types × 6 operators) can grow.
const RULES_SENSOR_LABELS = {
  air_temp_c: "기온 (°C)", rh_pct: "습도 (%)", vpd_kpa: "VPD (kPa)",
  co2_ppm: "CO₂ (ppm)", par_umol_m2_s: "광량 (μmol)",
  substrate_moisture_pct: "근권 수분 (%)", substrate_temp_c: "근권 온도 (°C)",
  substrate_ec_ds_m: "근권 EC (dS/m)",
  feed_ec_ds_m: "공급 EC (dS/m)", drain_ec_ds_m: "배액 EC (dS/m)",
  outside_rain_mm_10min: "외부 강우 (mm/10min)",
  outside_wind_ms: "외부 풍속 (m/s)",
  outside_temp_c: "외기 (°C)",
};
const RULES_OPERATOR_LABELS = {
  gt: ">", gte: "≥", lt: "<", lte: "≤", eq: "=",
  between: "범위", ne: "≠",
};
const RULES_DEVICE_LABELS = {
  roof_vent: "천장 개폐기", vent_window: "천장 개폐기",
  hvac_geothermal: "냉난방기", humidifier: "제습/가습기",
  fertigation_mixer: "양액 혼합기", irrigation_pump: "관수 밸브",
  shade_curtain: "차광막", fan_circulation: "순환팬",
  fan_dehum: "제습팬", co2_injector: "CO₂ 주입기",
  grow_light: "보광등", heater: "난방기",
};
const RULES_ACTION_LABELS = {
  adjust_vent: "개폐 조정", close_vent: "닫기", open_vent: "열기",
  set_level: "단계 설정", turn_on: "켜기", turn_off: "끄기",
};

function adaptServerRule(sr) {
  // Turn server serialize_rule() output → the shape RuleRow expects.
  const sensor = RULES_SENSOR_LABELS[sr.sensor_key] || sr.sensor_key || "";
  const op = RULES_OPERATOR_LABELS[sr.operator] || sr.operator || "";
  const threshold = sr.threshold_value != null
    ? sr.threshold_value
    : (sr.threshold_min != null && sr.threshold_max != null
        ? `${sr.threshold_min} ~ ${sr.threshold_max}`
        : "—");
  const device = RULES_DEVICE_LABELS[sr.target_device_type] || sr.target_device_type || "";
  const action = RULES_ACTION_LABELS[sr.target_action] || sr.target_action || "";
  return {
    id: sr.id,
    rule_id: sr.rule_id,
    name: sr.name || sr.rule_id,
    enabled: !!sr.enabled,
    when: `${sensor} ${op} ${threshold}`,
    then: `${device} ${action}`.trim(),
    mode: sr.runtime_mode_gate || "approval",
    runs24h: 0,   // Phase T-2c will aggregate /automation/triggers
    last: "—",
  };
}

async function fetchAutomationRules() {
  const res = await fetch("/automation/rules", { credentials: "same-origin" });
  if (!res.ok) throw new Error(`GET /automation/rules ${res.status}`);
  const body = await res.json();
  const rules = (body?.data?.rules) || [];
  return rules.map(adaptServerRule);
}

async function toggleAutomationRuleServer(ruleId, enabled) {
  const res = await fetch(`/automation/rules/${encodeURIComponent(ruleId)}/toggle`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ enabled }),
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => "");
    throw new Error(`PATCH toggle ${res.status} ${msg.slice(0, 120)}`);
  }
}

function RulesPage() {
  const [wizardOpen, setWizardOpen] = React.useState(false);
  const [editing, setEditing] = React.useState(null);
  const [rules, setRules] = React.useState(null);   // null = loading
  const [loadError, setLoadError] = React.useState(null);
  const [filter, setFilter] = React.useState("all");

  const load = React.useCallback(() => {
    setLoadError(null);
    fetchAutomationRules()
      .then(setRules)
      .catch(err => {
        setLoadError(err.message || String(err));
        setRules(MOCK.rules);  // fall back to mock so the page stays usable
      });
  }, []);
  React.useEffect(() => { load(); }, [load]);

  const handleToggle = async (ruleId, enabled) => {
    await toggleAutomationRuleServer(ruleId, enabled);
    setRules(prev => (prev || []).map(r => (r.rule_id === ruleId ? { ...r, enabled } : r)));
  };

  const all = rules || [];
  const counts = {
    all: all.length,
    on: all.filter(r => r.enabled).length,
    off: all.filter(r => !r.enabled).length,
    approval: all.filter(r => r.mode === "approval").length,
  };
  const filters = [
    { k: "all", label: "전체", n: counts.all },
    { k: "on", label: "켜짐", n: counts.on },
    { k: "off", label: "꺼짐", n: counts.off },
    { k: "approval", label: "승인 필요", n: counts.approval },
  ];
  const visible = all.filter(r => {
    if (filter === "on") return r.enabled;
    if (filter === "off") return !r.enabled;
    if (filter === "approval") return r.mode === "approval";
    return true;
  });

  return (
    <div className="p-6">
      <SectionHeader
        title="환경설정 · 자동화 규칙"
        sub="센서 값이 조건을 넘으면 장치를 자동으로 움직이도록 규칙을 만드세요."
        right={<button className="btn btn-primary" onClick={() => { setEditing(null); setWizardOpen(true); }}><Icon name="add"/> 새 규칙 만들기</button>}
      />

      {loadError && (
        <div className="card-ghost p-3 mb-4 flex items-start gap-3" style={{ background: "var(--warn-tint)", borderColor: "#f4d79a" }}>
          <Icon name="cloud_off" style={{ color: "var(--warn)", fontSize: 20 }} />
          <div className="flex-1 text-[13px]" style={{ color: "#8a5200" }}>
            규칙을 서버에서 불러오지 못했습니다 — 샘플 데이터를 표시합니다. ({loadError})
          </div>
          <button className="btn btn-sm" onClick={load}><Icon name="refresh" style={{ fontSize: 16 }}/> 다시 시도</button>
        </div>
      )}

      <div className="flex items-center gap-2 mb-4">
        {filters.map(f => (
          <button key={f.k} onClick={() => setFilter(f.k)}
            className={`btn btn-sm ${filter === f.k ? "" : "btn-ghost"}`}>
            {f.label} <span className="tnum ml-1" style={{ color: "var(--ink-soft)" }}>{f.n}</span>
          </button>
        ))}
      </div>

      {rules === null ? (
        <div className="card p-8 text-center text-[13px]" style={{ color: "var(--ink-soft)" }}>
          <Icon name="hourglass_empty" style={{ fontSize: 24 }} /> 규칙을 불러오는 중…
        </div>
      ) : visible.length === 0 ? (
        <div className="card p-8 text-center text-[13px]" style={{ color: "var(--ink-soft)" }}>
          {filter === "all" ? "등록된 규칙이 없습니다." : "이 필터에 해당하는 규칙이 없습니다."}
        </div>
      ) : (
        <div className="space-y-3 max-w-[960px]">
          {visible.map(r => (
            <RuleRow key={r.rule_id || r.id} r={r}
              onEdit={(r)=>{ setEditing(r); setWizardOpen(true); }}
              onToggle={loadError ? null : handleToggle} />
          ))}
        </div>
      )}

      <RuleWizard open={wizardOpen} onClose={() => setWizardOpen(false)} editing={editing} />
    </div>
  );
}

Object.assign(window, { RulesPage, RuleWizard, RuleRow, WizardStepper });

// ==== alerts.jsx ====
// alerts.jsx — Alerts screen

function AlertRow({ a, onOpen }) {
  const tone = a.sev === "crit" ? "crit" : a.sev === "warn" ? "warn" : "ok";
  const row = a.sev === "crit" ? "row-crit" : a.sev === "warn" ? "row-warn" : "";
  return (
    <div className={`flex items-start gap-4 px-4 py-4 ${row} rail-${tone}`} style={{ borderBottom: "1px solid var(--line-soft)" }}>
      <div className="rounded-lg flex items-center justify-center shrink-0" style={{
        width: 38, height: 38,
        background: a.sev === "crit" ? "var(--crit-tint)" : a.sev === "warn" ? "var(--warn-tint)" : "var(--ok-tint)",
      }}>
        <Icon name={a.sev === "crit" ? "error" : a.sev === "warn" ? "warning" : "check_circle"} style={{
          fontSize: 20,
          color: a.sev === "crit" ? "var(--crit)" : a.sev === "warn" ? "var(--warn)" : "var(--ok)"
        }} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <StatusChip state={tone} />
          <span className="chip chip-mute">{a.tag}</span>
          <span className="text-[11.5px] ml-auto" style={{ color: "var(--ink-soft)" }}>{a.time}</span>
        </div>
        <div className="font-display" style={{ fontSize: 14.5, fontWeight: 600 }}>{a.title}</div>
        <div className="text-[13px] mt-0.5" style={{ color: "var(--ink-muted)", lineHeight: 1.5, textWrap: "pretty" }}>{a.body}</div>
        <div className="text-[11.5px] mt-1 flex items-center gap-1" style={{ color: "var(--ink-soft)" }}>
          <Icon name="memory" style={{ fontSize: 13 }} /> {a.device}
        </div>
      </div>
      <div className="flex flex-col gap-1 items-end shrink-0">
        <button className="btn btn-sm" onClick={onOpen}>상세</button>
        <button className="btn btn-ghost btn-sm"><Icon name="close" style={{ fontSize: 16 }} /> 닫기</button>
      </div>
    </div>
  );
}

function AlertsPage() {
  const [filter, setFilter] = React.useState("all");
  const items = MOCK.alerts.filter(a =>
    filter === "all" ? true :
    filter === "crit" ? a.sev === "crit" :
    filter === "warn" ? a.sev === "warn" :
    filter === "automation" ? a.tag.includes("자동화") :
    filter === "policy" ? a.tag.includes("정책") : true
  );

  const counts = {
    all: MOCK.alerts.length,
    crit: MOCK.alerts.filter(a => a.sev === "crit").length,
    warn: MOCK.alerts.filter(a => a.sev === "warn").length,
    automation: MOCK.alerts.filter(a => a.tag.includes("자동화")).length,
    policy: MOCK.alerts.filter(a => a.tag.includes("정책")).length,
  };

  const presets = [
    ["all",        "전체"],
    ["crit",       "위험만"],
    ["warn",       "주의만"],
    ["automation", "자동화 실패만"],
    ["policy",     "정책 위반만"],
  ];

  return (
    <div className="p-6">
      <SectionHeader
        title="알림"
        sub="지난 24시간 동안 쌓인 경고. 위험부터 먼저 확인하세요."
        right={
          <div className="flex items-center gap-2">
            <button className="btn btn-sm btn-ghost"><Icon name="done_all" /> 모두 읽음</button>
            <button className="btn btn-sm"><Icon name="filter_list" /> 필터</button>
          </div>
        }
      />

      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {presets.map(([k,l]) => (
          <button key={k} className={`btn btn-sm ${filter===k ? "" : "btn-ghost"}`} onClick={()=>setFilter(k)}>
            {l} <span className="tnum ml-1" style={{ color: "var(--ink-soft)" }}>{counts[k]}</span>
          </button>
        ))}
      </div>

      <div className="card max-w-[960px]" style={{ padding: 0 }}>
        {items.map(a => <AlertRow key={a.id} a={a} onOpen={() => {}} />)}
        {items.length === 0 && (
          <div className="p-10 text-center">
            <Icon name="notifications_paused" style={{ fontSize: 32, color: "var(--ink-soft)" }}/>
            <div className="font-display font-semibold mt-2" style={{ fontSize: 15 }}>해당 필터에 알림이 없습니다</div>
            <div className="text-[13px]" style={{ color: "var(--ink-soft)" }}>다른 필터를 선택해보세요.</div>
          </div>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { AlertsPage, AlertRow });

// ==== zones.jsx ====
// zones.jsx — master/detail chart page

function BigChart({ metric, series, highlight, onHoverIdx }) {
  const W = 720, H = 280, PAD_L = 42, PAD_R = 16, PAD_T = 18, PAD_B = 32;
  const iw = W - PAD_L - PAD_R, ih = H - PAD_T - PAD_B;
  const vals = series;
  const min = Math.min(...vals), max = Math.max(...vals);
  const pad = (max - min) * 0.15 || 1;
  const lo = min - pad, hi = max + pad;
  const x = i => PAD_L + (i / (vals.length - 1)) * iw;
  const y = v => PAD_T + ih - ((v - lo) / (hi - lo)) * ih;
  const d = vals.map((v,i) => (i===0 ? "M" : "L") + x(i) + "," + y(v)).join(" ");
  const area = d + ` L${x(vals.length-1)},${PAD_T+ih} L${x(0)},${PAD_T+ih} Z`;
  const tone = metric.state === "warn" ? "var(--warn)" : metric.state === "crit" ? "var(--crit)" : "var(--brand)";

  // target band
  const [rLo, rHi] = metric.range.split("–").map(s => parseFloat(s.replace(/[^\d.\-]/g,"")));
  const bandY1 = y(Math.min(rHi, hi)); const bandY2 = y(Math.max(rLo, lo));

  // y-ticks: 4
  const ticks = Array.from({length: 4}, (_, i) => lo + (hi - lo) * (i / 3));

  // x-tick labels (24h)
  const xTicks = [0, 18, 36, 54, 71];
  const xLabels = ["24h 전", "18h", "12h", "6h", "지금"];

  const hv = highlight != null ? vals[highlight] : null;

  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ maxWidth: "100%", height: "auto", display: "block" }}
      onMouseLeave={() => onHoverIdx(null)}
      onMouseMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        const px = ((e.clientX - r.left) / r.width) * W;
        const t = Math.max(0, Math.min(vals.length - 1, Math.round(((px - PAD_L) / iw) * (vals.length - 1))));
        onHoverIdx(t);
      }}>
      {/* target band */}
      <rect x={PAD_L} y={bandY1} width={iw} height={Math.max(2, bandY2 - bandY1)} fill="var(--ok)" opacity="0.08" />
      <line x1={PAD_L} x2={PAD_L+iw} y1={bandY1} y2={bandY1} stroke="var(--ok)" strokeWidth="1" strokeDasharray="3 3" opacity="0.5" />
      <line x1={PAD_L} x2={PAD_L+iw} y1={bandY2} y2={bandY2} stroke="var(--ok)" strokeWidth="1" strokeDasharray="3 3" opacity="0.5" />

      {/* y-grid + labels */}
      {ticks.map((t, i) => (
        <g key={i}>
          <line x1={PAD_L} x2={PAD_L+iw} y1={y(t)} y2={y(t)} stroke="var(--line-soft)" strokeWidth="1" />
          <text x={PAD_L - 8} y={y(t) + 4} textAnchor="end" fontSize="11" fill="var(--ink-soft)" fontFamily="Space Grotesk">{t.toFixed(metric.key==="ec" ? 1 : 0)}</text>
        </g>
      ))}

      {/* x labels */}
      {xTicks.map((i, k) => (
        <text key={k} x={x(i)} y={H-10} textAnchor="middle" fontSize="11" fill="var(--ink-soft)">{xLabels[k]}</text>
      ))}

      {/* area + line */}
      <path d={area} fill={tone} opacity="0.10" />
      <path d={d} fill="none" stroke={tone} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

      {/* hover crosshair */}
      {highlight != null && (
        <g>
          <line x1={x(highlight)} x2={x(highlight)} y1={PAD_T} y2={PAD_T+ih} stroke="var(--ink-muted)" strokeWidth="1" strokeDasharray="3 3" />
          <circle cx={x(highlight)} cy={y(hv)} r="5" fill="#fff" stroke={tone} strokeWidth="2" />
          <g transform={`translate(${x(highlight)}, ${y(hv) - 14})`}>
            <rect x="-40" y="-22" width="80" height="22" rx="6" fill="var(--ink)" />
            <text x="0" y="-7" textAnchor="middle" fontSize="12" fontWeight="700" fill="#fff" fontFamily="Space Grotesk">{hv}{metric.unit}</text>
          </g>
        </g>
      )}
    </svg>
  );
}

function ZoneMiniMetric({ m, selected, onClick }) {
  return (
    <button onClick={onClick} className={`card-ghost p-3 text-left rail-${m.state}`} style={{
      cursor: "pointer",
      borderColor: selected ? "var(--brand)" : "var(--line)",
      borderWidth: selected ? 2 : 1,
      background: selected ? "var(--brand-tint)" : "#fff",
    }}>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[12.5px] font-semibold" style={{ color: "var(--ink-muted)" }}>{m.name}</div>
          <div className="text-[11px]" style={{ color: "var(--ink-soft)" }}>정상 {m.range}</div>
        </div>
        <StatusChip state={m.state} withIcon={false}>{STATUS[m.state].label}</StatusChip>
      </div>
      <div className="flex items-end justify-between mt-2">
        <div className="flex items-baseline gap-1">
          <div className="font-display tnum" style={{ fontSize: 22, fontWeight: 700 }}>{m.value}</div>
          <div className="text-[11.5px]" style={{ color: "var(--ink-soft)" }}>{m.unit}</div>
        </div>
        <Sparkline points={MOCK.sparks[m.key]} tone={m.state === "warn" ? "warn" : m.state === "crit" ? "crit" : "brand"} width={80} height={28} />
      </div>
      <div className="text-[11.5px] mt-1 flex items-center gap-1" style={{ color: "var(--ink-soft)" }}>
        <Icon name={m.delta >= 0 ? "north_east" : "south_east"} style={{ fontSize: 13 }} />
        24h {m.delta > 0 ? "+" : ""}{m.delta} {m.unit}
      </div>
    </button>
  );
}

function ZonesPage() {
  const [zoneKey, setZoneKey] = React.useState("A");
  const [metricKey, setMetricKey] = React.useState("air_humid");
  const [hover, setHover] = React.useState(null);
  const zone = MOCK.zonesDetail.find(z => z.key === zoneKey);
  const metric = MOCK.metrics.find(m => m.key === metricKey);
  const series = MOCK.series[metricKey];

  return (
    <div className="p-6">
      <SectionHeader
        title="구역 모니터링"
        sub="구역을 선택하고, 지표를 눌러 24시간 추이를 확인하세요."
        right={
          <div className="flex items-center gap-2">
            <button className="btn btn-sm"><Icon name="date_range" style={{ fontSize: 16 }} /> 지난 24시간</button>
            <button className="btn btn-sm btn-ghost"><Icon name="download" style={{ fontSize: 16 }} /> CSV</button>
          </div>
        }
      />

      {/* Zone tabs */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {MOCK.zonesDetail.map(z => (
          <button key={z.key} onClick={() => setZoneKey(z.key)}
            className={`card-ghost px-4 py-2.5 flex items-center gap-2 rail-${z.state}`}
            style={{
              cursor: "pointer",
              background: zoneKey === z.key ? "#fff" : "var(--surface-low)",
              borderColor: zoneKey === z.key ? "var(--brand)" : "var(--line)",
              borderWidth: zoneKey === z.key ? 2 : 1,
            }}>
            <Dot state={z.state} />
            <div className="text-left">
              <div className="font-display font-semibold" style={{ fontSize: 14 }}>{z.name}</div>
              <div className="text-[11.5px]" style={{ color: "var(--ink-soft)" }}>{z.crop}</div>
            </div>
          </button>
        ))}
      </div>

      <div className="grid gap-5 resp-2col" style={{ gridTemplateColumns: "minmax(280px, 320px) 1fr" }}>
        {/* Left: metric list */}
        <div className="space-y-2">
          <div className="text-[12px] font-semibold" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase", marginBottom: 6 }}>{zone.name} 지표</div>
          {MOCK.metrics.map(m => <ZoneMiniMetric key={m.key} m={m} selected={metricKey === m.key} onClick={() => setMetricKey(m.key)} />)}
        </div>

        {/* Right: detail chart */}
        <div className="space-y-4 min-w-0">
          <div className="card p-5">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="font-display font-semibold" style={{ fontSize: 18 }}>{metric.name} <span className="text-[13px] font-normal" style={{ color: "var(--ink-soft)" }}>({metric.unit})</span></h2>
                  <StatusChip state={metric.state} />
                </div>
                <div className="text-[12.5px] mt-0.5" style={{ color: "var(--ink-soft)" }}>정상 범위 {metric.range} {metric.unit} · 지난 24시간</div>
              </div>
              <div className="text-right">
                <div className="font-display tnum" style={{ fontSize: 32, fontWeight: 700, lineHeight: 1 }}>{metric.value}<span className="text-[13px] ml-1" style={{ color: "var(--ink-soft)", fontWeight: 400 }}>{metric.unit}</span></div>
                <div className="text-[12px] mt-1" style={{ color: "var(--ink-muted)" }}>24h {metric.delta > 0 ? "+" : ""}{metric.delta} {metric.unit}</div>
              </div>
            </div>
            <BigChart metric={metric} series={series} highlight={hover} onHoverIdx={setHover} />
          </div>

          <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            {[
              { lbl: "최저", v: Math.min(...series).toFixed(1), t: "06:12" },
              { lbl: "평균", v: (series.reduce((a,b)=>a+b,0)/series.length).toFixed(1), t: "24h" },
              { lbl: "최고", v: Math.max(...series).toFixed(1), t: "14:20" },
            ].map((s,i) => (
              <div key={i} className="card-ghost p-3">
                <div className="text-[11.5px] font-semibold" style={{ color: "var(--ink-soft)" }}>{s.lbl}</div>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="font-display tnum" style={{ fontSize: 20, fontWeight: 700 }}>{s.v}</span>
                  <span className="text-[11.5px]" style={{ color: "var(--ink-soft)" }}>{metric.unit}</span>
                </div>
                <div className="text-[11.5px]" style={{ color: "var(--ink-soft)" }}>{s.t}</div>
              </div>
            ))}
          </div>

          <div className="card p-4 rail-warn">
            <div className="flex items-start gap-3">
              <Icon name="lightbulb" style={{ color: "var(--warn)", fontSize: 20 }} />
              <div>
                <div className="font-display font-semibold" style={{ fontSize: 14 }}>AI 관찰</div>
                <div className="text-[13px] mt-0.5" style={{ color: "var(--ink-muted)", lineHeight: 1.5 }}>
                  최근 3시간 동안 {metric.name}이(가) {metric.delta > 0 ? "상승" : "하강"}세입니다.
                  {metric.state === "warn" && " 목표 범위를 벗어나고 있으니 결정·승인 화면의 권고를 확인해주세요."}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ZonesPage, BigChart });

// ==== chat.jsx ====
// chat.jsx — AI Assistant

function GroundingChips({ g }) {
  if (!g) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {g.zones?.map(z => <span key={z} className="chip chip-brand"><Icon name="place"/>{z}</span>)}
      {g.metrics?.map(m => <span key={m} className="chip chip-info"><Icon name="monitoring"/>{m}</span>)}
      {g.policies?.map(p => <span key={p} className="chip chip-mute"><Icon name="shield"/>{p}</span>)}
    </div>
  );
}

function MessageBubble({ m }) {
  if (m.who === "user") {
    return (
      <div className="flex justify-end mb-4">
        <div style={{ background: "var(--brand)", color: "#fff", padding: "10px 14px", borderRadius: "16px 16px 4px 16px", maxWidth: "72%", fontSize: 14, lineHeight: 1.5 }}>
          {m.text}
          <div className="text-[11px] mt-1" style={{ color: "rgba(255,255,255,.7)" }}>{m.t}</div>
        </div>
      </div>
    );
  }
  // AI
  // Render **bold** simple
  const parts = m.text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="rounded-lg shrink-0 flex items-center justify-center" style={{ width: 36, height: 36, background: "var(--brand-tint)" }}>
        <Icon name="smart_toy" style={{ color: "var(--brand)", fontSize: 20 }} />
      </div>
      <div className="min-w-0" style={{ maxWidth: "80%" }}>
        <div className="flex items-center gap-2 mb-1">
          <span className="chip chip-brand">적고추 전문 AI</span>
          <span className="text-[11px]" style={{ color: "var(--ink-soft)" }}>{m.t}</span>
        </div>
        <div style={{ background: "#fff", border: "1px solid var(--line)", padding: "12px 14px", borderRadius: "4px 16px 16px 16px", fontSize: 14, lineHeight: 1.6, textWrap: "pretty" }}>
          {parts.map((p, i) =>
            p.startsWith("**") ? <b key={i}>{p.slice(2, -2)}</b> : <span key={i}>{p}</span>
          )}
        </div>
        <GroundingChips g={m.grounds} />
      </div>
    </div>
  );
}

function ChatPage({ devViewUnlocked }) {
  const [messages, setMessages] = React.useState(MOCK.chatHistory);
  const [input, setInput] = React.useState("");
  const [typing, setTyping] = React.useState(false);
  const scrollRef = React.useRef(null);

  React.useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, typing]);

  const send = (txt) => {
    if (!txt.trim()) return;
    const now = new Date();
    const t = `${now.getHours()}:${String(now.getMinutes()).padStart(2,"0")}`;
    setMessages(m => [...m, { who: "user", text: txt, t }]);
    setInput("");
    setTyping(true);
    setTimeout(() => {
      setMessages(m => [...m, {
        who: "ai",
        text: "질문을 확인했어요. 관련된 구역 데이터와 안전 규칙을 함께 살펴보고 답변드릴게요. (데모 응답)",
        grounds: { zones: ["A구역", "B구역"], metrics: ["기온", "습도"], policies: ["HSV-03"] },
        t,
      }]);
      setTyping(false);
    }, 1100);
  };

  const lastAi = [...messages].reverse().find(m => m.who === "ai");

  return (
    <div className="p-6" style={{ height: "calc(100vh - 64px)" }}>
      <div className="grid gap-5 h-full resp-2col" style={{ gridTemplateColumns: "1fr 320px" }}>
        {/* Chat column */}
        <div className="card flex flex-col min-h-0" style={{ background: "var(--surface-low)" }}>
          <div className="px-5 py-3 flex items-center justify-between" style={{ borderBottom: "1px solid var(--line)", background: "#fff", borderRadius: "14px 14px 0 0" }}>
            <div className="flex items-center gap-2">
              <span className="chip chip-brand"><Icon name="smart_toy"/> 적고추 전문 AI</span>
              <span className="text-[12.5px]" style={{ color: "var(--ink-soft)" }}>적고추 온실 제2동에 대해 연결됨</span>
            </div>
            <button className="btn btn-ghost btn-sm"><Icon name="refresh" style={{ fontSize: 16 }} /> 새 대화</button>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto scroll-clean px-5 py-4 min-h-0">
            {messages.map((m, i) => <MessageBubble key={i} m={m} />)}
            {typing && (
              <div className="flex items-center gap-3 mb-4">
                <div className="rounded-lg shrink-0 flex items-center justify-center" style={{ width: 36, height: 36, background: "var(--brand-tint)" }}>
                  <Icon name="smart_toy" style={{ color: "var(--brand)", fontSize: 20 }} />
                </div>
                <div style={{ background: "#fff", border: "1px solid var(--line)", padding: "12px 14px", borderRadius: 16, display: "flex", gap: 5 }}>
                  <span className="pulse" style={{ width:6, height:6, borderRadius:999, background:"var(--brand)" }}></span>
                  <span className="pulse" style={{ width:6, height:6, borderRadius:999, background:"var(--brand)", animationDelay:".2s" }}></span>
                  <span className="pulse" style={{ width:6, height:6, borderRadius:999, background:"var(--brand)", animationDelay:".4s" }}></span>
                </div>
              </div>
            )}
          </div>

          <div className="px-5 pt-2 pb-3" style={{ background: "#fff", borderTop: "1px solid var(--line)", borderRadius: "0 0 14px 14px" }}>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {MOCK.quickPrompts.map((q, i) => (
                <button key={i} className="btn btn-sm btn-ghost" style={{ background: "var(--surface-low)", border: "1px solid var(--line)" }} onClick={() => send(q)}>{q}</button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input
                className="flex-1 px-4 py-3 rounded-xl text-[14px]"
                style={{ border: "1px solid var(--line)", background: "#fff" }}
                placeholder="온실 상태나 규칙에 대해 물어보세요…"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter") send(input); }}
              />
              <button className="btn btn-primary" onClick={() => send(input)}><Icon name="send"/> 보내기</button>
            </div>
            <div className="text-[11px] mt-1.5" style={{ color: "var(--ink-soft)" }}>AI 답변은 참고용입니다. 중요한 결정은 결정·승인 화면에서 검토해주세요.</div>
          </div>
        </div>

        {/* Grounding panel */}
        <aside className="card p-4 overflow-y-auto scroll-clean min-h-0" style={{ height: "100%" }}>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>지금 AI가 본 데이터</div>
          <div className="text-[13px] mb-4" style={{ color: "var(--ink-muted)", lineHeight: 1.5 }}>마지막 답변은 다음 정보를 참조했습니다.</div>

          <div className="mb-4">
            <div className="text-[12px] font-semibold mb-1.5" style={{ color: "var(--ink-soft)" }}>구역</div>
            <div className="flex flex-wrap gap-1.5">
              {lastAi?.grounds?.zones?.map(z => <span key={z} className="chip chip-brand"><Icon name="place"/>{z}</span>)}
            </div>
          </div>
          <div className="mb-4">
            <div className="text-[12px] font-semibold mb-1.5" style={{ color: "var(--ink-soft)" }}>지표</div>
            <div className="flex flex-wrap gap-1.5">
              {lastAi?.grounds?.metrics?.map(m => <span key={m} className="chip chip-info"><Icon name="monitoring"/>{m}</span>)}
            </div>
          </div>
          <div className="mb-4">
            <div className="text-[12px] font-semibold mb-1.5" style={{ color: "var(--ink-soft)" }}>참조한 안전 규칙</div>
            <div className="flex flex-wrap gap-1.5">
              {lastAi?.grounds?.policies?.map(p => (
                <span key={p} className="chip chip-mute"><Icon name="shield"/>{p}</span>
              ))}
            </div>
          </div>

          <div className="card-ghost p-3 mt-5" style={{ background: "var(--brand-tint)", borderColor: "var(--brand-tint-2)" }}>
            <div className="flex items-start gap-2">
              <Icon name="verified" style={{ color: "var(--brand)", fontSize: 18, marginTop: 1 }} />
              <div>
                <div className="font-display font-semibold" style={{ fontSize: 13, color: "var(--brand-700)" }}>적고추 전문 파인튜닝 AI</div>
                <div className="text-[12px] mt-0.5" style={{ color: "var(--brand-700)", lineHeight: 1.5 }}>한국 적고추 재배 생리·환경 데이터로 파인튜닝된 전용 모델입니다.</div>
              </div>
            </div>
          </div>

          {devViewUnlocked && (
            <details className="mt-4" style={{ borderTop: "1px dashed var(--line)", paddingTop: 12 }}>
              <summary className="text-[12px] font-semibold flex items-center gap-1.5" style={{ color: "var(--ink-muted)" }}>
                <Icon name="code" style={{ fontSize: 14 }} /> Grounding Inspector (개발자)
              </summary>
              <pre className="json mt-2" style={{ fontSize: 11 }}>{JSON.stringify({
                model_label: "pepper-ds_v11",
                provider: "openai:ft",
                prompt_version: "sft_v10",
                chat_system_prompt_id: "sp_pepper_v3",
                grounding_keys: ["zones.A", "metrics.humidity_pct", "policies.HSV-04"],
                retriever: "openai",
              }, null, 2)}</pre>
            </details>
          )}
        </aside>
      </div>
    </div>
  );
}

Object.assign(window, { ChatPage, GroundingChips });

// ==== devices.jsx ====
// devices.jsx — Devices & constraints

function DeviceIcon({ type }) {
  const map = {
    vent_roof: "unfold_less", fan_dehum: "mode_fan", irrigation: "water_drop",
    grow_light: "wb_incandescent", co2_inject: "co2", heater: "local_fire_department",
    cooler: "ac_unit", shade: "blinds",
  };
  return <Icon name={map[type] || "memory"} />;
}

function DeviceCard({ d }) {
  const state = d.state;
  return (
    <div className={`card p-4 rail-${state}`}>
      <div className="flex items-start gap-3">
        <div className="rounded-lg flex items-center justify-center shrink-0" style={{ width: 40, height: 40, background: "var(--brand-tint)", color: "var(--brand-700)" }}>
          <DeviceIcon type={d.type} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <StatusChip state={state} />
            <span className="chip chip-brand"><Icon name="place"/>{d.zone}구역</span>
          </div>
          <div className="font-display font-semibold truncate" style={{ fontSize: 14 }}>{d.name}</div>
          <div className="text-[12.5px]" style={{ color: "var(--ink-muted)" }}>현재 <b style={{ color: state === "crit" ? "var(--crit)" : "var(--ink)" }}>{d.value}</b></div>
        </div>
      </div>
      <div className="hairline mt-3 pt-2.5 flex items-center justify-between text-[11.5px]" style={{ color: "var(--ink-soft)" }}>
        <span className="flex items-center gap-1"><Icon name="sync" style={{ fontSize: 13 }} /> {d.lastSeen}</span>
        <span className="font-mono" title={d.id} style={{ fontSize: 11 }}>{d.id}</span>
      </div>
      {d.constraint && (
        <div className="mt-2 text-[11.5px] flex items-start gap-1" style={{ padding: "6px 8px", background: "var(--surface-low)", border: "1px solid var(--line-soft)", borderRadius: 8, color: "var(--ink-muted)" }}>
          <Icon name="lock" style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 1 }} /> {d.constraint}
        </div>
      )}
    </div>
  );
}

function DevicesPage() {
  const [filter, setFilter] = React.useState("all");
  const items = MOCK.devicesList.filter(d => filter === "all" ? true : filter === d.state || filter === d.zone);

  const counts = {
    all: MOCK.devicesList.length,
    ok:   MOCK.devicesList.filter(d => d.state === "ok").length,
    warn: MOCK.devicesList.filter(d => d.state === "warn").length,
    crit: MOCK.devicesList.filter(d => d.state === "crit").length,
    off:  MOCK.devicesList.filter(d => d.state === "off").length,
  };

  return (
    <div className="p-6">
      <SectionHeader title="장치 · 제약" sub="현재 연결된 장치와 적용 중인 제약(쿨다운·안전 범위)." right={
        <button className="btn btn-sm"><Icon name="add"/> 장치 등록</button>
      } />
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {[["all","전체"],["ok","정상"],["warn","주의"],["crit","위험"],["off","꺼짐"]].map(([k,l]) => (
          <button key={k} className={`btn btn-sm ${filter===k ? "" : "btn-ghost"}`} onClick={()=>setFilter(k)}>{l} <span className="tnum ml-1" style={{ color: "var(--ink-soft)" }}>{counts[k]}</span></button>
        ))}
      </div>
      <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
        {items.map(d => <DeviceCard key={d.id} d={d} />)}
      </div>
    </div>
  );
}

Object.assign(window, { DevicesPage, DeviceCard });

// ==== policies_robot.jsx ====
// policies.jsx + robot.jsx merged page components

function PolicyRow({ p }) {
  // Local state so clicking the toggle actually flips it. Phase T-1 keeps
  // the switch as pure UI (no server call yet); Phase T-2 will wire this
  // to POST /policies/{id}/toggle or similar.
  const [enabled, setEnabled] = React.useState(p.enabled);
  return (
    <div className={`card p-4 rail-${p.state}`}>
      <div className="flex items-center gap-4">
        <label className="relative inline-flex items-center cursor-pointer shrink-0">
          <input
            type="checkbox"
            checked={enabled}
            onChange={e => setEnabled(e.target.checked)}
            className="sr-only peer"
          />
          <div className="w-11 h-6 rounded-full transition-colors" style={{ background: enabled ? "var(--brand)" : "#cfd6d1" }}>
            <div className="w-5 h-5 rounded-full bg-white shadow-sm transition-transform" style={{ transform: `translate(${enabled ? 22 : 2}px, 2px)` }}></div>
          </div>
        </label>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <div className="font-display font-semibold" style={{ fontSize: 14.5 }}>{p.name}</div>
            <span className="chip chip-mute" title="내부 식별자" style={{ fontFamily: "ui-monospace, monospace", fontSize: 11 }}>{p.id}</span>
          </div>
          <div className="text-[12.5px]" style={{ color: "var(--ink-muted)" }}>{p.desc}</div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-[11.5px]" style={{ color: "var(--ink-soft)" }}>지난 24h 발동</div>
          <div className="font-display tnum" style={{ fontSize: 18, fontWeight: 700 }}>{p.triggers24h}<span className="text-[11px] font-normal ml-0.5" style={{ color: "var(--ink-soft)" }}>회</span></div>
        </div>
      </div>
    </div>
  );
}

function PoliciesPage() {
  return (
    <div className="p-6">
      <SectionHeader title="정책 · 이벤트" sub="안전 규칙의 현재 상태와 최근 트리거 이력." />
      <div className="grid gap-5 resp-2col" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
        <div>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>활성 안전 규칙</div>
          <div className="space-y-3">
            {MOCK.policies.map(p => <PolicyRow key={p.id} p={p} />)}
          </div>
        </div>
        <div>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>최근 이벤트</div>
          <div className="card px-4">
            {MOCK.policyEvents.map((e, i) => (
              <div key={i} className="flex items-start gap-3 py-3" style={{ borderBottom: i < MOCK.policyEvents.length - 1 ? "1px solid var(--line-soft)" : "none" }}>
                <div className="rounded-full flex items-center justify-center shrink-0" style={{ width: 30, height: 30, background: e.state === "warn" ? "var(--warn-tint)" : "var(--ok-tint)" }}>
                  <Icon name="shield" style={{ fontSize: 16, color: e.state === "warn" ? "var(--warn)" : "var(--ok)" }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[13.5px]" style={{ fontWeight: 600 }}>{e.title}</div>
                  <div className="text-[11.5px] mt-0.5 flex items-center gap-2" style={{ color: "var(--ink-soft)" }}>
                    <span>{e.t}</span> · <span className="chip chip-mute" style={{ fontSize: 10.5, padding: "1px 6px" }}>{e.policy}</span> · <span>{e.zone}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ——— Robot ———
function RobotPage() {
  const r = MOCK.robotTasks;
  return (
    <div className="p-6">
      <SectionHeader title="로봇" sub="현재 실행 중인 작업과 대기 큐, 오늘 완료 이력." right={
        <div className="flex items-center gap-2">
          <button className="btn btn-sm"><Icon name="pause"/> 일시정지</button>
          <button className="btn btn-sm btn-primary"><Icon name="add"/> 작업 추가</button>
        </div>
      } />

      <div className="grid gap-5 resp-2col" style={{ gridTemplateColumns: "1.3fr 1fr" }}>
        {/* Now running */}
        <div className="card p-5 rail-brand">
          <div className="flex items-center gap-2 mb-2">
            <span className="chip chip-brand"><Icon name="sync"/> 실행 중</span>
            <span className="text-[11.5px] font-mono" style={{ color: "var(--ink-soft)" }}>{r.now.id}</span>
          </div>
          <div className="font-display font-semibold" style={{ fontSize: 18 }}>{r.now.name} · {r.now.zone}</div>
          <div className="text-[13px] mt-0.5" style={{ color: "var(--ink-muted)" }}>로봇 {r.now.robot} · {r.now.started} 시작 · 예상 남은 시간 {r.now.eta}</div>

          <div className="mt-4">
            <div className="flex items-center justify-between text-[12.5px] mb-1" style={{ color: "var(--ink-muted)" }}>
              <span>진행률</span>
              <span className="tnum font-semibold">{Math.round(r.now.progress * 100)}%</span>
            </div>
            <div style={{ height: 10, borderRadius: 999, background: "var(--line-soft)", overflow: "hidden" }}>
              <div style={{ width: `${r.now.progress * 100}%`, height: "100%", background: "linear-gradient(90deg, var(--brand-500), var(--brand))" }}></div>
            </div>
          </div>

          <div className="hairline mt-4 pt-3 flex items-center gap-2">
            <button className="btn btn-sm"><Icon name="pause"/> 일시정지</button>
            <button className="btn btn-sm btn-danger"><Icon name="stop_circle"/> 중단</button>
            <button className="btn btn-ghost btn-sm ml-auto">작업 상세 <Icon name="arrow_forward" style={{fontSize:16}}/></button>
          </div>
        </div>

        {/* Queue */}
        <div>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>대기 큐 · {r.queue.length}건</div>
          <div className="card" style={{ padding: 2 }}>
            {r.queue.map((q, i) => (
              <div key={q.id} className="flex items-center gap-3 px-3 py-3" style={{ borderBottom: i < r.queue.length - 1 ? "1px solid var(--line-soft)" : "none" }}>
                <div className="rounded-md flex items-center justify-center" style={{ width: 28, height: 28, background: "var(--surface-low)", color: "var(--ink-muted)", fontWeight: 700, fontSize: 13 }}>{i+1}</div>
                <div className="flex-1 min-w-0">
                  <div className="text-[13.5px] font-semibold">{q.name} · {q.zone}</div>
                  <div className="text-[11.5px] flex items-center gap-2" style={{ color: "var(--ink-soft)" }}>
                    <span>예상 {q.eta}</span> · <span className={`chip ${q.priority === "높음" ? "chip-warn" : q.priority === "낮음" ? "chip-mute" : "chip-info"}`} style={{ fontSize: 10.5, padding: "1px 6px" }}>{q.priority}</span>
                  </div>
                </div>
                <button className="btn btn-ghost btn-sm"><Icon name="drag_indicator" style={{ fontSize: 18 }} /></button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5">
        <SectionHeader title="오늘 완료 이력" right={<button className="btn btn-ghost btn-sm">전체 이력</button>} />
        <div className="card px-4">
          {r.done.map((d, i) => (
            <div key={d.id} className="flex items-center gap-3 py-3" style={{ borderBottom: i < r.done.length - 1 ? "1px solid var(--line-soft)" : "none" }}>
              <div className="rounded-full flex items-center justify-center shrink-0" style={{ width: 30, height: 30, background: "var(--ok-tint)" }}>
                <Icon name="check_circle" style={{ color: "var(--ok)", fontSize: 18 }} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[13.5px]"><b>{d.name}</b> · {d.zone}</div>
                <div className="text-[11.5px]" style={{ color: "var(--ink-soft)" }}>{d.ended} · {d.result}</div>
              </div>
              <span className="text-[11px] font-mono" style={{ color: "var(--ink-soft)" }}>{d.id}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { PoliciesPage, PolicyRow, RobotPage });

// ==== designsystem.jsx ====
// designsystem.jsx — Design system showcase page

function DSSwatch({ name, token, value, textOn = "#fff" }) {
  return (
    <div className="card-ghost overflow-hidden">
      <div style={{ background: value, height: 72, display: "flex", alignItems: "flex-end", padding: 10, color: textOn, fontSize: 11, fontWeight: 600 }}>{value}</div>
      <div className="p-3">
        <div className="text-[13px] font-semibold">{name}</div>
        <div className="text-[11.5px]" style={{ color: "var(--ink-soft)" }}>{token}</div>
      </div>
    </div>
  );
}

function DSBlock({ title, sub, children }) {
  return (
    <section>
      <div className="mb-3">
        <h2 className="font-display font-semibold" style={{ fontSize: 18 }}>{title}</h2>
        {sub && <div className="text-[13px]" style={{ color: "var(--ink-soft)" }}>{sub}</div>}
      </div>
      <div className="card p-5">{children}</div>
    </section>
  );
}

function DesignSystemPage() {
  return (
    <div className="p-6 space-y-6 max-w-[1100px]">
      <div>
        <div className="text-[12px] font-semibold" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>Design System</div>
        <h1 className="font-display font-semibold" style={{ fontSize: 22 }}>iFarm 디자인 시스템</h1>
        <p className="text-[13.5px] mt-1 max-w-[680px]" style={{ color: "var(--ink-muted)", lineHeight: 1.55 }}>현장 운영자(태블릿 사용)를 1차 사용자로 두고, 밀도는 낮추고 상태 신호는 일관되게. 아이콘 + 한국어 + 자연어 한 문장을 기본 단위로 합니다.</p>
      </div>

      <DSBlock title="색" sub="브랜드 녹색은 주요 액션에만, 상태색은 신호등처럼 3단계로.">
        <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)" }}>BRAND</div>
        <div className="grid gap-3 mb-5" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
          <DSSwatch name="Brand 700" token="--brand-700" value="#005a20" />
          <DSSwatch name="Brand" token="--brand" value="#006a26" />
          <DSSwatch name="Brand 500" token="--brand-500" value="#00913a" />
          <DSSwatch name="Brand Tint" token="--brand-tint" value="#e8f2ec" textOn="#005a20" />
        </div>
        <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)" }}>STATUS</div>
        <div className="grid gap-3 mb-5" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
          <DSSwatch name="OK (정상)" token="--ok" value="#0a8f5a" />
          <DSSwatch name="Warn (주의)" token="--warn" value="#c77700" />
          <DSSwatch name="Crit (위험)" token="--crit" value="#c32222" />
          <DSSwatch name="Info" token="--info" value="#1d5db3" />
        </div>
        <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)" }}>NEUTRAL</div>
        <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
          <DSSwatch name="Ink" token="--ink" value="#0f1a14" />
          <DSSwatch name="Ink Muted" token="--ink-muted" value="#4b5a52" />
          <DSSwatch name="Line" token="--line" value="#e3e8e4" textOn="#4b5a52" />
          <DSSwatch name="Surface Low" token="--surface-low" value="#f6f8f6" textOn="#4b5a52" />
        </div>
      </DSBlock>

      <DSBlock title="타이포" sub="Pretendard 본문 + Space Grotesk 숫자·헤드라인. 숫자는 tabular-nums.">
        <div className="space-y-3">
          <div className="flex items-baseline gap-4"><span className="text-[11px]" style={{ color: "var(--ink-soft)", width: 90 }}>Display / 28</span><span className="font-display" style={{ fontSize: 28, fontWeight: 700 }}>24.8 °C · 오늘의 할 일</span></div>
          <div className="flex items-baseline gap-4"><span className="text-[11px]" style={{ color: "var(--ink-soft)", width: 90 }}>Title / 18</span><span className="font-display" style={{ fontSize: 18, fontWeight: 600 }}>AI가 권고한 조치</span></div>
          <div className="flex items-baseline gap-4"><span className="text-[11px]" style={{ color: "var(--ink-soft)", width: 90 }}>Body / 14</span><span style={{ fontSize: 14 }}>A구역 천장 개폐기를 20%로 닫고, 제습팬 단계를 2로 올립니다.</span></div>
          <div className="flex items-baseline gap-4"><span className="text-[11px]" style={{ color: "var(--ink-soft)", width: 90 }}>Caption / 12</span><span style={{ fontSize: 12, color: "var(--ink-soft)" }}>마지막 업데이트 2분 전</span></div>
          <div className="flex items-baseline gap-4"><span className="text-[11px]" style={{ color: "var(--ink-soft)", width: 90 }}>Metric / 30</span><span className="font-display tnum" style={{ fontSize: 30, fontWeight: 700 }}>2,435</span></div>
        </div>
      </DSBlock>

      <DSBlock title="Status chip" sub="정상 / 주의 / 위험 / 대기 / 꺼짐 — 아이콘 + 한국어.">
        <div className="flex flex-wrap gap-2">
          <StatusChip state="ok" />
          <StatusChip state="warn" />
          <StatusChip state="crit" />
          <StatusChip state="wait" />
          <StatusChip state="off" />
          <Chip tone="brand" icon="place">A구역</Chip>
          <Chip tone="info" icon="water_drop">외부 강우</Chip>
        </div>
      </DSBlock>

      <DSBlock title="Buttons" sub="44×44pt 이상. 기본 높이 40, 대형 48.">
        <div className="flex flex-wrap gap-2 mb-3">
          <button className="btn btn-primary"><Icon name="check"/> 승인하고 실행</button>
          <button className="btn"><Icon name="edit"/> 편집</button>
          <button className="btn btn-danger"><Icon name="close"/> 거절</button>
          <button className="btn btn-ghost">보조</button>
          <button className="btn btn-primary btn-lg">대형 버튼</button>
          <button className="btn btn-sm">소형</button>
        </div>
      </DSBlock>

      <DSBlock title="Action / Metric / Approval 카드" sub="좌측 색 띠 + 상태 tint. 자연어 한 문장 + 근거 chip + 액션.">
        <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <MetricCard m={MOCK.metrics[0]} />
          <MetricCard m={MOCK.metrics[1]} />
        </div>
      </DSBlock>

      <DSBlock title="Timeline · Empty state · Skeleton" sub="시간(상대표기) · 아이콘 · 자연어 · 우측 액션.">
        <div className="grid gap-4" style={{ gridTemplateColumns: "1.3fr 1fr" }}>
          <div className="card-ghost px-4">
            {MOCK.timeline.slice(0,3).map((t,i) => <TimelineRow key={i} item={t} />)}
          </div>
          <div>
            <div className="card-ghost p-6 text-center mb-3" style={{ borderStyle: "dashed" }}>
              <Icon name="inbox" style={{ fontSize: 28, color: "var(--ink-soft)" }} />
              <div className="font-display font-semibold mt-2" style={{ fontSize: 14 }}>아직 데이터가 없습니다</div>
              <div className="text-[12.5px]" style={{ color: "var(--ink-soft)" }}>첫 규칙을 만들어보세요.</div>
              <button className="btn btn-primary btn-sm mt-3"><Icon name="add"/> 새 규칙</button>
            </div>
            <div className="card-ghost p-3">
              <div className="pulse rounded-md" style={{ height: 10, background: "var(--line)", width: "60%", marginBottom: 8 }}></div>
              <div className="pulse rounded-md" style={{ height: 22, background: "var(--line)", width: "40%", marginBottom: 8 }}></div>
              <div className="pulse rounded-md" style={{ height: 10, background: "var(--line)", width: "80%" }}></div>
            </div>
          </div>
        </div>
      </DSBlock>

      <DSBlock title="용어 치환표" sub="내부 enum → 사람이 읽는 한국어. 운영자 화면 기본 표기.">
        <div className="text-[13px]">
          <div className="grid gap-0" style={{ gridTemplateColumns: "1fr 1fr", border: "1px solid var(--line)", borderRadius: 10, overflow: "hidden" }}>
            {[
              ["approval_pending", "승인 대기"],
              ["blocked_validator", "안전 규칙에 막힘"],
              ["dispatch_fault", "자동 실행 실패"],
              ["shadow_logged", "섀도우 기록됨"],
              ["HSV-01", "AI 응답 형식 규칙"],
              ["HSV-03", "EC 상한 안전 규칙"],
              ["runtime_mode_gate", "실행 방식"],
              ["policy_violation", "정책 위반"],
              ["decision_id", "권고 번호"],
              ["request_id", "요청 번호"],
            ].map(([en, ko], i) => (
              <React.Fragment key={i}>
                <div style={{ padding: "8px 12px", fontFamily: "ui-monospace, monospace", fontSize: 12.5, background: i%4<2 ? "var(--surface-low)" : "#fff", borderBottom: i < 8 ? "1px solid var(--line-soft)" : "none" }}>{en}</div>
                <div style={{ padding: "8px 12px", background: i%4<2 ? "var(--surface-low)" : "#fff", borderBottom: i < 8 ? "1px solid var(--line-soft)" : "none", borderLeft: "1px solid var(--line-soft)", fontWeight: 600 }}>{ko}</div>
              </React.Fragment>
            ))}
          </div>
        </div>
      </DSBlock>
    </div>
  );
}

Object.assign(window, { DesignSystemPage });

// ==== app.jsx ====
// app.jsx — router, top-level state, Tweaks protocol

function TweaksPanel({ open, onClose, tweaks, setTweak }) {
  if (!open) return null;
  return (
    <div style={{ position: "fixed", right: 20, bottom: 20, width: 320, zIndex: 80 }} className="card sheet p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="font-display font-semibold" style={{ fontSize: 15 }}>Tweaks</div>
        <button className="btn btn-ghost btn-sm" onClick={onClose}><Icon name="close" style={{ fontSize: 18 }} /></button>
      </div>
      <div className="space-y-3">
        <div>
          <div className="text-[11.5px] font-semibold mb-1" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>대시보드 Hero</div>
          <div className="flex gap-1">
            {[["hero-stats","숫자 3개"],["sentence","문장형"]].map(([k,l]) => (
              <button key={k} className={`btn btn-sm flex-1 ${tweaks.dashboardLayout === k ? "" : "btn-ghost"}`} onClick={()=>setTweak("dashboardLayout", k)}>{l}</button>
            ))}
          </div>
        </div>
        <div>
          <div className="text-[11.5px] font-semibold mb-1" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>라벨 언어</div>
          <div className="flex gap-1">
            {[["ko","한국어"],["en","English"]].map(([k,l]) => (
              <button key={k} className={`btn btn-sm flex-1 ${tweaks.labelLocale === k ? "" : "btn-ghost"}`} onClick={()=>setTweak("labelLocale", k)}>{l}</button>
            ))}
          </div>
        </div>
        <div>
          <div className="text-[11.5px] font-semibold mb-1" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>개발자 뷰</div>
          <button className={`btn btn-sm w-full ${tweaks.devViewUnlocked ? "btn-primary" : ""}`} onClick={()=>setTweak("devViewUnlocked", !tweaks.devViewUnlocked)}>
            <Icon name={tweaks.devViewUnlocked ? "toggle_on" : "toggle_off"} /> {tweaks.devViewUnlocked ? "켜짐 (JSON 원문 보임)" : "꺼짐"}
          </button>
        </div>
        <div>
          <div className="text-[11.5px] font-semibold mb-1" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>정보 밀도</div>
          <div className="flex gap-1">
            {[["airy","여유"],["comfortable","보통"],["dense","꽉"]].map(([k,l]) => (
              <button key={k} className={`btn btn-sm flex-1 ${tweaks.density === k ? "" : "btn-ghost"}`} onClick={()=>setTweak("density", k)}>{l}</button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Stubs for routes not in the 4 focus screens
function StubPage({ title, desc, icon = "construction" }) {
  return (
    <div className="p-6">
      <div className="card p-12 max-w-[760px] text-center" style={{ borderStyle: "dashed", background: "#fff" }}>
        <div className="rounded-full inline-flex items-center justify-center mb-3" style={{ width: 56, height: 56, background: "var(--brand-tint)" }}>
          <Icon name={icon} style={{ fontSize: 28, color: "var(--brand)" }} />
        </div>
        <div className="font-display font-semibold" style={{ fontSize: 18 }}>{title}</div>
        <div className="text-[13.5px] mt-1 max-w-[480px] mx-auto" style={{ color: "var(--ink-muted)", lineHeight: 1.55 }}>{desc}</div>
        <div className="hairline mt-5 pt-4 text-[12px]" style={{ color: "var(--ink-soft)" }}>이번 라운드 하이파이는 대시보드 · 결정/승인 · 환경설정 · 알림 · 디자인 시스템 5개 화면입니다. 나머지는 같은 디자인 시스템으로 확장 예정입니다.</div>
      </div>
    </div>
  );
}

function App() {
  const [route, setRoute] = React.useState("overview");
  const [tweaks, setTweaks] = React.useState(window.__TWEAK_DEFAULTS);
  const [tweaksOpen, setTweaksOpen] = React.useState(false);

  const setTweak = (k, v) => {
    setTweaks(prev => {
      const next = { ...prev, [k]: v };
      try { window.parent.postMessage({ type: "__edit_mode_set_keys", edits: { [k]: v } }, "*"); } catch(e) {}
      return next;
    });
  };

  React.useEffect(() => {
    const handler = (e) => {
      if (!e.data || typeof e.data !== "object") return;
      if (e.data.type === "__activate_edit_mode") setTweaksOpen(true);
      if (e.data.type === "__deactivate_edit_mode") setTweaksOpen(false);
    };
    window.addEventListener("message", handler);
    try { window.parent.postMessage({ type: "__edit_mode_available" }, "*"); } catch(e) {}
    return () => window.removeEventListener("message", handler);
  }, []);

  const labels = tweaks.labelLocale === "en" ? LABELS_EN : LABELS_KO;

  const titles = {
    overview:     { t: "대시보드", s: MOCK.greenhouse.name + " · 실시간" },
    zones:        { t: "구역 모니터링", s: "4개 구역의 24시간 추이" },
    decisions:    { t: "결정 · 승인", s: "AI가 권고한 조치를 확인·승인" },
    chat:         { t: "AI 어시스턴트", s: "적고추 전문 AI에게 질문하세요" },
    alerts:       { t: "알림", s: "지난 24시간 경고" },
    robot:        { t: "로봇", s: "작업 큐와 실행 이력" },
    devices:      { t: "장치 · 제약", s: "현재 연결된 장치 상태" },
    policies:     { t: "정책 · 이벤트", s: "안전 규칙과 최근 트리거" },
    automation:   { t: "환경설정 · 자동화 규칙", s: "센서 조건으로 장치를 자동 제어" },
    shadow:       { t: "Shadow Mode", s: "신규 모델 품질 모니터링 (관리자)" },
    system:       { t: "시스템", s: "실행 이력 · 런타임 (관리자)" },
    designsystem: { t: "디자인 시스템", s: "컴포넌트 · 토큰 · 복사 가이드" },
  };

  const onOpenApproval = (d) => { setRoute("decisions"); /* delegated inside page */ };

  const page = (() => {
    switch (route) {
      case "overview":     return <Dashboard tweaks={tweaks} setRoute={setRoute} onOpenApproval={onOpenApproval} />;
      case "decisions":    return <DecisionsPage devViewUnlocked={tweaks.devViewUnlocked} tweaks={tweaks} />;
      case "automation":   return <RulesPage />;
      case "alerts":       return <AlertsPage />;
      case "designsystem": return <DesignSystemPage />;
      case "zones":        return <ZonesPage />;
      case "chat":         return <ChatPage devViewUnlocked={tweaks.devViewUnlocked} />;
      case "robot":        return <RobotPage />;
      case "devices":      return <DevicesPage />;
      case "policies":     return <PoliciesPage />;
      case "shadow":       return <StubPage title="Shadow Mode (관리자)" icon="visibility" desc="운영자 동의율·중대 불일치 수를 게이지 UI로. Primary 사용자에게는 사이드바에서 '관리자' 그룹에 숨김." />;
      case "system":       return <StubPage title="시스템 (관리자)" icon="build" desc="실행 이력 · Runtime Mode · AI Runtime. prompt_version / retriever 등은 관리자 전용으로만 노출." />;
      default: return null;
    }
  })();

  return (
    <div className="flex min-h-screen" style={{ background: "var(--surface-low)" }}>
      <Sidebar route={route} setRoute={setRoute} labels={labels} />
      <div className="flex-1 min-w-0 flex flex-col">
        <Topbar
          title={titles[route].t} subtitle={titles[route].s}
          route={route} setRoute={setRoute}
          onToggleDev={() => setTweak("devViewUnlocked", !tweaks.devViewUnlocked)}
          devViewUnlocked={tweaks.devViewUnlocked}
          tweaks={tweaks} setTweaks={setTweaks}
        />
        <ConnectionBanner connected={true} />
        <main className="flex-1 min-w-0">{page}</main>
      </div>

      <TweaksPanel open={tweaksOpen} onClose={() => setTweaksOpen(false)} tweaks={tweaks} setTweak={setTweak} />
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

