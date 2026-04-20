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
