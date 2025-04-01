# tests/database/repositories/test_drawings_repository.py

import json
import uuid
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.database.repositories.drawings_repository import DrawingsRepository


class TestDrawingsRepository:
    @pytest.fixture
    def mock_drawing_data(self):
        """ テスト用の描画データを生成 """
        return {
            "id": str(uuid.uuid4()),
            "scene_id": "test_scene",
            "client_id": "test_client",
            "client_info": {
                "type": 1,
                "device_id": "device123",
                "device_name": "Test Device",
                "system_info": "Test System",
                "app_version": "1.0.0",
            },
            "draw_timestamp": 1705708800000,
            "data": {"draw_lines": []},
            "center_x": 0.0,
            "center_y": 0.0,
            "center_z": 0.0,
            "metadata": {"test_key": "test_value"},
            "ai_processing": True,
            "processed": False,
        }

    @pytest.fixture
    def mock_connection_and_cursor(self):
        """ モックされた接続とカーソルを生成 """
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        return mock_connection, mock_cursor

    def test_insert_drawings(
            self,
            mock_drawing_data,
            mock_connection_and_cursor
            ):
        """ 描画データの挿入テスト
        - 挿入した描画IDが期待値と一致すること
        - データベースへの挿入クエリが1回実行されること
        - 挿入パラメータが正確であること
        - トランザクションがコミットされること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        with patch(
            "src.database.repositories.drawings_repository.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            # モンキーパッチで_ensure_connectionメソッドを置き換え
            original_method = DrawingsRepository._ensure_connection
            DrawingsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = DrawingsRepository()
                result_id = repository.insert_drawings(mock_drawing_data)

                assert result_id == mock_drawing_data["id"]
                mock_cursor.execute.assert_called_once()

                # クエリパラメータの検証
                called_args = mock_cursor.execute.call_args[0]
                assert "INSERT INTO drawings" in called_args[0]
                params = called_args[1]

                # パラメータの詳細検証
                assert params["id"] == mock_drawing_data["id"]
                assert params["scene_id"] == "test_scene"
                assert params["client_id"] == "test_client"
                assert params["client_info"] == json.dumps(
                    mock_drawing_data["client_info"]
                    )
                assert params["draw_timestamp"] == 1705708800000
                assert params["data"] == json.dumps(mock_drawing_data["data"])
                assert params["center_x"] == 0.0
                assert params["center_y"] == 0.0
                assert params["center_z"] == 0.0
                assert params["metadata"] == json.dumps(
                    mock_drawing_data["metadata"]
                    )
                assert params["ai_processing"] is True
                assert params["processed"] is False

                mock_connection.commit.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                DrawingsRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_drawings(self, mock_connection_and_cursor):
        """ 描画データの一覧取得テスト
        - 描画データのリストが正常に取得されること
        - 取得したデータの件数が期待値と一致すること
        - 取得した描画のIDが正確であること
        - 描画のタイムスタンプが正確であること
        - データベース検索クエリが1回実行されること
        - 全結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        # テストデータの準備
        test_drawings = [
            {
                "id": str(uuid.uuid4()),
                "draw_timestamp": 1705708800000,
                "created_at": datetime.now(),
                "ai_processing": True,
                "processed": False,
                "shape_id": "test_shape",
            }
        ]
        mock_cursor.fetchall.return_value = test_drawings

        with patch(
            "src.database.repositories.drawings_repository.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = DrawingsRepository._ensure_connection
            DrawingsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = DrawingsRepository()
                drawings = await repository.get_drawings()

                assert len(drawings) == 1
                assert drawings[0]["id"] == test_drawings[0]["id"]
                assert drawings[0]["draw_timestamp"] == test_drawings[0][
                    "draw_timestamp"
                    ]
                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchall.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                DrawingsRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_drawing(self, mock_connection_and_cursor):
        """ 特定の描画データ取得テスト
        - 描画データが正常に取得されること
        - 取得した描画のIDが正確であること
        - データフィールドが正しく変換されること（辞書型）
        - メタデータフィールドが正しく変換されること（辞書型）
        - shape_idが正確であること
        - データベース検索クエリが1回実行されること
        - 結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        # テストデータの準備
        test_drawing_id = str(uuid.uuid4())
        test_drawing = {
            "id": test_drawing_id,
            "draw_timestamp": 1705708800000,
            "data": json.dumps({"draw_lines": []}),
            "metadata": json.dumps({"test_key": "test_value"}),
            "client_info": json.dumps({"type": 1}),
            "center_x": 0.0,
            "center_y": 0.0,
            "center_z": 0.0,
            "shape_id": "test_shape",
            "confidence_score": 0.95,
            "reasoning": "Test reasoning",
        }
        mock_cursor.fetchone.return_value = test_drawing

        with patch(
            "src.database.repositories.drawings_repository.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = DrawingsRepository._ensure_connection
            DrawingsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = DrawingsRepository()
                drawing = await repository.get_drawing(test_drawing_id)

                assert drawing is not None
                assert drawing["id"] == test_drawing_id
                assert isinstance(drawing["data"], dict)
                assert isinstance(drawing["metadata"], dict)
                assert drawing["shape_id"] == "test_shape"
                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchone.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                DrawingsRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_drawing_not_found(self, mock_connection_and_cursor):
        """ 存在しない描画データ取得テスト
        - 存在しない描画IDで結果が取得できないこと（Noneが返されること）
        - データベース検索クエリが1回実行されること
        - 結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor
        mock_cursor.fetchone.return_value = None

        with patch(
            "src.database.repositories.drawings_repository.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = DrawingsRepository._ensure_connection
            DrawingsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = DrawingsRepository()
                drawing = await repository.get_drawing(str(uuid.uuid4()))

                # 検証
                assert drawing is None
                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchone.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                DrawingsRepository._ensure_connection = original_method
