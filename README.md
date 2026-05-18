# outer

Canonical deploy/playground repo at **`/home/sha/outer`**. **`docker-lab/`** stays in sync with `~/ai agents with containers/docker-lab` when you ask to “use outer.”

## Quickstart

From **`/home/sha/outer`** (repo root):

```bash
docker compose up --build
```

(`compose.yaml` defines **`web` + `db`** together; **`web` shares `db`'s network** → **`DATABASE_URL`** uses **`127.0.0.1`** inside containers. Ports **8080** (API) and **`5433`**→5432 (Postgres on host — avoids clashes with a local Postgres on **5432**) are mapped on **`db`**. Override with **`LAB_PG_PUBLISH`** env if needed. You can also run `cd docker-lab && docker compose up --build`.)

- Swagger: http://localhost:8080/docs  
- DB ping: http://localhost:8080/db/ping  

## Deploy

- **Render:** repo-root **`render.yaml`** Blueprint — Postgres + **`DATABASE_URL`**. Sync after push.  
- **Railway (optional):** Root Directory **`docker-lab/backend`** (see **`docker-lab/README.md`**).

Do not commit **`.env`** — use **`docker-lab/.env.example`** as a template only.
