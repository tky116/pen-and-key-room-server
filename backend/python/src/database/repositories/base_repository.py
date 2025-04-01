import logging
from typing import Any, Optional
from ..connection import DatabaseConnection

logger = logging.getLogger(__name__)


class BaseRepository:
    """ リポジトリのベースクラス """

    async def execute_query(self, query: str, params: tuple = None) -> list[dict[str, Any]]:
        """ クエリを実行し、結果を返す

        Args:
            query (str): SQLクエリ
            params (tuple, optional): クエリパラメータ。デフォルトはNone
        Returns:
            list[dict[str, Any]]: クエリ結果のリスト
        """
        try:
            return await DatabaseConnection.execute_query(query, params)
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    async def execute_one(self, query: str, params: tuple = None) -> Optional[dict[str, Any]]:
        """ クエリを実行し、最初の結果を返す

        Args:
            query (str): SQLクエリ
            params (tuple, optional): クエリパラメータ。デフォルトはNone
        Returns:
            Optional[dict[str, Any]]: 最初のクエリ結果
        """
        results = await self.execute_query(query, params)
        return results[0] if results else None

    async def execute_update(self, query: str, params: tuple = None) -> int:
        """ クエリを実行し、更新行数を返す

        Args:
            query (str): SQLクエリ
            params (tuple, optional): クエリパラメータ。デフォルトはNone
        Returns:
            int: 更新された行数
        """
        try:
            pool = await DatabaseConnection.get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, params)
                    return cur.rowcount
        except Exception as e:
            logger.error(f"Update execution failed: {str(e)}")
            raise
