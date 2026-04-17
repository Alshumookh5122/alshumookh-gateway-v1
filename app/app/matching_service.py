from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import CryptoPayment, FiatSession, PaymentRequest
from .services.audit_service import add_audit
from .utils import utc_now


def _normalize_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def match_crypto_payment(
    db: Session,
    payment: CryptoPayment,
) -> PaymentRequest | None:
    payment_amount = _normalize_decimal(payment.amount)
    if payment_amount is None:
        return None

    rows = db.execute(
        select(PaymentRequest).where(PaymentRequest.status == "pending")
    ).scalars().all()

    for order in rows:
        order_amount = _normalize_decimal(order.amount)
        if order_amount is None:
            continue

        if (
            order.currency.upper() == payment.token_symbol.upper()
            and order.network.upper() == payment.network.upper()
            and order.wallet_address == payment.wallet_address
            and order_amount == payment_amount
        ):
            order.status = "paid"
            order.matched_payment_id = payment.payment_id
            order.paid_at = utc_now()
            db.commit()

            add_audit(
                db,
                event_type="CRYPTO_PAYMENT_MATCHED",
                reference_id=order.order_id,
                details={
                    "payment_id": payment.payment_id,
                    "tx_hash": payment.tx_hash,
                },
            )
            return order

    return None


def match_fiat_session(
    db: Session,
    session: FiatSession,
) -> PaymentRequest | None:
    if not session.order_id:
        return None

    order = db.execute(
        select(PaymentRequest).where(PaymentRequest.order_id == session.order_id)
    ).scalar_one_or_none()

    if not order:
        return None

    if session.status.lower() in {"completed", "paid", "success"}:
        order.status = "paid"
        order.matched_payment_id = session.session_id
        order.paid_at = utc_now()
        db.commit()

        add_audit(
            db,
            event_type="FIAT_SESSION_MATCHED",
            reference_id=order.order_id,
            details={
                "session_id": session.session_id,
                "provider": session.provider,
            },
        )
        return order

    return None
