export function makeIdem(prefix = "pix") {
  // chave curta, única por clique (ex.: "pix-20251021-1730-abc123")
  const s = Math.random().toString(36).slice(2, 8);
  const t = new Date();
  const hh = String(t.getHours()).padStart(2, "0");
  const mm = String(t.getMinutes()).padStart(2, "0");
  return `${prefix}-${t.getFullYear()}${String(t.getMonth()+1).padStart(2,"0")}${String(t.getDate()).padStart(2,"0")}-${hh}${mm}-${s}`;
}
