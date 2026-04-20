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
