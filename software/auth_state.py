"""
Xsolla Game Recap - Local Login State

Tracks sign-in state for this local install, including the device token
issued by the website after real authentication (Google Sign-In or
email/password — see sync_client.py and auth_server.py). The device token
is the real credential this app uses to sync sessions and media to the
authenticated web app; it's opaque, scoped to one user server-side, and
never contains or grants access to a password.
"""

import time
from typing import Dict
from config import load_config, save_config


def is_logged_in() -> bool:
    return bool(load_config().get("logged_in", False))


def get_user_label() -> str:
    return load_config().get("user_label", "") or "Player"


def get_device_token() -> str:
    return load_config().get("device_token", "") or load_config().get("auth_token", "")


def get_auth_token() -> str:
    return get_device_token()


def set_device_token(token: str):
    cfg = load_config()
    cfg["device_token"] = token
    cfg["auth_token"] = token
    save_config(cfg)


def get_current_user() -> Dict[str, str]:
    cfg = load_config()
    token = cfg.get("device_token", "") or cfg.get("auth_token", "")
    return {
        "logged_in": bool(cfg.get("logged_in", False)),
        "user_label": cfg.get("user_label", "Player"),
        "user_email": cfg.get("user_email", ""),
        "device_token": token,
        "auth_token": token,
        "login_time": cfg.get("login_time", ""),
    }


def log_in(user_label: str = "Player", email: str = "", token: str = ""):
    """Records a real, server-issued login. `token` must be a device token
    minted by the website after real authentication — never fabricate one
    locally; an empty token means sync calls will fail honestly instead of
    silently pretending to be authenticated."""
    cfg = load_config()
    cfg["logged_in"] = True
    cfg["user_label"] = user_label or "Player"
    cfg["user_email"] = email
    cfg["device_token"] = token
    cfg["auth_token"] = token
    cfg["login_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_config(cfg)


def log_out():
    cfg = load_config()
    cfg["logged_in"] = False
    cfg["user_label"] = ""
    cfg["user_email"] = ""
    cfg["device_token"] = ""
    cfg["login_time"] = ""
    save_config(cfg)
