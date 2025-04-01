# src/database/repositories/features_repository.py

import json
from typing import Dict, Any, Optional
from .base_repository import BaseRepository


class FeaturesRepository(BaseRepository):
    """ 形状特徴量のテーブル操作を行うリポジトリ """

    async def insert_features(self, feature_data: Dict[str, Any]) -> str:
        """ 特徴量データを挿入

        Args:
            feature_data (Dict[str, Any]): 特徴量データ
        Returns:
            str: 特徴量ID
        """
        query = """
            INSERT INTO shape_features (
                feature_id,
                drawing_id,
                total_strokes,
                total_points,
                features
            ) VALUES (
                %(feature_id)s,
                %(drawing_id)s,
                %(total_strokes)s,
                %(total_points)s,
                %(features)s
            )
        """
        params = {
            "feature_id": feature_data["feature_id"],
            "drawing_id": feature_data["drawing_id"],
            "total_strokes": feature_data["total_strokes"],
            "total_points": feature_data["total_points"],
            "features": json.dumps(feature_data["features"])
        }
        await self.execute_update(query, params)
        return feature_data["feature_id"]

    async def get_features(self, drawing_id: str) -> Optional[Dict[str, Any]]:
        """ 描画データIDに紐づく特徴量を取得

        Args:
            drawing_id (str): 描画データID
        Returns:
            Optional[Dict[str, Any]]: 特徴量データ
        """
        query = """
            SELECT 
                feature_id,
                drawing_id,
                total_strokes,
                total_points,
                features,
                created_at
            FROM shape_features
            WHERE drawing_id = %s
        """
        result = await self.execute_one(query, (drawing_id,))
        if result and isinstance(result["features"], str):
            result["features"] = json.loads(result["features"])
        return result
