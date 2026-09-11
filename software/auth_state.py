"""
Xsolla Game Recap - Local Login State
Tracks authenticated user details, session token, and active login state.
"""

import time
from typing import Dict
from config import load_config, save_config


def is_logged_in() -> bool:
    return bool(load_config().get("logged_in", False))


def get_user_label() -> str:
    return load_config().get("user_label", "") or "Player"


def get_current_user() -> Dict[str, str]:
    cfg = load_config()
    return {
        "logged_in": bool(cfg.get("logged_in", False)),
        "user_label": cfg.get("user_label", "Player"),
        "user_email": cfg.get("user_email", ""),
        "auth_token": cfg.get("auth_token", ""),
        "login_time": cfg.get("login_time", "")
    }


def log_in(user_label: str = "Player", email: str = "", token: str = ""):
    cfg = load_config()
    cfg["logged_in"] = True
    cfg["user_label"] = user_label or "Player"
    cfg["user_email"] = email
    cfg["auth_token"] = token or f"xsolla_session_{int(time.time())}"
    cfg["login_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_config(cfg)


def log_out():
    cfg = load_config()
    cfg["logged_in"] = False
    cfg["user_label"] = ""
    cfg["user_email"] = ""
    cfg["auth_token"] = ""
    cfg["login_time"] = ""
    save_config(cfg)
