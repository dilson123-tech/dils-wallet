# Aurea Gold / dils-wallet — Partner Readiness Matrix v1

Status: draft operacional  
Produto: Aurea Gold / dils-wallet  
Natureza: produto real/comercial, não projeto de estudo  
Objetivo: preparar a wallet para conversar com PSP/BaaS/parceiro financeiro sem lacunas críticas.

---

## 1. Regra-mãe do projeto

A Aurea Gold ainda NÃO deve operar dinheiro real.

Não liberar Pix real, saldo real, liquidação real, comprovante real ou atualização real de saldo sem:

- PSP/BaaS homologado;
- contrato/parceria formal;
- fluxo KYC/KYB real;
- compliance mínimo aprovado;
- webhook assinado/tokenizado;
- ledger real separado do sandbox;
- reconciliação oficial com o parceiro;
- plano de incidentes;
- termos e política de privacidade revisados;
- trilha de auditoria operacional.

---

## 2. Estado atual validado

### Já existe

- Wallet demo/local.
- Status da carteira.
- Saldo estruturado.
- Extrato estruturado.
- Foundation de recibo/reconciliação.
- Limites operacionais.
- Foundation KYC/KYB.
- Adapter sandbox parceiro.
- Cobrança PIX sandbox.
- Webhook sandbox com idempotência.
- Reconciliação sandbox.
- Histórico/auditoria sandbox.
- Runbook operacional sandbox.
- Correção do label semântico do SandboxPartnerAdapter.

### Validação determinística já feita

- Cobrança sandbox criada com amount.
- Webhook sandbox confirmed.
- Replay com mesma Idempotency-Key e mesmo payload retornou duplicated/replayed.
- Mesma Idempotency-Key com payload diferente retornou HTTP 409.
- Reconciliação por provider_reference retornou sandbox_reconciled.
- Histórico/auditoria retornou eventos.
- Todas as respostas mantiveram:
  - real_money_enabled=false;
  - can_credit_balance=false;
  - can_generate_real_receipt=false;
  - can_mark_real_paid=false.

---

## 3. Matriz de exigências antes do parceiro

| Área | Exigência | Estado atual | Falta para parceiro |
|---|---|---:|---|
| Produto | Deixar claro que sandbox não é dinheiro real | OK | Manter avisos visíveis |
| Configuração | Separar demo, sandbox e produção | Parcial | Criar matriz/env de produção |
| Adapter | Adapter sandbox funcional | OK | Criar interface para adapter real |
| Pix entrada | Simulação de cobrança sandbox | OK | Integrar cobrança real do PSP/BaaS |
| Pix saída | Envio real bloqueado | OK | Definir política de envio real |
| Webhook | Idempotência validada | OK | Assinatura/token obrigatório |
| Idempotência | Replay igual aceita, replay diferente bloqueia | OK | Persistência e monitoramento em produção |
| Ledger | Sandbox não altera saldo real | OK | Criar ledger real separado |
| Reconciliação | Reconciliação sandbox por provider_reference | OK | Reconciliação oficial com PSP/BaaS |
| Comprovante | Comprovante real bloqueado | OK | Emitir só após confirmação oficial |
| KYC/KYB | Foundation existe | Parcial | Fluxo real com status, documentos e revisão |
| Compliance | Diretrizes iniciais | Parcial | Checklist formal com jurídico/contador/parceiro |
| LGPD | Cuidados básicos | Parcial | Política de dados, consentimento e retenção |
| Segurança | JWT/segredos básicos | Parcial | Hardening, rotação, logs, rate limit |
| Observabilidade | Logs locais | Parcial | Logs estruturados, alertas e dashboards |
| Operação | Runbook sandbox | OK | Runbook produção/incidentes |
| Painel admin | Ainda baixo | Baixo | Painel operacional/admin |
| Suporte | Ainda baixo | Baixo | Fluxo de atendimento e incidentes |
| Termos | Existem/precisam revisão conforme produto final | Parcial | Revisão jurídica antes de cliente real |

---

## 4. Checklist técnico obrigatório

### 4.1 Ambientes

- [ ] `.env.example` separado para demo/sandbox/production.
- [ ] `WALLET_MODE=demo` para ambiente sem parceiro.
- [ ] `WALLET_MODE=partner` + `WALLET_PARTNER_PROVIDER=sandbox` apenas para sandbox.
- [ ] Produção real não pode usar provider sandbox.
- [ ] Segredos nunca commitados.
- [ ] Checklist Railway/produção documentado.

### 4.2 Adapter real

- [ ] Definir contrato interno do adapter real.
- [ ] Criar camada `PartnerAdapter` compatível com PSP/BaaS.
- [ ] Não misturar adapter sandbox com adapter real.
- [ ] Feature flag para bloquear dinheiro real por padrão.
- [ ] Testes determinísticos para adapter real sandbox oficial.

### 4.3 Webhook real

- [ ] Validar assinatura/token do parceiro.
- [ ] Validar timestamp/nonce quando o parceiro oferecer.
- [ ] Idempotência por evento/referência.
- [ ] Mesma chave + payload diferente = conflito.
- [ ] Replay igual = resposta segura.
- [ ] Persistir payload bruto sanitizado.
- [ ] Não confiar só em status textual do webhook.

### 4.4 Ledger real

- [ ] Criar tabela/estrutura de ledger real separada.
- [ ] Ledger deve ser imutável por append-only.
- [ ] Nunca recalcular saldo apenas pelo frontend.
- [ ] Toda alteração de saldo precisa de origem auditável.
- [ ] Separar saldo disponível, bloqueado e pendente.
- [ ] Conciliar saldo interno com parceiro.

### 4.5 Reconciliação

- [ ] Conciliar provider_reference.
- [ ] Conciliar valor.
- [ ] Conciliar status.
- [ ] Conciliar horário.
- [ ] Conciliar usuário/conta.
- [ ] Marcar divergências.
- [ ] Criar fila de revisão manual.

### 4.6 Comprovante

- [ ] Comprovante real somente após confirmação oficial.
- [ ] Incluir provider_reference.
- [ ] Incluir data/hora.
- [ ] Incluir valor.
- [ ] Incluir status final.
- [ ] Incluir identificador interno.
- [ ] Não emitir comprovante real em sandbox.

---

## 5. Checklist compliance/KYC/KYB

### Cliente pessoa física

- [ ] Nome completo.
- [ ] CPF.
- [ ] Data de nascimento quando necessário.
- [ ] Telefone/e-mail.
- [ ] Consentimento LGPD.
- [ ] Status de verificação.
- [ ] Bloqueio de uso real até aprovação.

### Cliente pessoa jurídica

- [ ] CNPJ.
- [ ] Razão social.
- [ ] Sócios/representantes quando aplicável.
- [ ] Responsável autorizado.
- [ ] Documento/contrato social quando exigido.
- [ ] Status KYB.
- [ ] Bloqueio de uso real até aprovação.

### Risco/limites

- [ ] Limite por transação.
- [ ] Limite diário.
- [ ] Limite mensal.
- [ ] Limite por perfil.
- [ ] Revisão manual para aumento de limite.
- [ ] Bloqueio por comportamento suspeito.

---

## 6. Checklist segurança

- [ ] JWT seguro.
- [ ] Rotação de segredos.
- [ ] Rate limit em login e endpoints sensíveis.
- [ ] Logs sem dados sensíveis.
- [ ] Auditoria de ações sensíveis.
- [ ] Proteção contra replay.
- [ ] Proteção contra payload adulterado.
- [ ] CORS restrito em produção.
- [ ] HTTPS obrigatório.
- [ ] Backup e restore documentados.
- [ ] Plano de incidentes.

---

## 7. Checklist operacional

- [ ] Runbook de produção.
- [ ] Runbook de incidentes.
- [ ] Fluxo de suporte.
- [ ] Painel de operações.
- [ ] Lista de eventos críticos.
- [ ] Alertas para webhook falhando.
- [ ] Alertas para divergência de reconciliação.
- [ ] Procedimento de bloqueio/desbloqueio de conta.
- [ ] Procedimento de estorno/devolução se aplicável pelo parceiro.
- [ ] Responsável operacional definido.

---

## 8. Perguntas para fazer ao PSP/BaaS

### Integração

- Qual ambiente sandbox oficial?
- Existe API de cobrança Pix?
- Existe API de Pix saída?
- Existe API de saldo?
- Existe API de extrato?
- Existe API de comprovante?
- Existe API de reconciliação?
- Existe webhook de pagamento confirmado?
- Como funciona idempotência?
- Como funciona assinatura de webhook?

### Compliance

- Quem faz KYC/KYB?
- Quem é responsável regulatório?
- A Aurea atua como subconta, white label, correspondente, marketplace ou camada tecnológica?
- Quais dados podemos armazenar?
- Quais dados não podemos armazenar?
- Quais termos precisam aparecer ao cliente?
- Existe exigência de aprovação prévia da interface?

### Operação

- SLA de webhook.
- SLA de liquidação.
- SLA de suporte.
- Procedimento de incidentes.
- Procedimento de contestação/devolução.
- Limites iniciais.
- Custos por transação.
- Custos mensais.
- Regras para bloqueio de conta.

---

## 9. Próximos PRs recomendados

1. `docs(wallet): add partner readiness matrix`
2. `docs(wallet): add production env checklist`
3. `feat(wallet): add real ledger foundation`
4. `feat(wallet): add webhook signature guard foundation`
5. `feat(wallet): add kyc kyb status model`
6. `feat(wallet): add admin operational dashboard foundation`
7. `docs(wallet): add PSP/BaaS due diligence questionnaire`

---

## 10. Critério para falar com parceiro

Só considerar pronto para abordagem técnica séria quando:

- Documentação de prontidão estiver no repo.
- Checklist de ambiente estiver claro.
- Sandbox visual validado no painel.
- Ledger real foundation estiver desenhado.
- Webhook signature guard estiver planejado.
- KYC/KYB real estiver especificado.
- Perguntas ao parceiro estiverem prontas.
- O projeto conseguir explicar claramente o que é sandbox, o que é real e o que depende do PSP/BaaS.

---

## 11. Fontes regulatórias para consulta

Basear decisões finais em fontes oficiais e revisão jurídica/contábil:

- Banco Central do Brasil — Regulamento e normas do Pix.
- Banco Central do Brasil — Manual de Segurança do Pix.
- Banco Central do Brasil — Participantes do Pix.
- Banco Central do Brasil — Arranjos de Pagamento.
- LGPD — Lei Geral de Proteção de Dados.
- Contrato e documentação técnica do PSP/BaaS escolhido.

---

## 12. Conclusão

A Aurea Gold está tecnicamente mais madura no sandbox, mas ainda não deve operar dinheiro real.

O objetivo desta matriz é impedir que o projeto avance de forma frágil para um parceiro financeiro. Antes de qualquer integração real, a wallet precisa provar segurança, rastreabilidade, segregação entre sandbox e produção, KYC/KYB, compliance, ledger real, reconciliação oficial e operação mínima.

Dinheiro real só entra quando o sistema, o parceiro e o processo estiverem blindados.
