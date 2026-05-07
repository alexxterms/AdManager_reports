from __future__ import annotations

import logging
import os
import threading

from src.app import run_worker
from src.oauth_web import create_web_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("admanager_reports")


def main() -> None:
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    logger.info("Started Slack Socket Mode worker thread")

    web_app = create_web_app()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))
    logger.info("Starting OAuth web server on %s:%s", host, port)
    web_app.run(host=host, port=port)


if __name__ == "__main__":
    main()
