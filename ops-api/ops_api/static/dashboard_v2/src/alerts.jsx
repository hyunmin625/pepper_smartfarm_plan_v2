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
