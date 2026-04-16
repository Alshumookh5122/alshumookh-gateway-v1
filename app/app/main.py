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
