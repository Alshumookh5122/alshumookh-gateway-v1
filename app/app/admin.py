from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .deps import get_db, require_api_key
from .models import AuditLog, CryptoPayment, FiatSession, PaymentRequest, WebhookEvent

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/summary")
def admin_summary(
    _: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    payment_requests = db.query(PaymentRequest).count()
    crypto_payments = db.query(CryptoPayment).count()
    fiat_sessions = db.query(FiatSession).count()
    webhook_events = db.query(WebhookEvent).count()
    audit_logs = db.query(AuditLog).count()

    paid_orders = db.query(PaymentRequest).filter(PaymentRequest.status == "paid").count()
    pending_orders = db.query(PaymentRequest).filter(PaymentRequest.status == "pending").count()

    return {
        "payment_requests": payment_requests,
        "paid_orders": paid_orders,
        "pending_orders": pending_orders,
        "crypto_payments": crypto_payments,
        "fiat_sessions": fiat_sessions,
        "webhook_events": webhook_events,
        "audit_logs": audit_logs,
    }


@router.get("/audit-logs")
def list_audit_logs(
    _: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc())
    ).scalars().all()

    return {
        "count": len(rows),
        "items": [
            {
                "id": r.id,
                "event_type": r.event_type,
                "reference_id": r.reference_id,
                "details_json": r.details_json,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }


@router.get("/webhook-events")
def list_webhook_events(
    _: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(WebhookEvent).order_by(WebhookEvent.created_at.desc())
    ).scalars().all()

    return {
        "count": len(rows),
        "items": [
            {
                "event_id": r.event_id,
                "source": r.source,
                "event_type": r.event_type,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }
