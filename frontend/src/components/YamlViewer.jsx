import { sanitizeBrand } from "../utils/format.js";

export default function YamlViewer({ title, text }) {
  const highlighted = highlight(sanitizeBrand(text || ""));
  return (
    <div className="panel overflow-hidden">
      <div className="border-b border-soc-border px-4 py-2 text-xs uppercase tracking-wide text-soc-muted">{title}</div>
      <pre className="max-h-[480px] overflow-auto p-4 font-mono text-xs leading-6" dangerouslySetInnerHTML={{ __html: highlighted }} />
    </div>
  );
}

function highlight(src) {
  return src
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replace(/#.*/g, '<span class="text-soc-muted">$&</span>')
    .replace(/^([ \t]*)([\w-]+)(?=:)/gm, '$1<span class="text-soc-accent">$2</span>')
    .replace(/(:\s*)(true|false|\d+|>\d+|".*?")/g, '$1<span class="text-soc-good">$2</span>');
}
