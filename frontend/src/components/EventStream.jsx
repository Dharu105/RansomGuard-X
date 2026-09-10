function severityTone(event) {
  const t = `${event?.event_type || ""} ${event?.severity || ""}`.toUpperCase();
  if (t.includes("ENCRYPT") || t.includes("RANSOM") || t.includes("CRITICAL")) return "bg-red-500";
  if (t.includes("LATERAL") || t.includes("PRIVILEGE") || t.includes("HIGH")) return "bg-orange-500";
  if (t.includes("CREDENTIAL") || t.includes("ACCESS") || t.includes("MEDIUM")) return "bg-amber-500";
  return "bg-cyan-400";
}

export default function EventStream({ events, lastId }) {
  const rows = events || [];
  return (
    <div className="overflow-hidden rounded-xl border border-cyan-500/15 bg-[#070b14] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-400/80">Live telemetry</div>
        <div className="text-[11px] text-soc-muted">Observed events only</div>
      </div>
      {rows.length === 0 ? (
        <div className="py-8 text-center">
          <div className="mx-auto h-16 w-16 rounded-full border border-soc-border" />
          <div className="mt-3 text-xs font-semibold uppercase tracking-[0.16em] text-soc-muted">No active incident</div>
          <p className="mt-1 text-sm text-soc-muted">Run Safe Simulation, then Next Event to ingest synthetic telemetry.</p>
        </div>
      ) : (
        <div className="max-h-[360px] overflow-auto font-mono text-[12px]">
          {rows.map((e, i) => {
            const live = e.id === lastId;
            const faded = i < rows.length - 3 && !live;
            return (
              <div
                key={e.id}
                className={`telemetry-row grid grid-cols-[76px_1fr] gap-3 border-l-2 px-3 py-2 ${
                  live ? "is-live border-cyan-400 bg-cyan-500/5" : "border-transparent"
                } ${faded ? "opacity-45" : ""}`}
              >
                <div className="text-soc-muted">{e.timestamp}</div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`h-1.5 w-1.5 rounded-full ${severityTone(e)}`} aria-hidden="true" />
                    <span className="font-medium uppercase tracking-wide text-soc-text">{e.event_type}</span>
                  </div>
                  <div className="mt-0.5 text-[11px] text-soc-muted">
                    {e.asset_id}
                    {e.user ? ` · ${e.user}` : ""}
                    {e.attack_stage ? ` · ${e.attack_stage}` : ""}
                  </div>
                  {e.summary ? <div className="mt-1 font-sans text-xs text-soc-muted">{e.summary}</div> : null}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
