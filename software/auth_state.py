"""
Xsolla Game Recap - Local Login State

Tracks whether the player has clicked "Login" via the tray icon in this
local install. This is a local UI flag only, stored in the same local
config.json used for everything else — there is no real session/token
exchange with the website yet. Treat it as a demo affordance, not real
authentication: it does not grant access to anything by itself.
"""

from config import load_config, save_config


def is_logged_in() -> bool:
    return bool(load_config().get("logged_in", False))


def get_user_label() -> str:
    return load_config().get("user_label", "")


def log_in(user_label: str = "Player"):
    cfg = load_config()
    cfg["logged_in"] = True
    cfg["user_label"] = user_label
    save_config(cfg)


def log_out():
    cfg = load_config()
    cfg["logged_in"] = False
    cfg["user_label"] = ""
    save_config(cfg)
