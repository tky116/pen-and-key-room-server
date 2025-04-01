# src/database/repositories/drawings_repository.py

import json
from typing import Dict, Any, List, Optional

from .base_repository import BaseRepository


class DrawingsRepository(BaseRepository):
    """ 描画データのテーブル操作を行うリポジトリ """

    async def insert_drawings(self, drawing_data: Dict[str, Any]) -> str:
        """ 描画データを挿入

        Args:
            drawing_data (Dict[str, Any]): 描画データ
        Returns:
            str: 描画データID
        """
        query = """
            INSERT INTO drawings (
                drawing_id, scene_id, draw_timestamp, draw_lines,
                center_x, center_y, center_z, use_ai,
                client_id, client_info, metadata
            ) VALUES (
                %(drawing_id)s, %(scene_id)s, %(draw_timestamp)s, 
                %(draw_lines)s, %(center_x)s, %(center_y)s, %(center_z)s,
                %(use_ai)s, %(client_id)s, %(client_info)s, %(metadata)s
            )
        """
        params = {
            "drawing_id": drawing_data["drawing_id"],
            "scene_id": drawing_data["scene_id"],
            "draw_timestamp": drawing_data["draw_timestamp"],
            "draw_lines": json.dumps(drawing_data["draw_lines"]),
            "center_x": drawing_data["center_x"],
            "center_y": drawing_data["center_y"],
            "center_z": drawing_data["center_z"],
            "use_ai": drawing_data["use_ai"],
            "client_id": drawing_data["client_id"],
            "client_info": json.dumps(drawing_data["client_info"]),
            "metadata": json.dumps(drawing_data.get("metadata", {})),
        }
        await self.execute_update(query, params)
        return drawing_data["drawing_id"]

    async def get_drawings(self) -> List[Dict[str, Any]]:
        """ 描画データを全て取得

        Returns:
            List[Dict[str, Any]]: 描画データのリスト
        """
        query = """
        SELECT 
            drawing_id,
            draw_timestamp,
            created_at,
            use_ai
        FROM drawings
        ORDER BY created_at DESC;
        """
        return await self.execute_query(query)

    async def get_drawing(self, drawing_id: str) -> Optional[Dict[str, Any]]:
        """ 任意のdrawing_idの描画データを取得 """
        query = """
            SELECT *
            FROM drawings
            WHERE drawing_id = %s
        """
        result = await self.execute_one(query, (drawing_id,))
        if result:
            if isinstance(result["draw_lines"], str):
                result["draw_lines"] = json.loads(result["draw_lines"])
            result["metadata"] = json.loads(result.get("metadata") or "{}")
            result["client_info"] = json.loads(result.get("client_info") or "{}")
        return result
