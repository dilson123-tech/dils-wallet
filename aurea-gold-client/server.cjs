/* Servidor estático para SPA (Vite build) + fallback de rotas */
const path = require('path');
const fs = require('fs');
const express = require('express');

const app = express();
const distDir = path.resolve(__dirname, 'dist');
const port = process.env.PORT || 8080;

/* healthcheck para o Railway */
app.get('/healthz', (_, res) => res.type('text').send('ok'));

/* estáticos com cache para assets fingerprintados */
app.use(express.static(distDir, {
  index: false,
  extensions: ['html'],
  setHeaders(res, filePath) {
    // assets gerados pelo Vite têm hash → pode cachear forte
    if (/\.(css|js|png|jpg|jpeg|svg|ico|webp|woff2?)$/.test(filePath) && filePath.includes('/assets/')) {
      res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
    } else {
      res.setHeader('Cache-Control', 'no-cache');
    }
  }
}));

/* fallback do SPA: qualquer rota que não for arquivo/asset devolve index.html */
app.get('*', (req, res, next) => {
  const p = req.path;
  // se parecer arquivo (tem extensão), deixa o static responder 404
  if (path.extname(p)) return next();
  const indexPath = path.join(distDir, 'index.html');
  try {
    const html = fs.readFileSync(indexPath, 'utf8');
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(200).send(html);
  } catch (e) {
    return res.status(500).send('index.html not found');
  }
});

app.listen(port, () => {
  console.log(`> SPA server on http://0.0.0.0:${port}`);
});
