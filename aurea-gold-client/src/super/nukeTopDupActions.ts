(function(){
  if (!location.pathname.startsWith('/super')) return;

  const KILL_WORDS = ['enviar pix','histórico','historico','limpar','+ enviar pix','fechar','his'];
  const norm = (s:string)=> (s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\s+/g,' ').trim();

  function killTabs(){
    const bars = document.querySelectorAll<HTMLElement>(
      '.aurea-tabs, nav[role="tablist"], .overflow-x-auto'
    );
    let removed = 0;

    for (const bar of bars){
      const texts = Array.from(bar.querySelectorAll('*')).map(el => norm(el.textContent||''));
      const hit = texts.some(t => KILL_WORDS.some(k => t.includes(k)));
      if (hit){
        bar.remove();
        removed++;
      }
    }

    if (removed>0) console.debug('[nukeTopDupActions] barras removidas:', removed);
  }

  const schedule = ()=> setTimeout(killTabs, 100);
  document.addEventListener('DOMContentLoaded', schedule);
  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true});
  addEventListener('resize', schedule, {passive:true});
})();
