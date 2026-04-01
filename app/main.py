from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes import router
from app.core.config import settings
from app.db.database import Base, engine

app = FastAPI(title="Skill Learning Agent", version="1.0.0")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
def on_startup():
    print(f"Starting Skill Learning Agent with DB: {settings.masked_database_url()}")
    if settings.uses_local_default_database():
        print("Warning: using the local default PostgreSQL URL. Set DATABASE_URL explicitly in Docker/Render.")
    Base.metadata.create_all(bind=engine)


@app.get("/")
def health():
    return {"status": "ok", "service": "skill-learning-agent", "ui": "/app"}


@app.get("/health/db")
def health_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
    return {"status": "ok", "database": "reachable", "result": result}


@app.get("/app", include_in_schema=False)
def frontend_app():
    return FileResponse(static_dir / "index.html")


app.include_router(router)
