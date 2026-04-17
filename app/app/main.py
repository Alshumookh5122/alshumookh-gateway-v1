from fastapi import FastAPI

from .config import settings
from .database import engine
from .models import Base
from .admin import router as admin_router
from .crypto import router as crypto_router
from .fiat import router as fiat_router
from .health import router as health_router
from .payments import router as payments_router
from .webhooks import router as webhooks_router

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
