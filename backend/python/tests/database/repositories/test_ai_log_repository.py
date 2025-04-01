# tests/database/repositories/test_result_details_repository.py

import json
import uuid
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.database.repositories.result_details_repository import ResultDetailsRepository


class TestResultDetailsRepository:
    @pytest.fixture
    def mock_ai_log_data(self):
        """ テスト用のAIログデータを生成 """
        return {
            "id": str(uuid.uuid4()),
            "drawing_id": str(uuid.uuid4()),
            "client_id": "test_client",
            "scene_id": "test_scene",
            "shape_id": "circle",
            "confidence_score": 0.95,
            "process_time_ms": 250,
            "api_response": {"model": "test_model", "predictions": ["circle"]},
            "success": True,
            "error_message": None,
        }

    @pytest.fixture
    def mock_connection_and_cursor(self):
        """ モックされた接続とカーソルを生成 """
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        return mock_connection, mock_cursor

    def test_insert_detail(self, mock_ai_log_data, mock_connection_and_cursor):
        """ AIログデータの挿入テスト
        - 挿入したログIDが期待値と一致すること
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

            original_method = ResultDetailsRepository._ensure_connection
            ResultDetailsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = ResultDetailsRepository()
                log_id = repository.insert_detail(mock_ai_log_data)

                # 検証
                assert log_id == mock_ai_log_data["id"]
                mock_cursor.execute.assert_called_once()

                # クエリパラメータの検証
                called_args = mock_cursor.execute.call_args[0]
                assert "INSERT INTO logs_ai_processing" in called_args[0]
                params = called_args[1]

                # パラメータの詳細検証
                assert params["id"] == mock_ai_log_data["id"]
                assert params["drawing_id"] == mock_ai_log_data["drawing_id"]
                assert params["client_id"] == "test_client"
                assert params["scene_id"] == "test_scene"
                assert params["shape_id"] == "circle"
                assert params["confidence_score"] == 0.95
                assert params["process_time_ms"] == 250
                assert params["api_response"] == json.dumps(
                    mock_ai_log_data["api_response"]
                    )
                assert params["success"] is True
                assert params["error_message"] is None

                mock_connection.commit.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                ResultDetailsRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_log_by_id(self, mock_connection_and_cursor):
        """ 特定のAIログ取得テスト
        - AIログデータが正常に取得されること
        - 取得したログのIDが正確であること
        - APIレスポンスが正確に変換されること
        - 成功フラグが正確であること
        - データベース検索クエリが1回実行されること
        - 結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        # テストデータの準備
        test_log_id = str(uuid.uuid4())
        test_log = {
            "id": test_log_id,
            "drawing_id": str(uuid.uuid4()),
            "client_id": "test_client",
            "scene_id": "test_scene",
            "shape_id": "circle",
            "confidence_score": 0.95,
            "process_time_ms": 250,
            "api_response": json.dumps(
                {"model": "test_model", "predictions": ["circle"]}
                ),
            "success": True,
            "error_message": None,
            "created_at": datetime.now(),
        }
        mock_cursor.fetchone.return_value = test_log

        with patch(
            "src.database.connection.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = ResultDetailsRepository._ensure_connection
            ResultDetailsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = ResultDetailsRepository()
                log = await repository.get_log_by_id(test_log_id)

                # 検証
                assert log is not None
                assert log["id"] == test_log_id
                assert log["api_response"] == {
                    "model": "test_model", "predictions": ["circle"]
                    }
                assert log["success"] is True

                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchone.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                ResultDetailsRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_logs_by_drawing_id(self, mock_connection_and_cursor):
        """ 描画IDに関連するAIログ取得テスト
        - 指定した描画IDのログが正常に取得されること
        - 取得したログの件数が期待値と一致すること
        - 各ログの描画IDが一致すること
        - APIレスポンスが正確に変換されること
        - データベース検索クエリが1回実行されること
        - 結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        # テストデータの準備
        test_drawing_id = str(uuid.uuid4())
        test_logs = [
            {
                "id": str(uuid.uuid4()),
                "drawing_id": test_drawing_id,
                "client_id": "test_client",
                "scene_id": "test_scene",
                "shape_id": "circle",
                "confidence_score": 0.95,
                "process_time_ms": 250,
                "api_response": json.dumps({"model": "test_model"}),
                "success": True,
                "error_message": None,
                "created_at": datetime.now(),
            },
            {
                "id": str(uuid.uuid4()),
                "drawing_id": test_drawing_id,
                "client_id": "test_client",
                "scene_id": "test_scene",
                "shape_id": "square",
                "confidence_score": 0.85,
                "process_time_ms": 200,
                "api_response": json.dumps({"model": "test_model_2"}),
                "success": True,
                "error_message": None,
                "created_at": datetime.now(),
            },
        ]
        mock_cursor.fetchall.return_value = test_logs

        with patch(
            "src.database.connection.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = ResultDetailsRepository._ensure_connection
            ResultDetailsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = ResultDetailsRepository()
                logs = await repository.get_logs_by_drawing_id(test_drawing_id)

                assert len(logs) == 2
                assert logs[0]["drawing_id"] == test_drawing_id
                assert logs[1]["drawing_id"] == test_drawing_id
                assert logs[0]["api_response"] == {"model": "test_model"}
                assert logs[1]["api_response"] == {"model": "test_model_2"}

                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchall.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                ResultDetailsRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_recent_ai_logs(self, mock_connection_and_cursor):
        """ 最近のAIログ取得テスト
        - 最近のAIログが正常に取得されること
        - 取得したログの件数が制限値と一致すること
        - 各ログのAPIレスポンスが正確であること
        - データベース検索クエリが1回実行されること
        - 結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        # テストデータの準備
        test_logs = [
            {
                "id": str(uuid.uuid4()),
                "drawing_id": str(uuid.uuid4()),
                "client_id": "test_client_1",
                "scene_id": "test_scene_1",
                "shape_id": "circle",
                "confidence_score": 0.95,
                "process_time_ms": 250,
                "api_response": json.dumps({"model": "test_model_1"}),
                "success": True,
                "error_message": None,
                "created_at": datetime.now(),
            },
            {
                "id": str(uuid.uuid4()),
                "drawing_id": str(uuid.uuid4()),
                "client_id": "test_client_2",
                "scene_id": "test_scene_2",
                "shape_id": "square",
                "confidence_score": 0.85,
                "process_time_ms": 200,
                "api_response": json.dumps({"model": "test_model_2"}),
                "success": True,
                "error_message": None,
                "created_at": datetime.now(),
            },
        ]
        mock_cursor.fetchall.return_value = test_logs

        with patch(
            "src.database.connection.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = ResultDetailsRepository._ensure_connection
            ResultDetailsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = ResultDetailsRepository()
                logs = await repository.get_recent_ai_logs(limit=2)

                # 検証
                assert len(logs) == 2
                assert logs[0]["api_response"] == {"model": "test_model_1"}
                assert logs[1]["api_response"] == {"model": "test_model_2"}

                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchall.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                ResultDetailsRepository._ensure_connection = original_method
