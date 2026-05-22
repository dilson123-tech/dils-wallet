import React, { useEffect, useState } from "react";
import { fetchWalletAccountStatus, fetchWalletStructuredBalance, fetchWalletStructuredStatement, fetchWalletReceiptReconciliation, fetchWalletOperationalLimits, fetchWalletOnboardingStatus, type WalletAccountStatus, type WalletStructuredBalance, type WalletStructuredStatement, type WalletReceiptReconciliation, type WalletOperationalLimits, type WalletOnboardingStatus } from "../super2/api";

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
  const [structuredStatement, setStructuredStatement] = useState<WalletStructuredStatement | null>(null);
  const [structuredStatementLoading, setStructuredStatementLoading] = useState(true);
  const [structuredStatementError, setStructuredStatementError] = useState<string | null>(null);
  const [receiptReconciliation, setReceiptReconciliation] = useState<WalletReceiptReconciliation | null>(null);
  const [receiptReconciliationLoading, setReceiptReconciliationLoading] = useState(true);
  const [receiptReconciliationError, setReceiptReconciliationError] = useState<string | null>(null);
  const [operationalLimits, setOperationalLimits] = useState<WalletOperationalLimits | null>(null);
  const [operationalLimitsLoading, setOperationalLimitsLoading] = useState(true);
  const [operationalLimitsError, setOperationalLimitsError] = useState<string | null>(null);
  const [walletOnboarding, setWalletOnboarding] = useState<WalletOnboardingStatus | null>(null);
  const [walletOnboardingLoading, setWalletOnboardingLoading] = useState(true);
  const [walletOnboardingError, setWalletOnboardingError] = useState<string | null>(null);

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

    fetchWalletStructuredStatement(20)
      .then((data) => {
        if (!alive) return;
        setStructuredStatement(data);
        setStructuredStatementError(null);
      })
      .catch((error) => {
        if (!alive) return;
        setStructuredStatementError(error instanceof Error ? error.message : "Falha ao carregar extrato estruturado.");
      })
      .finally(() => {
        if (!alive) return;
        setStructuredStatementLoading(false);
      });

    fetchWalletReceiptReconciliation("demo-ui-preview")
      .then((data) => {
        if (!alive) return;
        setReceiptReconciliation(data);
        setReceiptReconciliationError(null);
      })
      .catch((error) => {
        if (!alive) return;
        setReceiptReconciliationError(error instanceof Error ? error.message : "Falha ao carregar comprovante/reconciliação.");
      })
      .finally(() => {
        if (!alive) return;
        setReceiptReconciliationLoading(false);
      });

    fetchWalletOperationalLimits()
      .then((data) => {
        if (!alive) return;
        setOperationalLimits(data);
        setOperationalLimitsError(null);
      })
      .catch((error) => {
        if (!alive) return;
        setOperationalLimitsError(error instanceof Error ? error.message : "Falha ao carregar limites operacionais.");
      })
      .finally(() => {
        if (!alive) return;
        setOperationalLimitsLoading(false);
      });

    fetchWalletOnboardingStatus()
      .then((data) => {
        if (!alive) return;
        setWalletOnboarding(data);
        setWalletOnboardingError(null);
      })
      .catch((error) => {
        if (!alive) return;
        setWalletOnboardingError(error instanceof Error ? error.message : "Falha ao carregar onboarding da carteira.");
      })
      .finally(() => {
        if (!alive) return;
        setWalletOnboardingLoading(false);
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
  const statementWallet = structuredStatement?.wallet;
  const statementProviderLabel =
    statementWallet?.provider === "demo" ? "Demo" : statementWallet?.provider || "Não configurado";
  const statementSourceLabel =
    statementWallet?.source === "demo"
      ? "Demo"
      : statementWallet?.source === "partner"
      ? "Parceiro"
      : statementWallet?.source || "Não informado";
  const statementRealMoneyLabel = statementWallet?.real_money_enabled
    ? "Dinheiro real ativo"
    : "Dinheiro real desativado";
  const receiptWallet = receiptReconciliation?.wallet;
  const receiptRealMoneyLabel = receiptWallet?.real_money_enabled
    ? "Dinheiro real ativo"
    : "Dinheiro real desativado";
  const receiptProviderLabel =
    receiptWallet?.provider === "demo" ? "Demo" : receiptWallet?.provider || "Não configurado";
  const transactionStatusLabel =
    receiptReconciliation?.receipt.transaction_status === "demo_only"
      ? "Somente demonstração"
      : receiptReconciliation?.receipt.transaction_status || "Não informado";
  const auditStatusLabel =
    receiptReconciliation?.receipt.audit_status === "demo_recorded"
      ? "Auditoria demo registrada"
      : receiptReconciliation?.receipt.audit_status || "Não informado";
  const reconciliationStatusLabel =
    receiptReconciliation?.receipt.reconciliation_status === "not_applicable_demo"
      ? "Não aplicável em demo"
      : receiptReconciliation?.receipt.reconciliation_status || "Não informado";
  const operationalWallet = operationalLimits?.wallet;
  const operationalRealMoneyLabel = operationalWallet?.real_money_enabled
    ? "Dinheiro real ativo"
    : "Dinheiro real desativado";
  const canSendPixLabel = operationalLimits?.permissions.can_send_pix ? "Ativado" : "Desativado";
  const canReceivePixLabel = operationalLimits?.permissions.can_receive_pix ? "Ativado" : "Desativado";
  const confirmationLabel = operationalLimits?.permissions.requires_confirmation ? "Obrigatória" : "Não exigida";
  const onboardingWallet = walletOnboarding?.wallet;
  const onboardingRealMoneyLabel = onboardingWallet?.real_money_enabled
    ? "Dinheiro real ativo"
    : "Dinheiro real desativado";
  const onboardingStatusText: Record<string, string> = {
    not_started: "Não iniciado",
    pending: "Pendente",
    in_review: "Em análise",
    approved: "Aprovado",
    rejected: "Recusado",
    not_required: "Não exigido",
  };
  const onboardingCustomerTypeLabel =
    walletOnboarding?.onboarding.customer_type === "pf"
      ? "Pessoa física"
      : walletOnboarding?.onboarding.customer_type === "pj"
      ? "Pessoa jurídica"
      : "Não definido";
  const onboardingStatusLabel =
    onboardingStatusText[walletOnboarding?.onboarding.status || ""] ||
    walletOnboarding?.onboarding.status ||
    "Não informado";
  const onboardingKycLabel =
    onboardingStatusText[walletOnboarding?.onboarding.kyc_status || ""] ||
    walletOnboarding?.onboarding.kyc_status ||
    "Não informado";
  const onboardingKybLabel =
    onboardingStatusText[walletOnboarding?.onboarding.kyb_status || ""] ||
    walletOnboarding?.onboarding.kyb_status ||
    "Não informado";
  const onboardingCanOperateLabel = walletOnboarding?.onboarding.can_start_real_operations ? "Liberada" : "Bloqueada";
  const onboardingCanSendPixLabel = walletOnboarding?.onboarding.can_send_pix ? "Ativado" : "Desativado";
  const onboardingCanReceivePixLabel = walletOnboarding?.onboarding.can_receive_pix ? "Ativado" : "Desativado";

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

      <section className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          Extrato estruturado
        </div>

        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[#f4f8ff]">
              Contrato de transações da wallet
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
              Base para comprovantes, reconciliação e Pix via parceiro. No modo demo, a lista não representa movimentação financeira real.
            </p>
          </div>

          <span className={`inline-flex w-fit rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${
            statementWallet?.real_money_enabled
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
              : "border-amber-500/20 bg-amber-500/10 text-amber-200"
          }`}>
            {statementRealMoneyLabel}
          </span>
        </div>

        {structuredStatementLoading && (
          <p className="mt-4 text-sm text-[#B8AD95]">
            Carregando extrato estruturado...
          </p>
        )}

        {structuredStatementError && (
          <p className="mt-4 text-sm text-rose-300">
            Não foi possível carregar o extrato estruturado agora.
          </p>
        )}

        {structuredStatement && (
          <>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Transações</div>
                <div className="mt-1 text-lg font-semibold text-[#f4f8ff]">{structuredStatement.statement.count}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Origem</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{statementSourceLabel}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Provedor</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{statementProviderLabel}</div>
              </div>
            </div>

            {structuredStatement.statement.items.length > 0 ? (
              <div className="mt-4 space-y-2">
                {structuredStatement.statement.items.slice(0, 3).map((item) => (
                  <div
                    key={`${item.provider_reference}-${item.amount}-${item.status}`}
                    className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3"
                    style={{ padding: "14px 16px" }}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-[#f4f8ff]">{item.description}</div>
                        <div className="mt-1 text-[11px] text-[#B8AD95]">
                          {item.direction} • {item.status} • {item.provider_reference}
                        </div>
                      </div>
                      <div className="text-sm font-bold text-[#f4f8ff]">
                        R$ {item.amount.replace(".", ",")}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-4 rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Sem transações reais</div>
                <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                  O extrato estruturado está pronto, mas o modo demo ainda não possui movimentações reais via parceiro.
                </p>
              </div>
            )}

            <div className="mt-3 rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Aviso</div>
              <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                {structuredStatement.notice}
              </p>
            </div>
          </>
        )}
      </section>

      <section className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          Comprovante e reconciliação
        </div>

        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[#f4f8ff]">
              Fundação de auditoria da wallet
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
              Base para emitir comprovantes confiáveis somente quando houver transação confirmada via parceiro financeiro.
            </p>
          </div>

          <span className={`inline-flex w-fit rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${
            receiptWallet?.real_money_enabled
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
              : "border-amber-500/20 bg-amber-500/10 text-amber-200"
          }`}>
            {receiptRealMoneyLabel}
          </span>
        </div>

        {receiptReconciliationLoading && (
          <p className="mt-4 text-sm text-[#B8AD95]">
            Carregando comprovante e reconciliação...
          </p>
        )}

        {receiptReconciliationError && (
          <p className="mt-4 text-sm text-rose-300">
            Não foi possível carregar a fundação de comprovante agora.
          </p>
        )}

        {receiptReconciliation && (
          <>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Transação</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{transactionStatusLabel}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Auditoria</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{auditStatusLabel}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Reconciliação</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{reconciliationStatusLabel}</div>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Recibo</div>
                <p className="mt-2 break-words text-sm leading-relaxed text-[#D7D0BE]">
                  {receiptReconciliation.receipt.receipt_id}
                </p>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Origem</div>
                <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                  Provedor {receiptProviderLabel} • {receiptReconciliation.wallet.source}
                </p>
              </div>
            </div>

            <div className="mt-3 rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Aviso</div>
              <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                {receiptReconciliation.notice}
              </p>
            </div>
          </>
        )}
      </section>

      <section className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          Limites e segurança operacional
        </div>

        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[#f4f8ff]">
              Controle antes do PIX real
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
              Base de permissões, limites e confirmação sensível antes de qualquer operação financeira real via parceiro.
            </p>
          </div>

          <span className={`inline-flex w-fit rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${
            operationalWallet?.real_money_enabled
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
              : "border-amber-500/20 bg-amber-500/10 text-amber-200"
          }`}>
            {operationalRealMoneyLabel}
          </span>
        </div>

        {operationalLimitsLoading && (
          <p className="mt-4 text-sm text-[#B8AD95]">
            Carregando limites operacionais...
          </p>
        )}

        {operationalLimitsError && (
          <p className="mt-4 text-sm text-rose-300">
            Não foi possível carregar os limites operacionais agora.
          </p>
        )}

        {operationalLimits && (
          <>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Enviar PIX</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{canSendPixLabel}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Receber PIX</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{canReceivePixLabel}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Confirmação</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{confirmationLabel}</div>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Por transação</div>
                <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                  R$ {operationalLimits.limits.per_transaction_limit.replace(".", ",")}
                </p>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Diário</div>
                <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                  R$ {operationalLimits.limits.daily_limit.replace(".", ",")}
                </p>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Mensal</div>
                <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                  R$ {operationalLimits.limits.monthly_limit.replace(".", ",")}
                </p>
              </div>
            </div>

            <div className="mt-3 rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Motivo</div>
              <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                {operationalLimits.reason}
              </p>
            </div>
          </>
        )}
      </section>

      <section className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          Onboarding e verificação
        </div>

        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[#f4f8ff]">
              KYC/KYB antes da carteira real
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
              Base de aprovação cadastral da wallet. A operação real só deve ser liberada quando o parceiro financeiro validar cliente, documentos e regras de compliance.
            </p>
          </div>

          <span className={`inline-flex w-fit rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${
            onboardingWallet?.real_money_enabled
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
              : "border-amber-500/20 bg-amber-500/10 text-amber-200"
          }`}>
            {onboardingRealMoneyLabel}
          </span>
        </div>

        {walletOnboardingLoading && (
          <p className="mt-4 text-sm text-[#B8AD95]">
            Carregando onboarding da carteira...
          </p>
        )}

        {walletOnboardingError && (
          <p className="mt-4 text-sm text-rose-300">
            Não foi possível carregar o onboarding agora.
          </p>
        )}

        {walletOnboarding && (
          <>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Tipo de cliente</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{onboardingCustomerTypeLabel}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Onboarding</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{onboardingStatusLabel}</div>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Operação real</div>
                <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{onboardingCanOperateLabel}</div>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-4">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">KYC</div>
                <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                  {onboardingKycLabel}
                </p>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">KYB</div>
                <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                  {onboardingKybLabel}
                </p>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Enviar PIX</div>
                <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                  {onboardingCanSendPixLabel}
                </p>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Receber PIX</div>
                <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                  {onboardingCanReceivePixLabel}
                </p>
              </div>
            </div>

            <div className="mt-3 rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Motivo</div>
              <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                {walletOnboarding.reason}
              </p>
            </div>

            <div className="mt-3 rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Próximo passo</div>
              <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                {walletOnboarding.next_steps?.[0] || "Conectar parceiro financeiro e validar KYC/KYB."}
              </p>
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
