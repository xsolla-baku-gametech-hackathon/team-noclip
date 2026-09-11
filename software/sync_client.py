"""
Xsolla Game Recap - Website Sync Client

Bridges this desktop app to the authenticated web app via a device-pairing
flow (the same pattern CLIs like the GitHub/Vercel CLI use for "login"):

  1. start_pairing() asks the website for a short code and opens the
     browser to WEBSITE_LOGIN_URL?pair=CODE.
  2. The user is already (or becomes) signed in with Google in that tab;
     the website approves the code against THEIR real user_id server-side.
  3. poll_pairing() keeps checking until the website reveals a device
     token, which is stored locally and used as a Bearer credential for
     every sync call after that.

No email/password/API key is ever typed into or stored by this app —
only an opaque device token, and only after the website itself vouches
for who approved it.
"""

import base64
import mimetypes
import time
import webbrowser
import threading
from pathlib import Path
from typing import Callable, Optional

import requests

from config import WEBSITE_API_URL, WEBSITE_LOGIN_URL
import auth_state

# Media uploads proxy through a serverless function with a body-size limit —
# large video files need a direct-to-storage upload flow, not implemented
# yet. Matches MAX_UPLOAD_BYTES in website/api/_lib/storage.js.
MAX_UPLOAD_BYTES = 4 * 1024 * 1024


class SyncNotConfigured(Exception):
    """Raised when WEBSITE_API_URL is missing — no silent no-op."""


def _require_base_url() -> str:
    if not WEBSITE_API_URL:
        raise SyncNotConfigured(
            "WEBSITE_API_URL is not set. Copy software/.env.example to software/.env "
            "and point it at your deployed website's origin."
        )
    return WEBSITE_API_URL.rstrip("/")


def start_pairing() -> dict:
    """Asks the website for a pairing code and opens the browser to approve it."""
    base = _require_base_url()
    resp = requests.post(f"{base}/api/device", params={"action": "start"}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    code = data["code"]
    webbrowser.open(f"{WEBSITE_LOGIN_URL}?pair={code}")
    return data


def poll_once(code: str) -> dict:
    base = _require_base_url()
    resp = requests.get(f"{base}/api/device", params={"action": "poll", "code": code}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def pair_in_background(on_done: Callable[[bool, str], None], poll_interval_sec: float = 2.0):
    """Starts pairing, opens the browser, and polls on a background thread
    until approved/expired. on_done(success, message) is called exactly once."""
    try:
        pairing = start_pairing()
    except (SyncNotConfigured, requests.RequestException) as err:
        # Still let the player reach the login page even if pairing itself
        # isn't configured yet — just without the device-linking step.
        webbrowser.open(WEBSITE_LOGIN_URL)
        on_done(False, str(err))
        return

    code = pairing["code"]
    deadline = time.time() + pairing.get("expires_in_seconds", 600)

    def _poll_loop():
        while time.time() < deadline:
            time.sleep(poll_interval_sec)
            try:
                result = poll_once(code)
            except requests.RequestException:
                continue

            status = result.get("status")
            if status == "approved":
                auth_state.set_device_token(result["device_token"])
                auth_state.log_in()
                on_done(True, "Signed in.")
                return
            if status == "expired":
                on_done(False, "Pairing code expired — try Login again.")
                return
        on_done(False, "Pairing timed out — try Login again.")

    threading.Thread(target=_poll_loop, daemon=True).start()


def sync_session(session: dict) -> Optional[dict]:
    """Pushes a completed session (from RecapManager.end_session()) to the
    website. Silently skips if not configured or not paired — this is a
    best-effort background sync, not something that should block gameplay."""
    token = auth_state.get_device_token()
    if not WEBSITE_API_URL or not token:
        return None

    base = WEBSITE_API_URL.rstrip("/")
    payload = {
        "session_id": session.get("session_id"),
        "game_name": session.get("game_name"),
        "window_title": session.get("window_title"),
        "started_at": session.get("started_at"),
        "ended_at": session.get("ended_at"),
        "duration_seconds": session.get("duration_seconds"),
        "events": session.get("events", []),
    }
    try:
        resp = requests.post(
            f"{base}/api/me",
            params={"resource": "sync-session"},
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        resp.raise_for_status()
        print(f"[Sync] Session {session.get('session_id')} synced to website.")
        return resp.json()
    except requests.RequestException as err:
        print(f"[Sync] Failed to sync session: {err}")
        return None


def sync_media(
    filepath: str,
    media_type: str,
    game_name: str,
    session_id: Optional[str] = None,
    duration_seconds: Optional[float] = None,
) -> Optional[dict]:
    """Uploads a captured screenshot or video clip to the website. Best-effort,
    same as sync_session — skips quietly if not paired, and skips (with a
    printed reason) if the file is too large for the proxy-upload endpoint."""
    token = auth_state.get_device_token()
    if not WEBSITE_API_URL or not token:
        return None

    path = Path(filepath)
    if not path.exists():
        return None

    data = path.read_bytes()
    if len(data) > MAX_UPLOAD_BYTES:
        print(f"[Sync] Skipped uploading {path.name}: {len(data)} bytes exceeds the {MAX_UPLOAD_BYTES}-byte limit.")
        return None

    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    payload = {
        "game_name": game_name,
        "session_id": session_id,
        "type": media_type,
        "filename": path.name,
        "content_type": content_type,
        "duration_seconds": duration_seconds,
        "data_base64": base64.b64encode(data).decode("ascii"),
    }
    try:
        resp = requests.post(
            f"{WEBSITE_API_URL.rstrip('/')}/api/me",
            params={"resource": "media-upload"},
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        resp.raise_for_status()
        print(f"[Sync] Media {path.name} uploaded.")
        return resp.json()
    except requests.RequestException as err:
        print(f"[Sync] Failed to upload media {path.name}: {err}")
        return None
