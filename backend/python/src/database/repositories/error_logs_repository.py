# src/database/repositories/error_logs_repository.py

from typing import Dict, Any

from .base_repository import BaseRepository


class ErrorLogsRepository(BaseRepository):
    """ エラーログのテーブル操作を行うリポジトリ """
    async def insert_error_log(self, error_log: Dict[str, Any]) -> str:
        """ エラーログを挿入する

        Args:
            error_log (Dict[str, Any]): エラーログデータ
        Returns:
            str: エラーログID
        """
        query = """
            INSERT INTO error_logs (
                error_id, result_id, drawing_id, scene_id,
                error_type, error_message, stack_trace
            ) VALUES (
                %(error_id)s, %(result_id)s, %(drawing_id)s,
                %(scene_id)s, %(error_type)s, %(error_message)s,
                %(stack_trace)s
            )
        """
        params = {
            "error_id": error_log["error_id"],
            "result_id": error_log.get("result_id"),
            "drawing_id": error_log.get("drawing_id"),
            "scene_id": error_log.get("scene_id"),
            "error_type": error_log["error_type"],
            "error_message": error_log["error_message"],
            "stack_trace": error_log.get("stack_trace")
        }
        await self.execute_update(query, params)
        return error_log["error_id"]
