self.addEventListener('install', (event) => {
  // Ativa imediatamente a versão nova
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Assume controle de todas as abas abertas
  clients.claim();
});

// Placeholder: no futuro podemos colocar cache offline aqui
