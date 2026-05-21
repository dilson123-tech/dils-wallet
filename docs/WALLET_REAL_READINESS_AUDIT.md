# Aurea Gold Wallet — Auditoria de Prontidão para Carteira Real

## 1. Natureza oficial do produto

A Aurea Gold é um produto real e comercial, com foco em Play Store, mercado real e uso por clientes.

A Aurea Gold não será tratada como banco próprio no início.

A estratégia oficial é operar como wallet real por meio de parceiro financeiro, PSP ou BaaS regulado.

## 2. Papel da Aurea Gold

A Aurea controla:

- experiência premium do cliente;
- interface petróleo + ouro;
- IA financeira;
- gestão de caixa;
- relatórios;
- UX;
- planos;
- relacionamento com o cliente;
- leitura inteligente dos dados financeiros.

## 3. Papel do parceiro financeiro

O parceiro regulado deve fornecer:

- Pix real;
- saldo transacional;
- KYC/KYB;
- conta transacional;
- liquidação;
- webhooks;
- compliance financeiro;
- regras regulatórias;
- infraestrutura financeira de produção.

## 4. O que não prometer antes do parceiro

Enquanto não houver parceiro financeiro fechado, a Aurea não deve prometer:

- banco próprio;
- conta bancária própria;
- Pix real em produção;
- cartão físico real;
- cartão virtual real;
- rendimento real;
- crédito;
- empréstimo;
- maquininha própria;
- garantia de aprovação financeira.

## 5. Estado técnico atual

### Já existe

- frontend premium da Aurea Gold;
- Home da carteira;
- login;
- botão de sair integrado na Home;
- módulos PIX, Gestão, Pagamentos e Mais;
- backend com rotas de auth, users, wallet, pix, whoami e IA;
- documentação de estratégia via parceiro;
- camada inicial de Partner Adapter;
- tipos de parceiro;
- adapter demo;
- registry de parceiro;
- serviço `wallet_partner_service`;
- endpoint de status do parceiro;
- build do cliente validado;
- PIX guard validado;
- CI verde após PR #99;
- JWT padronizado para PyJWT.

### Existe, mas ainda é demo/base/lab

- saldo local/demo;
- histórico local/demo;
- PIX visual/base;
- IA com leitura inicial;
- gestão e pagamentos em modo visual/operacional;
- adapter demo de parceiro;
- status técnico do parceiro.

### Falta para cliente real

- onboarding completo;
- KYC PF;
- KYB PJ;
- status real da conta;
- saldo real via parceiro;
- saldo disponível;
- saldo bloqueado;
- saldo pendente;
- Pix real de entrada;
- Pix real de saída;
- QR Code Pix;
- Pix copia e cola;
- comprovante real;
- extrato real;
- filtros de extrato;
- detalhe de transação;
- webhooks do parceiro;
- idempotência;
- reconciliação;
- limites transacionais;
- confirmação antes de envio de dinheiro;
- suporte operacional;
- contestação/MED;
- termos de uso;
- política de privacidade;
- logs/auditoria;
- painel admin/operacional.

## 6. Régua preliminar de prontidão

| Área | Percentual |
|---|---:|
| Produto visual/UX | 65% |
| Wallet demo/local | 45% |
| Base de parceiro financeiro | 30% |
| PIX real via parceiro | 10% |
| KYC/KYB | 5% |
| Segurança/sessão | 40% |
| Extrato/comprovante | 30% |
| Suporte/cliente | 20% |
| Painel PJ/comercial | 35% |
| Pronta para cliente real | 22% |

## 7. Ordem recomendada de implementação

### P0 — Fundação real da wallet

1. Separar explicitamente modo demo, modo sandbox e modo produção.
2. Criar status estruturado da conta do cliente.
3. Criar contrato interno para saldo real: disponível, bloqueado e pendente.
4. Criar contrato interno para transações e extrato.
5. Criar contrato interno para Pix entrada/saída.
6. Criar camada de idempotência.
7. Criar base de auditoria/logs.

### P1 — Parceiro sandbox

1. Implementar adapter sandbox.
2. Implementar KYC/KYB sandbox.
3. Implementar receber Pix sandbox.
4. Implementar enviar Pix sandbox.
5. Implementar QR Code/copia e cola sandbox.
6. Implementar webhook sandbox.
7. Implementar comprovante sandbox.
8. Implementar reconciliação inicial.

### P2 — Produto vendável para cliente real

1. Tela de status da conta.
2. Tela de KYC/KYB.
3. Extrato profissional com filtros.
4. Comprovante visual/PDF.
5. Central de suporte.
6. Termos e política de privacidade.
7. Painel admin/operacional.
8. Checklist Play Store para app financeiro.

## 8. Decisão de qualidade

A Aurea Gold só deve ser considerada pronta para cliente real quando:

- não depender de dados fake para fluxos financeiros;
- deixar claro quando estiver em demo/sandbox;
- tiver integração real com parceiro;
- tiver logs e rastreabilidade;
- tiver suporte e contestação;
- tiver termos e privacidade;
- tiver confirmação antes de movimentar dinheiro;
- tiver extrato e comprovante confiáveis.

## 9. Próximo ataque técnico

O próximo passo recomendado é implementar o módulo:

**Wallet Account Status**

Esse módulo deve mostrar:

- modo da carteira: demo, sandbox ou produção;
- provedor configurado;
- status da conta;
- KYC/KYB pendente, aprovado, recusado ou em análise;
- se dinheiro real está habilitado;
- limitações do modo atual;
- próximos passos para ativação real.

