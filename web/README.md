# Google Group Maker Web App

FastAPI web interface for managing Google Groups with Google OAuth authentication.

## Features

- Google OAuth login
- Optional domain-restricted access
- Create groups
- Edit group name and description inline
- View members and manage their roles
- Delete groups
- htmx-enhanced interactions

## Local Development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-web.txt
cp .env.example .env
uvicorn web.app:app --reload
```

Open `http://localhost:8000`.

## Docker

```bash
docker-compose up -d
```

## Configuration

### Required

| Variable | Description |
| --- | --- |
| `DEFAULT_EMAIL` | Default email used for Admin SDK delegation |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `SESSION_SECRET` | Session signing secret |

### Optional

| Variable | Description |
| --- | --- |
| `ADMIN_EMAIL` | Explicit admin email for delegation |
| `GOOGLE_GROUP_DOMAIN` | Default domain for groups |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Service account credentials as JSON |
| `ALLOWED_DOMAIN` | Restrict sign-in to a Google Workspace domain |

You can also provide service account credentials via `service-account-credentials.json` in the project root.

For full credential setup, see [../docs/CREDENTIALS.md](../docs/CREDENTIALS.md).

## OAuth Setup

Create a Google OAuth Web Application client and add these redirect URIs:

- `http://localhost:8000/auth/callback`
- `https://your-domain.com/auth/callback`

## Routes

### Authentication

- `GET /auth/login`
- `GET /auth/start`
- `GET /auth/callback`
- `GET /auth/logout`
- `GET /auth/me`

### Groups

- `GET /groups`
- `GET /groups/new`
- `POST /groups`
- `GET /groups/{email}/members`
- `GET /groups/{email}/edit`
- `POST /groups/{email}/edit`
- `POST /groups/{email}/rename` (compatibility alias)
- `DELETE /groups/{email}`
- `POST /groups/{email}/delete`

### Members

- `POST /groups/{email}/members`
- `DELETE /groups/{email}/members/{member}`
- `POST /groups/{email}/members/{member}/remove`
- `POST /groups/{email}/members/{member}/role`
- `PATCH /groups/{email}/members/{member}`

## Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```
