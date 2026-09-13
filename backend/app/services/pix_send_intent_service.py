"""
Autoridade server-side da intenção de envio PIX (M2).

Resolve o gap confirmado na investigação PIX-RETRY-DESIGN: o frontend
guardava a Idempotency-Key do PIX apenas em memória (`pixIntentManager.ts`),
perdendo-a em reload/fechar app/outra aba/outro dispositivo. Este módulo
move essa autoridade para o backend, usando uma tabela própria
(`PixSendIntent`) — nunca reaproveitando `idempotency_keys` como registry
permanente de intenção (decisão já tomada e registrada na investigação).

Reaproveita, como única fonte de verdade, as mesmas funções já usadas por
`send_pix()` para computar o "formato" de um envio PIX
(`pix_send_request_hash`, `round_pix_money`) e para localizar/validar uma
resposta de PIX já concluída (`_pix_send_scoped_key`,
`_parse_pix_send_completed_response`, `_resolve_pix_send_completed_owner`)
— nenhuma fórmula é duplicada, e `send_pix()` não é alterado em
comportamento.

Nunca aceita `user_id`/fingerprint vindos livremente do chamador: o
`user_id` sempre vem de `current_user.id` (rota), e o fingerprint é
recalculado aqui a partir do payload já validado pelo schema Pydantic do
PIX — nunca do JSON cru.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.idempotency import IdempotencyKey
from app.models.pix_send_intent import PixSendIntent
from app.services.pix_service import (
    _parse_pix_send_completed_response,
    _pix_send_scoped_key,
    _resolve_pix_send_completed_owner,
    pix_send_request_hash,
    round_pix_money,
)


class PixSendIntentAckError(ValueError):
    """Erro fail-closed ao tentar confirmar (ack) uma intent.

    Nunca é lançado por dúvida — só quando a verificação server-side
    contra o mecanismo real de idempotência (`pix-send:`) confirma que
    não há, ainda, um PIX genuinamente concluído para a send_key
    informada.
    """


def _new_send_key() -> str:
    return str(uuid.uuid4())


def _intent_result(intent: PixSendIntent, *, reused: bool) -> dict[str, Any]:
    can_send = intent.state == "pending"
    return {
        "state": intent.state,
        "send_key": intent.send_key if can_send else None,
        "generation": intent.generation,
        "reused": reused,
        "can_send": can_send,
        "requires_explicit_new": intent.state == "acknowledged",
    }


def _pix_send_intent_fingerprint(
    user_id: int, valor: Decimal, chave_pix: str, descricao: str
) -> str:
    # Mesma fórmula de send_pix() (pix_send_request_hash) — fonte única.
    return pix_send_request_hash(
        user_id=user_id, valor=valor, chave_pix=chave_pix, descricao=descricao
    )


def reserve_pix_send_intent(
    db: Session,
    *,
    user_id: int,
    valor: Decimal,
    chave_pix: str,
    descricao: str = "PIX",
    force_new: bool = False,
) -> dict[str, Any]:
    """Cria, recupera ou (só quando explicitamente autorizado) renova a
    intent de envio para (user_id, fingerprint(valor, chave_pix, descricao)).

    Contrato (todas as combinações são fail-closed por construção):
    - sem registro prévio: cria `pending`, generation=1, send_key novo (K1).
    - registro `pending`: SEMPRE devolve o mesmo send_key existente,
      IGNORANDO force_new — nunca substitui K1 enquanto pending.
    - registro `acknowledged` + force_new=false: NÃO cria K2; devolve
      can_send=false, requires_explicit_new=true.
    - registro `acknowledged` + force_new=true: renova atomicamente
      (compare-and-swap) para uma nova geração com send_key novo (K2).
    """
    valor = round_pix_money(Decimal(valor))
    fingerprint_hash = _pix_send_intent_fingerprint(
        user_id=user_id, valor=valor, chave_pix=chave_pix, descricao=descricao
    )

    # --- 1) Tentativa de criação atômica (primeira vez para este fingerprint) ---
    try:
        intent = PixSendIntent(
            user_id=user_id,
            fingerprint_hash=fingerprint_hash,
            send_key=_new_send_key(),
            state="pending",
            generation=1,
        )
        db.add(intent)
        db.flush()
        db.commit()
        db.refresh(intent)
        return _intent_result(intent, reused=False)
    except IntegrityError:
        db.rollback()

    # --- 2) Já existe uma linha para (user_id, fingerprint_hash) ---
    existing = (
        db.query(PixSendIntent)
        .filter_by(user_id=user_id, fingerprint_hash=fingerprint_hash)
        .first()
    )
    if existing is None:
        # Colidiu no INSERT mas a linha não é encontrada agora — nunca
        # inventar um resultado; sinaliza estado indeterminado.
        raise RuntimeError("pix_send_intent_race_unresolved")

    if existing.state == "pending":
        # Requisito crítico: nunca substituir K1 enquanto pending, mesmo
        # que force_new=true tenha sido pedido — uma aba atrasada nunca
        # pode gerar uma segunda transferência silenciosamente.
        result = _intent_result(existing, reused=True)
        if force_new:
            result["force_new_rejected"] = True
        return result

    # existing.state == "acknowledged"
    if not force_new:
        return _intent_result(existing, reused=True)

    return _renew_acknowledged_intent(db, existing)


def _renew_acknowledged_intent(db: Session, existing: PixSendIntent) -> dict[str, Any]:
    """Renova (acknowledged -> pending, generation+1) via compare-and-swap
    transacional: o UPDATE só afeta a linha se ela ainda estiver EXATAMENTE
    no estado/geração que lemos — se outra requisição já renovou primeiro,
    `rowcount` vem 0 e relemos a linha real, nunca inventando uma segunda
    nova geração (nunca K2 e K3 simultâneos)."""
    new_send_key = _new_send_key()
    expected_generation = existing.generation

    updated_rows = (
        db.query(PixSendIntent)
        .filter(
            PixSendIntent.id == existing.id,
            PixSendIntent.state == "acknowledged",
            PixSendIntent.generation == expected_generation,
        )
        .update(
            {
                "send_key": new_send_key,
                "state": "pending",
                "generation": expected_generation + 1,
            },
            synchronize_session=False,
        )
    )
    db.commit()

    db.expire(existing)
    current = db.query(PixSendIntent).filter_by(id=existing.id).first()

    if updated_rows == 1:
        return _intent_result(current, reused=False)

    # Perdemos o CAS — outra chamada já renovou (ou o estado mudou por
    # outro motivo) entre a nossa leitura e este UPDATE.
    return _intent_result(current, reused=True)


def acknowledge_pix_send_intent(
    db: Session, *, user_id: int, send_key: str
) -> dict[str, Any]:
    """Confirma (ack) que a send_key foi genuinamente processada com
    sucesso, verificando SEMPRE server-side contra o mecanismo real de
    idempotência (`pix-send:`) — nunca aceita a alegação do chamador.

    Idempotente: chamar de novo uma intent já `acknowledged` não falha,
    apenas confirma o estado atual sem efeito adicional.

    Levanta PixSendIntentAckError (fail-closed) se:
    - a send_key não pertence a nenhuma intent do usuário autenticado;
    - não existe, na tabela real de idempotência do PIX, uma resposta de
      send_pix concluída para essa send_key;
    - a resposta encontrada não resolve, de forma inequívoca, ao mesmo
      usuário que está pedindo o ack;
    - CRÍTICO: o request_hash do PIX realmente concluído para essa
      send_key é DIFERENTE do fingerprint_hash desta intent — ou seja,
      alguém chamou POST /pix/send com esta send_key mas um payload
      diferente do que a intent reservou. Isso nunca deve fechar o slot
      da intent original: o PIX de outro payload que por acaso usou a
      mesma send_key é uma questão do próprio send_pix (que já o aceitou
      ou rejeitou pelas suas regras normais de idempotência), mas não
      autoriza este ack a confirmar uma intent para a qual esse PIX não
      corresponde.
    """
    intent = (
        db.query(PixSendIntent)
        .filter(PixSendIntent.user_id == user_id, PixSendIntent.send_key == send_key)
        .first()
    )
    if intent is None:
        raise PixSendIntentAckError("pix_send_intent_not_found")

    if intent.state == "acknowledged":
        return _intent_result(intent, reused=True)

    # intent.state == "pending" (único outro estado possível) — a send_key
    # buscada é, por construção, sempre a da geração atual: cada renovação
    # gera uma send_key nova (UUID), então uma geração antiga nunca
    # compartilha send_key com a geração corrente.
    scoped_key = _pix_send_scoped_key(user_id, send_key)
    row = db.query(IdempotencyKey).filter_by(key=scoped_key).first()
    if row is None:
        raise PixSendIntentAckError("pix_send_not_completed")

    payload = _parse_pix_send_completed_response(row.response_json)
    if payload is None:
        raise PixSendIntentAckError("pix_send_not_completed")

    owner_id = _resolve_pix_send_completed_owner(db, payload)
    if owner_id != user_id:
        raise PixSendIntentAckError("pix_send_not_completed")

    # Item crítico: o PIX concluído para esta send_key precisa ser
    # exatamente o mesmo "formato" (destino+valor+descrição) que esta
    # intent reservou — ambos calculados pela MESMA fonte única
    # (pix_send_request_hash). Sem isso, um ack poderia fechar a intent A
    # com base num PIX de payload B que só por acaso reusou a send_key.
    if row.request_hash != intent.fingerprint_hash:
        raise PixSendIntentAckError("pix_send_payload_mismatch")

    intent.state = "acknowledged"
    db.commit()
    db.refresh(intent)
    return _intent_result(intent, reused=False)
