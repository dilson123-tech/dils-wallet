const express = require('express');
const path = require('path');

const app = express();
const dist = path.resolve(__dirname, 'dist');

app.use(express.static(dist));
app.get('*', (_, res) => res.sendFile(path.join(dist, 'index.html')));

const port = process.env.PORT || 3000;
app.listen(port, () => console.log('Aurea client on :' + port));
