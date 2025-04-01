# tests/web_api/test_web_api.py

import uuid
from unittest.mock import patch
from aiohttp.test_utils import AioHTTPTestCase

from src.web_api import WebAPI


class TestWebAPI(AioHTTPTestCase):
    def assertMockPatched(self, target, *args, **kwargs):
        """ モックパッチのためのコンテキストマネージャ """
        return patch(target, *args, **kwargs)

    async def get_application(self):
        """ テスト用のWebアプリケーションを取得 """
        self.web_api = WebAPI()
        return self.web_api.app

    async def test_fetch_drawings_success(self):
        """ 描画データ一覧取得の成功テスト
        - HTTPステータスコードが200であること
        - レスポンスのsuccessフラグがTrueであること
        - 取得したデータ件数が1件であること
        - 取得したデータのIDが期待値と一致すること
        """
        # モックデータの準備
        mock_drawings = [
            {
                "id": str(uuid.uuid4()),
                "draw_timestamp": 1705708800000,
                "created_at": "2024-01-21T00:00:00",
                "ai_processing": True,
                "processed": False,
                "shape_id": "test_shape",
            }
        ]

        # DrawingsRepositoryのget_drawingsをモック
        with self.assertMockPatched(
            "src.web_api.DrawingsRepository.get_drawings",
            return_value=mock_drawings
        ):

            # GETリクエストを送信
            resp = await self.client.request("GET", "/api/drawings")

            # レスポンスの検証
            self.assertEqual(resp.status, 200)
            data = await resp.json()

            self.assertTrue(data["success"])
            self.assertEqual(len(data["data"]), 1)
            self.assertEqual(data["data"][0]["id"], mock_drawings[0]["id"])

    async def test_fetch_drawing_success(self):
        """ 特定の描画データ取得の成功テスト
        - HTTPステータスコードが200であること
        - レスポンスのsuccessフラグがTrueであること
        - 取得したデータ件数が1件であること
        - 取得したデータのIDが期待値と一致すること
        """
        # モックデータの準備
        test_drawing_id = str(uuid.uuid4())
        mock_drawing = {
            "id": test_drawing_id,
            "draw_timestamp": 1705708800000,
            "data": {"draw_lines": []},
            "center_x": 0.0,
            "center_y": 0.0,
            "center_z": 0.0,
            "shape_id": "test_shape",
            "confidence_score": 0.95,
            "reasoning": "Test reasoning",
        }

        # DrawingsRepositoryのget_drawingをモック
        with self.assertMockPatched(
            "src.web_api.DrawingsRepository.get_drawing",
            return_value=mock_drawing
        ):

            # GETリクエストを送信
            resp = await self.client.request(
                "GET",
                f"/api/drawings/{test_drawing_id}"
                )

            # レスポンスの検証
            self.assertEqual(resp.status, 200)
            data = await resp.json()

            self.assertTrue(data["success"])
            self.assertEqual(data["data"]["id"], test_drawing_id)
            self.assertEqual(data["data"]["shape_id"], "test_shape")

    async def test_fetch_drawing_not_found(self):
        """ 存在しない描画データ取得のテスト
        - HTTPステータスコードが404であること
        - レスポンスのsuccessフラグがFalseであること
        - エラーメッセージに「Drawing not found」が含まれること
        """
        # DrawingsRepositoryのget_drawingをモック
        test_drawing_id = str(uuid.uuid4())
        with self.assertMockPatched(
            "src.web_api.DrawingsRepository.get_drawing",
            return_value=None
        ):

            # GETリクエストを送信
            resp = await self.client.request(
                "GET",
                f"/api/drawings/{test_drawing_id}"
                )

            # レスポンスの検証
            self.assertEqual(resp.status, 404)
            data = await resp.json()

            self.assertFalse(data["success"])
            self.assertIn("Drawing not found", data["error"])

    async def test_fetch_drawings_repository_error(self):
        """ リポジトリでのエラー発生時のテスト
        - HTTPステータスコードが500であること
        - レスポンスのsuccessフラグがFalseであること
        - エラーメッセージに「Database error」が含まれること
        """
        # DrawingsRepositoryのget_drawingsをモック
        with self.assertMockPatched(
            "src.web_api.DrawingsRepository.get_drawings",
            side_effect=Exception("Database error"),
        ):

            # GETリクエストを送信
            resp = await self.client.request("GET", "/api/drawings")

            # レスポンスの検証
            self.assertEqual(resp.status, 500)
            data = await resp.json()

            self.assertFalse(data["success"])
            self.assertIn("Database error", data["error"])
