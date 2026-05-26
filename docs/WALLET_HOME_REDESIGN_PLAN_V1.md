# Aurea Gold — Plano de Redesign da Home/Conta Mobile V1

## Objetivo

Padronizar a tela Conta/Home para seguir a mesma identidade visual já aprovada nas abas Gestão, Pix, Pagar e Mais.

## Regra principal

Não mexer em Gestão, Pix, Pagar, Mais, AppShell, bottom nav, API, autenticação, saldo real/demo, Pix sandbox, forecast, IA ou status de parceiro.

## Arquivo alvo

aurea-gold-client/src/super2/SuperAureaHome.tsx

## Problema atual

A Home ainda parece uma tela diferente das outras abas. O card grande de saldo/patrimônio deixa o mobile pesado e fora do padrão premium aprovado.

## Padrão desejado

- hero compacto;
- fundo azul/petróleo;
- dourado premium;
- grid 3x3 de cards pequenos;
- textos curtos;
- banner de carteira protegida;
- modo demo/sandbox honesto;
- sem liberar dinheiro real, Pix real, boleto real, cartão real ou liquidação real.

## Estratégia

1. Criar bloco mobile novo somente na Home/Conta.
2. Manter desktop antigo preservado por segurança.
3. Esconder no mobile os blocos gigantes antigos.
4. Validar visual no celular antes de qualquer commit.
5. Se ficar ruim, restaurar somente SuperAureaHome.tsx.

## Rollback

git restore aurea-gold-client/src/super2/SuperAureaHome.tsx
