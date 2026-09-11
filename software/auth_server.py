"""
Xsolla Game Recap - Loopback Authentication Server
Implements standard desktop-to-web OAuth loopback redirect flow (RFC 8252).
Listens locally for the browser callback, logs in the player, and returns a confirmation page.
"""

import html
import socket
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Optional

DEFAULT_PORT = 28492

SUCCESS_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Xsolla Game Recap — Login Complete</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #080b10;
      color: #f0f6fc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Space Mono", monospace;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 24px;
    }}
    .card {{
      background: #0d1117;
      border: 1px solid #70e1ff44;
      border-radius: 12px;
      padding: 40px 36px;
      max-width: 440px;
      width: 100%;
      text-align: center;
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(112, 225, 255, 0.12);
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: rgba(112, 225, 255, 0.12);
      border: 1px solid #70e1ff;
      color: #70e1ff;
      font-size: 26px;
      margin-bottom: 20px;
    }}
    h1 {{
      font-size: 20px;
      font-weight: 600;
      color: #ffffff;
      margin-bottom: 10px;
      letter-spacing: -0.02em;
    }}
    p {{
      font-size: 14px;
      color: #8b949e;
      line-height: 1.5;
      margin-bottom: 20px;
    }}
    .user-pill {{
      display: inline-block;
      padding: 6px 14px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 20px;
      font-size: 13px;
      color: #70e1ff;
      font-weight: 500;
      margin-bottom: 24px;
    }}
    .hint {{
      font-size: 12px;
      color: #6e7681;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">&#10003;</div>
    <h1>Authentication Verified</h1>
    <p>You have successfully logged in to Xsolla Game Recap.</p>
    <div class="user-pill">{user} &bull; {email}</div>
    <p class="hint">You can safely close this browser window and return to your game. The in-game overlay has connected automatically.</p>
  </div>
  <script>
    setTimeout(function() {{
      try {{ window.close(); }} catch (e) {{}}
    }}, 2500);
  </script>
</body>
</html>
"""


class AuthCallbackServer:
    def __init__(self, on_success: Callable[[str, str, str], None]):
        self.on_success = on_success
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.port: int = DEFAULT_PORT

    def _find_available_port(self, start_port: int = DEFAULT_PORT) -> int:
        for p in range(start_port, start_port + 20):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", p))
                    return p
                except OSError:
                    continue
        return start_port

    def start(self) -> int:
        self.port = self._find_available_port(DEFAULT_PORT)
        parent = self

        class CallbackHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Silence default HTTP server console logging

            def do_OPTIONS(self):
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.end_headers()

            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path in ("/callback", "/callback/"):
                    params = urllib.parse.parse_qs(parsed.query)
                    token = params.get("token", [""])[0]
                    user = params.get("user", [""])[0]
                    email = params.get("email", [""])[0]

                    if not user and email:
                        user = email.split("@")[0].capitalize()
                    if not user:
                        user = "Player"
                    if not email:
                        email = "player@xsolla.com"

                    # Notify application callback
                    try:
                        parent.on_success(token, user, email)
                    except Exception as err:
                        print(f"[AuthServer] Error in success callback: {err}")

                    # Render response page
                    resp_body = SUCCESS_HTML_TEMPLATE.format(
                        user=html.escape(user),
                        email=html.escape(email)
                    ).encode("utf-8")

                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(resp_body)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(resp_body)

                    # Trigger server shutdown on a separate thread
                    threading.Thread(target=parent.stop, daemon=True).start()
                else:
                    self.send_response(404)
                    self.end_headers()

        self.server = HTTPServer(("127.0.0.1", self.port), CallbackHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"[AuthServer] Loopback callback listener active on http://127.0.0.1:{self.port}/callback")
        return self.port

    def stop(self):
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
            self.server = None
            print("[AuthServer] Loopback listener closed.")


_active_auth_server: Optional[AuthCallbackServer] = None


def start_login_flow(on_success: Callable[[str, str, str], None], base_url: str = "http://localhost:5183/login") -> str:
    """
    Starts the local loopback server and opens the browser to the website login page
    with the redirect callback parameter.
    """
    global _active_auth_server
    if _active_auth_server:
        _active_auth_server.stop()

    _active_auth_server = AuthCallbackServer(on_success)
    port = _active_auth_server.start()

    callback_url = f"http://127.0.0.1:{port}/callback"
    delimiter = "&" if "?" in base_url else "?"
    login_url = f"{base_url}{delimiter}redirect={urllib.parse.quote(callback_url, safe='')}"

    print(f"[Auth] Launching browser to {login_url}")
    webbrowser.open(login_url)
    return login_url
