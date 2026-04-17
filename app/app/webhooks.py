from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from web3 import Web3

from .alchemy_service import verify_alchemy_webhook
from .config import settings
from .database import SessionLocal
from .matching_service import match_crypto_payment, match_fiat_session
from .models import CryptoPayment, FiatSession, WebhookEvent
from .provider_service import verify_provider_webhook
from .schemas import ProviderWebhookPayload
from .services.audit_service import add_audit
from .utils import safe_json_dumps, utc_now

router = APIRouter()

USDT_TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()
USDT_CONTRACT = Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")


def _save_webhook_event(db: Session, source: str, event_type: str, payload: dict) -> WebhookEvent:
    event = WebhookEvent(
        event_id=str(uuid.uuid4()),
        source=source,
        event_type=event_type,
        payload_json=safe_json_dumps(payload),
        status="received",
        created_at=utc_now(),
    )
    db.add(event)
    db.flush()
    return event


@router.post("/webhook")
async def alchemy_webhook(request: Request):
    """Alchemy blockchain webhook — detects on-chain USDT transfers."""
    body = await request.body()

    if settings.ALCHEMY_WEBHOOK_SECRET:
        verify_alchemy_webhook(request, body)

    data = json.loads(body)

    db: Session = SessionLocal()
    try:
        _save_webhook_event(db, source="alchemy", event_type="block_log", payload=data)

        logs = (
            data.get("event", {})
            .get("data", {})
            .get("block", {})
            .get("logs", [])
        )

        for log in logs:
            address = log.get("address", "")
            if address.lower() != USDT_CONTRACT.lower():
                continue

            topics = log.get("topics", [])
            if len(topics) < 3:
                continue

            if topics[0] != USDT_TRANSFER_TOPIC:
                continue

            data_hex = log.get("data", "0x0")
            from_address = "0x" + topics[1][-40:]
            to_address = "0x" + topics[2][-40:]
            amount_raw = int(data_hex, 16)
            amount = str(amount_raw / (10 ** 6))  # USDT = 6 decimals

            tx_hash = log.get("transactionHash", str(uuid.uuid4()))
            payment_id = f"CP-{tx_hash[:20]}"

            # Skip if already recorded
            existing = db.execute(
                select(CryptoPayment).where(CryptoPayment.tx_hash == tx_hash)
            ).scalar_one_or_none()
            if existing:
                continue

            payment = CryptoPayment(
                payment_id=payment_id,
                tx_hash=tx_hash,
                wallet_address=to_address,
                network=settings.ALCHEMY_CHAIN,
                token_symbol=settings.DEFAULT_TOKEN_SYMBOL,
                amount=amount,
                from_address=from_address,
                status="detected",
                confirmations=1,
                created_at=utc_now(),
            )
            db.add(payment)
            db.flush()

            add_audit(
                db,
                event_type="CRYPTO_PAYMENT_DETECTED",
                reference_id=payment_id,
                details={
                    "tx_hash": tx_hash,
                    "from": from_address,
                    "to": to_address,
                    "amount": amount,
                    "token": settings.DEFAULT_TOKEN_SYMBOL,
                    "network": settings.ALCHEMY_CHAIN,
                },
            )

            match_crypto_payment(db, payment)

        db.commit()
    except Exception as exc:
        db.rollback()
        print("ALCHEMY WEBHOOK ERROR:", str(exc))
    finally:
        db.close()

    return {"status": "ok"}


@router.post("/webhook/provider")
async def provider_webhook(request: Request):
    """Fiat provider (Onramper) webhook — updates fiat session status."""
    body = await request.body()

    if settings.PROVIDER_WEBHOOK_SECRET:
        verify_provider_webhook(request, body)

    raw_data = json.loads(body)

    db: Session = SessionLocal()
    try:
        payload = ProviderWebhookPayload(**raw_data)

        event_type = payload.event_type or "unknown"
        _save_webhook_event(db, source=settings.PROVIDER_NAME, event_type=event_type, payload=raw_data)

        # Locate the fiat session by transaction_id or wallet_address
        session: FiatSession | None = None

        if payload.transaction_id:
            session = db.execute(
                select(FiatSession).where(
                    FiatSession.session_id == payload.transaction_id
                )
            ).scalar_one_or_none()

        # Map provider status to our status
        status_map = {
            "completed": "paid",
            "success": "paid",
            "paid": "paid",
            "failed": "failed",
            "cancelled": "cancelled",
            "pending": "pending",
        }
        new_status = status_map.get((payload.status or "").lower(), payload.status or "unknown")

        if session:
            session.status = new_status
            db.flush()

            add_audit(
                db,
                event_type="FIAT_WEBHOOK_RECEIVED",
                reference_id=session.order_id,
                details={
                    "provider": settings.PROVIDER_NAME,
                    "event_type": event_type,
                    "status": new_status,
                    "transaction_id": payload.transaction_id,
                },
            )

            if new_status == "paid":
                match_fiat_session(db, session)
        else:
            add_audit(
                db,
                event_type="FIAT_WEBHOOK_UNMATCHED",
                reference_id=payload.transaction_id,
                details={"event_type": event_type, "status": new_status},
            )

        db.commit()
    except Exception as exc:
        db.rollback()
        print("PROVIDER WEBHOOK ERROR:", str(exc))
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        db.close()

    return {"status": "ok"}
