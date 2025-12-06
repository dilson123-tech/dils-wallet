# Guia de uso do OpenAI Codex no projeto Dils Wallet

Este documento explica como usar o OpenAI Codex neste repositório `dils-wallet`
de forma segura, controlada e profissional.

## 1. O que é o Codex aqui dentro

- É um **agente de código** conectado ao seu plano do ChatGPT.
- Ele lê o repositório, sugere mudanças, escreve código, roda comandos e faz review.
- No nosso fluxo, ele é **dev júnior**; quem manda e aprova é você.

## 2. Modos de aprovação

Sempre conferir o modo com:

`/approvals`

Modos principais:

1. **Read Only**  
   - Codex só lê código e faz review.  
   - Não pode editar arquivos nem rodar comandos.

2. **Agent (current)** _(recomendado)_  
   - Pode propor edições e comandos, mas **NADA é aplicado sem `/approve`**.  
   - É o modo padrão para trabalhar no `dils-wallet`.

3. **Agent (full access)**  
   - Pode editar tudo e rodar comando com acesso de rede sem pedir.  
   - **NÃO usar** neste projeto.

## 3. Fluxo básico de trabalho

1. **Descrever a tarefa** em linguagem natural dentro do Codex, por exemplo:

   - “Explica o que este arquivo faz.”
   - “Refatora esta função para ficar mais legível.”
   - “Cria testes para o módulo X.”
   - “Analisa se esta mudança pode quebrar algo.”

2. O Codex monta um **plano** e, se for mudança de código, prepara um **patch**.

3. Ver o patch com:

`/review`

4. Se estiver tudo OK:

`/approve`

5. Se não gostou ou não quer aplicar:

`/reject`

## 4. Boas práticas neste repositório

- **Sempre** rodar `/review` antes de aprovar qualquer coisa.
- Não deixar o Codex alterar:
  - arquivos sensíveis de infra sem necessidade (`railway.toml`, `dockerfile`, scripts de deploy);
  - segredo/variáveis de ambiente.
- Manter commits pequenos:
  - De preferência, deixar o Codex resolver **uma tarefa por vez** e depois você faz `git add` + `git commit`.
- Para coisas grandes (refactor pesado, alteração em vários módulos):
  - Peça para ele primeiro **explicar o plano** em detalhes;
  - Depois deixar o patch pronto e só então revisar.

## 5. Exemplos de comandos úteis

- Explicar o repo:

  > “Explica em português o que é este repositório dils-wallet e quais são as principais pastas.”

- Revisar um arquivo específico:

  > “Faz um review completo do arquivo `app/models/pix_transaction.py` e aponta possíveis problemas.”

- Ajudar em migração Alembic:

  > “Verifica se a migration `migrations/versions/xxxx_add_pix_transaction_fee_columns.py` está coerente com o model `PixTransaction`.”

## 6. Segurança e produção

- Codex só mexe **no código local**.
- Nada vai para produção enquanto você não fizer:
  - `git push`  
  - e o fluxo de deploy (Railway/CI).
- Antes de aceitar patch grande:
  - garanta que está em uma branch de feature (`feature/...`);
  - faça um commit de checkpoint antes;
  - rode testes ou `uvicorn` local para validar.

---

Usar o Codex aqui é para **acelerar o desenvolvimento**, nunca para substituir revisão humana.
O controle final das mudanças no `dils-wallet` é sempre seu.
