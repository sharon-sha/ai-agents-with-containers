# outer

Canonical deploy/playground repo at **`/home/sha/outer`**. **`docker-lab/`** stays in sync with `~/ai agents with containers/docker-lab` when you ask to “use outer.”

## Quickstart

```bash
cd docker-lab
docker compose up --build
```

- Swagger: http://localhost:8080/docs  
- DB ping: http://localhost:8080/db/ping  

## Deploy

- **Render:** repo-root **`render.yaml`** Blueprint — Postgres + **`DATABASE_URL`**. Sync after push.  
- **Railway (optional):** Root Directory **`docker-lab/backend`** (see **`docker-lab/README.md`**).

Do not commit **`.env`** — use **`docker-lab/.env.example`** as a template only.
