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
