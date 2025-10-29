import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import serveStatic from "serve-static";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const app = express();

const distPath = path.join(__dirname, "dist");
console.log("[Aurea Gold] distPath =", distPath);
console.log("[Aurea Gold] index.html existe?", fs.existsSync(path.join(distPath, "index.html")));

// health check
app.get("/healthz", (req, res) => {
  res.json({ ok: true, service: "aurea-gold-client" });
});

// arquivos estáticos (JS, CSS, icons, manifest)
app.use(serveStatic(distPath, {
  index: ["index.html"],
  setHeaders: (res, filePath) => {
    if (filePath.endsWith(".webmanifest")) res.setHeader("Content-Type", "application/manifest+json");
    if (filePath.endsWith(".svg")) res.setHeader("Content-Type", "image/svg+xml");
  }
}));

// fallback total para SPA
app.get("*", (req, res) => {
  res.sendFile(path.join(distPath, "index.html"));
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`[Aurea Gold] produção rodando na porta ${PORT}`);
});
