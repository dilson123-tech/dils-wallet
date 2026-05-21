import React, { useEffect, useState } from "react";
import { fetchWalletAccountStatus, fetchWalletStructuredBalance, type WalletAccountStatus, type WalletStructuredBalance } from "../super2/api";

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
  const [walletStatus, setWalletStatus] = useState<WalletAccountStatus | null>(null);
  const [walletStatusLoading, setWalletStatusLoading] = useState(true);
  const [walletStatusError, setWalletStatusError] = useState<string | null>(null);
  const [structuredBalance, setStructuredBalance] = useState<WalletStructuredBalance | null>(null);
  const [structuredBalanceLoading, setStructuredBalanceLoading] = useState(true);
  const [structuredBalanceError, setStructuredBalanceError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    fetchWalletAccountStatus()
      .then((data) => {
        if (!alive) return;
        setWalletStatus(data);
        setWalletStatusError(null);
      })
      .catch((error) => {
        if (!alive) return;
        setWalletStatusError(error instanceof Error ? error.message : "Falha ao carregar status da carteira.");
      })
      .finally(() => {
        if (!alive) return;
        setWalletStatusLoading(false);
      });

    fetchWalletStructuredBalance()
      .then((data) => {
        if (!alive) return;
        setStructuredBalance(data);
        setStructuredBalanceError(null);
      })
      .catch((error) => {
        if (!alive) return;
        setStructuredBalanceError(error instanceof Error ? error.message : "Falha ao carregar saldo estruturado.");
      })
      .finally(() => {
        if (!alive) return;
        setStructuredBalanceLoading(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  const wallet = walletStatus?.wallet;
  const walletModeLabel = wallet?.mode === "partner" ? "Parceiro" : "Demonstração";
  const realMoneyLabel = wallet?.real_money_enabled ? "Dinheiro real ativo" : "Dinheiro real desativado";
  const kycLabel =
    wallet?.kyc_status === "not_started"
      ? "Pendente"
      : wallet?.kyc_status === "provider_required"
      ? "Exigido pelo parceiro"
      : wallet?.kyc_status || "Não informado";
  const kybLabel =
    wallet?.kyb_status === "not_started"
      ? "Pendente"
      : wallet?.kyb_status === "provider_required"
      ? "Exigido pelo parceiro"
      : wallet?.kyb_status || "Não informado";
  const providerLabel = wallet?.provider === "demo" ? "Demo" : wallet?.provider || "Não configurado";
  const accountStatusLabel =
    wallet?.account_status === "demo_active"
      ? "Demonstração ativa"
      : wallet?.account_status === "partner_ready"
      ? "Parceiro pronto"
      : wallet?.account_status || "Não informado";
  const structuredWallet = structuredBalance?.wallet;
  const structuredProviderLabel =
    structuredWallet?.provider === "demo" ? "Demo" : structuredWallet?.provider || "Não configurado";
  const structuredSourceLabel =
    structuredWallet?.source === "demo"
      ? "Demo"
      : structuredWallet?.source === "partner"
      ? "Parceiro"
      : structuredWallet?.source || "Não informado";
  const structuredRealMoneyLabel = structuredWallet?.real_money_enabled
    ? "Dinheiro real ativo"
    : "Dinheiro real desativado";

  return (
    <section className="w-full max-w-[960px] mx-auto space-y-5 md:space-y-6">
      <header className="ag-surface-elevated px-4 py-5 sm:px-5 sm:py-6">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          Aurea Gold • Mais
        </div>
        <h1 className="mt-2 text-[1.45rem] sm:text-2xl md:text-3xl font-bold text-[#f4f8ff] leading-tight">
          Ajuda, suporte e serviços
        </h1>
        <p className="mt-2 text-sm text-[#D7D0BE] max-w-2xl">
          Busca, suporte, assistente Aurea, histórico de consultas e recursos
          adicionais do aplicativo.
        </p>

        <div className="mt-4">
          <div className="flex items-center gap-3 rounded-[18px] border border-amber-500/14 bg-[rgba(12,30,42,0.88)] px-4 py-3">
            <span className="text-lg text-amber-300">⌕</span>
            <span className="text-sm text-[#B8AD95]">
              Busque ajuda, pagamentos e serviços
            </span>
          </div>
        </div>
      </header>

      <section className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          Status da carteira
        </div>

        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[#f4f8ff]">
              Carteira em modo {walletModeLabel}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
              A Aurea Gold está preparada para operar como wallet real via parceiro financeiro. No modo atual, o app informa limitações antes de qualquer operação financeira real.
            </p>
          </div>

          <span className={`inline-flex w-fit rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${
            wallet?.real_money_enabled
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
              : "border-amber-500/20 bg-amber-500/10 text-amber-200"
          }`}>
            {realMoneyLabel}
          </span>
        </div>

        {walletStatusLoading && (
          <p className="mt-4 text-sm text-[#B8AD95]">
            Carregando status da carteira...
          </p>
        )}

        {walletStatusError && (
          <p className="mt-4 text-sm text-rose-300">
            Não foi possível carregar o status agora. Tente novamente depois.
          </p>
        )}

        {walletStatus && (
          <>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Provedor</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{providerLabel}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Conta</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{accountStatusLabel}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">KYC</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{kycLabel}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">KYB</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{kybLabel}</div>
              </div>
            </div>

            <div className="mt-4 rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Limitação atual</div>
              <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                {walletStatus.limitations?.[0] || "A carteira ainda está em preparação para operação real via parceiro financeiro."}
              </p>
            </div>

            <div className="mt-3 rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Próximo passo</div>
              <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                {walletStatus.next_steps?.[0] || "Selecionar parceiro financeiro/PSP/BaaS."}
              </p>
            </div>
          </>
        )}
      </section>

      <section className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          Saldo estruturado
        </div>

        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[#f4f8ff]">
              Contrato de saldo da wallet
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
              Separação técnica entre saldo disponível, bloqueado e pendente. No modo demo, esses valores não representam dinheiro real.
            </p>
          </div>

          <span className={`inline-flex w-fit rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${
            structuredWallet?.real_money_enabled
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
              : "border-amber-500/20 bg-amber-500/10 text-amber-200"
          }`}>
            {structuredRealMoneyLabel}
          </span>
        </div>

        {structuredBalanceLoading && (
          <p className="mt-4 text-sm text-[#B8AD95]">
            Carregando saldo estruturado...
          </p>
        )}

        {structuredBalanceError && (
          <p className="mt-4 text-sm text-rose-300">
            Não foi possível carregar o saldo estruturado agora.
          </p>
        )}

        {structuredBalance && (
          <>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Disponível</div>
                <div className="mt-1 text-lg font-semibold text-[#f4f8ff]">R$ {structuredBalance.balance.available.replace(".", ",")}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Bloqueado</div>
                <div className="mt-1 text-lg font-semibold text-[#f4f8ff]">R$ {structuredBalance.balance.blocked.replace(".", ",")}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Pendente</div>
                <div className="mt-1 text-lg font-semibold text-[#f4f8ff]">R$ {structuredBalance.balance.pending.replace(".", ",")}</div>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Origem</div>
                <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                  {structuredSourceLabel} • Provedor {structuredProviderLabel}
                </p>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Aviso</div>
                <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                  {structuredBalance.notice}
                </p>
              </div>
            </div>
          </>
        )}
      </section>

      <section className="space-y-3">
        <div>
          <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
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
              className="ag-card rounded-[20px] px-4 py-4 text-center border border-amber-500/10 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]"
            >
              <div className="text-amber-300 text-lg">✦</div>
              <div className="mt-2 text-sm font-medium text-[#f4f8ff] leading-snug">
                {item}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          Assistente Aurea
        </div>
        <h2 className="mt-2 text-xl font-semibold text-[#f4f8ff]">
          Atendimento inteligente da carteira
        </h2>
        <p className="mt-2 text-sm text-[#D7D0BE]">
          O assistente da Aurea vai concentrar ajuda contextual, dúvidas sobre
          pagamentos, orientações rápidas e fluxos guiados dentro do app.
        </p>
      </section>

      <section className="space-y-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          Suporte e utilidades
        </div>
        <div className="grid grid-cols-1 gap-3">
          {atalhos.map((item) => (
            <article
              key={item}
              className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-4 text-sm text-[#f4f8ff]"
            >
              {item}
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
