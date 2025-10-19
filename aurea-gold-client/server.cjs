const express = require('express');
const path = require('path');

const app = express();
const dist = path.resolve(__dirname, 'dist');

// Assets com cache longo
app.use('/assets', express.static(path.join(dist, 'assets'), {
  immutable: true,
  maxAge: '1y',
}));

// Demais estáticos sem cache agressivo
app.use(express.static(dist, { maxAge: 0 }));

// SPA fallback — não cachear o index.html
app.get(/.*/, (_req, res) => {
  res.set('Cache-Control', 'no-cache');
  res.sendFile(path.join(dist, 'index.html'));
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, '0.0.0.0', () => console.log('client up on', PORT));
