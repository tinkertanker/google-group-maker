// groups.tk.sg: FastAPI web app (web/Dockerfile) running in a single
// Cloudflare Container.
//
// Minted API keys live in a SQLite file inside the container filesystem, so
// every request must reach the same instance: one Durable Object named
// "main", backed by one container (max_instances: 1 in wrangler.jsonc).
import { Container } from '@cloudflare/containers';

interface Env {
  GROUP_MAKER: DurableObjectNamespace<GroupMaker>;
  // vars
  GOOGLE_GROUP_DOMAIN: string;
  ALLOWED_DOMAIN: string;
  // secrets (wrangler secret put)
  DEFAULT_EMAIL?: string;
  ADMIN_EMAIL?: string;
  SESSION_SECRET?: string;
  API_KEY?: string;
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
  GOOGLE_SERVICE_ACCOUNT_JSON?: string;
}

const INSTANCE_NAME = 'main';
const ENV_FINGERPRINT_KEY = 'envFingerprint';

export class GroupMaker extends Container<Env> {
  defaultPort = 8000;
  // Logins and API calls are sporadic; idle after half a day and let the
  // first request after sleep pay the few-second container boot.
  sleepAfter = '12h';
  enableInternet = true; // Google OAuth + Admin SDK calls

  constructor(ctx: DurableObjectState<{}>, env: Env) {
    super(ctx, env);
    const secrets = {
      DEFAULT_EMAIL: env.DEFAULT_EMAIL,
      ADMIN_EMAIL: env.ADMIN_EMAIL,
      SESSION_SECRET: env.SESSION_SECRET,
      API_KEY: env.API_KEY,
      GOOGLE_CLIENT_ID: env.GOOGLE_CLIENT_ID,
      GOOGLE_CLIENT_SECRET: env.GOOGLE_CLIENT_SECRET,
      GOOGLE_SERVICE_ACCOUNT_JSON: env.GOOGLE_SERVICE_ACCOUNT_JSON,
    };
    this.envVars = {
      GOOGLE_GROUP_DOMAIN: env.GOOGLE_GROUP_DOMAIN,
      ALLOWED_DOMAIN: env.ALLOWED_DOMAIN,
      // Minted keys: the container disk is wiped on every restart or deploy.
      API_KEYS_DB: '/app/data/apikeys.db',
      // Unset secrets are left out rather than passed as empty strings.
      ...Object.fromEntries(Object.entries(secrets).filter(([, v]) => v)),
    } as Record<string, string>;
  }

  // envVars only reach the container when it starts, and a running container
  // survives Worker deploys and secret changes. So on the first request after
  // this object (re)starts, compare a hash of envVars with the one the running
  // container was started with, and restart the container if they differ.
  private envCheck?: Promise<void>;

  override async fetch(request: Request): Promise<Response> {
    this.envCheck ??= this.restartIfEnvChanged().catch((error) => {
      this.envCheck = undefined;
      throw error;
    });
    await this.envCheck;
    return super.fetch(request);
  }

  private async restartIfEnvChanged(): Promise<void> {
    const env = this.envVars ?? {};
    const sorted = Object.keys(env).sort().map((k) => [k, env[k]]);
    const digest = await crypto.subtle.digest(
      'SHA-256',
      new TextEncoder().encode(JSON.stringify(sorted)),
    );
    const fingerprint = [...new Uint8Array(digest)]
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
    if ((await this.ctx.storage.get<string>(ENV_FINGERPRINT_KEY)) === fingerprint) return;

    // Record the new fingerprint only once the old container has exited, so a
    // container still running with old secrets is retried on the next request.
    if (this.ctx.container?.running) {
      await this.stop();
      await this.waitForExit(60);
    }
    if (this.ctx.container?.running) {
      await this.destroy();
      await this.waitForExit(20);
    }
    if (this.ctx.container?.running) {
      throw new Error('Container did not stop after an env change; will retry');
    }
    await this.ctx.storage.put(ENV_FINGERPRINT_KEY, fingerprint);
  }

  private async waitForExit(polls: number): Promise<void> {
    for (let i = 0; i < polls && this.ctx.container?.running; i++) {
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // The app builds its OAuth redirect from X-Forwarded-Proto/Host, so keep
    // both accurate; X-Forwarded-For carries the real client address.
    const headers = new Headers(request.headers);
    const clientIp = request.headers.get('cf-connecting-ip');
    if (clientIp) headers.set('x-forwarded-for', clientIp);
    else headers.delete('x-forwarded-for');
    const url = new URL(request.url);
    headers.set('x-forwarded-proto', url.protocol.replace(':', ''));
    headers.set('x-forwarded-host', url.host);

    // The hint only matters when the object is first created: keep it (and so
    // the container) in Southeast Asia instead of wherever the first request
    // after deploy happens to come from.
    return env.GROUP_MAKER.getByName(INSTANCE_NAME, { locationHint: 'apac-se' })
      .fetch(new Request(request, { headers }));
  },
} satisfies ExportedHandler<Env>;
