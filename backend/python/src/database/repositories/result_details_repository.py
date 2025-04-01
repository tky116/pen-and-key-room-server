# src/database/repositories/result_details_repository.py

import json
from typing import Dict, Any

from .base_repository import BaseRepository


class ResultDetailsRepository(BaseRepository):
    """ リザルト詳細のテーブル操作を行うリポジトリ """
    async def insert_detail(self, log_data: Dict[str, Any]) -> str:
        """ リザルト詳細を挿入

        Args:
            log_data (Dict[str, Any]): リザルト詳細データ
        Returns:
            str: リザルトID
        """
        query = """
            INSERT INTO result_details (
                result_id, drawing_id, scene_id,
                shape_id, success, score,
                reasoning, process_time_ms,
                model_name, api_response,
                error_message, client_id
            ) VALUES (
                %(result_id)s, %(drawing_id)s, %(scene_id)s,
                %(shape_id)s, %(success)s, %(score)s,
                %(reasoning)s, %(process_time_ms)s,
                %(model_name)s, %(api_response)s,
                %(error_message)s, %(client_id)s
            )
        """
        params = log_data.copy()
        if "api_response" in params:
            params["api_response"] = json.dumps(params["api_response"])

        await self.execute_update(query, params)
        return log_data["result_id"]
