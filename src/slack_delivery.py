from __future__ import annotations
from io import BytesIO

from slack_sdk import WebClient


def send_text_to_channel(
    client: WebClient,
    channel_id: str,
    message_text: str,
) -> None:
    client.chat_postMessage(channel=channel_id, text=message_text)
    
def upload_pdf_to_channel(
    client: WebClient,
    channel_id: str,
    pdf_bytes: bytes,
    filename: str = "weekly_report.pdf",
    message_text: str = "Weekly Report",
) -> None:
    """Upload a PDF file to a Slack channel from bytes."""
    client.files_upload_v2(
        channel=channel_id,
        file=BytesIO(pdf_bytes),
        filename=filename,
        title="Weekly Ad Manager Report",
        initial_comment=message_text,
    )
