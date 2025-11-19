/**
 * Mantém só os botões de "Ações rápidas".
 * Remove "Enviar PIX / Histórico / Limpar" em QUALQUER outro lugar do /super.
 */
(function () {
  if (!location.pathname.startsWith("/super")) return;

  const KILL = new Set([
    "+ enviar pix","enviar pix","histórico","historico","limpar","fechar","his"
  ]);
  const norm = (t:string) => (t||"").toLowerCase().replace(/\s+/g," ").trim();

  function findQuickActionsRoot(): HTMLElement | null {
    // acha heading "Ações rápidas" e pega o próximo bloco que tenha botões
    const nodes = Array.from(document.querySelectorAll<HTMLElement>(".super *"));
    for (const el of nodes) {
      if (norm(el.textContent||"") === "ações rápidas") {
        let sib = el.nextElementSibling as HTMLElement | null;
        while (sib && !sib.querySelector("button")) sib = sib.nextElementSibling as HTMLElement | null;
        return sib || null;
      }
    }
    return null;
  }

  function cleanup() {
    const keep = findQuickActionsRoot();        // container oficial dos botões
    const all = Array.from(document.querySelectorAll<HTMLElement>(".super *"));
    for (const el of all) {
      // só candidatos interativos
      if (!(el instanceof HTMLButtonElement) && el.getAttribute("role") !== "button") continue;
      const t = norm(el.textContent||"");
      if (!KILL.has(t)) continue;
      if (keep && keep.contains(el)) continue;  // não remove os de Ações rápidas
      el.remove();                              // remove duplicados
    }
    // se uma faixa de navegação ficar vazia, some com ela
    document.querySelectorAll<HTMLElement>(".aurea-tabs, nav[role='tablist'], .overflow-x-auto, .tabs")
      .forEach(bar=>{
        if (!bar.querySelector("button,[role='button']")) {
          bar.style.display="none"; bar.style.height="0"; bar.style.margin="0"; bar.style.padding="0";
        }
      });
  }

  const schedule = () => setTimeout(cleanup, 200);
  schedule();
  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true});
  addEventListener("resize", schedule, { passive:true });
})();
