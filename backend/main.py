import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

load_dotenv(BASE_DIR / ".env")

from backend.database.db import Base, engine
from backend.models import interview, user  # noqa: F401
from backend.routes import auth, dashboard, interview as interview_routes


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Interview Preparation System",
    description="Full-stack interview practice platform with AI-assisted evaluation and progress tracking.",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(interview_routes.router)
app.include_router(dashboard.router)


@app.get("/health", include_in_schema=False)
def health_check():
    return JSONResponse({"status": "ok"})


page_routes = {
    "/": "index.html",
    "/index.html": "index.html",
    "/login": "login.html",
    "/login.html": "login.html",
    "/register": "register.html",
    "/register.html": "register.html",
    "/dashboard-app": "dashboard.html",
    "/dashboard": "dashboard.html",
    "/dashboard.html": "dashboard.html",
    "/interview-app": "interview.html",
    "/interview": "interview.html",
    "/interview.html": "interview.html",
}


def build_page_handler(file_name: str):
    async def serve_page():
        return FileResponse(FRONTEND_DIR / file_name)

    return serve_page


for route_path, file_name in page_routes.items():
    app.add_api_route(route_path, build_page_handler(file_name), methods=["GET"], include_in_schema=False)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
