from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.db.database import Base, engine

app = FastAPI(title="Skill Learning Agent", version="1.0.0")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def health():
    return {"status": "ok", "service": "skill-learning-agent", "ui": "/app"}


@app.get("/app", include_in_schema=False)
def frontend_app():
    return FileResponse(static_dir / "index.html")


app.include_router(router)
