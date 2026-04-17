from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .deps import get_db, require_api_key
from .models import PaymentRequest
from .schemas import CreatePaymentRequest
from .services.audit_service import add_audit
from .utils import generate_order_id, utc_now

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create")
def create_payment(
    req: CreatePaymentRequest,
    _: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    order_id = generate_order_id()

    row = PaymentRequest(
        order_id=order_id,
        amount=str(req.amount),
        currency=req.currency,
        network=req.network,
        wallet_address=settings.DEFAULT_WALLET_ADDRESS,
        customer_name=req.customer_name,
        customer_reference=req.customer_reference,
        provider=req.provider,
        provider_session_id=None,
        status="pending",
        matched_payment_id=None,
        created_at=utc_now(),
        paid_at=None,
    )
    db.add(row)
    db.commit()

    add_audit(
        db,
        event_type="PAYMENT_REQUEST_CREATED",
        reference_id=order_id,
        details={
            "amount": str(req.amount),
            "currency": req.currency,
            "network": req.network,
            "provider": req.provider,
        },
    )

    return {
        "status": "created",
        "order_id": order_id,
        "wallet_address": settings.DEFAULT_WALLET_ADDRESS,
        "currency": req.currency,
        "network": req.network,
        "provider": req.provider,
    }


@router.get("")
def list_payments(
    _: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(PaymentRequest).order_by(PaymentRequest.created_at.desc())
    ).scalars().all()

    return {
        "count": len(rows),
        "items": [
            {
                "order_id": r.order_id,
                "amount": r.amount,
                "currency": r.currency,
                "network": r.network,
                "wallet_address": r.wallet_address,
                "customer_name": r.customer_name,
                "customer_reference": r.customer_reference,
                "provider": r.provider,
                "provider_session_id": r.provider_session_id,
                "status": r.status,
                "matched_payment_id": r.matched_payment_id,
                "created_at": r.created_at.isoformat(),
                "paid_at": r.paid_at.isoformat() if r.paid_at else None,
            }
            for r in rows
        ],
    }


@router.get("/{order_id}")
def get_payment(
    order_id: str,
    _: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    row = db.execute(
        select(PaymentRequest).where(PaymentRequest.order_id == order_id)
    ).scalar_one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Payment request not found")

    return {
        "order_id": row.order_id,
        "amount": row.amount,
        "currency": row.currency,
        "network": row.network,
        "wallet_address": row.wallet_address,
        "customer_name": row.customer_name,
        "customer_reference": row.customer_reference,
        "provider": row.provider,
        "provider_session_id": row.provider_session_id,
        "status": row.status,
        "matched_payment_id": row.matched_payment_id,
        "created_at": row.created_at.isoformat(),
        "paid_at": row.paid_at.isoformat() if row.paid_at else None,
    }
