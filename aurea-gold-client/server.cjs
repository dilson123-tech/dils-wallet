const express = require('express');
const path = require('path');

const app = express();
const dist = path.resolve(__dirname, 'dist');

// arquivos estáticos do build
app.use(express.static(dist, { index: 'index.html', extensions: ['html'] }));

// healthcheck simples (útil pro Railway)
app.get('/healthz', (_, res) => res.type('text').send('ok'));

// start
const PORT = process.env.PORT || 8080;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🔊 Aurea client UP on :${PORT}`);
});
