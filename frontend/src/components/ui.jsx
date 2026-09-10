export function MetaBadge({ children, tone = "cyan" }) {
  const tones = {
    cyan: "border-cyan-500/40 text-cyan-400",
    blue: "border-blue-500/40 text-blue-400",
    purple: "border-violet-500/40 text-violet-400",
    amber: "border-soc-warn/40 text-soc-warn",
    red: "border-soc-crit/40 text-soc-crit",
    green: "border-soc-good/40 text-soc-good",
    mute: "border-soc-border text-soc-muted",
  };
  return (
    <span className={`inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${tones[tone] || tones.mute}`}>
      {children}
    </span>
  );
}

export function EmptyState({ title, body, action }) {
  return (
    <div className="panel flex min-h-[180px] flex-col items-start justify-center p-6">
      <div className="text-xs font-semibold uppercase tracking-[0.16em] text-soc-muted">{title}</div>
      <p className="mt-2 max-w-lg text-sm text-soc-muted">{body}</p>
      {action}
    </div>
  );
}

export function PageHeader({ title, subtitle, badges }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {subtitle ? <p className="mt-1 text-sm text-soc-muted">{subtitle}</p> : null}
        {badges ? <div className="mt-2 flex flex-wrap gap-1.5">{badges}</div> : null}
      </div>
    </div>
  );
}

export function KindBadge({ kind }) {
  const k = (kind || "OBSERVED").toUpperCase();
  const tone =
    k === "PREDICTED" ? "blue" : k === "SIMULATED" ? "purple" : k === "HISTORICAL" ? "mute" : "green";
  return <MetaBadge tone={tone}>{k}</MetaBadge>;
}

export function LoopStrip({ steps, active }) {
  return (
    <div className="panel flex flex-wrap items-center gap-1 px-3 py-2">
      {steps.map((step, i) => (
        <span key={step} className="flex items-center gap-1 text-[11px]">
          <span
            className={
              step === active
                ? "rounded bg-cyan-500/15 px-2 py-0.5 font-semibold text-cyan-400"
                : "px-1 text-soc-muted"
            }
          >
            {step}
          </span>
          {i < steps.length - 1 ? <span className="text-soc-border">→</span> : null}
        </span>
      ))}
    </div>
  );
}
