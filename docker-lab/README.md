# Docker lab — local & Railway

## Local (Compose)

From **`docker-lab/`**:

```bash
docker compose up --build
```

- API: http://localhost:8080  
- Swagger: http://localhost:8080/docs  

---

## Phase 4 — GitHub + Railway

### 1. Push to GitHub

```bash
git init   # if needed
git remote add origin git@github.com:YOUR_USER/YOUR_REPO.git
git add .
git commit -m "docker-lab: FastAPI phase 3"
git push -u origin main
```

Use **`main`** or whichever branch Railway will deploy.

### 2. Create the Railway service

1. [Railway](https://railway.app) → **New project** → **Deploy from GitHub**.
2. Install the GitHub app / authorize if prompted.
3. Select your repository and branch.

### 3. Root directory (critical)

Railway builds **only inside** the folder you set as **Root Directory**. It must be the folder that contains **`Dockerfile`**.

| Repo layout | Railway **Root Directory** |
|-------------|----------------------------|
| This workspace (**monorepo**): `docker-lab/backend/Dockerfile` | `docker-lab/backend` |
| Standalone deploy repo: top-level `backend/Dockerfile` | `backend` |
| App files **at repo root** (only `Dockerfile` + `main.py` here) | Leave empty or `.` |

Wrong roots (`deploy_ai_agent/backend`, repo root when Dockerfile is nested, etc.) produce **“directory does not exist”** or **Railpack** guessing wrong — fix the root first.

### 4. Builder & build logs

Open **Deployments → Build Logs** and confirm:

- Message like **“Using detected Dockerfile!”** (Docker build path).

If Railway tries **Railpack** instead of Docker while you intend Docker:

- Ensure **Root Directory** points at the folder that actually contains **`Dockerfile`**.
- Remove conflicting **`railway.json`** **`build.builder`** overrides unless you mean to use them ([Railway Dockerfile docs](https://docs.railway.com/builds/dockerfiles)).

### 5. Public URL & health

1. Service **Settings → Networking → Generate Domain**.
2. Visit **`https://YOUR_DOMAIN/docs`** — Swagger should load.

Railway sets **`PORT`**; the image **`CMD`** uses **`${PORT:-8000}`**, so no manual `PORT` variable is required for basic runs ([FastAPI on Railway](https://docs.railway.com/guides/fastapi)).

### 6. Checkpoint

| Check | OK when |
|-------|---------|
| Local | `docker compose up` → `/docs` works on localhost |
| Railway | Build succeeds → domain opens → `/docs` loads |

Same codebase + same Dockerfile → parity achieved.

### Optional: config-as-code

[`backend/railway.json`](backend/railway.json) in this folder adds a **`/docs`** healthcheck. If Railway doesn’t pick it up, set **Config file path** in service settings to **`docker-lab/backend/railway.json`** (monorepo) or **`backend/railway.json`** (standalone), per [Config as code](https://docs.railway.com/deploy/config-as-code).

---

## Troubleshooting

| Symptom | Likely fix |
|---------|------------|
| Directory … does not exist | Correct **Root Directory** to path containing `Dockerfile`. |
| Build succeeds, browser error | **Generate Domain**; ensure app binds **`0.0.0.0`** (already true in this lab). |
| Wrong builder | Dockerfile at wrong depth or Railpack override — fix root / config. |

---

## Phase 5 — Data & persistence (Compose + Render)

### Ephemeral vs persisted

| What | Survives container restart? |
|------|-----------------------------|
| Files **inside** the app container filesystem only | **No** (unless copied into an image layer). |
| **Docker volume** mounted at Postgres data dir (`postgres_data`) | **Yes** — DB files live on the host volume. |
| Render **managed Postgres** disk | **Yes** — Render operates the cluster + storage. |

### Local (Compose)

`compose.yaml` adds **`db`** (`postgres:16-alpine`) + named volume **`postgres_data`**.

```bash
docker compose down          # stops containers; volume keeps data
docker compose down -v       # deletes volume → empty DB next up
```

Checkpoint flow:

1. `docker compose up --build`
2. **POST** http://localhost:8080/db/items with JSON `{"name":"hello"}`
3. **GET** http://localhost:8080/db/items — row appears
4. **GET** http://localhost:8080/db/ping — `{"db":true}`
5. `docker compose restart web` — rows still there (data is in **`postgres_data`**)

Secrets: keep real credentials out of git — use **`docker-lab/.env.example`** as a template only; **`DATABASE_URL`** for Compose is inlined for local dev convenience.

### Render (hosted Postgres)

Repo-root **`render.yaml`** declares **`docker-lab-postgres`** and wires **`DATABASE_URL`** via **`fromDatabase.connectionString`** (same region **`oregon`** as the web service).

After you push:

```bash
git add docker-lab render.yaml .gitignore
git commit -m "Phase 5: Postgres + Render DATABASE_URL"
git push origin main
```

In Render → **Blueprints** → apply/sync so both **Postgres** and **web** pick up the changes (first deploy may take longer while Postgres provisions).

Verify:

- https://`your-service`.onrender.com/db/ping → `{"db":true}`
- POST/GET `/db/items` on the public URL

Render **free** Postgres tier may still spin down / have limits — upgrade **`plan`** on the database block when you outgrow it ([pricing](https://render.com/pricing#postgresql)).
