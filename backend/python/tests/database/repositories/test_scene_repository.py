# tests/database/repositories/test_scene_repository.py

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.database.repositories.scene_repository import SceneRepository


class TestSceneRepository:
    @pytest.fixture
    def mock_scene_data(self):
        """ テスト用のシーンデータを生成 """
        return {
            "id": "test_scene_001",
            "name_ja": "テストシーン",
            "name_en": "Test Scene",
            "available_shapes": ["circle", "square", "triangle"],
            "description_ja": "テスト用のシーンです",
            "description_en": "This is a test scene",
        }

    @pytest.fixture
    def mock_connection_and_cursor(self):
        """ モックされた接続とカーソルを生成 """
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        return mock_connection, mock_cursor

    def test_insert_scene(self, mock_scene_data, mock_connection_and_cursor):
        """ シーンデータの挿入テスト
        - 挿入したシーンIDが期待値と一致すること
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

            original_method = SceneRepository._ensure_connection
            SceneRepository._ensure_connection = mock_ensure_connection

            try:
                repository = SceneRepository()
                scene_id = repository.insert_scene(mock_scene_data)

                # 検証
                assert scene_id == mock_scene_data["id"]
                mock_cursor.execute.assert_called_once()

                # クエリパラメータの検証
                called_args = mock_cursor.execute.call_args[0]
                assert "INSERT INTO mstr_scenes" in called_args[0]
                params = called_args[1]

                # パラメータの詳細検証
                assert params["id"] == mock_scene_data["id"]
                assert params["name_ja"] == "テストシーン"
                assert params["name_en"] == "Test Scene"
                assert params["available_shapes"] == json.dumps(
                    mock_scene_data["available_shapes"]
                    )
                assert params["description_ja"] == "テスト用のシーンです"
                assert params["description_en"] == "This is a test scene"

                mock_connection.commit.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                SceneRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_scene_by_id(self, mock_connection_and_cursor):
        """ 特定のシーン取得テスト
        - シーンデータが正常に取得されること
        - 取得したシーンのIDが期待値と一致すること
        - 取得したシーンの日本語名が正確であること
        - 取得したシーンの利用可能な形状が正確であること
        - データベース検索クエリが1回実行されること
        - 結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        # テストデータの準備
        test_scene_id = "test_scene_001"
        test_scene = {
            "id": test_scene_id,
            "name_ja": "テストシーン",
            "name_en": "Test Scene",
            "available_shapes": json.dumps(["circle", "square"]),
            "description_ja": "テスト用のシーン",
            "description_en": "Test scene description",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        mock_cursor.fetchone.return_value = test_scene

        with patch(
            "src.database.connection.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = SceneRepository._ensure_connection
            SceneRepository._ensure_connection = mock_ensure_connection

            try:
                repository = SceneRepository()
                scene = await repository.get_scene_by_id(test_scene_id)

                # 検証
                assert scene is not None
                assert scene["id"] == test_scene_id
                assert scene["name_ja"] == "テストシーン"
                assert scene["available_shapes"] == ["circle", "square"]

                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchone.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                SceneRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_all_scenes(self, mock_connection_and_cursor):
        """ 全てのシーン取得テスト
        - シーンデータのリストが正常に取得されること
        - 取得したデータの件数が期待値と一致すること
        - 各シーンのIDが正確であること
        - 各シーンの利用可能な形状が正確であること
        - データベース検索クエリが1回実行されること
        - 全結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        # テストデータの準備
        test_scenes = [
            {
                "id": "scene_001",
                "name_ja": "シーン1",
                "name_en": "Scene 1",
                "available_shapes": json.dumps(["circle"]),
                "description_ja": "シーン1の説明",
                "description_en": "Scene 1 description",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
            {
                "id": "scene_002",
                "name_ja": "シーン2",
                "name_en": "Scene 2",
                "available_shapes": json.dumps(["square", "triangle"]),
                "description_ja": "シーン2の説明",
                "description_en": "Scene 2 description",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
        ]
        mock_cursor.fetchall.return_value = test_scenes

        with patch(
            "src.database.connection.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = SceneRepository._ensure_connection
            SceneRepository._ensure_connection = mock_ensure_connection

            try:
                repository = SceneRepository()
                scenes = await repository.get_all_scenes()

                # 検証
                assert len(scenes) == 2
                assert scenes[0]["id"] == "scene_001"
                assert scenes[1]["id"] == "scene_002"
                assert scenes[0]["available_shapes"] == ["circle"]
                assert scenes[1]["available_shapes"] == ["square", "triangle"]

                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchall.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                SceneRepository._ensure_connection = original_method
