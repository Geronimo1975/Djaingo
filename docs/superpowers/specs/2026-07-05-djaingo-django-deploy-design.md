# Djaingo — Django Deploy Design (GitHub → rsync → VPS Docker/Traefik)

**Date:** 2026-07-05
**Author:** George (Geronimo1975) + Claude
**Status:** Approved design → implementation planning

---

## 1. Summary

Deploy the **Djaingo** project — a Django 5 AI SaaS (ThemeForest "AI Wave / Wowdash"
template) — to the `macmini` VPS (`85.215.69.83`, Ubuntu 24.04, Plesk). Source of
truth is a **private GitHub repo `djaingo`** under account `Geronimo1975`. On every
push to `main`, **GitHub Actions** rsyncs the source to the VPS and rebuilds the
Docker stack. The app is fronted by the VPS's existing **Traefik v2.11** reverse
proxy on domain **djaingo.com**, with automatic Let's Encrypt TLS.

> Note: the original request said "WordPress", but the supplied template is Django 5.
> Confirmed with the user — this is a **Django** deployment; "WordPress" was a slip.

## 2. Current state (discovered)

### Local
- `/Users/get-hub/Projects/Djaingo_com/` — no git repo yet.
- Template at `themeforest-vNlO1S9D-aiwave-django-5-.../AI Wave/`:
  - Django 5.0.7, DRF, allauth, django-tailwind, python-dotenv.
  - Settings module `Wowdash.settings`; WSGI `Wowdash.wsgi:application`.
  - Config via env: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`.
  - DB: SQLite default; `psycopg2-binary` already in requirements (Postgres-ready).
  - Extras: n8n auto-blog integration, `google-generativeai` (Gemini), `twilio`.
  - Ships a committed `.env` with real-looking secrets → **must be excluded**.

### VPS (`macmini` = 85.215.69.83)
- Ubuntu 24.04, Plesk, root access via SSH alias `macmini` (key `id_ed25519_minimac`).
- Docker + `docker compose` v5.3.0; rsync 3.2.7.
- **Ports 80/443 owned by `gethub-traefik` (traefik:v2.11)** — the shared reverse proxy.
- External Docker network: **`gethub_gethub-network`**.
- ~40 containers already running (rotocon, cleosdeco, resume, gmx, social_media, n8n…).
- Standardized per-app pattern exists (model: `/home/resume/Get_Resume_v2/`).
- `djaingo.com` not yet in Plesk; no `djaingo` dir on VPS yet.

## 3. Decisions

| Topic | Decision |
|-------|----------|
| Platform | Django (existing template) |
| Repo | Private, `Geronimo1975/djaingo` |
| Domain | `djaingo.com` (+ `www`) |
| Runtime | Docker + existing Traefik reverse proxy |
| Deploy | GitHub Actions → rsync → VPS build |
| Database | PostgreSQL in a container (`postgres:16-alpine`) |
| Async | Redis + Celery worker + Celery Beat from the start |

## 4. Repo structure (`Geronimo1975/djaingo`, private)

Django project moves from `AI Wave/` to repo root:

```
djaingo/
├── manage.py
├── Wowdash/                  # settings, urls, wsgi, asgi
├── wowdash_app/  aiwave/  Bal/  Dal/  Wowdash(app)/  # Django apps
├── media/                    # runtime (gitignored contents)
├── requirements.txt
├── package.json / tailwind   # Tailwind build inputs
├── Dockerfile
├── docker-compose.prod.yml
├── .dockerignore
├── .gitignore
├── .env.prod.example
├── nginx/
│   ├── nginx.conf
│   └── conf.d/djaingo.conf
├── .github/workflows/deploy.yml
└── docs/superpowers/specs/2026-07-05-djaingo-django-deploy-design.md
```

**Gitignored (never committed):** `.env`, `.env.prod`, `db.sqlite3`, `media/*`
(keep `.gitkeep`), `__pycache__/`, `*.pyc`, `staticfiles/`, `node_modules/`.

**Settings hardening (added):** define `STATIC_ROOT = BASE_DIR/'staticfiles'`;
switch `DATABASES` to read `DATABASE_URL`/Postgres env vars with SQLite fallback;
keep `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` from env.

## 5. Production stack — `docker-compose.prod.yml`

Mirrors the VPS convention (`Get_Resume_v2`). Lives on VPS at `/home/djaingo/djaingo/`.

Services:
- **djaingo-web** — `gunicorn Wowdash.wsgi:application --bind 0.0.0.0:8000 --workers 3`;
  `env_file: .env.prod`; volumes `static_files:/app/staticfiles`, `media_files:/app/media`;
  networks `djaingo-internal` + `gethub-network`; `traefik.enable=false`; healthcheck.
- **djaingo-nginx** — `nginx:alpine`; serves static/media + proxies to web; networks
  `djaingo-internal` + `gethub-network`; **Traefik labels**:
  - `traefik.enable=true`
  - `Host(\`djaingo.com\`) || Host(\`www.djaingo.com\`)`
  - `entrypoints=websecure`, `tls=true`, `tls.certresolver=letsencrypt`
  - `middlewares=djaingo-chain` → `secure-headers@file,compress@file,rate-limit@file`
  - `services...server.port=80`, `traefik.docker.network=gethub_gethub-network`
- **djaingo-postgres** — `postgres:16-alpine`; volume `pg_data`; internal network only; healthcheck.
- **djaingo-redis** — `redis:7-alpine` with password + appendonly; internal network only.
- **djaingo-celery** — `celery -A Wowdash worker`; internal + gethub networks.
- **djaingo-beat** — `celery -A Wowdash beat`; internal + gethub networks.

> Celery app label: verify the Celery app module (`Wowdash` vs another) during
> implementation; the template may need a `celery.py` + `__init__.py` wiring if absent.

Networks:
```yaml
networks:
  djaingo-internal: { driver: bridge }
  gethub-network:   { external: true, name: gethub_gethub-network }
```

No host port collision: our gunicorn is container-internal (host `:8000` gunicorn is
an unrelated non-Docker process).

## 6. CI/CD — `.github/workflows/deploy.yml`

Trigger: `push` to `main` (+ manual `workflow_dispatch`).

Steps:
1. Checkout.
2. Install SSH key from secret; add `85.215.69.83` to known_hosts.
3. `rsync -az --delete` (excluding `.git`, `.env*`, `media`, `__pycache__`,
   `staticfiles`, `db.sqlite3`) to `root@85.215.69.83:/home/djaingo/djaingo/`.
4. Over SSH on VPS:
   `docker compose -f docker-compose.prod.yml build`
   → `up -d`
   → `exec djaingo-web python manage.py migrate --noinput`
   → `exec djaingo-web python manage.py collectstatic --noinput`.

**GitHub Secrets:** `SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`.
Django/app secrets (`SECRET_KEY`, DB password, Gemini/Twilio keys) live only in
`/home/djaingo/djaingo/.env.prod` on the VPS, created once by hand, never in git.

## 7. First-deploy bootstrap (one-time, manual)

1. Point DNS: `djaingo.com` + `www.djaingo.com` A records → `85.215.69.83`
   (**blocking** — Traefik cannot issue LE cert otherwise).
2. Create `/home/djaingo/djaingo/` on VPS; author `.env.prod` (SECRET_KEY, Postgres
   creds, Redis password, ALLOWED_HOSTS=`djaingo.com,www.djaingo.com`, DEBUG=False,
   API keys).
3. First `docker compose build && up -d`, then `migrate`, `collectstatic`,
   `createsuperuser`.
4. Verify TLS + site, then hand ongoing deploys to GitHub Actions.

## 8. Out of scope (YAGNI)

- Plesk-managed vhost for the domain (Traefik handles routing/TLS directly).
- Data migration from the template's `db.sqlite3` (fresh Postgres; re-seed via admin
  or a one-off `dumpdata`/`loaddata` if the user wants the demo content).
- Staging environment (can add a `docker-compose.staging.yml` later).

## 8b. Security hardening (pre-launch, from automated review)

Pre-existing vulnerabilities in the ThemeForest template that MUST be fixed before
the app is public on `djaingo.com`. Tracked here; addressed during implementation.

| Sev | File | Issue | Fix |
|-----|------|-------|-----|
| HIGH | `aiwave/views/pages.py` `n8n_create_blog` | `@csrf_exempt` webhook trusts body `author_username` → author impersonation / unauth publish | Require `X-Webhook-Token` header, constant-time compare vs server secret; reject if missing |
| HIGH | `aiwave/views/pages.py` | `markdown.markdown(content)` rendered with `|safe` → stored XSS | `bleach.clean()` with allowlist, or markdown + sanitizer |
| HIGH | `wowdash_app/views/wowdash.py` `blogDelete` (+ other admin views) | No auth/authorization → IDOR, unauth deletion | `@login_required` + `@user_passes_test(is_staff)` on all admin views |
| MED | `aiwave/views/authentication.py` | `redirect(next_url)` unvalidated → open redirect | `url_has_allowed_host_and_scheme(...)` before redirect |
| MED | `wowdash_app/management/commands/populate_dummy_data.py` | Seeds placeholder secrets (`JWT_SECRET_KEY`, AWS, Stripe) | Remove from seed / gate behind `DEBUG`; never seed real secret keys |

These are added to the implementation plan as a "harden template" work item that
runs before (or alongside) the first production deploy.

## 9. Risks / open items

- **DNS** must resolve to the VPS before first deploy (couldn't verify from local).
- **Celery wiring** may be missing in the template — confirm during implementation.
- Template `.env` contains secrets — ensure it is never pushed to GitHub.
- Confirm no other Traefik router already claims `djaingo.com`.
