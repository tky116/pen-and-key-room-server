# src/web_api/web_api.py

from aiohttp import web
import json
import logging
from datetime import datetime

from src.database.repositories.drawings_repository import DrawingsRepository

logger = logging.getLogger(__name__)


class WebAPI:
    def __init__(self):
        self.drawings_repository = DrawingsRepository()
        self.app = web.Application()
        self.setup_routes()

    def datetime_handler(self, obj):
        """datetimeオブジェクトをISO形式の文字列に変換

        Args:
            obj: datetimeオブジェクト
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def setup_routes(self):
        """ルーティングを設定"""
        self.app.router.add_get("/api/drawings", self.fetch_drawings)
        self.app.router.add_get("/api/drawings/{id}", self.fetch_drawing)
        self.app.add_routes([web.static("/viewer", "/usr/share/nginx/html/frontend/public")])

    async def fetch_drawings(self, request: web.Request) -> web.Response:
        """ 描画データの一覧を取得

        Args:
            request: リクエスト情報

        Returns:
            web.Response: レスポンス
        """
        try:
            drawings = await self.drawings_repository.get_drawings()
            return web.json_response(
                {"success": True, "data": drawings},
                dumps=lambda obj: json.dumps(obj, default=self.datetime_handler),
            )
        except Exception as e:
            logger.error(f"Error fetching drawings: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def fetch_drawing(self, request: web.Request) -> web.Response:
        """ 特定の描画データを取得

        Args:
            request: リクエスト情報

        Returns:
            web.Response: レスポンス
        """
        try:
            drawing_id = request.match_info["id"]
            drawing = await self.drawings_repository.get_drawing(drawing_id)

            if drawing is None:
                return web.json_response(
                    {"success": False, "error": "Drawing not found"}, status=404
                )

            return web.json_response(
                {"success": True, "data": drawing},
                dumps=lambda obj: json.dumps(obj, default=self.datetime_handler),
            )
        except Exception as e:
            logger.error(f"Error fetching drawing {drawing_id}: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def run(self, host: str = "0.0.0.0", port: int = 8080):
        """ サーバーを起動 

        Args:
            host: ホスト名
            port: ポート番号
        """
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"REST API server started on {host}:{port}")
