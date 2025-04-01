import asyncio
import logging

from src.config.logging_config import setup_logging
from src.grpc_server import start_grpc_server
from src.web_api import WebAPI

# ロガーの設定
setup_logging()
logger = logging.getLogger(__name__)


async def main():
    try:
        # gRPCサーバーとWebサーバーを非同期で起動
        grpc_task = asyncio.create_task(start_grpc_server())
        rest_api = WebAPI()
        rest_task = asyncio.create_task(rest_api.run())

        logger.info("All servers started successfully")

        # サーバーの終了を待機
        await asyncio.gather(grpc_task, rest_task)

    except KeyboardInterrupt:
        logger.info("Server stopping...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
