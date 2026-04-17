from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .alchemy_service import verify_alchemy_webhook
from .config import settings
from .database import SessionLocal
from .matching_service import match_crypto_payment, match_fiat_session
from .models import CryptoPayment, FiatSession, WebhookEvent
from .provider_service import verify_provider_webhook
from .services.audit_service import add_audit
from .utils import safe_json_dumps, utc_now

router = APIRouter(tags=["webhooks"])


@router.post("/webhook")
async def provider_webhook(request: Request):
    raw_body = await request.body()
    verify_provider_webhook(request, raw_body)

    try:
        data = json.loads(raw_body.decode("utf-8"))
    except Exception:
        data = {"raw": "invalid json"}

    print("=== PROVIDER WEBHOOK RECEIVED ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    payload = data.get("payload", {}) if isinstance(data, dict) else {}

    event_id = str(data.get("id") or uuid.uuid4())
    event_type = data.get("type") or data.get("eventType") or "unknown"

    session_id = (
        payload.get("sessionId")
        or payload.get("id")
        or payload.get("transactionId")
        or payload.get("transaction_id")
    )
    status = payload.get("status") or data.get("status") or "unknown"

    db: Session = SessionLocal()
    try:
        existing = db.execute(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        ).scalar_one_or_none()

        if existing:
            return JSONResponse(
                status_code=200,
                content={"status": "ok", "message": "provider webhook already processed"},
            )

        event = WebhookEvent(
            event_id=event_id,
            source=settings.PROVIDER_NAME,
            event_type=event_type,
            payload_json=safe_json_dumps(data),
            status="received",
            created_at=utc_now(),
        )
        db.add(event)
        db.commit()

        if session_id:
            fiat_session = db.execute(
                select(FiatSession).where(FiatSession.session_id == session_id)
            ).scalar_one_or_none()

            if fiat_session:
                fiat_session.status = str(status).lower()
                if not fiat_session.raw_session_json:
                    fiat_session.raw_session_json = safe_json_dumps(data)
                db.commit()

                matched = match_fiat_session(db, fiat_session)

                add_audit(
                    db,
                    event_type="PROVIDER_WEBHOOK_PROCESSED",
                    reference_id=session_id,
                    details={
                        "event_id": event_id,
                        "status": status,
                        "matched_order": matched.order_id if matched else None,
                    },
                )

        return JSONResponse(
            status_code=200,
            content={"status": "processed", "event_id": event_id},
        )

    finally:
        db.close()


@router.post("/webhooks/alchemy")
async def alchemy_webhook(request: Request):
    raw_body = await request.body()
    verify_alchemy_webhook(request, raw_body)

    try:
        data = json.loads(raw_body.decode("utf-8"))
    except Exception:
        data = {"raw": "invalid json"}

    print("=== ALCHEMY WEBHOOK RECEIVED ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    event_id = str(data.get("id") or uuid.uuid4())
    event_type = data.get("type") or data.get("eventType") or "alchemy_event"

    payload = data.get("payload", {}) if isinstance(data, dict) else {}

    tx_hash = (
        payload.get("hash")
        or payload.get("txHash")
        or payload.get("transactionHash")
        or payload.get("tx_hash")
        or str(uuid.uuid4())
    )
    payment_id = tx_hash
    wallet_address = payload.get("toAddress") or payload.get("walletAddress") or settings.DEFAULT_WALLET_ADDRESS
    network = payload.get("network") or settings.ALCHEMY_CHAIN
    token_symbol = payload.get("tokenSymbol") or payload.get("symbol") or settings.DEFAULT_TOKEN_SYMBOL
    amount = str(payload.get("amount") or payload.get("value") or "0")
    from_address = payload.get("fromAddress") or payload.get("from")
    confirmations = int(payload.get("confirmations") or 0)

    db: Session = SessionLocal()
    try:
        existing = db.execute(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        ).scalar_one_or_none()

        if existing:
            return JSONResponse(
                status_code=200,
                content={"status": "ok", "message": "alchemy webhook already processed"},
            )

        event = WebhookEvent(
            event_id=event_id,
            source="alchemy",
            event_type=event_type,
            payload_json=safe_json_dumps(data),
            status="received",
            created_at=utc_now(),
        )
        db.add(event)
        db.commit()

        payment = db.execute(
            select(CryptoPayment).where(CryptoPayment.payment_id == payment_id)
        ).scalar_one_or_none()

        if not payment:
            payment = CryptoPayment(
                payment_id=payment_id,
                tx_hash=tx_hash,
                wallet_address=wallet_address,
                network=network,
                token_symbol=token_symbol,
                amount=amount,
                from_address=from_address,
                status="confirmed" if confirmations >= settings.MIN_CONFIRMATIONS else "pending",
                confirmations=confirmations,
                created_at=utc_now(),
            )
            db.add(payment)
            db.commit()
        else:
            payment.confirmations = confirmations
            payment.status = "confirmed" if confirmations >= settings.MIN_CONFIRMATIONS else "pending"
            db.commit()

        matched = None
        if payment.confirmations >= settings.MIN_CONFIRMATIONS:
            matched = match_crypto_payment(db, payment)

        add_audit(
            db,
            event_type="ALCHEMY_WEBHOOK_PROCESSED",
            reference_id=tx_hash,
            details={
                "event_id": event_id,
                "confirmations": confirmations,
                "matched_order": matched.order_id if matched else None,
            },
        )

        return JSONResponse(
            status_code=200,
            content={"status": "processed", "event_id": event_id, "tx_hash": tx_hash},
        )

    finally:
        db.close()
