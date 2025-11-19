/**
 * Mantém só os botões de "Ações rápidas".
 * Remove "Enviar PIX / Histórico / Limpar" em QUALQUER outro lugar do /super.
 */
(function () {
  if (!location.pathname.startsWith("/super")) return;

  const KILL = new Set([
    "+ enviar pix", "enviar pix", "histórico", "historico", "limpar", "fechar", "his"
  ]);
  const norm = (t: string) => (t || "").toLowerCase().trim();

  function findQuickActionsRoot(): HTMLElement | null {
    // acha heading com o texto "Ações rápidas" e pega o próximo bloco (container de botões)
    const nodes = Array.from(document.querySelectorAll<HTMLElement>(".super *"));
    for (const el of nodes) {
      const txt = norm(el.textContent || "");
      if (txt === "ações rápidas") {
        // pega próximo irmão que contenha botões
        let sib = el.nextElementSibling as HTMLElement | null;
        while (sib && !sib.querySelector("button")) sib = sib.nextElementSibling as HTMLElement | null;
        return sib || null;
      }
    }
    return null;
  }

  function cleanup() {
    const keep = findQuickActionsRoot(); // pode ser null se ainda não montou
    const allBtns = Array.from(document.querySelectorAll<HTMLButtonElement>(".super button"));
    for (const b of allBtns) {
      const t = norm(b.textContent || "");
      if (!KILL.has(t)) continue;
      // se está DENTRO do container de ações rápidas, não remove
      if (keep && keep.contains(b)) continue;
      // se não sabemos qual é o keep ainda, não mexe (espera próxima rodada)
      if (!keep) continue;
      b.remove();
    }

    // se existir uma faixa de navegação vazia (sem botões), colapsa
    document.querySelectorAll<HTMLElement>(".aurea-tabs, nav[role='tablist'], .overflow-x-auto, .tabs")
      .forEach(el => {
        if (!el.querySelector("button")) {
          el.style.display = "none";
          el.style.height = "0";
          el.style.margin = "0";
          el.style.padding = "0";
        }
      });
  }

  // roda após montagem inicial e em mudanças subsequentes
  const schedule = () => setTimeout(cleanup, 200); // dá tempo do React pintar
  schedule();
  const obs = new MutationObserver(schedule);
  obs.observe(document.body, { childList: true, subtree: true });
  window.addEventListener("resize", schedule, { passive: true });
})();
