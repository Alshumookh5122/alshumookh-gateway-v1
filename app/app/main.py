from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .admin import router as admin_router
from .config import settings
from .crypto import router as crypto_router
from .database import engine
from .fiat import router as fiat_router
from .health import router as health_router
from .models import Base
from .payments import router as payments_router
from .webhooks import router as webhooks_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ALSHUMOOKH Payment Gateway API",
)

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/app/static"), name="static")


@app.get("/dashboard-ui", include_in_schema=False)
def dashboard_ui():
    return FileResponse("app/app/static/dashboard.html")


@app.get("/payment-status-ui", include_in_schema=False)
def payment_status_ui():
    return FileResponse("app/app/static/payment-status.html")


app.include_router(health_router)
app.include_router(payments_router)
app.include_router(fiat_router)
app.include_router(crypto_router)
app.include_router(admin_router)
app.include_router(webhooks_router)
