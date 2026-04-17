from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_db, require_api_key
from app.models import FiatSession, PaymentRequest
from app.schemas import CreateFiatSessionRequest
from app.services.audit_service import add_audit
from app.utils import generate_session_id, safe_json_dumps, utc_now

router = APIRouter(prefix="/fiat", tags=["fiat"])


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

    session_id = generate_session_id()

    checkout_url = f"https://buy.onramper.com/?apiKey=YOUR_PUBLIC_KEY&sessionId={session_id}"

    session = FiatSession(
        session_id=session_id,
        provider=settings.PROVIDER_NAME,
        order_id=order.order_id,
        status="created",
        raw_session_json=safe_json_dumps({"checkout_url": checkout_url}),
        created_at=utc_now(),
    )
    db.add(session)

    order.provider_session_id = session_id
    db.commit()

    add_audit(
        db,
        event_type="FIAT_SESSION_CREATED",
        reference_id=order.order_id,
        details={
            "session_id": session_id,
            "provider": settings.PROVIDER_NAME,
        },
    )

    return {
        "status": "created",
        "session_id": session_id,
        "provider": settings.PROVIDER_NAME,
        "checkout_url": checkout_url,
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
