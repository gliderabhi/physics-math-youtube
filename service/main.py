from fastapi import FastAPI

from .routes_admin import router as admin_router
from .routes_api import router as api_router
from .routes_health import router as health_router

app = FastAPI(title="Physics/Math YouTube Web API")
app.include_router(health_router)
app.include_router(api_router)
app.include_router(admin_router)
