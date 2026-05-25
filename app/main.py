from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import ping_database
from app.routes import (
    action_routes,
    admin_routes,
    alert_routes,
    auth_routes,
    behavior_routes,
    client_routes,
    dashboard_routes,
    health_routes,
    history_routes,
    notification_routes,
    prediction_routes,
    reports_routes,
    search_routes,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await ping_database()
    except Exception as e:
        print("⚠️ MongoDB non connecté :", e)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", docs_url="/docs", redoc_url="/redoc", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.cors_origins] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "ChurnGuard Backend API", "docs": "/docs"}


for router in [
    auth_routes.router,
    client_routes.router,
    behavior_routes.router,
    prediction_routes.router,
    alert_routes.router,
    action_routes.router,
    dashboard_routes.router,
    reports_routes.router,
    notification_routes.router,
    search_routes.router,
    history_routes.router,
    admin_routes.router,
    health_routes.router,
]:
    app.include_router(router, prefix=settings.api_prefix)
