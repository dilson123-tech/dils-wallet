(function(){
  if (!location.pathname.startsWith('/super')) return;
  const apply = ()=> document.body.classList.add('aurea-mobile');
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', apply);
  } else {
    apply();
  }
})();
