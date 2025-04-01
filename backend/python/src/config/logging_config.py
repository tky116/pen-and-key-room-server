# src/config/logging_config.py
import logging
import sys


def setup_logging(log_level=logging.INFO):
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,  # 明示的にstdoutを指定
        force=True,  # 既存の設定を上書き
    )
