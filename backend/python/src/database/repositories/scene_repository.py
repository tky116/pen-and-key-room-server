# src/database/repositories/scene_repository.py

import json
from typing import Dict, Any, Optional

from .base_repository import BaseRepository


class SceneRepository(BaseRepository):
    """ シーンのテーブル操作を行うリポジトリ """
    async def get_scene_by_id(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """ 任意のscene_idのシーンを取得

        Args:
            scene_id (str): シーンID
        Returns:
            Optional[Dict[str, Any]]: シーン情報
        """
        query = """
            SELECT 
                scene_id, shapes_list, 
                description_ja, description_en,
                created_at, updated_at
            FROM mstr_scenes
            WHERE scene_id = %s
        """
        result = await self.execute_one(query, (scene_id,))
        if result and result["shapes_list"]:
            result["shapes_list"] = json.loads(result["shapes_list"])
        return result
