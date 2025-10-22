export function formatBRL(v: number | string){
  const n = typeof v === "string" ? Number(v) : (v ?? 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
