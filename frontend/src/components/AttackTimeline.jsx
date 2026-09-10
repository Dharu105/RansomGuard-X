export default function AttackTimeline({ events, lastId }) {
  const rows = events || [];
  return (
    <div className="rounded-lg border border-soc-border/80 bg-[#070b14] px-3 py-2">
      <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-soc-muted">Incident spine</div>
      {rows.length === 0 ? (
        <p className="text-sm text-soc-muted">Observed progression will appear here after events are ingested.</p>
      ) : (
        <div className="flex items-stretch gap-0 overflow-x-auto pb-1">
          <div className="mr-2 self-center text-[10px] uppercase text-soc-muted">Start</div>
          {rows.map((e, i) => {
            const current = e.id === lastId;
            return (
              <div key={e.id} className="flex items-center">
                <div className="flex flex-col items-center">
                  <span className={`h-2 w-2 rounded-full ${current ? "bg-cyan-400" : "bg-soc-border"}`} />
                  <div className={`mt-1 max-w-[110px] truncate text-center text-[10px] uppercase ${current ? "text-cyan-300" : "text-soc-muted"}`}>
                    {e.event_type}
                  </div>
                </div>
                {i < rows.length - 1 ? <div className="mx-1 mb-4 h-px w-8 bg-soc-border" /> : null}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
