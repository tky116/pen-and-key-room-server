# tests/database/repositories/test_shape_repository.py

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.database.repositories.shape_repository import ShapeRepository


class TestShapeRepository:
    @pytest.fixture
    def mock_shape_data(self):
        """ テスト用の形状データを生成 """
        return {
            "id": "circle",
            "name_ja": "円",
            "name_en": "Circle",
            "prefab_name": "CirclePrefab",
            "description_ja": "円の形状",
            "description_en": "Circle shape",
        }

    @pytest.fixture
    def mock_connection_and_cursor(self):
        """ モックされた接続とカーソルを生成 """
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        return mock_connection, mock_cursor

    def test_insert_shape(self, mock_shape_data, mock_connection_and_cursor):
        """ 形状データの挿入テスト
        - 挿入した形状IDが期待値と一致すること
        - データベースへの挿入クエリが1回実行されること
        - 挿入パラメータが正確であること
        - トランザクションがコミットされること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        with patch(
            "src.database.connection.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = ShapeRepository._ensure_connection
            ShapeRepository._ensure_connection = mock_ensure_connection

            try:
                repository = ShapeRepository()
                shape_id = repository.insert_shape(mock_shape_data)

                # 検証
                assert shape_id == mock_shape_data["id"]
                mock_cursor.execute.assert_called_once()

                # クエリパラメータの検証
                called_args = mock_cursor.execute.call_args[0]
                assert "INSERT INTO mstr_shapes" in called_args[0]
                params = called_args[1]

                # パラメータの詳細検証
                assert params["id"] == "circle"
                assert params["name_ja"] == "円"
                assert params["name_en"] == "Circle"
                assert params["prefab_name"] == "CirclePrefab"
                assert params["description_ja"] == "円の形状"
                assert params["description_en"] == "Circle shape"

                mock_connection.commit.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                ShapeRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_shape_by_id(self, mock_connection_and_cursor):
        """ 特定の形状取得テスト
        - 形状データが正常に取得されること
        - 取得した形状のIDが期待値と一致すること
        - 取得した形状の日本語名が正確であること
        - 取得した形状のプレハブ名が正確であること
        - データベース検索クエリが1回実行されること
        - 結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        # テストデータの準備
        test_shape_id = "circle"
        test_shape = {
            "id": test_shape_id,
            "name_ja": "円",
            "name_en": "Circle",
            "prefab_name": "CirclePrefab",
            "description_ja": "円の形状",
            "description_en": "Circle shape",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        mock_cursor.fetchone.return_value = test_shape

        with patch(
            "src.database.connection.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = ShapeRepository._ensure_connection
            ShapeRepository._ensure_connection = mock_ensure_connection

            try:
                repository = ShapeRepository()
                shape = await repository.get_shape_by_id(test_shape_id)

                # 検証
                assert shape is not None
                assert shape["id"] == test_shape_id
                assert shape["name_ja"] == "円"
                assert shape["prefab_name"] == "CirclePrefab"

                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchone.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                ShapeRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_all_shapes(self, mock_connection_and_cursor):
        """ 全ての形状取得テスト
        - 形状データのリストが正常に取得されること
        - 取得したデータの件数が期待値と一致すること
        - 各形状のIDが正確であること
        - 各形状のプレハブ名が正確であること
        - データベース検索クエリが1回実行されること
        - 全結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        # テストデータの準備
        test_shapes = [
            {
                "id": "circle",
                "name_ja": "円",
                "name_en": "Circle",
                "prefab_name": "CirclePrefab",
                "description_ja": "円の形状",
                "description_en": "Circle shape",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
            {
                "id": "square",
                "name_ja": "四角",
                "name_en": "Square",
                "prefab_name": "SquarePrefab",
                "description_ja": "四角の形状",
                "description_en": "Square shape",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
        ]
        mock_cursor.fetchall.return_value = test_shapes

        with patch(
            "src.database.connection.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = ShapeRepository._ensure_connection
            ShapeRepository._ensure_connection = mock_ensure_connection

            try:
                repository = ShapeRepository()
                shapes = await repository.get_all_shapes()

                # 検証
                assert len(shapes) == 2
                assert shapes[0]["id"] == "circle"
                assert shapes[1]["id"] == "square"
                assert shapes[0]["prefab_name"] == "CirclePrefab"
                assert shapes[1]["prefab_name"] == "SquarePrefab"

                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchall.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                ShapeRepository._ensure_connection = original_method
