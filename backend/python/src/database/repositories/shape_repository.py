# src/database/repositories/shape_repository.py

import logging
import json
from typing import Dict, Any, List, Optional

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ShapeRepository(BaseRepository):
    """ 形状のテーブル操作を行うリポジトリ """
    async def get_shape_info_by_id(self, shape_id: str) -> Optional[Dict[str, Any]]:
        """
        指定された shape_id に対応する情報（prefab_name, threshold）を取得する

        Args:
            shape_id (str): 形状ID

        Returns:
            Optional[Dict[str, Any]]: 形状情報（プレハブ名、閾値など）
        """
        query = """
            SELECT prefab_name, threshold
            FROM mstr_shapes
            WHERE shape_id = %s
            """
        return await self.execute_one(query, (shape_id,))

    async def get_available_shapes(self, scene_id: str) -> List[Dict[str, Any]]:
        """ 指定されたシーンIDに関連する形状情報を取得する

        Args:
            scene_id (str): シーンID
        Returns:
            List[Dict[str, Any]]: 形状情報のリスト
        """
        # シーンのshapes_listを取得
        scene_query = "SELECT shapes_list FROM mstr_scenes WHERE scene_id = %s"
        scene_data = await self.execute_one(scene_query, (scene_id,))

        if not scene_data:
            return []

        shape_ids = json.loads(scene_data['shapes_list'])
        if not shape_ids:
            return []

        # shape_idsに対応する形状情報を取得
        placeholders = ', '.join(['%s'] * len(shape_ids))
        shapes_query = f"""
            SELECT
                shape_id, prefab_name, threshold,
                name_ja, name_en, description_ja, description_en,
                positive_examples, negative_examples
            FROM mstr_shapes
            WHERE shape_id IN ({placeholders})
            """
        results = await self.execute_query(shapes_query, tuple(shape_ids))

        # JSON文字列をPythonオブジェクトに変換
        for result in results:
            if isinstance(result.get("positive_examples"), str):
                result["positive_examples"] = json.loads(result["positive_examples"])
            if isinstance(result.get("negative_examples"), str):
                result["negative_examples"] = json.loads(result["negative_examples"])

        return results
