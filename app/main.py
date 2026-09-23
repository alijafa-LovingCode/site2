from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routes import (
    admin_routes,
    auth_routes,
    backup_routes,
    chat_routes,
    cycle_routes,
    exam_routes,
    message_routes,
    planner_routes,
    resource_routes,
    student_routes,
    telegram_routes,
)
from app.services.startup_seed import run_startup_seed
from app.utils.logging_config import configure_logging
from app.utils.rate_limit import limiter

configure_logging()
logger = logging.getLogger("main")

app = FastAPI(title="Mehrsa Study Planner", description="برنامه مطالعاتی مهرسا", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# --------------------------------------------------------------- Routers ---
app.include_router(auth_routes.router)
app.include_router(planner_routes.router)
app.include_router(exam_routes.router)
app.include_router(resource_routes.router)
app.include_router(message_routes.router)
app.include_router(chat_routes.router)
app.include_router(cycle_routes.router)
app.include_router(telegram_routes.router)
app.include_router(admin_routes.router)
app.include_router(backup_routes.router)
app.include_router(student_routes.router)


# ------------------------------------------------------------- Startup ---
@app.on_event("startup")
def on_startup() -> None:
    logger.info("Starting Mehrsa Study Planner (env=%s)", settings.app_env)
    # Safety net: ensure tables exist even if `alembic upgrade head` was not
    # run yet. Migrations remain the recommended path for schema changes.
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        run_startup_seed(db)
    logger.info("Startup complete.")


# --------------------------------------------------------- Health check ---
@app.get("/health")
def health():
    return {"status": "ok"}


# ------------------------------------------------------------ Frontend ---
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/student", response_class=HTMLResponse)
def student_page(request: Request):
    return templates.TemplateResponse("student.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


# ------------------------------------------------------- Error handling ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, str) and request.url.path.startswith("/api/"):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if exc.status_code == 404 and not request.url.path.startswith("/api/"):
        return HTMLResponse("<h1>404</h1><p>صفحه پیدا نشد.</p>", status_code=404)
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "اطلاعات ارسالی نامعتبر است."})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "خطایی رخ داد. لطفاً دوباره تلاش کنید."})
