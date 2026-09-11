"""
Xsolla Game Recap - Local Login State

Tracks sign-in state for this local install, including the device token
issued by the website's device-pairing flow (see sync_client.py). The
device token is the real credential this app uses to sync sessions to the
authenticated web app — it's opaque, scoped to one user server-side, and
never contains or grants access to a password.
"""

from config import load_config, save_config


def is_logged_in() -> bool:
    return bool(load_config().get("logged_in", False))


def get_user_label() -> str:
    return load_config().get("user_label", "")


def get_device_token() -> str:
    return load_config().get("device_token", "")


def set_device_token(token: str):
    cfg = load_config()
    cfg["device_token"] = token
    save_config(cfg)


def log_in(user_label: str = "Player"):
    cfg = load_config()
    cfg["logged_in"] = True
    cfg["user_label"] = user_label
    save_config(cfg)


def log_out():
    cfg = load_config()
    cfg["logged_in"] = False
    cfg["user_label"] = ""
    cfg["device_token"] = ""
    save_config(cfg)
