import express from "express";
const app = express();
const port = process.env.PORT || 8080;
app.use(express.static("dist"));
app.get("*", (_, res) => res.sendFile("index.html", { root: "dist" }));
app.listen(port, () => console.log(`[Aurea Gold] produção rodando na porta ${port}`));
