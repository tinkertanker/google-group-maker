# Google Group Maker

CLI and FastAPI web app for managing Google Groups via the Google Admin SDK Directory API.

## Setup

- Python 3.9; project venv in `venv/` (`source venv/bin/activate`)
- `pip install -r requirements.txt` (CLI) plus `-r requirements-web.txt` (web app)
- Copy `.env.example` to `.env`. See `docs/CREDENTIALS.md` for service account setup.
- Credentials resolve in order: `GOOGLE_SERVICE_ACCOUNT_JSON` env var, then `service-account-credentials.json` in the repo root (gitignored — never commit it).
- The service account needs domain-wide delegation; API calls impersonate `ADMIN_EMAIL` (falling back to `DEFAULT_EMAIL`).

## Commands

```bash
# CLI — subcommands: create, list, members, add, remove, delete, rename
./groupmaker.py create <group> <trainer-email>   # details: ./groupmaker.py <cmd> -h
./groupmaker.py list --query test

# Web app (port 8000)
uvicorn web.app:app --reload
```

## Architecture

- `groupmaker_core.py` — all business logic. Functions return `OperationResult` / `ValidationResult` / `CredentialsResult` dataclasses and never print. Both interfaces import it.
- `groupmaker.py` — argparse CLI; owns all user-facing output.
- `web/` — FastAPI + Jinja2 + htmx + Tailwind (CDN)
  - `app.py` — app setup, session middleware, router registration
  - `dependencies.py` — `require_auth`, `get_google_service`, flash helpers, `AVAILABLE_DOMAINS`
  - `routers/` — `auth.py` (Google OAuth), `groups.py`, `members.py`
  - `templates/`, `static/`, `Dockerfile`

### Conventions

- Functional core, imperative shell: new behaviour goes in `groupmaker_core.py` returning dataclasses; printing and request handling stay in the interface layer.
- Type hints, PEP 8, British spelling in user-facing copy.
- Group identifiers accept `name` or `name@domain`. Domain precedence: `@` in the name → `--domain` flag → `GOOGLE_GROUP_DOMAIN` → built-in default.
- The web app manages multiple Workspace domains — the allowed list is `AVAILABLE_DOMAINS` in `web/dependencies.py`; the groups list page aggregates all of them. The CLI only queries one domain at a time.
- `update_member_role` exists in core but is not wired into the CLI.
- Web auth is Google OAuth for the logged-in user; Google API calls always use the service account delegated to `ADMIN_EMAIL`, not the user's identity.

## Testing

There is no test suite and no linter config. Verification is manual against the **live** Google API — always use throwaway groups (`test-*-delete-me`) and clean up afterwards:

```bash
./groupmaker.py create test-x-delete-me someone@example.com --skip-self
./groupmaker.py delete test-x-delete-me
```

Gotchas:

- "Resource Not Found" right after creating a group is propagation delay — `ensure_group_exists` and `add_member` already retry; don't add more sleeps.
- Auth failures: check which credential source `load_credentials` picked, and that `ADMIN_EMAIL` is a Workspace admin.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `DEFAULT_EMAIL` | yes | Your email; fallback for `ADMIN_EMAIL` |
| `ADMIN_EMAIL` | no | Delegation subject for API calls |
| `GOOGLE_GROUP_DOMAIN` | no | Default group domain |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | no* | Service account JSON (*or use the credentials file) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | web | OAuth credentials |
| `ALLOWED_DOMAIN` | web | Comma-separated list of allowed login domains |
| `SESSION_SECRET` | web | Session signing key |
| `API_KEY` | web | Master token for `/api/*` (bootstrap/recovery) |
| `API_KEYS_DB` | web | SQLite path for minted keys (default `data/apikeys.db`, a Docker volume) |

## HTTP API

Token-authenticated JSON API for automation (Slack workflows, scripts). Safe actions only — delete, rename, remove member and role changes stay in the web UI. Auth: `X-API-Key` header. Implemented in `web/routers/api.py`.

Any logged-in user can mint keys at `/keys` — keys are stored hashed in `web/apikeys.py`'s SQLite DB, shown once at creation, and every API call is written to the audit log shown on that page. Revoke from `/keys`; the env `API_KEY` remains as a master key.

Interactive docs: `/docs` (Swagger — click Authorize and paste a key to try endpoints), `/redoc`, `/openapi.json`. These are public; they expose schemas only.

```bash
# List groups / members
curl -H "X-API-Key: $API_KEY" "https://groups.tk.sg/api/groups?domain=tinkercademy.com"
curl -H "X-API-Key: $API_KEY" "https://groups.tk.sg/api/groups/name@domain.com/members"

# Create a group (members added as MEMBER)
curl -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"name":"new-group","domain":"tinkertanker.com","members":["a@b.com"]}' \
  https://groups.tk.sg/api/groups

# Add a member (MEMBER role only)
curl -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"email":"a@b.com"}' \
  https://groups.tk.sg/api/groups/name@domain.com/members
```

## Deployment

`docker-compose.yml` builds `web/Dockerfile` and serves the app at groups.tk.sg behind nginx-proxy (`VIRTUAL_HOST`). Deploy = push to `main`, then pull and `docker compose up -d --build` on the server (see local `deploy.sh`, gitignored).

## Git

- Conventional Commits (`feat:`, `fix:`, `chore:`, ...)
- Rebase onto `origin/main` before pushing
