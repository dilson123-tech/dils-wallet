export function formatBRL(n: number | undefined | null): string {
  const v = typeof n === "number" ? n : 0;
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
