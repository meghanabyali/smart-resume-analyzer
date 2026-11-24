# Deployment Guide (Render)

The whole application (pages + API) is one Flask service, so it is deployed to **Render** as a single web service. Netlify/Vercel are only relevant if a separately hosted frontend is added later (then set `CORS_ORIGINS`).

## Production setup in this repository

| File | Purpose |
|---|---|
| `requirements.txt` | Pinned dependencies, including the spaCy `en_core_web_sm` model wheel and Gunicorn |
| `gunicorn.conf.py` | Binds to `$PORT`, 2 workers × 2 threads, 120 s timeout, `preload_app` so spaCy loads once |
| `render.yaml` | Render Blueprint: build/start commands, health check, env vars, persistent disk |
| `/health` | Health endpoint used by Render |

Start command: `gunicorn run:app` (Gunicorn reads `gunicorn.conf.py` automatically).
Build command: `pip install -r requirements.txt && python -m nltk.downloader -d data/nltk_data stopwords`

## Option A – Blueprint with persistent disk (recommended)

1. Push the repository to GitHub (see the README).
2. In Render: **New → Blueprint**, select the repository. Render reads `render.yaml`.
3. Confirm the service. Render generates `SECRET_KEY` and mounts a 1 GB disk at `/var/data`, where the SQLite database (`DATABASE_URL=sqlite:////var/data/resume_analyzer.db`) and uploads (`UPLOAD_FOLDER=/var/data/uploads`) live.
4. Wait for the build, then open `https://<your-service>.onrender.com/health` – it should return `{"status": "ok", ...}`.

Persistent disks require a paid instance type (the blueprint uses `starter`). A disk-backed service runs a single instance.

## Option B – Free instance (demo only)

1. **New → Web Service**, connect the repository, runtime Python.
2. Build command and start command as above; set `PYTHON_VERSION=3.11.9` and a random `SECRET_KEY`.
3. Leave `DATABASE_URL` and `UPLOAD_FOLDER` empty.

**SQLite limitation:** a free instance's filesystem is *ephemeral* – the database and uploaded files are wiped on every redeploy and restart (free services also sleep when idle). That is acceptable for a demo because each analysis is self-contained, but links to old dashboards will stop working. For persistence without a disk, set `DATABASE_URL` to a managed PostgreSQL database (`postgresql://…`, add `psycopg2-binary` to requirements) and `KEEP_UPLOADED_FILES=false` so no files need to survive.

## Environment variables

| Variable | Default | Notes |
|---|---|---|
| `SECRET_KEY` | dev value | **Must** be set in production |
| `DATABASE_URL` | `sqlite:///instance/resume_analyzer.db` | `postgres://` is auto-rewritten to `postgresql://` |
| `UPLOAD_FOLDER` | `./uploads` | |
| `KEEP_UPLOADED_FILES` | `true` | `false` = keep only extracted text |
| `MAX_UPLOAD_MB` | `5` | |
| `RETENTION_DAYS` | `7` | `0` disables automatic purge |
| `CORS_ORIGINS` | empty | Comma-separated origins for a separate frontend |
| `WEB_CONCURRENCY` | `2` | Gunicorn workers |

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Build fails installing `en_core_web_sm` | The model is installed from a GitHub release URL; retry the build, or check outbound network access |
| `Worker timeout` / 502 on first request | spaCy loading on a cold start; `timeout = 120` and `preload_app` handle this – increase `timeout` if needed |
| Out of memory on free tier | Set `WEB_CONCURRENCY=1` |
| Old dashboards return 404 | Ephemeral storage was reset (Option B) or the retention period expired |
| `/health` returns 503 | Database path not writable – check that the disk is mounted at `/var/data` |
| Styles missing | The pages load Bootstrap/Chart.js from `cdn.jsdelivr.net`; check network/CSP |
| 413 errors | File exceeds `MAX_UPLOAD_MB` |

## Note on Windows

Gunicorn does not run on Windows. Locally, use `python run.py` (Flask's server) – Render runs Linux, where Gunicorn works.

## Deployment status

Deployment requires the project owner's Render and GitHub accounts. **No deployment URL exists yet**; add it to the README once the service is live.
