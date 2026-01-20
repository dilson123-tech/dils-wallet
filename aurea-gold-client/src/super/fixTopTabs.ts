(function(){
  if (!location.pathname.startsWith('/super')) return;
  const selector = 'div.overflow-x-auto.no-scrollbar.-mx-1.px-1';
  const nuke = () => {
    document.querySelectorAll(selector).forEach(el => el.remove());
  };
  document.addEventListener('DOMContentLoaded', nuke);
  new MutationObserver(nuke).observe(document.body, { childList: true, subtree: true });
})();
