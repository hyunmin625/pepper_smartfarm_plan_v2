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
