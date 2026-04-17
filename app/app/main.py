from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.routes.admin import router as admin_router
from app.routes.crypto import router as crypto_router
from app.routes.fiat import router as fiat_router
from app.routes.health import router as health_router
from app.routes.payments import router as payments_router
from app.routes.webhooks import router as webhooks_router

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
