# tests/database/repositories/test_results_repository.py

import uuid
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.database.repositories.results_repository import ResultsRepository


class TestResultsRepository:
    @pytest.fixture
    def mock_result_data(self):
        """ テスト用の結果データを生成 """
        return {
            "id": str(uuid.uuid4()),
            "drawing_id": str(uuid.uuid4()),
            "shape_id": "test_shape",
            "confidence_score": 0.95,
            "reasoning": "Test AI reasoning",
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

    def test_insert_result(self, mock_result_data, mock_connection_and_cursor):
        """ 結果データの挿入テスト
        - 挿入した結果IDが期待値と一致すること
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

            original_method = ResultsRepository._ensure_connection
            ResultsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = ResultsRepository()
                result_id = repository.insert_result(mock_result_data)

                # 検証
                assert result_id == mock_result_data["id"]
                mock_cursor.execute.assert_called_once()

                # クエリパラメータの検証
                called_args = mock_cursor.execute.call_args[0]
                assert "INSERT INTO results" in called_args[0]
                params = called_args[1]

                # パラメータの詳細検証
                assert params["id"] == mock_result_data["id"]
                assert params["drawing_id"] == mock_result_data["drawing_id"]
                assert params["shape_id"] == mock_result_data["shape_id"]
                assert params["confidence_score"] == mock_result_data[
                    "confidence_score"
                    ]
                assert params["reasoning"] == mock_result_data["reasoning"]
                assert params["success"] == mock_result_data["success"]
                assert params["error_message"] == mock_result_data[
                    "error_message"
                    ]

                mock_connection.commit.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                ResultsRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_results_by_drawing_id(self, mock_connection_and_cursor):
        """ 特定の描画IDに紐づく結果取得テスト
        - 結果データが正常に取得されること
        - 取得した結果のIDが正確であること
        - 取得した結果の描画IDが一致すること
        - 取得した結果のshape_idが正確であること
        - データベース検索クエリが1回実行されること
        - 結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        # テストデータの準備
        test_drawing_id = str(uuid.uuid4())
        test_result = {
            "id": str(uuid.uuid4()),
            "drawing_id": test_drawing_id,
            "shape_id": "test_shape",
            "confidence_score": 0.95,
            "reasoning": "Test reasoning",
            "success": True,
            "error_message": None,
            "created_at": datetime.now(),
        }
        mock_cursor.fetchone.return_value = test_result

        with patch(
            "src.database.connection.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = ResultsRepository._ensure_connection
            ResultsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = ResultsRepository()
                result = await repository.get_results_by_drawing_id(
                    test_drawing_id
                    )

                # 検証
                assert result is not None
                assert result["id"] == test_result["id"]
                assert result["drawing_id"] == test_drawing_id
                assert result["shape_id"] == "test_shape"
                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchone.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                ResultsRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_results_by_drawing_id_not_found(
            self,
            mock_connection_and_cursor
            ):
        """ 存在しない描画IDの結果取得テスト
        - 存在しない描画IDで結果が取得できないこと（Noneが返されること）
        - データベース検索クエリが1回実行されること
        - 結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor
        mock_cursor.fetchone.return_value = None

        with patch(
            "src.database.connection.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = ResultsRepository._ensure_connection
            ResultsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = ResultsRepository()
                result = await repository.get_results_by_drawing_id(
                    str(uuid.uuid4())
                    )

                # 検証
                assert result is None
                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchone.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                ResultsRepository._ensure_connection = original_method

    @pytest.mark.asyncio
    async def test_get_all_results(self, mock_connection_and_cursor):
        """ 全ての結果取得テスト
        - 結果データのリストが正常に取得されること
        - 取得したデータの件数が期待値と一致すること
        - 各結果のIDが正確であること
        - データベース検索クエリが1回実行されること
        - 全結果取得メソッドが1回呼ばれること
        - カーソルがクローズされること
        """
        mock_connection, mock_cursor = mock_connection_and_cursor

        # テストデータの準備
        test_results = [
            {
                "id": str(uuid.uuid4()),
                "drawing_id": str(uuid.uuid4()),
                "shape_id": "test_shape_1",
                "confidence_score": 0.95,
                "reasoning": "Test reasoning 1",
                "success": True,
                "error_message": None,
                "created_at": datetime.now(),
            },
            {
                "id": str(uuid.uuid4()),
                "drawing_id": str(uuid.uuid4()),
                "shape_id": "test_shape_2",
                "confidence_score": 0.85,
                "reasoning": "Test reasoning 2",
                "success": True,
                "error_message": None,
                "created_at": datetime.now(),
            },
        ]
        mock_cursor.fetchall.return_value = test_results

        with patch(
            "src.database.connection.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):

            def mock_ensure_connection(self):
                self.conn = mock_connection

            original_method = ResultsRepository._ensure_connection
            ResultsRepository._ensure_connection = mock_ensure_connection

            try:
                repository = ResultsRepository()
                results = await repository.get_all_results()

                # 検証
                assert len(results) == 2
                assert results[0]["id"] == test_results[0]["id"]
                assert results[1]["id"] == test_results[1]["id"]
                mock_cursor.execute.assert_called_once()
                mock_cursor.fetchall.assert_called_once()
                mock_cursor.close.assert_called_once()
            finally:
                ResultsRepository._ensure_connection = original_method
