from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
from datetime import datetime

app = FastAPI()

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {
        "message": "ALSHUMOOKH API is running"
    }

# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health():
    return {
        "status": "ok",
        "time": str(datetime.utcnow())
    }

# =========================
# TEST ENDPOINT
# =========================
@app.get("/webhook-test")
def webhook_test():
    return {
        "status": "ok",
        "message": "webhook endpoint is live"
    }

# =========================
# WEBHOOK (IMPORTANT)
# =========================
@app.post("/webhook")
async def webhook(request: Request):
    try:
        raw_body = await request.body()
        print("===== RAW BODY =====")
        print(raw_body.decode())

        try:
            data = json.loads(raw_body)
        except:
            data = {"raw": raw_body.decode()}

        print("===== JSON DATA =====")
        print(json.dumps(data, indent=2, ensure_ascii=False))


        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "message": "webhook received successfully"
            }
        )

    except Exception as e:
        print("ERROR:", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

# =========================
# FAKE TEST (POSTMAN TEST)
# =========================
@app.post("/simulate-payment")
async def simulate_payment():
    test_data = {
        "id": "test_tx_123",
        "status": "completed",
        "amount": 100,
        "currency": "USD",
        "crypto": "BTC",
        "wallet": "test_wallet_address",
        "timestamp": str(datetime.utcnow())
    }

    print("===== SIMULATED PAYMENT =====")
    print(json.dumps(test_data, indent=2))

    return {
        "status": "ok",
        "data": test_data
    }
