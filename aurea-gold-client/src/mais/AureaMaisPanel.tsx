import React from "react";

const sugestoes = [
  "Recarga de celular",
  "Convide e ganhe",
  "Buscar ajuda",
  "Assistente Aurea",
];

const atalhos = [
  "Consultas recentes",
  "Ouvidoria",
  "Atendimento em Libras",
  "Termos e condições",
  "Segurança da conta",
  "Configurações",
];

export default function AureaMaisPanel() {
  return (
    <section className="w-full max-w-[960px] mx-auto space-y-5 md:space-y-6">
      <header className="ag-surface-elevated px-4 py-5 sm:px-5 sm:py-6">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#86c0ff]">
          Aurea Gold • Mais
        </div>
        <h1 className="mt-2 text-[1.45rem] sm:text-2xl md:text-3xl font-bold text-[#f4f8ff] leading-tight">
          Ajuda, suporte e serviços
        </h1>
        <p className="mt-2 text-sm text-[#bfd0ec] max-w-2xl">
          Busca, suporte, assistente Aurea, histórico de consultas e recursos
          adicionais do aplicativo.
        </p>

        <div className="mt-4">
          <div className="flex items-center gap-3 rounded-[18px] border border-sky-500/26 bg-[rgba(8,18,35,0.88)] px-4 py-3">
            <span className="text-lg text-sky-300">⌕</span>
            <span className="text-sm text-[#8fa8cf]">
              Busque ajuda, pagamentos e serviços
            </span>
          </div>
        </div>
      </header>

      <section className="space-y-3">
        <div>
          <div className="text-[10px] uppercase tracking-[0.16em] text-[#86c0ff]">
            Sugestões
          </div>
          <h2 className="mt-2 text-xl font-semibold text-[#f4f8ff]">
            Acessos rápidos
          </h2>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {sugestoes.map((item) => (
            <article
              key={item}
              className="ag-card rounded-[20px] px-4 py-4 text-center border border-sky-500/16 bg-[linear-gradient(180deg,rgba(12,24,46,0.96),rgba(7,15,30,0.98))]"
            >
              <div className="text-sky-300 text-lg">✦</div>
              <div className="mt-2 text-sm font-medium text-[#f4f8ff] leading-snug">
                {item}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-sky-500/20 bg-[linear-gradient(180deg,rgba(12,24,46,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#86c0ff]">
          Assistente Aurea
        </div>
        <h2 className="mt-2 text-xl font-semibold text-[#f4f8ff]">
          Atendimento inteligente da carteira
        </h2>
        <p className="mt-2 text-sm text-[#bfd0ec]">
          O assistente da Aurea vai concentrar ajuda contextual, dúvidas sobre
          pagamentos, orientações rápidas e fluxos guiados dentro do app.
        </p>
      </section>

      <section className="space-y-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#86c0ff]">
          Suporte e utilidades
        </div>
        <div className="grid grid-cols-1 gap-3">
          {atalhos.map((item) => (
            <article
              key={item}
              className="rounded-[18px] border border-sky-500/18 bg-[rgba(8,18,35,0.74)] px-4 py-4 text-sm text-[#f4f8ff]"
            >
              {item}
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
