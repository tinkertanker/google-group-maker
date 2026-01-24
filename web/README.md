# Google Group Maker - Web App

Modern FastAPI web interface for managing Google Groups with OAuth authentication.

## Features

- Google OAuth for user authentication
- Domain-restricted access (optional)
- Create, list, rename, and delete groups
- Manage group members (add, remove, change roles)
- htmx for dynamic updates
- Docker-ready deployment

## Quick Start

### Prerequisites

- Python 3.9+
- Google Cloud project with:
  - OAuth 2.0 credentials
  - Service account with domain-wide delegation

### Local Development

1. **Install dependencies:**
   ```bash
   cd google-group-maker
   pip install -r requirements.txt -r requirements-web.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the app:**
   ```bash
   uvicorn web.app:app --reload
   ```

4. **Access:** http://localhost:8000

### Docker

```bash
docker-compose up -d
```

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `DEFAULT_EMAIL` | Default admin email for API delegation |
| `GOOGLE_CLIENT_ID` | OAuth 2.0 client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 client secret |
| `SESSION_SECRET` | Random string for session signing |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_DOMAIN` | (none) | Restrict login to specific domain |
| `GOOGLE_GROUP_DOMAIN` | tinkertanker.com | Default domain for groups |
| `ADMIN_EMAIL` | `DEFAULT_EMAIL` | Admin email for API delegation |

### Service Account Credentials

Provide credentials via one of:

1. **Environment variable:** `GOOGLE_SERVICE_ACCOUNT_JSON` (JSON string)
2. **File:** `service-account-credentials.json` in project root

## OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)

2. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Name: Google Group Maker

3. Add Authorised redirect URIs:
   - Development: `http://localhost:8000/auth/callback`
   - Production: `https://your-domain.com/auth/callback`

4. Copy Client ID and Secret to your `.env` file

5. (Optional) Restrict to your domain:
   ```
   ALLOWED_DOMAIN=yourdomain.com
   ```

## Project Structure

```
web/
├── app.py              # FastAPI application
├── dependencies.py     # Shared utilities
├── Dockerfile          # Container definition
├── routers/
│   ├── auth.py         # OAuth routes
│   ├── groups.py       # Group management
│   └── members.py      # Member management
├── templates/
│   ├── base.html       # Base template
│   ├── dashboard.html  # Home page
│   ├── login.html      # Login page
│   └── groups/         # Group templates
└── static/
    └── style.css       # Custom styles
```

## API Routes

### Authentication
- `GET /auth/login` - Show login page
- `GET /auth/start` - Start OAuth flow
- `GET /auth/callback` - OAuth callback
- `GET /auth/logout` - Log out
- `GET /auth/me` - Get current user (API)

### Groups
- `GET /groups` - List groups
- `GET /groups/new` - Create group form
- `POST /groups` - Create group
- `GET /groups/{email}/members` - View group members
- `GET /groups/{email}/edit` - Edit group form
- `POST /groups/{email}/rename` - Rename group
- `DELETE /groups/{email}` - Delete group (htmx)
- `POST /groups/{email}/delete` - Delete group (form)

### Members
- `POST /groups/{email}/members` - Add member
- `DELETE /groups/{email}/members/{member}` - Remove member (htmx)
- `POST /groups/{email}/members/{member}/remove` - Remove member (form)
- `POST /groups/{email}/members/{member}/role` - Update role (form)
- `PATCH /groups/{email}/members/{member}` - Update role (htmx)

## Health Check

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## Troubleshooting

### OAuth Errors

- **"OAuth not configured"**: Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- **"redirect_uri_mismatch"**: Add correct redirect URI in Cloud Console
- **"Access denied"**: Check `ALLOWED_DOMAIN` matches your email domain

### Service Account Errors

- **"No credentials found"**: Provide `GOOGLE_SERVICE_ACCOUNT_JSON` or mount credentials file
- **"Permission denied"**: Verify service account has domain-wide delegation

### Docker Issues

- **Health check failing**: Check logs with `docker-compose logs web`
- **Credentials not found**: Verify volume mount for credentials file
