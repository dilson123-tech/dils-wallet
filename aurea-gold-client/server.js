const serve = require('serve');
const port = process.env.PORT || 8080;

// single: true -> SPA (histórico do Vite) cai para index.html
serve('dist', { port, single: true });
