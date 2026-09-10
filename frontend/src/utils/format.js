export function bandColor(band) {
  if (band === "CRITICAL") return "text-soc-crit";
  if (band === "HIGH") return "text-soc-high";
  if (band === "MEDIUM") return "text-soc-warn";
  return "text-soc-good";
}

export function bandBg(band) {
  if (band === "CRITICAL") return "bg-soc-crit/20 text-soc-crit";
  if (band === "HIGH") return "bg-soc-high/20 text-soc-high";
  if (band === "MEDIUM") return "bg-soc-warn/20 text-soc-warn";
  return "bg-soc-good/20 text-soc-good";
}

export function fmt(v, fallback = "—") {
  if (v === null || v === undefined || v === "") return fallback;
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(1);
  return String(v);
}

/** Strip college / fictional-lab branding from API-sourced copy shown in the UI. */
export function sanitizeBrand(text) {
  if (text == null) return "";
  return String(text)
    .replace(/RMK College Cyber Defense Center\s*\(fictional\)/gi, "synthetic environment")
    .replace(/RMK College Cyber Defense Center/gi, "synthetic environment")
    .replace(/RMK College/gi, "")
    .replace(/\bRMK\b/gi, "")
    .replace(/Cyber Defense Center/gi, "")
    .replace(/fictional lab/gi, "synthetic environment")
    .replace(/college project/gi, "")
    .replace(/student project/gi, "")
    .replace(/\(fictional\)/gi, "")
    .replace(/\bfictional\b/gi, "")
    .replace(/\s{2,}/g, " ")
    .replace(/\s+([.,;:])/g, "$1")
    .trim();
}
