# Aurea Gold — Notas de Acesso ao Asaas Sandbox v1

Status: draft
Marco planejado: v0.2.32-wallet-asaas-sandbox-access-notes
Projeto: Aurea Gold / dils-wallet
Parceiro candidato: Asaas
Prioridade atual: A
Natureza: produto real/comercial, não projeto de estudo.

## 1. Objetivo

Este documento registra as notas de acesso ao ambiente Asaas Sandbox antes de qualquer spike técnico com código.

O objetivo é documentar o que foi possível localizar, acessar e confirmar no painel do Asaas, mantendo segurança total sobre credenciais e evitando qualquer operação financeira real.

Este marco ainda não implementa integração.

## 2. Regra central

Este documento não pode conter:

- token real;
- API key real;
- senha;
- segredo;
- print com token;
- print com chave completa;
- dado pessoal sensível;
- dado bancário real;
- URL com credencial;
- payload real com informação sensível.

Este documento pode conter apenas:

- status de acesso;
- caminho de menu;
- nomes de telas;
- nomes de seções;
- links públicos de documentação;
- observações técnicas sem segredo;
- pendências;
- bloqueios;
- próximos passos.

## 3. Base documental anterior

Este documento complementa:

- `docs/WALLET_PARTNER_CONTACT_LOG_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_VALIDATION_PLAN_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_READINESS_CHECKLIST_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_TECHNICAL_SPIKE_PLAN_V1.md`
- `docs/WALLET_SANDBOX_CYCLE_RUNBOOK.md`

## 4. Confirmação recebida do Asaas

O Asaas informou que o acesso ao ambiente Sandbox pode ser feito pelo painel, no caminho:

`Minha Conta > Integrações > Acessar ambiente Sandbox`

Também foi informado que o ambiente deve ser usado com dados fictícios e sem movimentação real de dinheiro.

## 5. Estado atual do acesso

Status atual: pendente de confirmação manual.

Itens a confirmar:

- [ ] Conta Asaas acessível.
- [ ] Menu `Minha Conta` localizado.
- [ ] Área `Integrações` localizada.
- [ ] Opção `Acessar ambiente Sandbox` localizada.
- [ ] Ambiente Sandbox aberto com sucesso.
- [ ] Conta de teste criada ou disponível.
- [ ] Documentação técnica localizada.
- [ ] Credencial Sandbox gerada com segurança.
- [ ] Credencial Sandbox armazenada fora do Git.
- [ ] URL base Sandbox identificada.
- [ ] Endpoint de cobrança localizado.
- [ ] Endpoint de consulta de cobrança localizado.
- [ ] Área de webhooks localizada.
- [ ] Orientação sobre `asaas-access-token` localizada.
- [ ] Área de extrato ou histórico localizada.
- [ ] Informações sobre subcontas localizadas, se disponíveis.
- [ ] Informações sobre split localizadas, se disponíveis.

## 6. Credenciais

Nenhuma credencial deve ser registrada neste documento.

Variáveis previstas para ambiente local seguro:

- `ASAAS_ENV=sandbox`
- `ASAAS_BASE_URL`
- `ASAAS_API_KEY`
- `ASAAS_WEBHOOK_TOKEN`
- `ASAAS_WEBHOOK_ALLOWED_IPS`
- `WALLET_PARTNER_PROVIDER=asaas`
- `WALLET_MODE=partner`
- `REAL_MONEY_ENABLED=false`

A credencial Sandbox deve ficar somente em ambiente local seguro, fora do Git.

## 7. Evidências permitidas

Podem ser registradas:

- nome da tela;
- caminho de navegação;
- data da verificação;
- status geral;
- mensagem genérica de erro;
- link público da documentação;
- observação técnica sem segredo.

Não podem ser registradas:

- token;
- chave de API;
- segredo;
- QR Code real;
- payload com dados sensíveis;
- print com credencial;
- dados de cliente real;
- dados bancários reais.

## 8. Observações de acesso

Data da primeira verificação: pendente.

Resultado inicial:

- Acesso ao painel Asaas: pendente.
- Acesso ao ambiente Sandbox: pendente.
- Geração de credencial Sandbox: pendente.
- Documentação técnica localizada: pendente.
- Webhook Sandbox localizado: pendente.
- Consulta de cobranças localizada: pendente.
- Extrato/histórico Sandbox localizado: pendente.
- Subcontas Sandbox localizadas: pendente.
- Split Sandbox localizado: pendente.

## 9. Bloqueios atuais

Bloqueios antes do spike técnico:

- Não iniciar código sem confirmar acesso ao Sandbox.
- Não iniciar código sem confirmar onde ficam as credenciais.
- Não iniciar código sem confirmar URL base Sandbox.
- Não iniciar código sem confirmar endpoints mínimos.
- Não iniciar código sem confirmar validação de webhook.
- Não iniciar código se houver risco de usar produção.
- Não iniciar código se a credencial puder vazar em log.
- Não iniciar código se houver dúvida entre ambiente Sandbox e produção.

## 10. Critério para liberar o próximo marco

O próximo marco técnico só deve avançar se:

- o Sandbox estiver acessível;
- a credencial Sandbox estiver segura;
- a URL base Sandbox estiver identificada;
- os endpoints mínimos estiverem localizados;
- o webhook estiver entendido;
- o token de webhook puder ser validado;
- produção continuar explicitamente bloqueada;
- nenhum segredo estiver no repositório.

## 11. Próximo marco provável

Se o acesso ao Sandbox for confirmado com segurança, o próximo marco poderá ser:

- `v0.2.33-wallet-asaas-sandbox-technical-spike`

Se o acesso ainda estiver incompleto, o próximo marco deve continuar documental ou operacional, sem código produtivo.
