from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} API is running"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "chain": settings.ALCHEMY_CHAIN,
        "network": settings.DEFAULT_NETWORK,
        "wallet": settings.DEFAULT_WALLET_ADDRESS
    }

@app.get("/transactions")
def get_transactions():
    return {
        "status": "success",
        "data": []
    }
