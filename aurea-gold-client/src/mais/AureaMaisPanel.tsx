import React, { useEffect, useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  BadgeCheck,
  FileText,
  FlaskConical,
  Gauge,
  Headphones,
  ScrollText,
  Search,
  Settings,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { fetchWalletAccountStatus, fetchWalletStructuredBalance, fetchWalletStructuredStatement, fetchWalletReceiptReconciliation, fetchWalletOperationalLimits, fetchWalletOnboardingStatus, createWalletPixSandboxPayment, fetchWalletPixSandboxReconciliation, fetchWalletPixSandboxAuditHistory, type WalletAccountStatus, type WalletStructuredBalance, type WalletStructuredStatement, type WalletReceiptReconciliation, type WalletOperationalLimits, type WalletOnboardingStatus, type WalletPixSandboxPayment, type WalletPixSandboxReconciliation, type WalletPixSandboxAuditHistory } from "../super2/api";

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

type MaisPageKey =
  | "perfil"
  | "seguro"
  | "suporte"
  | "termos"
  | "kyc"
  | "limites"
  | "sandbox"
  | "auditoria"
  | "config";

type MaisPageInfo = {
  key: MaisPageKey;
  icon: LucideIcon;
  title: string;
  subtitle: string;
  description: string;
  detail: string;
  statusLabel: string;
};

const maisPageCards: MaisPageInfo[] = [
  {
    key: "perfil",
    icon: UserRound,
    title: "Perfil",
    subtitle: "Conta",
    description: "Dados da conta, status da carteira e identificação operacional.",
    detail: "Central para visualizar situação da carteira, modo de operação, provedor, KYC/KYB e informações da conta sem expor dados sensíveis.",
    statusLabel: "Conta em controle",
  },
  {
    key: "seguro",
    icon: ShieldCheck,
    title: "Seguro",
    subtitle: "Proteção",
    description: "Camada de proteção operacional da carteira.",
    detail: "Reúne limites, bloqueios, confirmações obrigatórias e regras para impedir operação real sem parceiro financeiro homologado.",
    statusLabel: "Proteção ativa",
  },
  {
    key: "suporte",
    icon: Headphones,
    title: "Suporte",
    subtitle: "Ajuda",
    description: "Central de suporte e orientação da Aurea.",
    detail: "Área para dúvidas, operação assistida, regras do produto, onboarding e atendimento ao usuário.",
    statusLabel: "Suporte preparado",
  },
  {
    key: "termos",
    icon: FileText,
    title: "Termos",
    subtitle: "Política",
    description: "Documentos, termos e políticas operacionais.",
    detail: "Base para termos de uso, privacidade, segurança, regras de sandbox, responsabilidade e operação com parceiro.",
    statusLabel: "Documentação em evolução",
  },
  {
    key: "kyc",
    icon: BadgeCheck,
    title: "KYC",
    subtitle: "KYB",
    description: "Onboarding de pessoa física e jurídica.",
    detail: "Módulo preparado para validação cadastral, KYC/KYB real, exigências do parceiro e bloqueios antes de operação financeira real.",
    statusLabel: "Onboarding preparado",
  },
  {
    key: "limites",
    icon: Gauge,
    title: "Limites",
    subtitle: "Operação",
    description: "Limites operacionais e regras de bloqueio.",
    detail: "Controle de envio, recebimento, confirmação obrigatória, limites zerados no sandbox e liberação futura por parceiro homologado.",
    statusLabel: "Limites protegidos",
  },
  {
    key: "sandbox",
    icon: FlaskConical,
    title: "Sandbox",
    subtitle: "Pix teste",
    description: "Ambiente seguro para simular Pix e reconciliação.",
    detail: "Permite validar cobrança, evento, conciliação e auditoria sem movimentar dinheiro real.",
    statusLabel: "Sandbox ativo",
  },
  {
    key: "auditoria",
    icon: ScrollText,
    title: "Auditoria",
    subtitle: "Logs",
    description: "Histórico técnico e rastreabilidade operacional.",
    detail: "Registra eventos sandbox, reconciliação, status e evidências técnicas para segurança e controle.",
    statusLabel: "Auditoria registrada",
  },
  {
    key: "config",
    icon: Settings,
    title: "Config",
    subtitle: "Ajustes",
    description: "Configurações operacionais da carteira.",
    detail: "Área para ajustes técnicos, preferências, ambiente, modo de operação e parâmetros futuros.",
    statusLabel: "Configuração segura",
  },
];


type MoreTileProps = {
  title: string;
  subtitle: string;
  Icon: LucideIcon;
  onClick?: () => void;
};

function MoreTile({
  title,
  subtitle,
  Icon,
  onClick,
}: MoreTileProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col items-center justify-center bg-[linear-gradient(180deg,#E9CF43_0%,#CBA500_100%)] text-center shadow-[0_8px_18px_rgba(15,23,42,0.14)] transition hover:brightness-105 active:scale-[0.98]"
      style={{ height: 72, width: "85%", justifySelf: "center", borderRadius: 15, padding: "8px 6px", boxSizing: "border-box" }}
    >
      <div
        className="mb-1 flex items-center justify-center rounded-[14px] bg-white/18"
        style={{ width: 34, height: 34 }}
      >
        <Icon size={20} strokeWidth={2.4} className="text-[#0B2536]" />
      </div>

      <div
        className="text-[#0B2536]"
        style={{
          fontSize: 11.8,
          lineHeight: 1,
          fontFamily: '"Arial Black", Arial, sans-serif',
          fontWeight: 900,
        }}
      >
        {title}
      </div>

      <p
        className="mt-1 leading-tight text-[#123047]/80"
        style={{ fontSize: 10.2, fontWeight: 800, lineHeight: 1.05 }}
      >
        {subtitle}
      </p>
    </button>
  );
}

export default function AureaMaisPanel() {
  const [activePage, setActivePage] = useState<MaisPageInfo | null>(null);
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
  const [pixSandboxPayment, setPixSandboxPayment] = useState<WalletPixSandboxPayment | null>(null);
  const [pixSandboxPaymentLoading, setPixSandboxPaymentLoading] = useState(false);
  const [pixSandboxPaymentError, setPixSandboxPaymentError] = useState<string | null>(null);
  const [sandboxReconciliationReference, setSandboxReconciliationReference] = useState("aurea-ui-sandbox-payment");
  const [sandboxReconciliation, setSandboxReconciliation] = useState<WalletPixSandboxReconciliation | null>(null);
  const [sandboxReconciliationLoading, setSandboxReconciliationLoading] = useState(false);
  const [sandboxReconciliationError, setSandboxReconciliationError] = useState<string | null>(null);
  const [sandboxAuditHistory, setSandboxAuditHistory] = useState<WalletPixSandboxAuditHistory | null>(null);
  const [sandboxAuditHistoryLoading, setSandboxAuditHistoryLoading] = useState(false);
  const [sandboxAuditHistoryError, setSandboxAuditHistoryError] = useState<string | null>(null);

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
  const pixSandboxPaymentStatusLabel =
    pixSandboxPayment?.payment.status === "pending"
      ? "Pendente sandbox"
      : pixSandboxPayment?.payment.status || "Não gerada";
  const sandboxReconciliationStatusText: Record<string, string> = {
    confirmed: "Confirmado sandbox",
    pending: "Pendente sandbox",
    processing: "Processando sandbox",
    rejected: "Recusado sandbox",
    failed: "Falhou sandbox",
    canceled: "Cancelado sandbox",
    not_found: "Não encontrado",
  };
  const sandboxReconciliationStatusLabel =
    sandboxReconciliationStatusText[sandboxReconciliation?.reconciliation.status || ""] ||
    sandboxReconciliation?.reconciliation.status ||
    "Não consultado";
  const sandboxReconciliationEventLabel = sandboxReconciliation?.reconciliation.event_found
    ? "Evento localizado"
    : "Aguardando webhook";
  const sandboxReconciliationRealMoneyLabel = sandboxReconciliation?.wallet.real_money_enabled
    ? "Dinheiro real ativo"
    : "Dinheiro real desativado";
  const sandboxAuditHistoryRealMoneyLabel = sandboxAuditHistory?.wallet.real_money_enabled
    ? "Dinheiro real ativo"
    : "Dinheiro real desativado";
  const sandboxAuditHistoryTotalLabel =
    sandboxAuditHistory?.history.total_returned ?? 0;
  const sandboxAuditHistoryStatusLabel =
    sandboxAuditHistoryTotalLabel > 0 ? "Eventos registrados" : "Sem eventos";

  async function handleCreatePixSandboxPayment() {
    setPixSandboxPaymentLoading(true);
    setPixSandboxPaymentError(null);

    try {
      const data = await createWalletPixSandboxPayment({
        amount: "10.00",
        description: "Cobrança sandbox Aurea Gold",
        external_id: "aurea-ui-sandbox-payment",
      });
      setPixSandboxPayment(data);
      setSandboxReconciliationReference(data.payment.provider_reference || "aurea-ui-sandbox-payment");
    } catch (error) {
      setPixSandboxPaymentError(
        error instanceof Error
          ? error.message
          : "Falha ao gerar cobrança PIX sandbox."
      );
    } finally {
      setPixSandboxPaymentLoading(false);
    }
  }

  async function handleFetchSandboxReconciliation() {
    const reference = sandboxReconciliationReference.trim();

    if (!reference) {
      setSandboxReconciliationError("Informe uma referência sandbox para consultar.");
      return;
    }

    setSandboxReconciliationLoading(true);
    setSandboxReconciliationError(null);

    try {
      const data = await fetchWalletPixSandboxReconciliation(reference);
      setSandboxReconciliation(data);
      void handleFetchSandboxAuditHistory();
    } catch (error) {
      setSandboxReconciliationError(
        error instanceof Error
          ? error.message
          : "Falha ao consultar reconciliação sandbox."
      );
    } finally {
      setSandboxReconciliationLoading(false);
    }
  }

  async function handleFetchSandboxAuditHistory() {
    setSandboxAuditHistoryLoading(true);
    setSandboxAuditHistoryError(null);

    try {
      const data = await fetchWalletPixSandboxAuditHistory(10);
      setSandboxAuditHistory(data);
    } catch (error) {
      setSandboxAuditHistoryError(
        error instanceof Error
          ? error.message
          : "Falha ao carregar histórico sandbox."
      );
    } finally {
      setSandboxAuditHistoryLoading(false);
    }
  }

  // MAIS_EARLY_INTERNAL_PAGE_OK
  if (activePage) {
    const Icon = activePage.icon;

    return (
      <main className="w-full max-w-[390px] sm:max-w-[430px] md:max-w-[960px] mx-auto px-4 pt-8 pb-32 space-y-5">
        <header className="rounded-[30px] bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.14),transparent_28%),linear-gradient(180deg,rgba(7,59,88,0.98),rgba(6,30,47,0.98))] px-5 pt-5 pb-6 text-white shadow-[0_14px_32px_rgba(0,0,0,0.18)]">
          <button
            type="button"
            onClick={() => setActivePage(null)}
            className="inline-flex items-center rounded-full border border-emerald-300/30 bg-emerald-400/14 px-3 py-1 text-[11px] font-black text-emerald-200 shadow-[0_8px_18px_rgba(16,185,129,0.12)]"
          >
            ← Voltar para Mais
          </button>

          <p className="mt-5 text-[10px] uppercase tracking-[0.18em] text-[#D4AF37]">
            Mais Aurea
          </p>

          <div className="mt-3 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-[16px] bg-[linear-gradient(180deg,#E6C84F_0%,#C99A06_100%)] text-[#0A1F2E] shadow-[0_8px_18px_rgba(15,23,42,0.14)]">
              <Icon size={24} strokeWidth={2.4} />
            </div>

            <h1
              className="text-[#F5C842]"
              style={{
                fontSize: 26,
                lineHeight: 1,
                fontFamily: '"Arial Black", Arial, sans-serif',
                fontWeight: 900,
                letterSpacing: "-0.02em",
              }}
            >
              {activePage.title}
            </h1>
          </div>

          <p className="mt-3 text-[14px] leading-relaxed text-[#E6EDF5]">
            {activePage.description}
          </p>
        </header>

        <section className="rounded-[28px] bg-[linear-gradient(180deg,#16364B_0%,#0D2436_100%)] px-5 pt-5 pb-6 text-[#f4f8ff] shadow-[0_10px_22px_rgba(0,0,0,0.12)]">
          <p
            className="text-[#F5C842]"
            style={{
              fontSize: 18,
              lineHeight: 1,
              fontFamily: '"Arial Black", Arial, sans-serif',
              fontWeight: 900,
            }}
          >
            {activePage.subtitle}
          </p>

          <p className="mt-3 text-[13px] leading-relaxed text-[#D7D0BE]">
            {activePage.detail}
          </p>

          <div className="mt-5 rounded-[22px] border border-amber-500/16 bg-[rgba(12,30,42,0.74)] px-4 py-4">
            <p className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
              Status
            </p>
            <p className="mt-2 text-[13px] font-semibold leading-relaxed text-[#CBD5E1]">
              {activePage.statusLabel}
            </p>
          </div>

          <div className="mt-5 rounded-[22px] border border-white/12 bg-[linear-gradient(180deg,rgba(13,43,63,0.98),rgba(8,26,40,0.98))] px-4 py-4">
            <p className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
              Segurança operacional
            </p>
            <p className="mt-2 text-[12px] leading-relaxed text-[#B8AD95]">
              A carteira mantém separação entre demonstração, sandbox e operação real. Dinheiro real, Pix real, liquidação e comprovante real seguem bloqueados até parceiro homologado.
            </p>
          </div>
        </section>
      </main>
    );
  }

  return (
    <section className="w-full max-w-[390px] sm:max-w-[430px] md:max-w-[960px] mx-auto px-4 pt-8 pb-32 space-y-5">
      <header className="rounded-[30px] bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.14),transparent_28%),linear-gradient(180deg,rgba(7,59,88,0.98),rgba(6,30,47,0.98))] px-5 pt-6 pb-7 text-white shadow-[0_14px_32px_rgba(0,0,0,0.18)]">
        <div className="inline-flex items-center rounded-full border border-amber-300/20 bg-amber-400/10 px-3 py-1 text-[11px] font-semibold tracking-[0.02em] text-[#F6D66B]">
          Mais Aurea
        </div>

        <h1
          className="mt-5 text-[#F5C842]"
          style={{
            fontSize: 26,
            lineHeight: 1.05,
            fontFamily: '"Arial Black", Arial, sans-serif',
            fontWeight: 900,
            letterSpacing: "-0.02em",
          }}
        >
          Central da carteira
        </h1>

        <p className="mt-3 text-[15px] leading-relaxed text-[#E6EDF5]">
          Status, segurança, suporte, sandbox e operação técnica da Aurea Gold em um só lugar.
        </p>

        <div className="mt-4 flex items-center gap-3 rounded-[18px] border border-white/12 bg-white/8 px-4 py-3">
          <Search size={18} strokeWidth={2.4} className="text-[#F5C842]" />
          <span className="text-sm text-[#CBD5E1]">
            Busque ajuda, segurança e serviços
          </span>
        </div>
      </header>

      <section className="rounded-[28px] bg-[linear-gradient(180deg,#16364B_0%,#0D2436_100%)] px-5 pt-5 pb-6 shadow-[0_10px_22px_rgba(0,0,0,0.12)]">
        <div
          className="text-[#D6DEE8]"
          style={{
            fontSize: 13,
            fontFamily: '"Arial Black", Arial, sans-serif',
            fontWeight: 900,
          }}
        >
          Mais rápido
        </div>

        <div
          className="mt-5 grid grid-cols-3"
          style={{ gap: 8 }}
        >
          {maisPageCards.map((item) => (
            <MoreTile
              key={item.key}
              title={item.title}
              subtitle={item.subtitle}
              Icon={item.icon}
              onClick={() => setActivePage(item)}
            />
          ))}
        </div>

        <div className="mt-6 rounded-[24px] border border-white/12 bg-[linear-gradient(180deg,rgba(13,43,63,0.98),rgba(8,26,40,0.98))] px-4 pt-4 pb-5 shadow-[0_12px_24px_rgba(0,0,0,0.16)]">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-[14px] bg-white/8 text-[#F5C842]">
              <ShieldCheck size={24} strokeWidth={2.3} />
            </div>

            <div className="min-w-0 flex-1">
              <h3
                className="text-[#F8FAFC]"
                style={{
                  fontSize: 20,
                  lineHeight: 1.1,
                  fontFamily: '"Arial Black", Arial, sans-serif',
                  fontWeight: 900,
                }}
              >
                Carteira protegida
              </h3>

              <p className="mt-2 text-[14px] leading-relaxed text-[#CBD5E1]">
                Dinheiro real, Pix real, comprovante real e liquidação real seguem bloqueados até parceiro homologado.
              </p>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-white/8 px-3 py-1 text-[11px] font-semibold text-[#E6EDF5]">
                  {walletModeLabel}
                </span>
                <span className="rounded-full bg-white/8 px-3 py-1 text-[11px] font-semibold text-[#E6EDF5]">
                  {realMoneyLabel}
                </span>
                <span className="rounded-full bg-white/8 px-3 py-1 text-[11px] font-semibold text-[#E6EDF5]">
                  KYC {kycLabel}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>


      <section id="mais-wallet-status" className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
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

      <section id="mais-operational-limits" className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
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

      <section id="mais-pix-sandbox" className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          PIX sandbox
        </div>

        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[#f4f8ff]">
              Cobrança simulada de entrada
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
              Gera uma cobrança PIX apenas em sandbox técnico. Não movimenta dinheiro real, não altera saldo e não emite comprovante financeiro real.
            </p>
          </div>

          <span className="inline-flex w-fit rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-amber-200">
            Dinheiro real desativado
          </span>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Valor de teste</div>
            <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">R$ 10,00</div>
          </div>

          <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Status</div>
            <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{pixSandboxPaymentStatusLabel}</div>
          </div>

          <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Saldo real</div>
            <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">Não altera</div>
          </div>
        </div>

        <button
          type="button"
          onClick={handleCreatePixSandboxPayment}
          disabled={pixSandboxPaymentLoading}
          className="mt-4 inline-flex w-full items-center justify-center rounded-[18px] border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm font-semibold text-amber-100 transition hover:bg-amber-400/15 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          {pixSandboxPaymentLoading ? "Gerando sandbox..." : "Gerar cobrança sandbox"}
        </button>

        {pixSandboxPaymentError && (
          <p className="mt-3 text-sm leading-relaxed text-rose-300">
            {pixSandboxPaymentError}
          </p>
        )}

        {pixSandboxPayment && (
          <>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Referência sandbox</div>
                <p className="mt-2 break-words text-sm leading-relaxed text-[#D7D0BE]">
                  {pixSandboxPayment.payment.provider_reference}
                </p>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Copia e cola sandbox</div>
                <p className="mt-2 break-words text-sm leading-relaxed text-[#D7D0BE]">
                  {pixSandboxPayment.payment.copy_paste || "Não informado"}
                </p>
              </div>
            </div>

            <div className="mt-3 rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Aviso</div>
              <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                {pixSandboxPayment.notice}
              </p>
            </div>
          </>
        )}
      </section>

      <section className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          Reconciliação sandbox
        </div>

        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[#f4f8ff]">
              Consulta por referência
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
              Consulta o evento sandbox processado para uma provider_reference. Não credita saldo, não confirma pagamento real e não gera comprovante financeiro real.
            </p>
          </div>

          <span className="inline-flex w-fit rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-amber-200">
            {sandboxReconciliationRealMoneyLabel}
          </span>
        </div>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            type="text"
            value={sandboxReconciliationReference}
            onChange={(event) => setSandboxReconciliationReference(event.target.value)}
            placeholder="provider_reference sandbox"
            className="w-full rounded-[18px] border border-amber-500/14 bg-[rgba(12,30,42,0.88)] px-4 py-3 text-sm text-[#f4f8ff] outline-none placeholder:text-[#8f846f]"
          />

          <button
            type="button"
            onClick={handleFetchSandboxReconciliation}
            disabled={sandboxReconciliationLoading}
            className="inline-flex w-full items-center justify-center rounded-[18px] border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm font-semibold text-amber-100 transition hover:bg-amber-400/15 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
          >
            {sandboxReconciliationLoading ? "Consultando..." : "Consultar reconciliação"}
          </button>
        </div>

        {sandboxReconciliationError && (
          <p className="mt-3 text-sm leading-relaxed text-rose-300">
            {sandboxReconciliationError}
          </p>
        )}

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Status</div>
            <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{sandboxReconciliationStatusLabel}</div>
          </div>

          <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Evento</div>
            <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{sandboxReconciliationEventLabel}</div>
          </div>

          <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Saldo real</div>
            <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">Não altera</div>
          </div>
        </div>

        {sandboxReconciliation && (
          <>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Referência</div>
                <p className="mt-2 break-words text-sm leading-relaxed text-[#D7D0BE]">
                  {sandboxReconciliation.reconciliation.provider_reference}
                </p>
              </div>

              <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Reconciliação</div>
                <p className="mt-2 break-words text-sm leading-relaxed text-[#D7D0BE]">
                  {sandboxReconciliation.reconciliation.reconciliation_status}
                </p>
              </div>
            </div>

            <div className="mt-3 rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Aviso</div>
              <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                {sandboxReconciliation.notice}
              </p>
            </div>
          </>
        )}
      </section>

      <section id="mais-sandbox-audit" className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
          Auditoria sandbox
        </div>

        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[#f4f8ff]">
              Últimos eventos técnicos
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
              Lista os últimos eventos PIX sandbox registrados para auditoria técnica. Não representa movimentação financeira real.
            </p>
          </div>

          <span className="inline-flex w-fit rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-amber-200">
            {sandboxAuditHistoryRealMoneyLabel}
          </span>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Status</div>
            <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{sandboxAuditHistoryStatusLabel}</div>
          </div>

          <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Total exibido</div>
            <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">{sandboxAuditHistoryTotalLabel}</div>
          </div>

          <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.74)] px-4 py-3" style={{ padding: "14px 16px", minHeight: "74px" }}>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[#B8AD95]">Saldo real</div>
            <div className="mt-1 text-sm font-semibold text-[#f4f8ff]">Não altera</div>
          </div>
        </div>

        <button
          type="button"
          onClick={handleFetchSandboxAuditHistory}
          disabled={sandboxAuditHistoryLoading}
          className="mt-4 inline-flex w-full items-center justify-center rounded-[18px] border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm font-semibold text-amber-100 transition hover:bg-amber-400/15 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          {sandboxAuditHistoryLoading ? "Carregando..." : "Atualizar histórico sandbox"}
        </button>

        {sandboxAuditHistoryError && (
          <p className="mt-3 text-sm leading-relaxed text-rose-300">
            {sandboxAuditHistoryError}
          </p>
        )}

        {sandboxAuditHistory && (
          <>
            <div className="mt-4 space-y-3">
              {sandboxAuditHistory.items.length === 0 ? (
                <div className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3 text-sm text-[#D7D0BE]" style={{ padding: "14px 16px" }}>
                  Nenhum evento sandbox registrado ainda.
                </div>
              ) : (
                sandboxAuditHistory.items.slice(0, 5).map((item) => (
                  <article
                    key={`${item.provider_reference}-${item.received_at || item.idempotency?.key || item.status}`}
                    className="rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3"
                    style={{ padding: "14px 16px" }}
                  >
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">
                          {item.status || "unknown"}
                        </div>
                        <p className="mt-1 break-words text-sm font-semibold text-[#f4f8ff]">
                          {item.provider_reference}
                        </p>
                      </div>

                      <span className="inline-flex w-fit rounded-full border border-amber-500/16 bg-amber-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-amber-100">
                        {item.reconciliation_status}
                      </span>
                    </div>

                    <p className="mt-2 text-xs leading-relaxed text-[#B8AD95]">
                      Valor: {item.amount || "não informado"} • Evento: {item.event_type || "não informado"} • Recebido: {item.received_at || "não informado"}
                    </p>
                  </article>
                ))
              )}
            </div>

            <div className="mt-3 rounded-[18px] border border-amber-500/10 bg-[rgba(12,30,42,0.56)] px-4 py-3" style={{ padding: "14px 16px" }}>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[#D4AF37]">Aviso</div>
              <p className="mt-2 text-sm leading-relaxed text-[#D7D0BE]">
                {sandboxAuditHistory.notice}
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

      <section id="mais-support" className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-amber-500/12 bg-[linear-gradient(180deg,rgba(16,42,55,0.96),rgba(7,15,30,0.98))]">
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

      <section id="mais-utilities" className="space-y-3">
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
