from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from src.analysis import analyze_metrics
from src.config import load_settings
from src.fx_service import FxService
from src.history import MetricsHistoryStore
from src.idempotency import IdempotencyStore
from src.groq_service import GroqInsightService
from src.parser import parse_metrics_message
from src.slack_delivery import send_text_to_channel, upload_pdf_to_channel
from src.html_renderer import render_report_html
from src.slack_oauth import build_authorize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("admanager_reports")


def main() -> None:
    settings = load_settings()
    fx_service = FxService(
        api_url=settings.fx_api_url,
        api_key=settings.fx_api_key,
        timeout_seconds=settings.fx_api_timeout_seconds,
        ttl_seconds=settings.fx_cache_ttl_seconds,
    )
    groq_service = (
        GroqInsightService(api_key=settings.groq_api_key, model=settings.groq_model)
        if settings.groq_api_key
        else None
    )
    idempotency = IdempotencyStore(settings.idempotency_db_path)
    history = MetricsHistoryStore(settings.idempotency_db_path.with_name("metrics_history.db"))

    logger.info("Listening for messages from user %s", settings.ad_manager_user_id)
    logger.info(
        "Allowed channels: %s",
        settings.allowed_channel_ids if settings.allowed_channel_ids else "any",
    )
    if settings.slack_client_id and settings.slack_client_secret:
        app = App(signing_secret=settings.slack_signing_secret, authorize=build_authorize(settings))
    elif settings.slack_bot_token:
        app = App(token=settings.slack_bot_token, signing_secret=settings.slack_signing_secret)
    else:
        raise ValueError(
            "Missing Slack bot configuration. Provide either OAuth client credentials or SLACK_BOT_TOKEN."
        )

    @app.event("message")
    def handle_message_events(event, client, logger):  # type: ignore[no-untyped-def]
        subtype = event.get("subtype")
        channel_type = event.get("channel_type")
        logger.info(
            "Received event: type=message subtype=%s user=%s channel=%s type=%s",
            subtype,
            event.get("user"),
            event.get("channel"),
            channel_type,
        )
        if subtype is not None:
            logger.info("Ignoring non-standard message subtype %s", subtype)
            return

        user_id = event.get("user", "")
        if user_id != settings.ad_manager_user_id:
            logger.info("Ignoring message from user %s", user_id)
            return

        channel_id = event.get("channel", "")
        if channel_type == "im" or channel_type == "mpim":
            logger.info("Ignoring direct or multi-party IM channel %s", channel_id)
            return

        if settings.allowed_channel_ids and channel_id not in settings.allowed_channel_ids:
            logger.info("Ignoring message from channel %s", channel_id)
            return

        event_ts = event.get("event_ts", "")
        if not event_ts:
            logger.info("Skipping message because it has no event timestamp")
            return

        event_id = f"{channel_id}:{event_ts}"
        if idempotency.is_processed(event_id):
            logger.info("Skipping duplicate event %s", event_id)
            return

        text = event.get("text", "")
        try:
            parsed = parse_metrics_message(text)
            previous = history.get_previous(channel_id)
            analysis = None
            analysis_source = "local"
            if groq_service is not None:
                analysis = groq_service.generate(parsed, previous)
                if analysis is not None:
                    analysis_source = "groq"
                    logger.info("Using Groq for insights on event %s", event_id)
                else:
                    logger.info("Groq returned no usable insights for event %s; falling back to local analysis", event_id)
            if analysis is None:
                analysis = analyze_metrics(parsed, previous)
                logger.info("Using local fallback analysis for event %s", event_id)
            converted = fx_service.convert(parsed)

            message_text = (
                f"*Converted metrics for {parsed.report_date.strftime('%d/%m/%Y')}*\n"
                f"Insight engine: {analysis_source}\n"
                f"Spend: ${converted.spend_usd:,.2f} USD (was ${parsed.spend_cad:,.2f} CAD)\n"
                f"CPC: ${converted.cpc_usd:,.2f} USD (was ${parsed.cpc_cad:,.2f} CAD)\n"
                f"CPM: ${converted.cpm_usd:,.2f} USD (was ${parsed.cpm_cad:,.2f} CAD)\n"
                f"CPL: ${converted.cpl_usd:,.2f} USD (was ${parsed.cpl_cad:,.2f} CAD)\n"
                f"Impressions: {parsed.impressions:,}\n"
                f"CTR: {parsed.ctr_percent:.2f}%\n"
                f"Link Clicks: {parsed.link_clicks}\n"
                f"Leads: {parsed.leads}\n"
                f"FX rate CAD->USD: {converted.fx_rate_cad_to_usd:.6f}\n\n"
                f"*Problems:*\n- " + "\n- ".join(analysis.problems) + "\n\n"
                f"*Solutions:*\n- " + "\n- ".join(analysis.solutions)
            )
            history.store(channel_id, parsed)

            idempotency.mark_processed(
                event_id=event_id,
                processed_at_utc_iso=datetime.now(timezone.utc).isoformat(),
            )

            logger.info("Converted metrics message delivered")

            # Generate and upload PDF report directly to Slack (no disk writes)
            try:
                current_metrics = {
                    "ad_spend": converted.spend_usd,
                    "ctr": parsed.ctr_percent,
                    "cpc": converted.cpc_usd,
                    "cpm": converted.cpm_usd,
                    "form_fills": parsed.leads,
                    "cost_per_form_fill": converted.cpl_usd,
                    "sales": 0,
                    "cost_per_sale": 0,
                    "revenue": 0,
                    "roas": 0,
                }
                pdf_bytes = render_report_html(
                    current_metrics=current_metrics,
                    problems=analysis.problems,
                    solutions=analysis.solutions,
                    report_date=parsed.report_date.strftime('%b %d, %Y'),
                    template_dir='.'
                )
                upload_pdf_to_channel(
                    client=client,
                    channel_id=channel_id,
                    pdf_bytes=pdf_bytes,
                    filename=f"Weekly_Report_{parsed.report_date.strftime('%b_%d_%Y')}.pdf",
                    message_text=f"Weekly Report for {parsed.report_date.strftime('%B %d, %Y')}",
                )
                logger.info("PDF report uploaded for event %s", event_id)
            except Exception as pdf_exc:
                logger.exception("Failed to generate PDF for event %s: %s", event_id, pdf_exc)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to process report event: %s", exc)
            # Optional operator alert can be added here.

    SocketModeHandler(app, settings.slack_app_token).start()


if __name__ == "__main__":
    main()
