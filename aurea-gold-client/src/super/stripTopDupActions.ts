(function(){
  if (!location.pathname.startsWith('/super')) return;

  const KILL = new Set(['+ enviar pix','enviar pix','histórico','historico','limpar','fechar','his']);
  const norm = (t:string)=> (t||'').toLowerCase().replace(/\s+/g,' ').trim();

  function run(){
    const superRoot = document.querySelector('.super') as HTMLElement | null;
    if (!superRoot) return;

    // achamos o bloco do título "Ações rápidas"
    const all = Array.from(superRoot.children) as HTMLElement[];
    let until = all.length;
    for (let i=0;i<all.length;i++){
      const txt = norm(all[i].textContent||'');
      if (txt.includes('ações rápidas')) { until = i; break; }
    }

    // em todos os filhos ANTES de "Ações rápidas", remova nós cujo texto bata com KILL
    for (let i=0;i<until;i++){
      const zone = all[i];
      const nodes = Array.from(zone.querySelectorAll<HTMLElement>('*'));
      for (const el of nodes){
        const t = norm(el.textContent||'');
        if (KILL.has(t)){
          el.remove();
        }
      }
      // se a faixa ficar vazia, colapsa
      if (!zone.querySelector('*')) {
        zone.style.display='none'; zone.style.height='0'; zone.style.margin='0'; zone.style.padding='0';
      }
    }
  }

  const schedule = ()=> setTimeout(run,150);
  document.addEventListener('DOMContentLoaded', schedule);
  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true});
  addEventListener('resize', schedule, { passive:true });
})();
