from fastapi import FastAPI
from .config import settings

app = FastAPI()

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
    return {
        "status": "success",
        "data": []
    }
from fastapi import Request

@app.post("/webhook")
async def alchemy_webhook(request: Request):
    data = await request.json()

    print("🔥 Incoming Webhook:", data)

    activities = data.get("event", {}).get("activity", [])

    for tx in activities:
        amount = tx.get("value")
        asset = tx.get("asset")
        from_addr = tx.get("fromAddress")
        to_addr = tx.get("toAddress")

        print("💰 Transaction Detected")
        print(f"Amount: {amount} {asset}")
        print(f"From: {from_addr}")
        print(f"To: {to_addr}")
        print("----------------------")

    return {"status": "processed"}
