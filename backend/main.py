from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from config import get_settings
from routers import auth, code

settings = get_settings()
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"

app = FastAPI(
    title="AI Code Editor API",
    description="Authentication, AI code assistance, and session history endpoints.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(code.router, prefix="/code", tags=["Code"])


@app.get("/")
async def root():
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    return {"message": "AI Code Editor API is running!"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if FRONTEND_INDEX.exists():
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        candidate = FRONTEND_DIST / full_path

        if full_path and candidate.is_file():
            return FileResponse(candidate)

        return FileResponse(FRONTEND_INDEX)
