from fastapi import FastAPI

from config import settings
from database import Base, engine
from routes.admin import router as admin_router
from routes.crypto import router as crypto_router
from routes.fiat import router as fiat_router
from routes.health import router as health_router
from routes.payments import router as payments_router
from routes.webhooks import router as webhooks_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ALSHUMOOKH Payment Gateway API",
)

Base.metadata.create_all(bind=engine)

app.include_router(health_router)
app.include_router(payments_router)
app.include_router(fiat_router)
app.include_router(crypto_router)
app.include_router(admin_router)
app.include_router(webhooks_router)
