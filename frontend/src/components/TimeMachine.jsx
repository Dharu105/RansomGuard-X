export default function TimeMachine({ data }) {
  const branches = data?.alternate_futures || {};
  return (
    <div className="panel p-4">
      <div className="mb-3 text-xs uppercase tracking-wide text-soc-muted">Cyber Defense Time Machine</div>
      <div className="grid gap-3 md:grid-cols-4">
        <Column title="Past" items={data?.past?.length ? data.past : ["Quiet"]} />
        <Column title="Current" items={[data?.current || "NORMAL"]} highlight label="YOU ARE HERE" />
        <Column title="Predicted future" items={[data?.predicted_future || "No prediction yet"]} />
        <div>
          <div className="text-xs text-soc-muted">Alternate futures</div>
          <div className="mt-2 space-y-2">
            {["NO_ACTION", "REVOKE_CREDENTIALS", "ISOLATE_ENDPOINT", "ISOLATE_AND_REVOKE"].map((k) => {
              const b = branches[k];
              return (
                <div key={k} className="rounded-lg border border-soc-border bg-soc-raised p-2 text-xs">
                  <div className="font-medium">{k.replaceAll("_", " ")}</div>
                  {b ? (
                    <div className="text-soc-muted">
                      {b.systems_affected} systems · exposure {b.exposure} · {b.impact_level}
                      <div className="text-[10px]">{b.label}</div>
                    </div>
                  ) : (
                    <div className="text-soc-muted">Run events to simulate</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function Column({ title, items, highlight, label }) {
  return (
    <div className={`rounded-lg border p-3 ${highlight ? "border-soc-accent bg-soc-accent/10" : "border-soc-border"}`}>
      <div className="text-xs text-soc-muted">{title}</div>
      {label ? <div className="mt-1 text-[10px] font-semibold text-soc-accent">{label}</div> : null}
      <ul className="mt-2 space-y-1 text-sm">
        {(items || []).map((x, i) => (
          <li key={i}>{x}</li>
        ))}
      </ul>
    </div>
  );
}
