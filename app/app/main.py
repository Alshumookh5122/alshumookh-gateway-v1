from fastapi import FastAPI, Request
import json
import uuid

from .config import settings
from .database import engine, SessionLocal
from .models import Base, Transaction, PaymentRequest

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)


# -----------------------
# Root Endpoint
# -----------------------
@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} is running"
    }


# -----------------------
# Health Check
# -----------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "wallet": settings.WALLET_ADDRESS
    }


# -----------------------
# Get Transactions
# -----------------------
@app.get("/transactions")
def get_transactions():
    db = SessionLocal()
    try:
        rows = db.query(Transaction).all()
        result = []

        for row in rows:
            result.append({
                "id": row.id,
                "tx_hash": row.tx_hash,
                "asset": row.asset,
                "amount": row.amount,
                "from_address": row.from_address,
                "to_address": row.to_address,
                "network": row.network,
            })

        return {
            "status": "success",
            "count": len(result),
            "data": result
        }

    finally:
        db.close()


# -----------------------
# Webhook Endpoint (Alchemy)
# -----------------------
@app.post("/webhook")
async def alchemy_webhook(request: Request):
    data = await request.json()

    print("Incoming Webhook:", data)

    activities = data.get("event", {}).get("activity", [])
    network = data.get("event", {}).get("network", "")

    db = SessionLocal()

    try:
        for tx in activities:
            tx_hash = tx.get("hash")
           raw_value = tx.get("value", 0)
decimals = tx.get("rawContract", {}).get("decimals", 6)

amount = str(raw_value / (10 ** decimals))
            asset = tx.get("asset")
            from_addr = tx.get("fromAddress")
            to_addr = tx.get("toAddress")

            print("Transaction Detected")
            print(f"Amount: {amount} {asset}")
            print(f"From: {from_addr}")
            print(f"To: {to_addr}")
            print("----------------------")

            # Prevent duplicate transactions
            exists = db.query(Transaction).filter(
                Transaction.tx_hash == tx_hash
            ).first()

            if not exists:
                new_tx = Transaction(
                    tx_hash=tx_hash,
                    asset=asset,
                    amount=amount,
                    from_address=from_addr,
                    to_address=to_addr,
                    network=network,
                    raw_data=json.dumps(tx),
                )
                db.add(new_tx)

            # Match payment request
            payment = db.query(PaymentRequest).filter(
                PaymentRequest.wallet_address == to_addr,
                PaymentRequest.amount == amount,
                PaymentRequest.asset == asset,
                PaymentRequest.status == "pending"
            ).first()

            if payment:
                payment.status = "paid"
                print(f"Payment matched: {payment.reference}")

        db.commit()

        return {"status": "processed"}

    except Exception as e:
        db.rollback()
        print("Error:", str(e))
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


# -----------------------
# Create Payment Request
# -----------------------
@app.post("/create-payment")
def create_payment(amount: str, asset: str):
    db = SessionLocal()

    try:
        reference = str(uuid.uuid4())

        payment = PaymentRequest(
            reference=reference,
            amount=amount,
            asset=asset,
            wallet_address=settings.WALLET_ADDRESS,
            status="pending"
        )

        db.add(payment)
        db.commit()

        return {
            "reference": reference,
            "amount": amount,
            "asset": asset,
            "wallet": settings.WALLET_ADDRESS,
            "status": "pending"
        }

    finally:
        db.close()
@app.get("/payment-requests")
def get_payment_requests():
    db = SessionLocal()
    try:
        rows = db.query(PaymentRequest).all()
        result = []

        for row in rows:
            result.append({
                "id": row.id,
                "reference": row.reference,
                "amount": row.amount,
                "asset": row.asset,
                "wallet_address": row.wallet_address,
                "status": row.status,
            })

        return {
            "status": "success",
            "count": len(result),
            "data": result
        }

    finally:
        db.close()
