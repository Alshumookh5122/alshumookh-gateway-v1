from __future__ import annotations

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .deps import get_db, require_api_key
from .models import FiatSession, PaymentRequest
from .schemas import CreateFiatSessionRequest
from .services.audit_service import add_audit
from .utils import generate_session_id, safe_json_dumps, utc_now

router = APIRouter(prefix="/fiat", tags=["fiat"])

ONRAMPER_API_BASE = "https://api.onramper.com"


def _call_onramper_create_transaction(
    order: PaymentRequest,
    session_id: str,
) -> dict:
    """Call Onramper API server-to-server to create a checkout transaction."""
    payload = {
        "type": "buy",
        "source": order.currency,
        "destination": f"{order.currency}_{order.network}",
        "amount": str(order.amount),
        "walletAddress": order.wallet_address,
        "externalId": order.order_id,
        "partnerContext": session_id,
    }

    headers = {
        "Authorization": f"Bearer {settings.PROVIDER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            f"{ONRAMPER_API_BASE}/checkout/init",
            json=payload,
            headers=headers,
            timeout=15,
        )
        if resp.status_code in (200, 201):
            return resp.json()
        # Log non-fatal errors but don't fail — fall back to URL-only mode
        return {"error": resp.text, "status_code": resp.status_code}
    except requests.RequestException as exc:
        return {"error": str(exc)}


@router.post("/create-session")
def create_fiat_session(
    req: CreateFiatSessionRequest,
    _: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    order = db.execute(
        select(PaymentRequest).where(PaymentRequest.order_id == req.order_id)
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Payment request not found")

    if not settings.PROVIDER_PUBLIC_KEY:
        raise HTTPException(
            status_code=503,
            detail="Fiat provider not configured: PROVIDER_PUBLIC_KEY is missing",
        )

    session_id = generate_session_id()

    # Build checkout URL with wallet pre-filled
    crypto_dest = f"{order.currency}_{order.network}".upper()
    checkout_url = (
        f"https://buy.onramper.com/"
        f"?apiKey={settings.PROVIDER_PUBLIC_KEY}"
        f"&onlyCryptos={crypto_dest}"
        f"&wallets={crypto_dest}:{order.wallet_address}"
        f"&partnerContext={session_id}"
        f"&externalId={order.order_id}"
    )

    # Server-to-server call to Onramper if API key is available
    provider_response: dict = {}
    if settings.PROVIDER_API_KEY:
        provider_response = _call_onramper_create_transaction(order, session_id)
        # Use provider-returned URL if available
        if "url" in provider_response:
            checkout_url = provider_response["url"]
        elif "checkoutUrl" in provider_response:
            checkout_url = provider_response["checkoutUrl"]

    raw = safe_json_dumps(
        {
            "checkout_url": checkout_url,
            "provider_response": provider_response,
        }
    )

    session = FiatSession(
        session_id=session_id,
        provider=settings.PROVIDER_NAME,
        order_id=order.order_id,
        status="created",
        raw_session_json=raw,
        created_at=utc_now(),
    )
    db.add(session)

    order.provider = settings.PROVIDER_NAME
    order.provider_session_id = session_id
    db.commit()

    add_audit(
        db,
        event_type="FIAT_SESSION_CREATED",
        reference_id=order.order_id,
        details={
            "session_id": session_id,
            "provider": settings.PROVIDER_NAME,
            "api_to_api": bool(settings.PROVIDER_API_KEY),
        },
    )

    return {
        "status": "created",
        "session_id": session_id,
        "provider": settings.PROVIDER_NAME,
        "checkout_url": checkout_url,
        "provider_response": provider_response if provider_response else None,
    }


@router.get("/session/{session_id}")
def get_fiat_session(
    session_id: str,
    _: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    row = db.execute(
        select(FiatSession).where(FiatSession.session_id == session_id)
    ).scalar_one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Fiat session not found")

    return {
        "session_id": row.session_id,
        "provider": row.provider,
        "order_id": row.order_id,
        "status": row.status,
        "raw_session_json": row.raw_session_json,
        "created_at": row.created_at.isoformat(),
    }
