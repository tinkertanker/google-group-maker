"""Slack alerting for /api/* use.

Set SLACK_WEBHOOK_URL (a Slack incoming webhook) to get a message on every
authenticated API call and on rejected keys. Alerts go through a bounded
queue drained by one daemon thread, so a Slack outage never delays the API
call or accumulates threads; alerts past the queue depth are dropped.
"""

import os
import queue
import threading

import httpx

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

_QUEUE: "queue.Queue[str]" = queue.Queue(maxsize=100)
_worker_started = False
_worker_lock = threading.Lock()


def _post(text: str) -> None:
    """POST to the Slack incoming webhook. Never raises."""
    try:
        httpx.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=5)
    except Exception:
        pass


def _worker() -> None:
    while True:
        _post(_QUEUE.get())


def send_slack_alert(text: str) -> None:
    """Queue an alert in the background; returns immediately."""
    if not SLACK_WEBHOOK_URL:
        return
    global _worker_started
    with _worker_lock:
        if not _worker_started:
            threading.Thread(target=_worker, daemon=True).start()
            _worker_started = True
    try:
        _QUEUE.put_nowait(text)
    except queue.Full:
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
