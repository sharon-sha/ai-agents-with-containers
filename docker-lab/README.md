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
