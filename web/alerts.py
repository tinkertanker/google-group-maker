"""Slack alerting for /api/* use.

Set SLACK_WEBHOOK_URL (a Slack incoming webhook) to get a message on every
authenticated API call and on rejected keys. Alerts are fire-and-forget on a
daemon thread so a Slack outage never delays the API call itself.
"""

import os
import threading

import httpx

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")


def _post(text: str) -> None:
    """POST to the Slack incoming webhook. Never raises."""
    try:
        httpx.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=5)
    except Exception:
        pass


def send_slack_alert(text: str) -> None:
    """Queue an alert in the background; returns immediately."""
    if not SLACK_WEBHOOK_URL:
        return
    threading.Thread(target=_post, args=(text,), daemon=True).start()


def notify_api_use(key: dict, action: str, detail: str, status: int) -> None:
    """Alert that an API key was used. Called alongside apikeys.log_action."""
    key_label = (key or {}).get("name") or "unknown key"
    send_slack_alert(
        f"[groups.tk.sg] `{action}` by {key_label} — {detail} (HTTP {status})"
    )


def notify_auth_failure(reason: str) -> None:
    """Alert that an /api/* call was rejected (missing or bad key)."""
    send_slack_alert(f"[groups.tk.sg] API call rejected: {reason}")
