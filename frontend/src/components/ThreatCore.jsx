import { bandColor, fmt } from "../utils/format.js";

export default function ThreatCore({ score, band, events, assets, stage, idle }) {
  const pct = Math.max(0, Math.min(100, Number(score) || 0));
  const rings = [
    { r: 58, w: 2, op: 0.25 },
    { r: 50, w: 7, op: 1 },
    { r: 40, w: 2, op: 0.35 },
  ];
  const stroke = band === "CRITICAL" ? "#EF4444" : band === "HIGH" ? "#F97316" : band === "MEDIUM" ? "#F59E0B" : "#22D3EE";
  const pulse = band === "CRITICAL" ? "threat-crit" : band === "HIGH" || band === "MEDIUM" ? "threat-warn" : "threat-calm";

  return (
    <div className="flex h-full flex-col px-3 py-4">
      <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-soc-muted">Threat core</div>
      {idle ? (
        <div className="mt-6 text-center">
          <div className="mx-auto h-28 w-28 rounded-full border border-soc-border" />
          <div className="mt-3 text-[11px] uppercase tracking-[0.16em] text-soc-muted">System ready</div>
          <p className="mt-1 text-xs text-soc-muted">No active threat. Start the synthetic incident from the command bar.</p>
        </div>
      ) : (
        <>
          <div className={`relative mx-auto mt-2 flex h-[176px] w-[176px] items-center justify-center ${pulse}`}>
            {band === "CRITICAL" ? <div className="pointer-events-none absolute inset-4 rounded-full bg-red-500/10 blur-md" /> : null}
            <svg viewBox="0 0 140 140" className="h-full w-full -rotate-90" aria-hidden="true">
              {rings.map((ring) => {
                const circ = 2 * Math.PI * ring.r;
                const offset = ring.w > 3 ? circ - (pct / 100) * circ : circ * 0.08;
                return (
                  <circle
                    key={ring.r}
                    cx="70"
                    cy="70"
                    r={ring.r}
                    fill="none"
                    stroke={ring.w > 3 ? stroke : "#1D2A3A"}
                    strokeWidth={ring.w}
                    strokeLinecap="round"
                    strokeDasharray={circ}
                    strokeDashoffset={offset}
                    opacity={ring.op}
                    style={{ transition: "stroke-dashoffset 280ms ease, stroke 280ms ease" }}
                  />
                );
              })}
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className={`font-mono text-3xl font-semibold tabular-nums ${bandColor(band)}`}>{fmt(score)}</div>
              <div className={`text-[11px] font-semibold uppercase ${bandColor(band)}`}>{band || "LOW"}</div>
            </div>
          </div>
          <div className="mt-2 grid grid-cols-2 gap-1.5 text-[10px] uppercase tracking-wide">
            <div className="text-soc-muted">Risk <span className="ml-1 font-mono text-soc-text">{fmt(score)}</span></div>
            <div className="text-soc-muted">Events <span className="ml-1 font-mono text-soc-text">{events ?? 0}</span></div>
            <div className="text-soc-muted">Assets <span className="ml-1 font-mono text-soc-text">{assets ?? 0}</span></div>
            <div className="truncate text-soc-muted">Stage <span className="ml-1 text-soc-text">{stage || "NORMAL"}</span></div>
          </div>
        </>
      )}
    </div>
  );
}
