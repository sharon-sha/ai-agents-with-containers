import os
from collections.abc import Generator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


def _database_url() -> str:
    raw = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/docker_lab",
    )
    if raw.startswith("postgresql+psycopg2://"):
        return raw
    # Render sometimes supplies postgres://; SQLAlchemy wants postgresql+psycopg2.
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+psycopg2://", 1)
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+psycopg2://", 1)
    return raw


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
