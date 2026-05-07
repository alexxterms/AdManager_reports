from __future__ import annotations

import html
import os

from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings

from src.config import load_settings
from src.slack_oauth import build_installation_store, build_state_store


def _render_page(title: str, heading: str, body: str, success: bool) -> tuple[str, int, dict[str, str]]:
        accent = "#16a34a" if success else "#dc2626"
        html_doc = f"""
<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{html.escape(title)}</title>
    <style>
        :root {{
            --bg: #0b1220;
            --panel: #111827;
            --text: #e5e7eb;
            --muted: #9ca3af;
            --accent: {accent};
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            min-height: 100vh;
            font-family: Arial, sans-serif;
            background: radial-gradient(circle at 20% 20%, #1f2937 0%, var(--bg) 55%);
            color: var(--text);
            display: grid;
            place-items: center;
            padding: 24px;
        }}
        .card {{
            width: min(720px, 100%);
            background: linear-gradient(180deg, #0f172a, var(--panel));
            border: 1px solid #1f2937;
            border-top: 4px solid var(--accent);
            border-radius: 14px;
            padding: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.45);
        }}
        h1 {{ margin: 0 0 10px; font-size: 28px; }}
        p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
        .hint {{ margin-top: 14px; font-size: 14px; color: #cbd5e1; }}
        code {{ background: #0b1020; border: 1px solid #1f2937; padding: 2px 6px; border-radius: 6px; }}
    </style>
</head>
<body>
    <main class=\"card\">
        <h1>{html.escape(heading)}</h1>
        <p>{body}</p>
        <p class=\"hint\">You can now close this tab and return to Slack.</p>
    </main>
</body>
</html>
"""
        return html_doc, 200, {"Content-Type": "text/html; charset=utf-8"}


def create_web_app() -> Flask:
    settings = load_settings()

    if not settings.slack_client_id or not settings.slack_client_secret:
        raise ValueError(
            "OAuth web service requires SLACK_CLIENT_ID and SLACK_CLIENT_SECRET."
        )

    bolt_app = App(
        signing_secret=settings.slack_signing_secret,
        oauth_settings=OAuthSettings(
            client_id=settings.slack_client_id,
            client_secret=settings.slack_client_secret,
            scopes=settings.slack_scopes,
            user_scopes=settings.slack_user_scopes,
            installation_store=build_installation_store(settings),
            state_store=build_state_store(settings),
            redirect_uri=settings.slack_redirect_uri,
        ),
    )

    web_app = Flask(__name__)
    handler = SlackRequestHandler(bolt_app)

    @web_app.get("/")
    def index():
        return {
            "ok": True,
            "service": "slack-oauth",
            "install_path": "/slack/install",
            "redirect_path": "/slack/oauth_redirect",
        }

    @web_app.get("/healthz")
    def healthz():
        return {"ok": True}

    @web_app.route("/slack/install", methods=["GET"])
    def install():
        return handler.handle(request)

    @web_app.route("/slack/oauth_redirect", methods=["GET"])
    def oauth_redirect():
        if request.args.get("error"):
            err = html.escape(request.args.get("error", "unknown_error"))
            desc = html.escape(request.args.get("error_description", "OAuth installation was cancelled or failed."))
            body = f"Slack returned <code>{err}</code>. {desc}"
            return _render_page(
                title="Slack Install Failed",
                heading="Installation failed",
                body=body,
                success=False,
            )

        response = handler.handle(request)
        status_code = getattr(response, "status_code", 200)
        if status_code >= 400:
            return _render_page(
                title="Slack Install Failed",
                heading="Installation failed",
                body="The OAuth callback could not be completed. Please retry from the install link.",
                success=False,
            )

        return _render_page(
            title="Slack App Installed",
            heading="Installation complete",
            body="Your workspace is now connected and ready to use this bot.",
            success=True,
        )

    return web_app


def main() -> None:
    app = create_web_app()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))
    app.run(host=host, port=port)


if __name__ == "__main__":
    main()
