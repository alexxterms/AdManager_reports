from __future__ import annotations

from typing import Callable

from slack_bolt.authorization.authorize import AuthorizeResult
from slack_sdk.oauth.installation_store.file import FileInstallationStore
from slack_sdk.oauth.state_store.file import FileOAuthStateStore

from src.config import Settings


def build_installation_store(settings: Settings) -> FileInstallationStore:
    return FileInstallationStore(base_dir=str(settings.oauth_installation_store_dir))


def build_state_store(settings: Settings) -> FileOAuthStateStore:
    return FileOAuthStateStore(
        expiration_seconds=600,
        base_dir=str(settings.oauth_state_store_dir),
    )


def build_authorize(settings: Settings) -> Callable:
    installation_store = build_installation_store(settings)

    def authorize(enterprise_id, team_id, user_id, client):  # type: ignore[no-untyped-def]
        installation = installation_store.find_installation(
            enterprise_id=enterprise_id,
            team_id=team_id,
            is_enterprise_install=False,
        )
        if installation is None:
            return None

        bot = installation_store.find_bot(
            enterprise_id=enterprise_id,
            team_id=team_id,
            is_enterprise_install=False,
        )

        bot_token = bot.bot_token if bot and bot.bot_token else installation.bot_token
        bot_id = bot.bot_id if bot else installation.bot_id
        bot_user_id = bot.bot_user_id if bot else installation.bot_user_id

        if not bot_token:
            return None

        return AuthorizeResult(
            enterprise_id=installation.enterprise_id,
            team_id=installation.team_id,
            bot_token=bot_token,
            bot_id=bot_id,
            bot_user_id=bot_user_id,
            user_id=user_id,
        )

    return authorize
