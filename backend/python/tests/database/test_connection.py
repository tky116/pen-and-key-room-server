# tests/database/test_connection.py

import os
import pytest
from unittest.mock import patch, MagicMock
import mysql.connector

from src.database.connection import DatabaseConnection

class TestDatabaseConnection:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """各テスト前にデータベース接続インスタンスをリセット"""
        DatabaseConnection._instance = None

    @patch.dict(os.environ, {
        "DB_ENV": "dev",
        "DB_HOST": "test_host",
        "DB_PORT": "3307",
        "DB_NAME": "vrdb01",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_pass"
    }, clear=True)
    def test_get_connection_first_call(self):
        """初回接続テスト
        - 初回呼び出し時に新しいデータベース接続が作成されること
        - 環境変数から取得した値が接続情報に使用されること
        - 接続メソッドが正しいパラメータで呼び出されること
        - コネクションプールが正しく設定されること
        """
        with patch("mysql.connector.connect") as mock_connect:
            # モック接続オブジェクトの準備
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection
            
            # カーソルのモック作成
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value = mock_cursor

            # 接続メソッド呼び出し
            connection = DatabaseConnection.get_connection()

            # 接続パラメータの検証
            mock_connect.assert_called_once_with(
                host="test_host",
                port=3306,
                database="vrdb01",
                user="test_user",
                password="test_pass",
                connection_timeout=10,
                pool_name="vrdb_pool",
                pool_size=5
            )

            # セッション設定の検証
            mock_cursor.execute.assert_any_call(
                "SET SESSION wait_timeout=28800"
                )
            mock_cursor.execute.assert_any_call("SET NAMES utf8mb4")
            mock_cursor.close.assert_called_once()

            # 返された接続オブジェクトの検証
            assert connection == mock_connection

    def test_get_connection_existing_connection(self):
        """既存接続の再利用テスト
        - 接続が有効な場合、後続の呼び出しで同じ接続インスタンスが返されること
        - 既存の接続がアクティブな場合、接続が1回だけ作成されること
        """
        with patch("mysql.connector.connect") as mock_connect:
            # 有効な接続をモック
            mock_connection = MagicMock()
            mock_connection.is_connected.return_value = True
            mock_connect.return_value = mock_connection

            # セッション設定用のカーソルをモック
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value = mock_cursor

            # 最初の接続
            first_connection = DatabaseConnection.get_connection()
            # 2回目の接続
            second_connection = DatabaseConnection.get_connection()

            # 接続メソッドが1回だけ呼び出されたことを検証
            mock_connect.assert_called_once()
            # 同じ接続インスタンスが返されることを検証
            assert first_connection == second_connection

    def test_connection_timeout_handling(self):
        """タイムアウト処理テスト
        - 接続タイムアウトが発生した場合、適切に処理されること
        - リトライロジックが正しく動作すること
        """
        with patch("mysql.connector.connect") as mock_connect, \
                patch("time.sleep") as mock_sleep:
            # タイムアウトエラーをシミュレート
            mock_connect.side_effect = [
                mysql.connector.errors.OperationalError(
                    2013,  # CR_SERVER_LOST error number
                    "Connection timed out"
                ),
                MagicMock()  # 2回目は成功
            ]

            # 接続の取得
            DatabaseConnection.get_connection()

            # 接続とリトライの検証
            assert mock_connect.call_count == 2
            assert mock_sleep.call_count == 1

    def test_get_connection_retry_logic(self):
        """接続リトライロジックテスト
        - 接続が失敗した場合、リトライロジックが正しく動作すること
        - メソッドが諦める前に複数回の再接続を試みること
        - エラー時の待機時間が適切であること
        """
        with patch("mysql.connector.connect") as mock_connect, \
                patch("time.sleep") as mock_sleep:
            # 接続失敗をシミュレート
            mock_connect.side_effect = [
                mysql.connector.Error("Connection failed"),
                mysql.connector.Error("Connection failed"),
                MagicMock()  # 3回目で成功
            ]

            # 接続の取得
            DatabaseConnection.get_connection()

            # リトライ回数と待機時間の検証
            assert mock_connect.call_count == 3
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(2)  # 待機時間の検証

    def test_close_connection(self):
        """接続クローズテスト
        - 接続が正しく閉じられること
        - インスタンスがNoneにリセットされること
        - コネクションプールが適切にクリーンアップされること
        """
        with patch("mysql.connector.connect") as mock_connect:
            # モック接続の準備
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection

            # 接続の取得と終了
            DatabaseConnection.get_connection()
            DatabaseConnection.close_connection()

            # クローズ処理の検証
            mock_connection.close.assert_called_once()
            assert DatabaseConnection._instance is None

    def test_connection_with_default_values(self):
        """デフォルト値テスト
        - 環境変数が設定されていない場合、デフォルト値が使用されること
        - デフォルトのコネクションプール設定が適用されること
        """
        with patch.dict(os.environ, clear=True), \
                patch("mysql.connector.connect") as mock_connect:
            # モック接続とカーソルの準備
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value = mock_cursor

            # 接続の取得
            DatabaseConnection.get_connection()

            # デフォルト値での接続検証
            mock_connect.assert_called_once_with(
                host="mysql",
                port=3306,
                database="vrdb01",
                user="db_user",
                password="db_pass",
                connection_timeout=10,
                pool_name="vrdb_pool",
                pool_size=5
            )
