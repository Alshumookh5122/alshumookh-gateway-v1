from fastapi import FastAPI, Request
import json

from .config import settings
from .database import engine, SessionLocal
from .models import Base, Transaction

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "wallet": settings.WALLET_ADDRESS
    }


@app.get("/transactions")
def get_transactions():
    db = SessionLocal()
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

    db.close()

    return {
        "status": "success",
        "count": len(result),
        "data": result
    }


@app.post("/webhook")
async def alchemy_webhook(request: Request):
    data = await request.json()

    print("🔥 Incoming Webhook:", data)

    activities = data.get("event", {}).get("activity", [])
    network = data.get("event", {}).get("network", "")

    db = SessionLocal()

    for tx in activities:
        tx_hash = tx.get("hash")
        amount = str(tx.get("value"))
        asset = tx.get("asset")
        from_addr = tx.get("fromAddress")
        to_addr = tx.get("toAddress")

        print("💰 Transaction Detected")
        print(f"Amount: {amount} {asset}")
        print(f"From: {from_addr}")
        print(f"To: {to_addr}")
        print("----------------------")

        exists = db.query(Transaction).filter(Transaction.tx_hash == tx_hash).first()
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

    db.commit()
    db.close()

    return {"status": "processed"}

import uuid

@app.post("/create-payment")
def create_payment(amount: str, asset: str):
    db = SessionLocal()

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
    db.close()

    return {
        "reference": reference,
        "amount": amount,
        "asset": asset,
        "wallet": settings.WALLET_ADDRESS,
        "status": "pending"
    }
