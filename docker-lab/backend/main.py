import os
from collections.abc import Generator
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


def _is_render() -> bool:
    """Render sets these on native services; Docker deploys may omit them."""
    if os.environ.get("RENDER", "").lower() in {"true", "1", "yes"}:
        return True
    if os.environ.get("RENDER_SERVICE_ID"):
        return True
    if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
        return True
    return False


def _bootstrap_env() -> None:
    """Load docker-lab/.env for local dev. Render injects env vars — never rely on .env in prod."""
    if _is_render():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    here = Path(__file__).resolve().parent
    for path in (here / ".env", here.parent / ".env"):
        if path.is_file():
            load_dotenv(path, override=False)


_bootstrap_env()


def _pg_hostname(url: str) -> str | None:
    for prefix in ("postgresql+psycopg2://", "postgresql://", "postgres://"):
        if url.startswith(prefix):
            u = url.replace(prefix, "postgresql://", 1)
            return urlparse(u).hostname
    return urlparse(url).hostname


def _normalize_sqlalchemy_url(raw: str) -> str:
    if raw.startswith("postgresql+psycopg2://"):
        return raw
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+psycopg2://", 1)
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+psycopg2://", 1)
    return raw


def _allow_loopback_db() -> bool:
    return os.environ.get("ALLOW_LOOPBACK_DATABASE", "").lower() in {"1", "true", "yes"}


def _raw_database_url_string() -> str:
    """Prefer env; optional file path; Render Docker secret files under /etc/secrets/."""
    direct = (os.environ.get("DATABASE_URL") or "").strip()
    if direct:
        return direct
    path = (os.environ.get("DATABASE_URL_FILE") or "").strip()
    if path:
        p = Path(path)
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    for candidate in (Path("/etc/secrets/DATABASE_URL"), Path("/etc/secrets/database_url")):
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    return ""


def _database_url() -> str:
    raw = _raw_database_url_string()
    if not raw:
        hint = (
            "Docker Compose should set DATABASE_URL on the web service. "
            "On Render: PostgreSQL → Internal Database URL → Web service → Environment "
            "(runtime variables, not build-only) → key exactly DATABASE_URL → "
            "Save *and deploy* (not Save only). "
            "If the web service was not created from this repo Blueprint, render.yaml fromDatabase "
            "does not apply. "
            "URL host must be your Render Postgres host (private URLs often look like dpg-…@…/db)."
        )
        if _is_render():
            related = sorted(
                k
                for k in os.environ
                if any(
                    x in k.upper()
                    for x in ("DATABASE", "POSTGRES", "POSTGRE", "SQL", "PG")
                )
            )
            extra = f" Env keys mentioning DB/postgres: {related or 'none'}."
            raise RuntimeError(f"DATABASE_URL is missing on Render.{extra} {hint}")
        raise RuntimeError(f"DATABASE_URL is missing. {hint}")

    out = _normalize_sqlalchemy_url(raw)
    host = _pg_hostname(out)

    if host in (None, "localhost", "127.0.0.1", "::1"):
        if _is_render():
            raise RuntimeError(
                "DATABASE_URL points at localhost, but Render Postgres is on another host. "
                "Paste the **Internal Database URL** from your Render PostgreSQL service "
                "(host looks like dpg-xxxx.a.region-postgres.render.com)."
            )
        if not _allow_loopback_db():
            raise RuntimeError(
                "DATABASE_URL uses localhost but ALLOW_LOOPBACK_DATABASE is not set. "
                "Local Compose sets both (see compose.yaml)."
            )

    return out


class Base(DeclarativeBase):
    pass


class DbItem(Base):
    __tablename__ = "db_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(index=True)


engine = create_engine(_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Docker lab — Phase 5", lifespan=lifespan)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "Open /docs for Swagger UI."}


@app.get("/health")
def health() -> dict[str, bool]:
    """Light probe for Render/Railway — does not touch the database."""
    return {"ok": True}


@app.get("/db/ping")
def db_ping() -> dict[str, bool]:
    """True when Postgres accepts connections."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"db": True}
    except Exception:
        raise HTTPException(status_code=503, detail="database unreachable")


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


@app.get("/db/items")
def list_items(db: Session = Depends(get_db)) -> list[dict[str, int | str]]:
    rows = db.scalars(select(DbItem).order_by(DbItem.id)).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@app.post("/db/items", status_code=201)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)) -> dict[str, int | str]:
    row = DbItem(name=payload.name.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name}


@app.get("/db/items/{item_id}")
def read_db_item(item_id: int, db: Session = Depends(get_db)) -> dict[str, int | str]:
    row = db.get(DbItem, item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": row.id, "name": row.name}


def _port() -> int:
    return int(os.environ.get("PORT", "8000"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=_port())
