# Aurea Gold Wallet — Backlog para Parceiros Financeiros

## Objetivo

Preparar a Aurea Gold para operar como wallet real via parceiro financeiro, PSP ou BaaS.

A Aurea controla experiência, IA, gestão, interface e relacionamento.
O parceiro regulado fornece Pix real, conta transacional, saldo, KYC, liquidação, webhooks e compliance financeiro.

## P0 — Fundamentos obrigatórios para conversar com parceiro

### Produto e arquitetura

- [x] Definir contrato interno do Partner Adapter.
- [ ] Separar claramente modo demo/lab de modo real.
- [x] Criar configuração `WALLET_MODE=demo|partner`.
- [x] Criar interface única para provedores financeiros.
- [x] Mapear dados mínimos exigidos pelo parceiro.
- [x] Documentar fluxos de Pix, saldo, extrato e webhook.

### Cadastro e KYC

- [ ] Definir cadastro PF/PJ.
- [ ] Adicionar campos mínimos para KYC.
- [ ] Validar CPF/CNPJ.
- [ ] Criar status de KYC: pending, approved, rejected, manual_review.
- [ ] Criar tela/estado de “verificação em análise”.
- [ ] Registrar consentimento LGPD.

### Pix real

- [ ] Criar contrato para receber Pix.
- [ ] Criar contrato para enviar Pix.
- [ ] Criar estrutura para QR Code Pix.
- [ ] Criar estrutura para Pix copia e cola.
- [ ] Criar status de transação: pending, processing, confirmed, failed, canceled.
- [ ] Criar idempotência obrigatória para envio Pix.
- [ ] Criar comprovante básico.

### Segurança

- [ ] Definir limites por transação.
- [ ] Definir limite diário.
- [ ] Exigir confirmação forte antes de envio Pix.
- [ ] Registrar logs de auditoria.
- [ ] Proteger endpoints sensíveis.
- [ ] Revisar expiração de sessão e refresh token.
- [ ] Criar trilha de eventos financeiros.

### Compliance e Play Store

- [ ] Criar termos de uso inicial.
- [ ] Criar política de privacidade inicial.
- [ ] Criar aviso de que operação real depende de parceiro regulado.
- [ ] Criar checklist Play Store para app financeiro.
- [ ] Criar texto de posicionamento honesto.

## P1 — Integração sandbox

- [ ] Escolher primeiro parceiro candidato.
- [ ] Criar adapter sandbox.
- [ ] Criar client HTTP do parceiro.
- [ ] Implementar criação de conta/carteira sandbox.
- [ ] Implementar consulta de saldo sandbox.
- [ ] Implementar recebimento Pix sandbox.
- [ ] Implementar envio Pix sandbox.
- [ ] Implementar webhook sandbox.
- [ ] Persistir eventos recebidos por webhook.
- [ ] Garantir idempotência de webhook.
- [ ] Gerar comprovante sandbox.
- [ ] Criar testes determinísticos via curl.

## P2 — Expansão comercial

- [ ] Link de pagamento.
- [ ] Cobrança recorrente.
- [ ] Cartão virtual via parceiro.
- [ ] Cartão físico via parceiro.
- [ ] Tap to Pay via parceiro.
- [ ] Rendimento/saldo remunerado via parceiro.
- [ ] Crédito via parceiro.
- [ ] Aurea Black/Gold Card.
- [ ] Painel administrativo de suporte.
- [ ] Contestação/MED assistida.
- [ ] Relatórios comerciais para empresas.

## Fora de escopo agora

- Banco próprio.
- Licença financeira própria.
- Cartão próprio sem parceiro.
- Crédito próprio.
- Maquininha própria.
- Promessa de rendimento sem parceiro.
- Operação Pix real sem parceiro regulado.

## Critério de pronto para parceiro

A Aurea estará pronta para abordagem técnica inicial quando tiver:

- Partner Adapter documentado;
- modo demo/partner separado;
- fluxos de Pix/saldo/extrato mapeados;
- KYC desenhado;
- termos e privacidade iniciais;
- tela premium estável;
- apresentação clara do produto;
- checklist técnico para integração.

## Critério de pronto para Play Store como wallet real

Somente considerar quando houver:

- parceiro financeiro definido;
- KYC funcional;
- Pix real validado;
- saldo real validado;
- webhooks auditados;
- comprovantes funcionando;
- limites e segurança mínimos;
- termos e privacidade publicados;
- política Play Store revisada;
- QA mobile completo.

## Progresso técnico já concluído

- [x] Estratégia oficial de wallet via parceiro documentada.
- [x] Backlog P0/P1/P2 criado.
- [x] `WALLET_MODE=demo|partner` implementado no backend e frontend.
- [x] `/healthz` expõe `wallet_mode`.
- [x] Partner Adapter criado.
- [x] Demo Partner Adapter criado.
- [x] Wallet Partner Service criado.
- [x] Endpoint `/api/v1/wallet/partner/status` criado e validado.
- [x] Smoke test `scripts/wallet_partner_smoke.sh` criado e validado.
- [x] Tag `v0.2.1-wallet-partner-foundation` criada.
- [x] Dados mínimos para parceiro documentados em `PARTNER_DATA_REQUIREMENTS.md`.
- [x] Fluxo PIX frontend exibe modo demonstração/partner e deixa claro quando não há dinheiro real.
