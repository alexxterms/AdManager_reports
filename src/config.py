from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Settings:
    slack_bot_token: str | None
    slack_app_token: str
    slack_signing_secret: str
    slack_client_id: str | None
    slack_client_secret: str | None
    slack_scopes: list[str]
    slack_user_scopes: list[str]
    slack_redirect_uri: str | None
    oauth_installation_store_dir: Path
    oauth_state_store_dir: Path
    ad_manager_user_id: str
    allowed_channel_ids: set[str]
    dm_recipient_ids: list[str]
    timezone_name: str
    pdf_template_path: Path
    output_dir: Path
    idempotency_db_path: Path
    fx_api_url: str
    fx_api_key: str | None
    fx_api_timeout_seconds: int
    fx_cache_ttl_seconds: int
    groq_api_key: str | None
    groq_model: str
    pdf_field_coords: Dict[str, Point]


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _parse_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _parse_points(raw_json: str) -> Dict[str, Point]:
    raw = json.loads(raw_json)
    out: Dict[str, Point] = {}
    for field_name, value in raw.items():
        out[field_name] = Point(x=float(value["x"]), y=float(value["y"]))
    return out


def load_settings() -> Settings:
    load_dotenv()

    ad_manager_user_id = _required_env("SLACK_AD_MANAGER_USER_ID")
    slack_bot_token = os.getenv("SLACK_BOT_TOKEN", "").strip() or None
    slack_app_token = _required_env("SLACK_APP_TOKEN")
    slack_signing_secret = _required_env("SLACK_SIGNING_SECRET")
    slack_client_id = os.getenv("SLACK_CLIENT_ID", "").strip() or None
    slack_client_secret = os.getenv("SLACK_CLIENT_SECRET", "").strip() or None
    slack_scopes = _parse_csv(
        os.getenv(
            "SLACK_SCOPES",
            "channels:history,chat:write,files:write,groups:history,im:history,mpim:history",
        )
    )
    slack_user_scopes = _parse_csv(os.getenv("SLACK_USER_SCOPES", ""))
    slack_redirect_uri = os.getenv("SLACK_REDIRECT_URI", "").strip() or None
    oauth_installation_store_dir = Path(
        os.getenv("OAUTH_INSTALLATION_STORE_DIR", "state/slack_installations")
    ).resolve()
    oauth_state_store_dir = Path(
        os.getenv("OAUTH_STATE_STORE_DIR", "state/slack_oauth_states")
    ).resolve()

    # Require either a fixed bot token OR OAuth client credentials.
    if not slack_bot_token and not (slack_client_id and slack_client_secret):
        raise ValueError(
            "Missing Slack auth configuration. Provide SLACK_BOT_TOKEN "
            "or both SLACK_CLIENT_ID and SLACK_CLIENT_SECRET."
        )

    allowed_channels_raw = os.getenv("SLACK_ALLOWED_CHANNEL_IDS", "").strip()
    allowed_channel_ids = set(_parse_csv(allowed_channels_raw)) if allowed_channels_raw else set()

    dm_recipient_ids = _parse_csv(_required_env("SLACK_DM_RECIPIENT_IDS"))

    timezone_name = os.getenv("TIMEZONE", "Asia/Kolkata").strip() or "Asia/Kolkata"
    pdf_template_path = Path(os.getenv("PDF_TEMPLATE_PATH", "(BIAB - Weekly) (5126) (2).pdf")).resolve()
    output_dir = Path(os.getenv("OUTPUT_DIR", "output")).resolve()
    idempotency_db_path = Path(os.getenv("IDEMPOTENCY_DB_PATH", "state/idempotency.db")).resolve()

    fx_api_url = os.getenv("FX_API_URL", "https://open.er-api.com/v6/latest/CAD").strip()
    fx_api_key = os.getenv("FX_API_KEY", "").strip() or None
    fx_api_timeout_seconds = int(os.getenv("FX_API_TIMEOUT_SECONDS", "10"))
    fx_cache_ttl_seconds = int(os.getenv("FX_CACHE_TTL_SECONDS", "1800"))
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip() or None
    groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"

    default_coords = (
        '{"date":{"x":80,"y":725},"spend_usd":{"x":80,"y":700},"impressions":{"x":80,"y":675},'
        '"ctr":{"x":80,"y":650},"link_clicks":{"x":80,"y":625},"leads":{"x":80,"y":600},'
        '"cpc_usd":{"x":80,"y":575},"cpm_usd":{"x":80,"y":550},"cpl_usd":{"x":80,"y":525},'
        '"fx_note":{"x":80,"y":500}}'
    )
    pdf_field_coords = _parse_points(os.getenv("PDF_FIELD_COORDS_JSON", default_coords))

    output_dir.mkdir(parents=True, exist_ok=True)
    idempotency_db_path.parent.mkdir(parents=True, exist_ok=True)
    oauth_installation_store_dir.mkdir(parents=True, exist_ok=True)
    oauth_state_store_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_template_path.exists():
        raise ValueError(f"Template PDF not found: {pdf_template_path}")

    return Settings(
        slack_bot_token=slack_bot_token,
        slack_app_token=slack_app_token,
        slack_signing_secret=slack_signing_secret,
        slack_client_id=slack_client_id,
        slack_client_secret=slack_client_secret,
        slack_scopes=slack_scopes,
        slack_user_scopes=slack_user_scopes,
        slack_redirect_uri=slack_redirect_uri,
        oauth_installation_store_dir=oauth_installation_store_dir,
        oauth_state_store_dir=oauth_state_store_dir,
        ad_manager_user_id=ad_manager_user_id,
        allowed_channel_ids=allowed_channel_ids,
        dm_recipient_ids=dm_recipient_ids,
        timezone_name=timezone_name,
        pdf_template_path=pdf_template_path,
        output_dir=output_dir,
        idempotency_db_path=idempotency_db_path,
        fx_api_url=fx_api_url,
        fx_api_key=fx_api_key,
        fx_api_timeout_seconds=fx_api_timeout_seconds,
        fx_cache_ttl_seconds=fx_cache_ttl_seconds,
        groq_api_key=groq_api_key,
        groq_model=groq_model,
        pdf_field_coords=pdf_field_coords,
    )
