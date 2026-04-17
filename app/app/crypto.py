from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.models import CryptoPayment

router = APIRouter(prefix="/crypto", tags=["crypto"])


@router.get("/payments")
def list_crypto_payments(
    _: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(CryptoPayment).order_by(CryptoPayment.created_at.desc())
    ).scalars().all()

    return {
        "count": len(rows),
        "items": [
            {
                "payment_id": r.payment_id,
                "tx_hash": r.tx_hash,
                "wallet_address": r.wallet_address,
                "network": r.network,
                "token_symbol": r.token_symbol,
                "amount": r.amount,
                "from_address": r.from_address,
                "status": r.status,
                "confirmations": r.confirmations,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }


@router.post("/sync")
def crypto_sync_stub(
    _: str = Depends(require_api_key),
):
    return {
        "status": "ok",
        "message": "Use Alchemy webhooks for live crypto events"
    }
