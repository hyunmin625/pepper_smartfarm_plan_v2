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
