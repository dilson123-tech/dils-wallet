import express from "express";
import compression from "compression";
import serveStatic from "serve-static";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const app = express();

// CSP que libera a API do backend
const CSP = [
  "default-src 'self'",
  "connect-src 'self' https://dils-wallet-production.up.railway.app",
  "img-src 'self' data: blob:",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self' data:",
  "frame-ancestors 'self'",
  "base-uri 'self'",
].join("; ");

app.use((req, res, next) => {
  res.setHeader("Content-Security-Policy", CSP);
  next();
});

app.use(compression());
app.use(serveStatic(path.join(__dirname, "dist"), { index: ["index.html"] }));

const port = process.env.PORT || 8080;
app.listen(port, () => {
  console.log(`Client up on :${port}`);
});
