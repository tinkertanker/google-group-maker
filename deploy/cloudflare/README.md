# Cloudflare hosting

The app runs on Cloudflare as a Worker in front of one
[Cloudflare Container](https://developers.cloudflare.com/containers/) running
[`web/Dockerfile`](../../web/Dockerfile) unchanged — the same image the old
`docker-compose.yml`/nginx-proxy deployment built.

This directory is a standalone npm project, not part of any workspace.

Throughout this runbook, `<hostname>` is the app's public hostname and
`<zone>` is the Cloudflare zone it lives under.

## How it maps from the Docker setup

- **One instance.** Minted API keys live in `data/apikeys.db` (SQLite) inside
  the container filesystem, so every request goes to the Durable Object named
  `main` (location hint `apac-se`). That object runs one container, with
  `max_instances: 1`.
- **Container settings.** The instance type is `basic` (1/4 vCPU, 1 GiB).
  `sleepAfter` is `12h`, so an idle night lets the container sleep and the
  next morning's first request waits a few seconds for boot.
- **Forwarded headers.** The Worker sets `X-Forwarded-Proto`/`Host`/`For`;
  the app's OAuth redirect URI is built from them, so callbacks stay on
  `https://<hostname>/auth/callback`.
- **Secrets into the container.** Worker `vars` and secrets reach the
  container through `GroupMaker.envVars` in [`src/index.ts`](src/index.ts).
  On the first request after they change, the running container is restarted
  so it picks the new env up (same fingerprint trick as
  classroom-widgets-backend).

## Token permissions

`CLOUDFLARE_API_TOKEN` for deploys and rollback needs:

- **Account:**
  - Workers Scripts: Edit (covers Durable Objects and Worker secrets)
  - Containers: Edit (pushes to `registry.cloudflare.com` and creates the
    container application)
  - Account Settings: Read
- **Zone `<zone>`:**
  - Workers Routes: Edit (custom domains)
  - DNS: Edit (only needed to restore the old CNAME on rollback)
  - Zone: Read

Workers Paid is required for Containers.

## Deploy

Run this from a clean checkout of the commit you are deploying, on a machine
with Docker that builds `linux/amd64`.

```sh
cd deploy/cloudflare
export CLOUDFLARE_ACCOUNT_ID=<your-account-id>
export CLOUDFLARE_API_TOKEN=...            # see "Token permissions"
npm install

# Read-only preflight
npx wrangler whoami
npm run typecheck
npm run dry-run
```

### 1. Secrets

Write the secrets to a file outside the repo, readable only by you:

```sh
umask 077
cat > /tmp/groups.secrets <<'EOF'
DEFAULT_EMAIL=<admin user email>
ADMIN_EMAIL=<same, or the Workspace super-admin to delegate to>
SESSION_SECRET=<openssl rand -hex 32>
API_KEY=<openssl rand -hex 32>
GOOGLE_CLIENT_ID=<...apps.googleusercontent.com>
GOOGLE_CLIENT_SECRET=<...>
GOOGLE_SERVICE_ACCOUNT_JSON=<single-line service account JSON>
EOF
```

- `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`: the OAuth 2.0 Web Application
  client already used by the old deployment. Its authorised redirect URI
  `https://<hostname>/auth/callback` is unchanged, so no Google Console
  change is needed.
- `GOOGLE_SERVICE_ACCOUNT_JSON`: the domain-wide-delegation service account
  JSON — the same value the Docker host had in
  `service-account-credentials.json`, on one line.
- `API_KEY` is the master `/api/*` token. Generate a fresh one; minted keys
  from the old deployment are gone with the old volume anyway.

### 2. Deploy

If the hostname was previously covered by a wildcard record pointing at the
old host, there is nothing to delete first — a Workers custom domain takes
precedence over the wildcard.

```sh
npx wrangler deploy -c wrangler.jsonc --secrets-file /tmp/groups.secrets
rm -f /tmp/groups.secrets
```

`wrangler deploy` builds the image, pushes it, creates the container
application and the Durable Object class (migration `v1`), and binds
`<hostname>`. The first container takes a few minutes to provision; until
then requests return 503. Watch with `npx wrangler containers list` and
`npx wrangler tail google-group-maker`.

### 3. Verify

```sh
curl -s https://<hostname>/health          # {"status":"ok"}
curl -sI https://<hostname>/               # 302 -> /auth/login
```

The login page renders an "OAuth not configured" error until
`GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` are set, so set them before
declaring victory. Then log in once through Google.

### Later deploys

- **Deploy:** push your branch, merge, then `npm run deploy` from the merge
  commit on a machine with Docker. Secrets persist across deploys.
- **Secret changes:** `npx wrangler secret put NAME --name google-group-maker`
  (or `secret bulk <file>`). A warm Durable Object keeps the env it was
  constructed with, so the env-fingerprint check may not notice the change —
  run a no-op `wrangler deploy` afterwards to force the object onto the new
  version; the container then restarts with the new secrets on the next
  request.
- **Rollback:** `npx wrangler rollback -c wrangler.jsonc`. To leave
  Cloudflare entirely, delete the `<hostname>` worker domain
  (`DELETE /accounts/{acct}/workers/domains/{id}`); the wildcard record then
  resolves the name to the old host again — no DNS record to restore.

## Caveats

- **Ephemeral `apikeys.db`.** The container disk is wiped on every restart
  or deploy, so minted `/keys` API keys die with it; the env `API_KEY`
  master key survives. Move to D1 or the Secret Store if that ever matters.
- **Cold start.** The first request after the container has slept or been
  redeployed waits for boot, typically a few seconds.
- **Single instance.** A deploy or crash drops in-flight work; the OAuth
  login is cookie-stateless so users just log back in.
- **Cost.** `basic` billed while the container is running; `sleepAfter`
  keeps idle nights free.
