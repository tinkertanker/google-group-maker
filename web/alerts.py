"""Slack alerting for /api/* use.

Set SLACK_WEBHOOK_URL (a Slack incoming webhook) to get a message on every
authenticated API call and on rejected keys. Alerts are best-effort: a
missing URL or a failed POST never breaks the API call itself.
"""

import os

import httpx

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")


def send_slack_alert(text: str) -> None:
    """POST to the Slack incoming webhook. Never raises."""
    if not SLACK_WEBHOOK_URL:
        return
    try:
        httpx.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=5)
    except Exception:
        pass


def notify_api_use(key: dict, action: str, detail: str, status: int) -> None:
    """Alert that an API key was used. Called alongside apikeys.log_action."""
    key_label = (key or {}).get("name") or "unknown key"
    send_slack_alert(
        f"[groups.tk.sg] `{action}` by {key_label} — {detail} (HTTP {status})"
    )


def notify_auth_failure(reason: str) -> None:
    """Alert that an /api/* call was rejected (missing or bad key)."""
    send_slack_alert(f"[groups.tk.sg] API call rejected: {reason}")
