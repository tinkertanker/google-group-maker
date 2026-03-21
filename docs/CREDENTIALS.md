# Google Credentials Setup

Google Group Maker uses two kinds of Google credentials:

1. A **service account** for Google Admin SDK calls
2. An **OAuth client** for FastAPI web login

## Service Account Setup

The CLI and web app both need a service account with domain-wide delegation.

### 1. Create a service account

1. Open the [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable the **Admin SDK API**
4. Create a service account
5. Generate a JSON key and download it

### 2. Enable domain-wide delegation

In the Google Workspace Admin console:

1. Go to **Security → API controls → Domain-wide Delegation**
2. Add the service account client ID
3. Grant these scopes:
   - `https://www.googleapis.com/auth/admin.directory.group`
   - `https://www.googleapis.com/auth/admin.directory.group.member`

### 3. Provide the credentials to the app

Use either of these approaches:

#### Option A: JSON file in the project root

```bash
cp service-account-credentials.example.json service-account-credentials.json
```

Then replace the example values with your real service account JSON.

#### Option B: Environment variable

Add this to `.env`:

```bash
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

## OAuth Setup for the Web App

The FastAPI app also needs a Google OAuth client.

1. Open [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create an **OAuth 2.0 Client ID** for a **Web application**
3. Add authorised redirect URIs:
   - `http://localhost:8000/auth/callback`
   - `https://your-domain.com/auth/callback`
4. Add these values to `.env`:

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
SESSION_SECRET=replace-me
```

Optional:

```bash
ALLOWED_DOMAIN=yourdomain.com
```

## Required Environment Variables

### Shared

| Variable | Description |
| --- | --- |
| `DEFAULT_EMAIL` | Default email used for delegation |
| `ADMIN_EMAIL` | Optional explicit admin email; defaults to `DEFAULT_EMAIL` |
| `GOOGLE_GROUP_DOMAIN` | Optional default group domain |

### Web App Only

| Variable | Description |
| --- | --- |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `SESSION_SECRET` | Session signing secret |
| `ALLOWED_DOMAIN` | Optional login restriction |

## Verifying the Setup

### CLI

```bash
./groupmaker.py list
```

### Web App

```bash
uvicorn web.app:app --reload
```

Then visit `http://localhost:8000` and log in.

## Troubleshooting

### Service account errors

- Confirm the Admin SDK API is enabled
- Confirm domain-wide delegation is configured
- Confirm `DEFAULT_EMAIL` or `ADMIN_EMAIL` belongs to a Google Workspace admin
- Check that the JSON key is valid and complete

### OAuth errors

- `redirect_uri_mismatch`: fix the authorised redirect URIs in Google Cloud Console
- `access_denied`: check `ALLOWED_DOMAIN` and the Google account used to sign in
- `OAuth not configured`: set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

## Security Notes

- Never commit real credentials to Git
- Keep `service-account-credentials.json` local only
- Prefer environment variables or your deployment platform's secret manager in production
- Rotate service account keys regularly