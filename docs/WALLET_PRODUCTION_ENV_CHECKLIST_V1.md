# Aurea Gold / dils-wallet — Production Environment Checklist v1

Status: draft operacional
Produto: Aurea Gold / dils-wallet
Natureza: produto real/comercial, não projeto de estudo
Objetivo: impedir deploy/produção acidental com configuração insegura, sandbox indevido ou dinheiro real sem parceiro homologado.

---

## 1. Regra-mãe

A Aurea Gold NÃO deve operar dinheiro real em produção até existir:

- PSP/BaaS homologado;
- contrato/parceria formal;
- KYC/KYB real;
- compliance mínimo aprovado;
- webhook assinado/tokenizado;
- ledger real separado;
- reconciliação oficial;
- plano de incidentes;
- operação/admin mínima;
- revisão jurídica dos termos e política de privacidade.

Produção sem esses itens deve rodar apenas como ambiente controlado, sem Pix real, sem saldo real, sem comprovante real e sem liquidação real.

---

## 2. Separação obrigatória de ambientes

| Ambiente | Finalidade | Pode ter dinheiro real? | Provider permitido |
|---|---|---:|---|
| demo | demonstração local/visual | Não | demo |
| sandbox | teste técnico com adapter sandbox/parceiro | Não | sandbox |
| staging | ensaio de produção sem dinheiro real | Não | sandbox ou provider homologado em sandbox oficial |
| production | ambiente real | Só após homologação | PSP/BaaS real homologado |

Regra: demo, sandbox e production não podem compartilhar banco, segredos, flags ou provider real.

---

## 3. Variáveis críticas da wallet

| Variável | Demo | Sandbox | Production |
|---|---|---|---|
| WALLET_MODE | demo | partner | partner |
| WALLET_PARTNER_PROVIDER | vazio/demo | sandbox | provider real homologado |
| REAL_MONEY_ENABLED | false | false | true somente após aprovação |
| WALLET_ALLOW_REAL_PIX | false | false | true somente após aprovação |
| WALLET_ALLOW_REAL_RECEIPT | false | false | true somente após confirmação oficial |

Regras obrigatórias:

- Produção NÃO pode usar WALLET_PARTNER_PROVIDER=sandbox.
- Produção NÃO pode usar segredos locais.
- Produção NÃO pode liberar Pix real por padrão.
- Produção NÃO pode gerar comprovante real sem confirmação oficial do PSP/BaaS.
- Se houver dúvida, bloquear dinheiro real.

---

## 4. Segredos obrigatórios

Antes de qualquer deploy público:

- [ ] SECRET_KEY forte.
- [ ] JWT_SECRET forte.
- [ ] segredos diferentes entre demo/sandbox/staging/production.
- [ ] nenhum segredo commitado.
- [ ] nenhum segredo exposto em log.
- [ ] rotação planejada.
- [ ] variáveis configuradas no Railway/infra, não no código.

Valores proibidos em produção:

- ci-local-smoke-secret-1234567890
- dev
- local
- changeme
- secret
- password
- qualquer valor usado em teste local.

---

## 5. CORS e domínio

Produção precisa ter CORS restrito:

- [ ] não usar asterisco.
- [ ] não liberar localhost.
- [ ] não liberar 127.0.0.1.
- [ ] incluir apenas domínio oficial da Aurea.
- [ ] separar domínio de staging e produção.
- [ ] validar HTTPS obrigatório.

Exemplo conceitual:

CORS_ORIGINS=https://app.aureagold.com.br

---

## 6. Banco de dados

Antes de produção:

- [ ] banco separado de desenvolvimento.
- [ ] banco separado de sandbox.
- [ ] banco separado de produção.
- [ ] backups configurados.
- [ ] restore testado.
- [ ] migrações revisadas.
- [ ] acesso restrito.
- [ ] logs sem dados sensíveis.
- [ ] nenhum dado real em banco local.
- [ ] seed/demo desabilitado em produção.

---

## 7. Travas contra produção acidental

A aplicação deve bloquear ou alertar quando:

- [ ] APP_ENV=production e WALLET_PARTNER_PROVIDER=sandbox.
- [ ] APP_ENV=production e CORS contiver localhost.
- [ ] APP_ENV=production e CORS contiver 127.0.0.1.
- [ ] APP_ENV=production e segredo fraco for detectado.
- [ ] APP_ENV=production e webhook real não tiver assinatura/token.
- [ ] APP_ENV=production e ledger real não estiver ativo.
- [ ] APP_ENV=production e reconciliação real não estiver ativa.
- [ ] APP_ENV=production e KYC/KYB real não estiver ativo.

Regra de ouro: produção pode até subir como ambiente público controlado, mas dinheiro real deve continuar bloqueado até aprovação formal.

---

## 8. Pix real

Pix real só pode ser habilitado quando todos os itens abaixo estiverem OK:

- [ ] PSP/BaaS contratado/homologado.
- [ ] ambiente sandbox oficial do parceiro validado.
- [ ] ambiente produção do parceiro liberado formalmente.
- [ ] adapter real implementado.
- [ ] webhook assinado/tokenizado.
- [ ] idempotência validada.
- [ ] ledger real separado.
- [ ] reconciliação oficial.
- [ ] KYC/KYB real.
- [ ] limites operacionais.
- [ ] auditoria.
- [ ] painel operacional.
- [ ] plano de incidentes.
- [ ] suporte definido.

---

## 9. Webhook real

Antes de aceitar webhook real:

- [ ] validar assinatura.
- [ ] validar token.
- [ ] validar origem quando aplicável.
- [ ] validar timestamp/nonce se o parceiro oferecer.
- [ ] validar provider_reference.
- [ ] validar valor.
- [ ] validar status.
- [ ] validar idempotência.
- [ ] persistir payload bruto sanitizado.
- [ ] rejeitar payload adulterado.
- [ ] não creditar saldo sem reconciliação mínima.

---

## 10. Ledger real

O ledger real precisa ser separado do sandbox:

- [ ] não reutilizar tabela/fluxo sandbox como ledger real.
- [ ] lançamentos append-only.
- [ ] saldo derivado de eventos auditáveis.
- [ ] saldo disponível/bloqueado/pendente.
- [ ] vínculo com provider_reference.
- [ ] vínculo com usuário/conta.
- [ ] timestamp confiável.
- [ ] trilha de auditoria.
- [ ] rotina de reconciliação.
- [ ] divergências precisam ir para revisão manual.

---

## 11. Comprovante real

Comprovante real só pode existir quando:

- [ ] pagamento confirmado oficialmente pelo PSP/BaaS.
- [ ] provider_reference válido.
- [ ] valor conciliado.
- [ ] horário registrado.
- [ ] status final confirmado.
- [ ] ledger atualizado corretamente.
- [ ] usuário/conta vinculados.
- [ ] documento indique origem oficial.

Sandbox nunca gera comprovante financeiro real.

---

## 12. KYC/KYB

Produção real exige:

### Pessoa física

- [ ] identificação mínima.
- [ ] CPF.
- [ ] consentimento LGPD.
- [ ] status de verificação.
- [ ] bloqueio de uso real antes da aprovação.

### Pessoa jurídica

- [ ] CNPJ.
- [ ] razão social.
- [ ] responsável autorizado.
- [ ] status KYB.
- [ ] bloqueio de uso real antes da aprovação.

---

## 13. Railway/deploy

Antes de publicar:

- [ ] conferir serviço correto no Railway.
- [ ] conferir ambiente correto.
- [ ] conferir variáveis.
- [ ] conferir domínio.
- [ ] conferir logs.
- [ ] conferir healthcheck.
- [ ] conferir banco conectado.
- [ ] conferir CORS.
- [ ] conferir flags de dinheiro real.
- [ ] registrar versão/tag deployada.

Checklist local recomendado antes de deploy:

- git status -sb
- git log --oneline -5
- git tag --list v0.2.*

---

## 14. Healthcheck mínimo

Produção/staging deve ter endpoints ou validações equivalentes:

- [ ] backend responde.
- [ ] banco responde.
- [ ] provider adapter responde.
- [ ] wallet status responde.
- [ ] modo atual explícito.
- [ ] provider atual explícito.
- [ ] dinheiro real ativo/inativo explícito.

---

## 15. Observabilidade

Antes de cliente real:

- [ ] logs estruturados.
- [ ] erros de webhook monitorados.
- [ ] divergência de reconciliação monitorada.
- [ ] falha de login monitorada.
- [ ] tentativas suspeitas monitoradas.
- [ ] alertas mínimos.
- [ ] retenção de logs definida.
- [ ] logs sem senha/token/documentos sensíveis.

---

## 16. Operação e incidentes

Antes de dinheiro real:

- [ ] plano de incidente.
- [ ] responsável operacional.
- [ ] canal de suporte.
- [ ] procedimento de bloqueio.
- [ ] procedimento de desbloqueio.
- [ ] procedimento de divergência.
- [ ] procedimento de estorno/devolução, se aplicável pelo parceiro.
- [ ] comunicação ao cliente.
- [ ] comunicação ao parceiro.

---

## 17. Critério de aprovação para produção real

A produção real só pode ser considerada liberada quando:

- [ ] checklist de ambiente aprovado.
- [ ] checklist parceiro aprovado.
- [ ] checklist KYC/KYB aprovado.
- [ ] checklist webhook aprovado.
- [ ] checklist ledger aprovado.
- [ ] checklist reconciliação aprovado.
- [ ] checklist suporte/incidente aprovado.
- [ ] teste fim a fim em sandbox oficial do PSP/BaaS aprovado.
- [ ] revisão jurídica/compliance feita.
- [ ] decisão explícita registrada em PR/tag/handoff.

---

## 18. Status atual

Estado atual recomendado:

- Dinheiro real: bloqueado
- Pix real: bloqueado
- Comprovante real: bloqueado
- Saldo real: bloqueado
- Sandbox técnico: validado
- Runbook sandbox: criado
- Matriz PSP/BaaS: criada
- Checklist produção: em criação

---

## 19. Próximos passos após este documento

1. Validar visualmente sandbox na aba Mais.
2. Criar travas automáticas de ambiente.
3. Criar foundation de ledger real.
4. Criar foundation de webhook signature guard.
5. Criar questionário técnico para PSP/BaaS.
6. Definir shortlist de parceiros.
7. Conversar com parceiro somente com matriz e checklist prontos.

---

## 20. Conclusão

Este checklist existe para proteger a Aurea Gold de produção acidental, configuração insegura e liberação precoce de dinheiro real.

A wallet deve continuar explícita: demo é demo, sandbox é sandbox, produção real só com parceiro homologado e processo blindado.

Dinheiro real só entra quando o ambiente, o parceiro, o ledger, o webhook, a reconciliação e a operação estiverem prontos.
