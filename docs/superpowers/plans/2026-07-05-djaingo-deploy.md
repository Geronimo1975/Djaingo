# Djaingo Deploy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Django 5 "AI Wave / Wowdash" template as a private GitHub repo that auto-deploys to the `macmini` VPS Docker/Traefik stack on `djaingo.com`, with Postgres + Redis/Celery and the template's known vulnerabilities hardened.

**Architecture:** Django app moves to repo root. A production `docker-compose.prod.yml` (web=gunicorn, nginx=static+proxy, postgres, redis, celery, beat) joins the VPS's shared `gethub_gethub-network`; Traefik routes `djaingo.com` → nginx with automatic Let's Encrypt TLS. GitHub Actions rsyncs source to the VPS on push to `main` and rebuilds the stack.

**Tech Stack:** Django 5.0.7, gunicorn, PostgreSQL 16, Redis 7, Celery, nginx:alpine, Docker Compose, Traefik v2.11, GitHub Actions.

**Key facts discovered (do not re-derive):**
- Template lives at `themeforest-vNlO1S9D-aiwave-django-5-ai-saas-website-dashboard-ui-kit/AI Wave/` relative to repo root; its contents move to root in Task 1.
- Settings module `Wowdash.settings`; WSGI `Wowdash.wsgi:application`; `Wowdash/__init__.py` is empty.
- Config indirection: `wowdash_app/env_cache.py` `get()` reads an `EnvVar` DB table (populated by a seed). It does NOT fall back to `os.environ` — Task 3 fixes that so `.env.prod` drives config.
- Tailwind CSS is **precompiled** (`*/static/**/style.css` exist); no `input.css`/config. **Dockerfile needs no Node** — `collectstatic` ships the CSS.
- No `STATIC_ROOT` in settings yet; Task 3 adds it.
- Celery is **not** present anywhere; Task 4 scaffolds it minimally.
- VPS external network: `gethub_gethub-network`. Traefik TLS resolver: `letsencrypt`. Middleware chain: `secure-headers@file,compress@file,rate-limit@file`. Model stack: `/home/resume/Get_Resume_v2/`.
- An `AuthAndRoleRequiredMiddleware` exists — Task 7 verifies its route coverage before adding decorators.
- SSH alias `macmini` = `root@85.215.69.83`. Deploy target dir: `/home/djaingo/djaingo/`.

**Working directory:** repo root `/Users/get-hub/Projects/Djaingo_com` (git already initialized, branch `main`, spec committed).

---

## File structure (created/modified)

```
djaingo/                      (repo root — Django project moved here in Task 1)
├── manage.py                 modify: none (works from root)
├── Wowdash/
│   ├── __init__.py           modify: import celery_app (Task 4)
│   ├── settings.py           modify: prod config (Task 3), celery config (Task 4)
│   ├── celery.py             create (Task 4)
│   ├── urls.py / wsgi.py / asgi.py
├── wowdash_app/
│   ├── env_cache.py          modify: os.environ fallback (Task 3)
│   ├── tasks.py              create: example task (Task 4)
│   ├── views/wowdash.py      modify: auth decorators (Task 7)
│   └── management/commands/populate_dummy_data.py  modify: drop seeded secrets (Task 7)
├── aiwave/
│   └── views/
│       ├── pages.py          modify: webhook token + markdown sanitize (Task 7)
│       └── authentication.py modify: safe next_url (Task 7)
├── requirements.txt          modify: add gunicorn, psycopg2-binary(has), redis, celery, django-celery-beat, bleach (Task 2/4)
├── Dockerfile                create (Task 5)
├── docker-compose.prod.yml   create (Task 6)
├── .dockerignore             create (Task 2)
├── .env.prod.example         create (Task 2)
├── .gitignore                modify (Task 1)
├── nginx/
│   ├── nginx.conf            create (Task 5)
│   └── conf.d/djaingo.conf   create (Task 5)
└── .github/workflows/deploy.yml  create (Task 8)
```

---

## Task 1: Move the Django project to the repo root

**Files:**
- Move: `themeforest-.../AI Wave/*` → repo root
- Modify: `.gitignore`

- [ ] **Step 1: Move template contents to root (including dotfiles)**

```bash
cd /Users/get-hub/Projects/Djaingo_com
SRC="themeforest-vNlO1S9D-aiwave-django-5-ai-saas-website-dashboard-ui-kit/AI Wave"
# move visible + hidden files, keep docs/ and .git/ intact
rsync -a --exclude='.git' "$SRC"/ ./
# keep the ThemeForest Documentation for reference, drop the now-empty template shell
rm -rf "themeforest-vNlO1S9D-aiwave-django-5-ai-saas-website-dashboard-ui-kit/AI Wave"
```

- [ ] **Step 2: Remove committed secrets & local DB from the tree**

```bash
rm -f .env db.sqlite3
mkdir -p media && touch media/.gitkeep
```

- [ ] **Step 3: Extend `.gitignore` (overwrite with full list)**

```gitignore
.env
.env.prod
*.pyc
__pycache__/
db.sqlite3
staticfiles/
node_modules/
media/*
!media/.gitkeep
logs/*.log
.DS_Store
```

- [ ] **Step 4: Verify Django still resolves from root**

Run: `python -c "import ast,sys; ast.parse(open('manage.py').read()); print('manage.py OK')"`
Expected: `manage.py OK` (no venv needed for this check)

Run: `ls Wowdash/settings.py wowdash_app/env_cache.py aiwave/views/pages.py`
Expected: all three paths listed.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: move Django project to repo root; drop template secrets"
```

---

## Task 2: Dependencies, dockerignore, env template

**Files:**
- Modify: `requirements.txt`
- Create: `.dockerignore`, `.env.prod.example`

- [ ] **Step 1: Append production deps to `requirements.txt`**

Add these lines (psycopg2-binary already present — do not duplicate):

```
gunicorn==22.0.0
redis==5.0.7
celery==5.4.0
django-celery-beat==2.6.0
bleach==6.1.0
```

- [ ] **Step 2: Create `.dockerignore`**

```dockerignore
.git
.github
.env
.env.prod
db.sqlite3
media
staticfiles
__pycache__
*.pyc
node_modules
docs
themeforest-*
Documentation
logs/*.log
.DS_Store
```

- [ ] **Step 3: Create `.env.prod.example`**

```dotenv
# ---- Django ----
SECRET_KEY=CHANGE_ME_generate_50_random_chars
DEBUG=False
ALLOWED_HOSTS=djaingo.com,www.djaingo.com
# ---- Postgres ----
POSTGRES_DB=djaingo
POSTGRES_USER=djaingo
POSTGRES_PASSWORD=CHANGE_ME_strong_password
POSTGRES_HOST=djaingo-postgres
POSTGRES_PORT=5432
# ---- Redis / Celery ----
REDIS_PASSWORD=CHANGE_ME_redis_password
CELERY_BROKER_URL=redis://:CHANGE_ME_redis_password@djaingo-redis:6379/0
CELERY_RESULT_BACKEND=redis://:CHANGE_ME_redis_password@djaingo-redis:6379/1
# ---- App integrations (were in EnvVar seed) ----
GEMINI_API_KEY=
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
# ---- n8n webhook auth (Task 7) ----
N8N_WEBHOOK_TOKEN=CHANGE_ME_shared_secret
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt .dockerignore .env.prod.example
git commit -m "build: add prod deps, dockerignore, env template"
```

---

## Task 3: Production-ready settings

**Files:**
- Modify: `Wowdash/settings.py`
- Modify: `wowdash_app/env_cache.py`

- [ ] **Step 1: `env_cache.get()` — fall back to `os.environ`**

In `wowdash_app/env_cache.py`, replace the `get` function:

```python
def get(key: str, default=None):
    import os
    return _env_vars.get(key) or os.environ.get(key, default)
```

- [ ] **Step 2: Switch `DATABASES` to Postgres-via-env with SQLite fallback**

In `Wowdash/settings.py`, replace the `DATABASES = {...}` block (lines ~156-161):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql' if os.getenv('POSTGRES_HOST')
                  else 'django.db.backends.sqlite3',
        'NAME': os.getenv('POSTGRES_DB', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('POSTGRES_USER', ''),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', ''),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}
```

- [ ] **Step 3: Add `STATIC_ROOT` and proxy/security settings**

In `Wowdash/settings.py`, immediately after the `STATICFILES_DIRS = [...]` block (after line ~190) add:

```python
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Behind Traefik TLS termination
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
```

- [ ] **Step 4: Sanity-check settings parse**

Run: `python -c "import ast; ast.parse(open('Wowdash/settings.py').read()); ast.parse(open('wowdash_app/env_cache.py').read()); print('settings parse OK')"`
Expected: `settings parse OK`

- [ ] **Step 5: Commit**

```bash
git add Wowdash/settings.py wowdash_app/env_cache.py
git commit -m "feat: production settings (Postgres env, STATIC_ROOT, proxy SSL, env fallback)"
```

---

## Task 4: Minimal Celery scaffolding

> YAGNI note: the template ships zero Celery tasks; this wires a working Celery app + one health task so the infra is ready. Do not build tasks that have no caller.

**Files:**
- Create: `Wowdash/celery.py`, `wowdash_app/tasks.py`
- Modify: `Wowdash/__init__.py`, `Wowdash/settings.py`

- [ ] **Step 1: Create `Wowdash/celery.py`**

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Wowdash.settings')

app = Celery('Wowdash')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

- [ ] **Step 2: Wire the app in `Wowdash/__init__.py`**

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

- [ ] **Step 3: Add Celery config + app to settings**

In `Wowdash/settings.py`, add `'django_celery_beat'` to `INSTALLED_APPS` (after `'aiwave',`) and append at end of file:

```python
# ======================
# Celery
# ======================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

- [ ] **Step 4: Create `wowdash_app/tasks.py` (one example task)**

```python
from celery import shared_task


@shared_task
def ping():
    """Health task to verify Celery wiring."""
    return 'pong'
```

- [ ] **Step 5: Verify parse**

Run: `python -c "import ast; [ast.parse(open(f).read()) for f in ['Wowdash/celery.py','Wowdash/__init__.py','wowdash_app/tasks.py']]; print('celery scaffolding parse OK')"`
Expected: `celery scaffolding parse OK`

- [ ] **Step 6: Commit**

```bash
git add Wowdash/celery.py Wowdash/__init__.py Wowdash/settings.py wowdash_app/tasks.py
git commit -m "feat: minimal Celery app + beat scheduler wiring"
```

---

## Task 5: Dockerfile + nginx config

**Files:**
- Create: `Dockerfile`, `nginx/nginx.conf`, `nginx/conf.d/djaingo.conf`

- [ ] **Step 1: Create `Dockerfile`**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/staticfiles /app/media /app/logs

EXPOSE 8000
CMD ["gunicorn", "Wowdash.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
```

- [ ] **Step 2: Create `nginx/nginx.conf`**

```nginx
user nginx;
worker_processes auto;
events { worker_connections 1024; }
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 25m;
    include /etc/nginx/conf.d/*.conf;
}
```

- [ ] **Step 3: Create `nginx/conf.d/djaingo.conf`**

```nginx
upstream djaingo_web {
    server djaingo-web:8000;
}

server {
    listen 80;
    server_name _;

    location /static/ {
        alias /usr/share/nginx/static/;
        expires 30d;
        access_log off;
    }
    location /media/ {
        alias /usr/share/nginx/media/;
        expires 30d;
        access_log off;
    }
    location / {
        proxy_pass http://djaingo_web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
        proxy_redirect off;
    }
}
```

- [ ] **Step 4: Validate nginx config syntax with a throwaway container**

Run: `docker run --rm -v "$PWD/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" -v "$PWD/nginx/conf.d:/etc/nginx/conf.d:ro" nginx:alpine nginx -t`
Expected: `syntax is ok` / `test is successful`

- [ ] **Step 5: Commit**

```bash
git add Dockerfile nginx/
git commit -m "build: Dockerfile (gunicorn) and nginx static+proxy config"
```

---

## Task 6: Production compose stack

**Files:**
- Create: `docker-compose.prod.yml`

- [ ] **Step 1: Create `docker-compose.prod.yml`**

```yaml
services:
  djaingo-web:
    build: { context: ., dockerfile: Dockerfile }
    container_name: djaingo-web
    command: >
      sh -c "python manage.py migrate --noinput &&
             python manage.py collectstatic --noinput &&
             gunicorn Wowdash.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120 --access-logfile - --error-logfile -"
    env_file: [.env.prod]
    volumes:
      - static_files:/app/staticfiles
      - media_files:/app/media
    depends_on:
      djaingo-postgres: { condition: service_healthy }
      djaingo-redis: { condition: service_healthy }
    restart: unless-stopped
    networks: [djaingo-internal, gethub-network]
    labels: ["traefik.enable=false"]
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS -H 'Host: djaingo.com' http://localhost:8000/ >/dev/null || exit 1"]
      interval: 20s
      timeout: 10s
      retries: 5
      start_period: 60s

  djaingo-nginx:
    image: nginx:alpine
    container_name: djaingo-nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - static_files:/usr/share/nginx/static:ro
      - media_files:/usr/share/nginx/media:ro
    depends_on: [djaingo-web]
    restart: unless-stopped
    networks: [djaingo-internal, gethub-network]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.djaingo.rule=Host(`djaingo.com`) || Host(`www.djaingo.com`)"
      - "traefik.http.routers.djaingo.entrypoints=websecure"
      - "traefik.http.routers.djaingo.tls=true"
      - "traefik.http.routers.djaingo.tls.certresolver=letsencrypt"
      - "traefik.http.routers.djaingo.middlewares=djaingo-chain"
      - "traefik.http.middlewares.djaingo-chain.chain.middlewares=secure-headers@file,compress@file,rate-limit@file"
      - "traefik.http.services.djaingo.loadbalancer.server.port=80"
      - "traefik.docker.network=gethub_gethub-network"

  djaingo-postgres:
    image: postgres:16-alpine
    container_name: djaingo-postgres
    env_file: [.env.prod]
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes: [pg_data:/var/lib/postgresql/data]
    restart: unless-stopped
    networks: [djaingo-internal]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  djaingo-redis:
    image: redis:7-alpine
    container_name: djaingo-redis
    env_file: [.env.prod]
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes: [redis_data:/data]
    restart: unless-stopped
    networks: [djaingo-internal]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  djaingo-celery:
    build: { context: ., dockerfile: Dockerfile }
    container_name: djaingo-celery
    command: celery -A Wowdash worker --loglevel=info --concurrency=2
    env_file: [.env.prod]
    depends_on:
      djaingo-redis: { condition: service_healthy }
    restart: unless-stopped
    networks: [djaingo-internal, gethub-network]

  djaingo-beat:
    build: { context: ., dockerfile: Dockerfile }
    container_name: djaingo-beat
    command: celery -A Wowdash beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file: [.env.prod]
    depends_on:
      djaingo-redis: { condition: service_healthy }
    restart: unless-stopped
    networks: [djaingo-internal, gethub-network]

volumes:
  pg_data: { driver: local }
  redis_data: { driver: local }
  static_files: { driver: local }
  media_files: { driver: local }

networks:
  djaingo-internal: { driver: bridge }
  gethub-network:
    external: true
    name: gethub_gethub-network
```

- [ ] **Step 2: Validate compose file locally (config only, no build)**

Run: `docker compose -f docker-compose.prod.yml --env-file /dev/null config -q 2>&1 | head` (external network may warn locally — acceptable; syntax errors are not)
Expected: no YAML/schema errors printed.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.prod.yml
git commit -m "build: production compose stack (web, nginx, postgres, redis, celery, beat)"
```

---

## Task 7: Security hardening (the 5 template findings)

**Files:**
- Modify: `aiwave/views/pages.py`, `wowdash_app/views/wowdash.py`, `aiwave/views/authentication.py`, `wowdash_app/management/commands/populate_dummy_data.py`
- Test: `tests/test_security.py`

- [ ] **Step 1: Write failing security tests**

Create `tests/test_security.py`:

```python
import json
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_n8n_webhook_rejects_without_token(client, settings):
    settings.N8N_WEBHOOK_TOKEN = "secret-token"
    resp = client.post(
        "/aiwave/n8n/create-blog/",
        data=json.dumps({"author_username": "admin"}),
        content_type="application/json",
    )
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_open_redirect_blocked(client):
    User = get_user_model()
    User.objects.create_user(username="u", email="u@x.com", password="pw12345!")
    resp = client.post(
        "/aiwave/signin/?next=https://evil.example.com",
        {"email": "u@x.com", "password": "pw12345!"},
    )
    # must never 302 to an external host
    assert resp.get("Location", "").startswith("https://evil.example.com") is False
```

> Note: confirm the exact URL names/paths from `aiwave/urls.py` before running; adjust the two paths above to the real routes for `n8n_create_blog` and `signin`.

- [ ] **Step 2: Run tests to confirm they fail**

Run: `python -m pytest tests/test_security.py -v`
Expected: FAIL (webhook currently accepts without token; redirect currently unvalidated).

- [ ] **Step 3: Fix #1 — authenticate the n8n webhook** (`aiwave/views/pages.py`)

At the top of `n8n_create_blog` (line ~353, first line inside the function body after `def`), add a constant-time token check before any processing:

```python
import hmac
from django.conf import settings

@csrf_exempt
def n8n_create_blog(request):
    expected = getattr(settings, 'N8N_WEBHOOK_TOKEN', '') or ''
    provided = request.headers.get('X-Webhook-Token', '')
    if not expected or not hmac.compare_digest(provided, expected):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    # ... existing body unchanged ...
```

Also add to `Wowdash/settings.py`: `N8N_WEBHOOK_TOKEN = os.getenv('N8N_WEBHOOK_TOKEN', '')`.

- [ ] **Step 4: Fix #2 — sanitize markdown** (`aiwave/views/pages.py`, line ~126)

Replace:

```python
context['post'].html_content = markdown.markdown(context['post'].content)
```

with:

```python
import bleach
_ALLOWED_TAGS = ['p','br','strong','em','u','a','ul','ol','li','blockquote',
                 'code','pre','h1','h2','h3','h4','h5','h6','img','hr','table',
                 'thead','tbody','tr','th','td']
_ALLOWED_ATTRS = {'a': ['href','title','rel'], 'img': ['src','alt','title']}
context['post'].html_content = bleach.clean(
    markdown.markdown(context['post'].content, extensions=['extra']),
    tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True,
)
```

- [ ] **Step 5: Fix #3 — authorize admin views** (`wowdash_app/views/wowdash.py`)

First verify middleware coverage:

Run: `sed -n '1,60p' wowdash_app/middleware.py`
Expected: inspect whether `AuthAndRoleRequiredMiddleware` already gates these routes. If it does NOT cover the destructive views, add decorators as defense-in-depth.

Add imports at top of `wowdash_app/views/wowdash.py`:

```python
from django.contrib.auth.decorators import login_required, user_passes_test

_staff_only = user_passes_test(lambda u: u.is_active and u.is_staff)
```

Decorate every destructive/admin view (add both lines directly above each `def`): `deleteQuery`, `deleteAllReadInquiries`, `faqCreate`, `faqEdit`, `faqDelete`, `faqToggleVisibility`, `add_team_member`, `delete_team_member`, `edit_team_member`, `blogManagement`, `editBlog`, `blogDelete`, `releaseNoteDelete`:

```python
@login_required
@_staff_only
def blogDelete(request, post_id):
    ...
```

- [ ] **Step 6: Fix #4 — safe redirect** (`aiwave/views/authentication.py`, lines ~71-73)

Replace:

```python
next_url = request.GET.get('next')
if next_url:
    return redirect(next_url)
```

with:

```python
from django.utils.http import url_has_allowed_host_and_scheme
next_url = request.GET.get('next')
if next_url and url_has_allowed_host_and_scheme(
    next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
):
    return redirect(next_url)
```

- [ ] **Step 7: Fix #5 — remove seeded secrets** (`wowdash_app/management/commands/populate_dummy_data.py`)

Delete the `env_vars` dict entries for `OPENAI_API_KEY`, `STRIPE_SECRET_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `JWT_SECRET_KEY`, `ENCRYPTION_KEY` (and any other real-looking keys). If the command needs placeholders, use `'REPLACE_ME_IN_ENV'` values only.

- [ ] **Step 8: Run security tests to confirm they pass**

Run: `python -m pytest tests/test_security.py -v`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add aiwave/views/pages.py wowdash_app/views/wowdash.py aiwave/views/authentication.py wowdash_app/management/commands/populate_dummy_data.py Wowdash/settings.py tests/test_security.py
git commit -m "security: webhook auth, markdown sanitize, admin authz, safe redirect, drop seeded secrets"
```

---

## Task 8: GitHub Actions deploy workflow

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Create `.github/workflows/deploy.yml`**

```yaml
name: Deploy to VPS

on:
  push:
    branches: [main]
  workflow_dispatch:

concurrency:
  group: deploy-prod
  cancel-in-progress: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_deploy
          chmod 600 ~/.ssh/id_deploy
          ssh-keyscan -H "${{ secrets.SSH_HOST }}" >> ~/.ssh/known_hosts

      - name: Rsync source to VPS
        run: |
          rsync -az --delete \
            -e "ssh -i ~/.ssh/id_deploy" \
            --exclude '.git' --exclude '.github' --exclude '.env*' \
            --exclude 'media' --exclude 'staticfiles' --exclude 'db.sqlite3' \
            --exclude '__pycache__' --exclude 'docs' --exclude 'Documentation' \
            ./ "${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }}:/home/djaingo/djaingo/"

      - name: Build & restart stack
        run: |
          ssh -i ~/.ssh/id_deploy "${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }}" \
            'cd /home/djaingo/djaingo && \
             docker compose -f docker-compose.prod.yml build && \
             docker compose -f docker-compose.prod.yml up -d && \
             docker compose -f docker-compose.prod.yml exec -T djaingo-web python manage.py migrate --noinput && \
             docker compose -f docker-compose.prod.yml exec -T djaingo-web python manage.py collectstatic --noinput'
```

- [ ] **Step 2: Lint the workflow YAML**

Run: `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/deploy.yml')); print('workflow YAML OK')"`
Expected: `workflow YAML OK`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: GitHub Actions rsync deploy to VPS on push to main"
```

---

## Task 9: Create the private GitHub repo and push

**Files:** none (remote setup)

- [ ] **Step 1: Create the private repo under Geronimo1975**

Run: `gh repo create Geronimo1975/djaingo --private --source=. --remote=origin --description "Django 5 AI SaaS (Djaingo) — deploys to macmini VPS"`
Expected: repo created, `origin` remote added.

- [ ] **Step 2: Generate a dedicated deploy SSH keypair (local, not committed)**

```bash
ssh-keygen -t ed25519 -f ~/.ssh/djaingo_deploy -N "" -C "djaingo-github-actions"
ssh-copy-id -i ~/.ssh/djaingo_deploy.pub macmini   # or append pubkey to root@VPS authorized_keys
```

- [ ] **Step 3: Add GitHub Secrets**

```bash
gh secret set SSH_HOST -b "85.215.69.83" -R Geronimo1975/djaingo
gh secret set SSH_USER -b "root" -R Geronimo1975/djaingo
gh secret set SSH_PRIVATE_KEY < ~/.ssh/djaingo_deploy -R Geronimo1975/djaingo
```

- [ ] **Step 4: Push `main` (this triggers the first Actions run — expect it to need the VPS bootstrap from Task 10 first; if it runs before bootstrap, re-run after)**

```bash
git push -u origin main
```

Expected: branch pushed; Actions workflow appears under the repo.

---

## Task 10: VPS bootstrap and first deploy

**Files:** none (server setup); run these interactively.

- [ ] **Step 1: Re-confirm DNS resolves to the VPS (blocking for TLS)**

Run: `ssh macmini 'echo "A: $(dig +short @8.8.8.8 djaingo.com A) / www: $(dig +short @8.8.8.8 www.djaingo.com A)"'`
Expected: both print `85.215.69.83`. If empty, STOP — fix DNS before continuing (Traefik cannot issue the Let's Encrypt cert).

- [ ] **Step 2: Create the target dir and author `.env.prod` on the VPS**

```bash
ssh macmini 'mkdir -p /home/djaingo/djaingo'
# Copy the example, then fill REAL secrets on the server (never commit):
scp .env.prod.example macmini:/home/djaingo/djaingo/.env.prod
ssh macmini 'nano /home/djaingo/djaingo/.env.prod'   # set SECRET_KEY, POSTGRES_PASSWORD, REDIS_PASSWORD, CELERY_BROKER_URL, N8N_WEBHOOK_TOKEN, GEMINI_API_KEY, email creds
```

- [ ] **Step 3: Confirm no other Traefik router already claims the domain**

Run: `ssh macmini "docker ps -q | xargs -r docker inspect -f '{{.Name}} {{index .Config.Labels \"traefik.http.routers.djaingo.rule\"}}' 2>/dev/null | grep -i djaingo || echo 'no existing djaingo router'"`
Expected: `no existing djaingo router`.

- [ ] **Step 4: Trigger the deploy (via Actions or manually) and build the stack**

Run: `gh workflow run "Deploy to VPS" -R Geronimo1975/djaingo` (or `git commit --allow-empty -m "ci: trigger deploy" && git push`)
Then watch: `gh run watch -R Geronimo1975/djaingo`
Expected: build + up succeed; migrate + collectstatic run without error.

- [ ] **Step 5: Create the Django superuser**

Run: `ssh macmini 'cd /home/djaingo/djaingo && docker compose -f docker-compose.prod.yml exec djaingo-web python manage.py createsuperuser'`
Expected: superuser created.

- [ ] **Step 6: Verify TLS + site end-to-end**

Run: `curl -sSI https://djaingo.com | head -5`
Expected: `HTTP/2 200` (or a 302 to a login route) with a valid Let's Encrypt cert (no cert warning).

Run: `curl -sSI https://djaingo.com/admin/ | head -3`
Expected: `200` or `302` to the admin login.

- [ ] **Step 7: Verify Celery worker is healthy**

Run: `ssh macmini 'cd /home/djaingo/djaingo && docker compose -f docker-compose.prod.yml exec -T djaingo-web python -c "from wowdash_app.tasks import ping; print(ping.delay().get(timeout=10))"'`
Expected: `pong`.

---

## Self-review notes

- **Spec coverage:** repo (T1,T9), Docker stack web/nginx/pg/redis/celery/beat (T4,T5,T6), Traefik labels/network/TLS (T6), CI/CD rsync+build (T8,T9), Postgres (T3,T6), Redis+Celery (T4,T6), settings hardening incl. STATIC_ROOT (T3), all 5 security findings (T7), DNS/bootstrap/superuser/TLS verify (T10), secrets excluded from git (T1,T2). ✅
- **YAGNI flag:** Celery has no real tasks yet (T4) — scaffolding only; do not invent tasks.
- **Verify-before-run flags:** exact URL routes for the two security tests (T7 Step 1) and middleware coverage (T7 Step 5) must be confirmed against the code before relying on them.
- **Ordering caveat:** T9 push can trigger Actions before T10 bootstrap exists; deploy is idempotent — re-run after `.env.prod` and dir are in place.
