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
