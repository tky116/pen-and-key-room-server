# src/database/repositories/results_repository.py

from typing import Dict, Any

from .base_repository import BaseRepository


class ResultsRepository(BaseRepository):
    """ リザルトのテーブル操作を行うリポジトリ """
    async def insert_result(self, result_data: Dict[str, Any]) -> str:
        """ リザルトを挿入

        Args:
            result_data (Dict[str, Any]): リザルトデータ
        Returns:
            str: リザルトID
        """
        query = """
            INSERT INTO results (
                result_id, drawing_id, shape_id,
                success
            ) VALUES (
                %(result_id)s, %(drawing_id)s, %(shape_id)s,
                %(success)s
            )
        """
        params = {
            "result_id": result_data["result_id"],
            "drawing_id": result_data["drawing_id"],
            "shape_id": result_data["shape_id"],
            "success": result_data["success"]
        }
        await self.execute_update(query, params)
        return result_data["result_id"]
