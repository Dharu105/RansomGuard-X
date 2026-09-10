export default function MetricCard({ label, value, hint, tone = "text-white" }) {
  return (
    <div className="panel p-4">
      <div className="text-xs uppercase tracking-wide text-soc-muted">{label}</div>
      <div className={`mt-2 text-2xl font-semibold ${tone}`}>{value}</div>
      {hint ? <div className="mt-1 text-xs text-soc-muted">{hint}</div> : null}
    </div>
  );
}
