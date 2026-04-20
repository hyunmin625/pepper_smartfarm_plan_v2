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
