# Aurea Gold / dils-wallet — PSP/BaaS Questionnaire v1

Status: draft operacional
Produto: Aurea Gold / dils-wallet
Natureza: produto real/comercial, não projeto de estudo
Objetivo: preparar perguntas técnicas, comerciais, operacionais e regulatórias antes de conversar com PSP/BaaS/parceiro financeiro.

---

## 1. Regra-mãe

A Aurea Gold não deve operar dinheiro real sem parceiro financeiro homologado.

Antes de qualquer Pix real, saldo real, comprovante real ou liquidação real, precisamos entender claramente:

- modelo de parceria;
- responsabilidade regulatória;
- APIs disponíveis;
- ambiente sandbox oficial;
- homologação;
- KYC/KYB;
- webhooks;
- idempotência;
- ledger e reconciliação;
- custos;
- SLAs;
- suporte;
- limites;
- requisitos jurídicos/compliance.

---

## 2. Objetivo da conversa com o parceiro

A conversa com PSP/BaaS precisa responder:

- A Aurea pode operar como wallet usando a infraestrutura do parceiro?
- O parceiro oferece Pix entrada?
- O parceiro oferece Pix saída?
- O parceiro oferece conta/saldo/subconta?
- O parceiro oferece KYC/KYB?
- O parceiro oferece webhook assinado?
- O parceiro permite modelo white label ou embedded finance?
- Quais responsabilidades ficam com o parceiro?
- Quais responsabilidades ficam com a Aurea?
- Qual o caminho de homologação até produção?

---

## 3. Identificação do parceiro

| Campo | Resposta |
|---|---|
| Nome do parceiro | |
| Site | |
| Contato comercial | |
| Contato técnico | |
| E-mail | |
| Telefone/WhatsApp | |
| Modelo oferecido | |
| Data da reunião | |
| Responsável Aurea | |

---

## 4. Modelo de parceria

Perguntas obrigatórias:

- Vocês atuam como PSP, BaaS, IP, gateway, subadquirente, banco parceiro ou plataforma white label?
- A Aurea entraria como cliente, subconta, marketplace, correspondente, white label ou integradora?
- Quem é o responsável regulatório perante Banco Central e arranjos de pagamento?
- A Aurea precisa de autorização própria para operar neste modelo?
- O usuário final teria conta no parceiro, na Aurea ou em estrutura de subconta?
- O dinheiro fica custodiado por quem?
- A Aurea pode exibir saldo em nome próprio?
- A Aurea pode usar marca própria no app?
- Existe aprovação prévia da interface?
- Existe contrato específico para wallet/app?

---

## 5. Ambientes e homologação

Perguntas obrigatórias:

- Existe ambiente sandbox oficial?
- O sandbox simula Pix entrada?
- O sandbox simula Pix saída?
- O sandbox simula webhook?
- O sandbox simula saldo/extrato?
- Existe ambiente staging/homologação?
- Quanto tempo dura a homologação?
- Quais testes são obrigatórios?
- Quem aprova a ida para produção?
- Existe checklist técnico do parceiro?
- Existe checklist jurídico/compliance?
- Existe limite de transações no sandbox?
- Existe massa de dados de teste?
- Existe painel de homologação?

Critério Aurea:

- Sem sandbox oficial validado, não avançar para produção real.

---

## 6. APIs disponíveis

### 6.1 Autenticação

- Qual padrão de autenticação?
- API Key?
- OAuth2?
- mTLS?
- Certificado?
- Assinatura HMAC?
- IP allowlist?
- Token por ambiente?
- Rotação de credenciais?
- Escopos/permissões por endpoint?

### 6.2 Pix entrada/cobrança

- Existe API para criar cobrança Pix?
- Suporta QR Code dinâmico?
- Suporta Pix copia e cola?
- Suporta expiração?
- Suporta multa/juros/desconto?
- Suporta metadata/external_id?
- Retorna provider_reference?
- Retorna status inicial?
- Permite consulta da cobrança?
- Permite cancelar cobrança?
- Permite listar cobranças?

### 6.3 Pix saída/pagamento

- Existe API para envio de Pix?
- Quais tipos de chave Pix são suportados?
- Há validação de destinatário antes do envio?
- Há confirmação em duas etapas?
- Existe idempotência no envio?
- Existe limite por transação?
- Existe limite diário/mensal?
- Existe bloqueio por risco?
- Existe consulta de status?
- Existe comprovante oficial?

### 6.4 Saldo

- Existe API de saldo?
- O saldo é por conta, subconta ou carteira?
- Existe saldo disponível?
- Existe saldo bloqueado?
- Existe saldo pendente?
- Existe saldo por moeda?
- Existe atualização em tempo real?
- Existe conciliação de saldo?

### 6.5 Extrato

- Existe API de extrato?
- Permite filtros por data?
- Permite filtros por status?
- Permite filtros por provider_reference?
- Permite paginação?
- Retorna taxas?
- Retorna contraparte?
- Retorna identificador único?
- Retorna tipo de operação?

### 6.6 Comprovante

- Existe API de comprovante?
- O comprovante é PDF, imagem, JSON ou URL?
- O comprovante tem validade oficial?
- O comprovante traz identificador do parceiro?
- O comprovante traz data/hora?
- O comprovante traz valor?
- O comprovante traz pagador/recebedor?
- A Aurea pode gerar comprovante próprio baseado nos dados oficiais?

---

## 7. Webhooks

Perguntas obrigatórias:

- Quais eventos possuem webhook?
- Pagamento Pix confirmado?
- Pagamento Pix expirado?
- Pagamento Pix cancelado?
- Pix enviado?
- Pix recusado?
- Estorno/devolução?
- Bloqueio de conta?
- Atualização KYC/KYB?
- Alteração de saldo?

Segurança:

- Webhook tem assinatura?
- Webhook tem token?
- Webhook tem timestamp?
- Webhook tem nonce?
- Webhook exige IP allowlist?
- Como validar autenticidade?
- Como lidar com replay?
- O parceiro reenvia webhook em caso de falha?
- Qual política de retry?
- Qual timeout esperado?
- Qual formato do payload?
- Existe documentação com exemplos?

Idempotência:

- Existe event_id único?
- Existe provider_reference único?
- Existe idempotency_key?
- Existe request_id?
- O mesmo evento pode chegar mais de uma vez?
- O payload pode mudar entre retries?
- Como detectar conflito?

Critério Aurea:

- Webhook real sem assinatura/token não deve creditar saldo real automaticamente.

---

## 8. KYC/KYB

### 8.1 Pessoa física

- Quem coleta KYC?
- Quais dados são obrigatórios?
- CPF?
- Nome?
- Data de nascimento?
- Endereço?
- Documento?
- Selfie?
- Prova de vida?
- Validação antifraude?
- Status possíveis?
- Tempo médio de aprovação?
- Motivos de reprovação?
- Webhook de atualização de status?
- A Aurea pode exibir status no app?

### 8.2 Pessoa jurídica

- Quem coleta KYB?
- Quais dados são obrigatórios?
- CNPJ?
- Razão social?
- Sócios?
- Representante legal?
- Contrato social?
- CNAE?
- Endereço?
- Faturamento?
- Beneficiário final?
- Tempo médio de aprovação?
- Motivos de reprovação?
- Webhook de atualização de status?

Critério Aurea:

- Usuário sem KYC/KYB aprovado não pode operar dinheiro real.

---

## 9. Ledger, subcontas e custódia

Perguntas obrigatórias:

- O parceiro oferece subcontas?
- O parceiro oferece wallet/account por cliente?
- O dinheiro fica em conta individual, conta omnibus ou subconta?
- Como identificar saldo de cada cliente?
- Existe ledger do parceiro?
- Existe exportação de ledger?
- Existe conciliação por transação?
- Existe trava de saldo?
- Existe split?
- Existe bloqueio judicial/operacional?
- Existe reserva financeira?
- Como lidar com divergência de saldo?

Critério Aurea:

- A Aurea precisa manter ledger interno auditável, separado do sandbox e conciliado com o parceiro.

---

## 10. Reconciliação

Perguntas obrigatórias:

- Existe endpoint de reconciliação?
- Existe relatório diário?
- Existe relatório por período?
- Existe arquivo CNAB, CSV, JSON ou API?
- Existe conciliação por provider_reference?
- Existe conciliação por valor?
- Existe conciliação por horário?
- Existe conciliação por status?
- Existe webhook mais consulta ativa?
- Qual é a fonte da verdade?
- Como tratar divergência?
- Existe SLA para correção de divergência?

Critério Aurea:

- Nenhum comprovante real deve ser emitido sem dados oficiais conciliáveis.

---

## 11. Limites, risco e bloqueios

Perguntas obrigatórias:

- Quais limites por transação?
- Quais limites diários?
- Quais limites mensais?
- Limite muda por perfil?
- Limite muda após KYC/KYB?
- Existe limite para Pix saída?
- Existe limite para Pix entrada?
- Existe bloqueio automático por risco?
- Existe bloqueio manual?
- Existe desbloqueio via API?
- Existe análise antifraude?
- Existe monitoramento de transações suspeitas?
- Quem decide bloqueio/desbloqueio?

---

## 12. Tarifas e custos

Perguntas comerciais:

- Existe mensalidade?
- Existe setup?
- Existe custo por Pix entrada?
- Existe custo por Pix saída?
- Existe custo por conta/subconta?
- Existe custo por KYC/KYB?
- Existe custo por webhook?
- Existe custo por consulta?
- Existe mínimo mensal?
- Existe volume mínimo?
- Existe tarifa de saque/transferência?
- Existe tarifa de chargeback/devolução/contestação?
- Existe tarifa de suporte premium?
- Existe tabela progressiva por volume?

Campos para preencher:

| Item | Valor |
|---|---:|
| Setup | |
| Mensalidade | |
| Pix entrada | |
| Pix saída | |
| KYC PF | |
| KYB PJ | |
| Conta/subconta | |
| Consulta saldo | |
| Consulta extrato | |
| Webhook | |
| Suporte | |
| Mínimo mensal | |

---

## 13. SLA e suporte

Perguntas obrigatórias:

- SLA de uptime?
- SLA de webhook?
- SLA de liquidação?
- SLA de suporte?
- Suporte 24/7?
- Canal de suporte técnico?
- Canal de suporte emergencial?
- Existe gerente de conta?
- Existe status page?
- Existe comunicação de incidentes?
- Existe prazo para correção?
- Existe ambiente de incidentes/testes?

---

## 14. Segurança

Perguntas obrigatórias:

- Existe documentação de segurança?
- Existe criptografia em trânsito?
- Existe criptografia em repouso?
- Existe mTLS?
- Existe IP allowlist?
- Existe assinatura HMAC?
- Existe rotação de chave?
- Existe segregação por ambiente?
- Existe auditoria de acesso?
- Existe relatório de segurança?
- Existe teste de intrusão?
- Existe ISO, SOC, PCI ou certificações equivalentes?
- Como reportar vulnerabilidade?
- Como tratar incidente de segurança?

---

## 15. LGPD e dados

Perguntas obrigatórias:

- Quais dados a Aurea pode armazenar?
- Quais dados a Aurea não pode armazenar?
- Quem é controlador?
- Quem é operador?
- Existe DPA/contrato de tratamento de dados?
- Qual base legal sugerida?
- Existe política de retenção?
- Como excluir dados?
- Como exportar dados?
- Como atender solicitação do titular?
- Dados trafegam fora do Brasil?
- Existe suboperador?

---

## 16. Jurídico e compliance

Perguntas obrigatórias:

- Quais contratos são necessários?
- A Aurea precisa exibir termos do parceiro?
- A Aurea precisa coletar aceite específico?
- Existe política de uso aceitável?
- Existe lista de atividades proibidas?
- Existe análise de segmento/risco?
- Existe aprovação prévia do modelo de negócio?
- Existe obrigação de reporte?
- Existe revisão de tela/app?
- Existe manual de marca/uso?

---

## 17. Operação

Perguntas obrigatórias:

- Como bloquear conta?
- Como desbloquear conta?
- Como consultar status operacional?
- Como tratar devolução/estorno?
- Como tratar pagamento duplicado?
- Como tratar divergência de saldo?
- Como tratar webhook atrasado?
- Como tratar webhook ausente?
- Como tratar Pix enviado e não confirmado?
- Como tratar falha parcial?
- Como tratar manutenção do parceiro?

---

## 18. Checklist de aprovação do parceiro

Antes de escolher parceiro, preencher:

| Critério | Status | Observação |
|---|---|---|
| Sandbox oficial | | |
| Pix entrada | | |
| Pix saída | | |
| Saldo | | |
| Extrato | | |
| Comprovante | | |
| Webhook assinado | | |
| Idempotência | | |
| KYC/KYB | | |
| Ledger/subconta | | |
| Reconciliação | | |
| SLA | | |
| Suporte | | |
| Tarifas | | |
| Compliance | | |
| LGPD | | |
| Produção liberável | | |

---

## 19. Critério interno Aurea

O parceiro só deve ser considerado viável se:

- oferece sandbox oficial;
- oferece documentação técnica clara;
- permite webhook seguro;
- permite idempotência;
- permite reconciliação confiável;
- esclarece responsabilidade regulatória;
- suporta KYC/KYB;
- possui SLAs aceitáveis;
- possui suporte técnico real;
- possui custos compatíveis;
- permite operar com marca/experiência Aurea conforme estratégia.

---

## 20. Conclusão

Este questionário existe para impedir que a Aurea Gold escolha parceiro no escuro.

A carteira só deve avançar para Pix/dinheiro real quando o parceiro responder claramente sobre APIs, segurança, compliance, KYC/KYB, ledger, reconciliação, custos, SLA, suporte e responsabilidade regulatória.

Sem resposta clara, não há produção real.
