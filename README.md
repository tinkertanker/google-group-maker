# Google Group Maker

Google Group Maker is a CLI and FastAPI web app for managing Google Groups with the Google Admin SDK.

## What it includes

- A CLI for scripted or ad-hoc group management
- A FastAPI web app with Google OAuth authentication
- Docker deployment for self-hosted use

## Requirements

- Python 3.9+
- Google Workspace admin access
- A Google Cloud service account with domain-wide delegation
- For the web app: an OAuth 2.0 Web Application client

## Quick Start

### CLI

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp service-account-credentials.example.json service-account-credentials.json
chmod +x groupmaker.py
./groupmaker.py --help
```

### Web app (local development)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-web.txt
cp .env.example .env
uvicorn web.app:app --reload
```

Open `http://localhost:8000`.

### Production (Docker host)

Production runs `docker-compose.yml` on the office Docker host, behind the
host's nginx-proxy (external `devtksg` network; `VIRTUAL_HOST` routes the
hostname and the proxy terminates TLS). The checkout on that host holds:

- `.env`: the web app settings and secrets (see Configuration below), including
  the master `API_KEY` and the optional `SLACK_WEBHOOK_URL`
- `service-account-credentials.json`: the domain-wide-delegation service
  account, mounted read-only
- the `groups-data` named volume: `data/apikeys.db`, the minted API keys and
  their audit log. Keep it; recreating the container does not touch it.

Run these in the production checkout. Its directory is `groups`, so Compose
uses project `groups`: image `groups-groups`, volume `groups_groups-data`. From
any other directory, pass `-p groups` so you reuse that volume instead of
creating an empty one. Never run `docker compose down -v`; it deletes the keys.

Deploy from `main`:

```bash
docker tag groups-groups:latest groups-groups:rollback-$(git rev-parse --short HEAD)
git pull --ff-only
docker compose up -d --build
curl -s https://<hostname>/health   # {"status":"ok"}
```

Roll back with `git checkout <previous sha>` and
`docker compose up -d --build` (run `git switch main` before the next deploy,
since the checkout detaches HEAD), or retag the saved image as
`groups-groups:latest` and run `docker compose up -d --no-build`.
After changing `.env`, run `docker compose up -d` so the container picks it up.

[deploy/cloudflare/](deploy/cloudflare/README.md) is a retired Cloudflare
setup kept only for rollback; it is not production.

## Configuration

Copy `.env.example` to `.env` and set the values you need.

### Required

| Variable | Description |
| --- | --- |
| `DEFAULT_EMAIL` | Default email used for API delegation |

### Optional for CLI and web

| Variable | Description |
| --- | --- |
| `ADMIN_EMAIL` | Admin email used for delegation; defaults to `DEFAULT_EMAIL` |
| `GOOGLE_GROUP_DOMAIN` | Default domain for groups |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Service account credentials as a JSON string |

### Web app only

| Variable | Description |
| --- | --- |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `SESSION_SECRET` | Session signing secret |
| `ALLOWED_DOMAIN` | Optional login domain restriction |

You can provide service account credentials in either of these ways:

1. `GOOGLE_SERVICE_ACCOUNT_JSON`
2. `service-account-credentials.json` in the project root

See [docs/CREDENTIALS.md](docs/CREDENTIALS.md) for the full setup.

## OAuth Setup

1. Open the [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create an OAuth 2.0 Client ID for a Web application
3. Add an authorised redirect URI:
   - Local development: `http://localhost:8000/auth/callback`
   - Production: `https://your-domain.com/auth/callback`
4. Copy the client ID and secret into `.env`

## CLI Commands

The CLI supports these commands:

- `create`
- `list`
- `members`
- `add`
- `remove`
- `delete`
- `rename`

Examples:

```bash
./groupmaker.py list
./groupmaker.py create test-group trainer@example.com
./groupmaker.py members test-group
./groupmaker.py rename old-group new-group
```

## Web App

The FastAPI app supports:

- Logging in with Google OAuth
- Creating groups
- Viewing groups and members
- Editing group details inline
- Adding, removing, and updating member roles
- Deleting groups

For more detail, see [web/README.md](web/README.md).

## Project Structure

```text
groupmaker.py         CLI entry point
groupmaker_core.py    Shared Google Groups business logic
web/                  FastAPI web app
requirements.txt      CLI/core dependencies
requirements-web.txt  Web app dependencies
```

## Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Development Notes

- `groupmaker_core.py` is the shared logic layer used by both interfaces
- The web app uses OAuth for user login and a service account for Admin SDK calls
- Always test changes against non-production groups first
