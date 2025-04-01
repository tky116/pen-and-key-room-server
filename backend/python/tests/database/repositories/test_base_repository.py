# tests/database/repositories/test_base_repository.py

import pytest
from unittest.mock import MagicMock, patch

from src.database.repositories.base_repository import BaseRepository


class TestBaseRepository:
    def test_ensure_connection_success(self):
        """ データベース接続の確立テスト - 成功ケース
        - データベース接続が正常に確立されること
        - 接続オブジェクトが正確に設定されること
        """
        mock_connection = MagicMock()

        with patch(
            "src.database.repositories.base_repository.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):
            repository = BaseRepository()

            assert repository.conn == mock_connection

    def test_ensure_connection_failure(self):
        """ データベース接続の確立テスト - 失敗ケース
        - 接続失敗時にコネクションオブジェクトがNoneになること
        - 例外が適切に処理されること
        """
        with patch(
            "src.database.repositories.base_repository.DatabaseConnection.get_connection",
            side_effect=Exception("Connection failed"),
        ):
            repository = BaseRepository()

            assert repository.conn is None

    def test_execute_with_retry_success(self):
        """ _execute_with_retryメソッドのテスト - 成功ケース
        - 操作が正常に実行されること
        - 期待する戻り値が返されること
        - 操作が1回で成功すること
        """
        mock_connection = MagicMock()

        def test_operation(arg1, arg2):
            return arg1 + arg2

        with patch(
            "src.database.repositories.base_repository.DatabaseConnection.get_connection",
            return_value=mock_connection,
        ):
            repository = BaseRepository()

            result = repository._execute_with_retry(test_operation, 2, 3)

            assert result == 5

    def test_execute_with_retry_connection_failure(self):
        """ _execute_with_retryメソッド - 接続失敗リトライテスト
        - 複数回の接続失敗後に操作が成功すること
        - リトライメカニズムが正常に動作すること
        - 最終的に期待する結果が返されること
        """
        # テスト用の操作関数
        def test_operation():
            return "success"

        with patch(
            "src.database.repositories.base_repository.DatabaseConnection.get_connection",
            side_effect=[
                Exception("First connection failed"),
                Exception("Second connection failed"),
                MagicMock(),  # 3回目の呼び出しで成功
            ],
        ):
            repository = BaseRepository()

            result = repository._execute_with_retry(test_operation)

            assert result == "success"

    def test_execute_with_retry_ultimate_failure(self):
        """ _execute_with_retryメソッド - 最終的な接続失敗
        - すべての接続試行が失敗した場合に例外が発生すること
        - 例外メッセージが適切であること
        """
        # テスト用の操作関数
        def test_operation():
            return "success"

        with patch(
            "src.database.repositories.base_repository.DatabaseConnection.get_connection",
            side_effect=Exception("Connection always fails"),
        ):
            repository = BaseRepository()

            with pytest.raises(Exception, match="Could not establish database connection"):
                repository._execute_with_retry(test_operation)
