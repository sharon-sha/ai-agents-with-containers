import os

from fastapi import FastAPI

app = FastAPI(title="Docker lab — Phase 3")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "Open /docs for Swagger UI."}


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None) -> dict:
    """Sample route so `/docs` shows path/query params."""
    return {"item_id": item_id, "q": q}


def _port() -> int:
    return int(os.environ.get("PORT", "8000"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=_port())
