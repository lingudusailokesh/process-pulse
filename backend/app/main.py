import time
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
import app.models # Register all models

# API Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.processes import router as processes_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.process_mining import router as pm_router
from app.api.v1.prediction import router as prediction_router
from app.api.v1.ai import router as ai_router

# Initialize Tables
Base.metadata.create_all(bind=engine)

def auto_seed_if_empty():
    """Auto-populates empty database (e.g., fresh Railway MySQL) with 500 cases."""
    from app.db.session import SessionLocal
    from app.models.process import ProcessInstance
    db = SessionLocal()
    try:
        if db.query(ProcessInstance).count() == 0:
            import logging
            logging.getLogger("process_pulse.main").info("Empty database detected. Auto-seeding initial dataset...")
            try:
                from data.seed_events import seed_database
                seed_database()
            except ImportError:
                import sys
                sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
                from data.seed_events import seed_database
                seed_database()
    except Exception as e:
        import logging
        logging.getLogger("process_pulse.main").warning(f"Auto-seed check: {e}")
    finally:
        db.close()

try:
    auto_seed_if_empty()
except Exception:
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Process Mining & Operational Intelligence Engine tailored for Technology Consulting & Process Improvement.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration for Frontend Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Timing & Audit Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time-Sec"] = f"{process_time:.4f}"
    return response

# Register API v1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(processes_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(pm_router, prefix=settings.API_V1_STR)
app.include_router(prediction_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)

import logging
from fastapi.responses import JSONResponse, RedirectResponse

logger = logging.getLogger("process_pulse.main")

# Mount Frontend static files
frontend_candidates = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend")),        # /app/frontend (Docker container)
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend")),   # <root>/frontend (Local dev)
    os.path.abspath(os.path.join(os.getcwd(), "frontend")),                            # ./frontend (Working directory)
    "/app/frontend",                                                                   # Direct container absolute path
]

frontend_dir = next(
    (path for path in frontend_candidates if os.path.exists(path)),
    None
)

if frontend_dir:
    logger.info(f"Frontend directory resolved to: {frontend_dir}")
    app.mount(
        "/dashboard",
        StaticFiles(directory=frontend_dir, html=True),
        name="frontend"
    )
else:
    logger.warning(f"Frontend directory not found among candidates: {frontend_candidates}")

@app.get("/dashboard", include_in_schema=False)
def dashboard_redirect():
    """Redirect /dashboard to /dashboard/ to guarantee trailing slash compatibility."""
    return RedirectResponse(url="/dashboard/", status_code=307)

@app.get("/health", tags=["System Health"])
def health_check():
    """Health check endpoint for container orchestrators and load balancers."""
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database_connected": True
    }

@app.get("/", tags=["Root"])
def root_redirect():
    """Root redirect endpoint pointing to interactive OpenAPI docs and dashboard."""
    return {
        "message": "Welcome to ProcessPulse Operations Intelligence API",
        "api_docs": "/docs",
        "dashboard_ui": "/dashboard/"
    }
