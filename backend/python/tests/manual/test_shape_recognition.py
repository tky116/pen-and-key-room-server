# test_shape_recognition.py

"""
- マスタ
b59105dc-7b28-4fcf-9f76-fc8aecf3afbd

- Aグループ
3a0f6a94-e1ba-4d60-87d5-460a02d8d2f8
5592560e-294c-4089-ac30-df2c87095866
6344f293-6285-4f3e-a9a8-014c256a86ce
6c9cc4cb-c186-44c6-8243-f57cf3f7ea10
a2b2a1df-0f90-440b-9707-72d9505a6406
bdfcbb9a-d6d5-4b7e-8fad-7e46d0052fb5
c27efc24-d91d-4eb5-add5-ec9a22d06eb5
e525bd83-bfd0-47e5-9a31-a623618ca272
fd51c8e8-8c06-4041-832c-8754d13eb5f3

- Bグループ
926c1582-1fca-4626-b36d-522b1d0e1cee
b1c6f548-a27a-4a81-b042-03fa6d8ea1c0
b3861c9b-3ee2-4bfd-ab86-776a8fc3b4c6
d900615f-6297-4e7e-ad2b-3c9d0bc8d58d

- BOTHグループ
20de84e5-7df0-4f74-bb6c-ccbd1460ca60
48df1f17-ead7-4863-ac7d-8b8ff2c4b57a
51fcd4c4-ce7f-4bfc-b2fe-244ebd92c2cf
5444bd7a-7c01-4978-a557-4ac11d3566fb
73fa23bc-9ff2-4e7b-b5a2-80b44e5680a4
a4da1317-1aec-4458-996a-5b0ea38ec495
dbfcf684-9d52-4ac7-abcd-f304d9f7e39a
dec078bb-755f-4b6d-ad3a-02c40af6d25d
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from src.database.repositories.drawings_repository import DrawingsRepository
from src.database.repositories.shape_repository import ShapeRepository
from src.database.repositories.features_repository import FeaturesRepository
from src.database.repositories.results_repository import ResultsRepository
from src.database.repositories.result_details_repository import ResultDetailsRepository
from src.features.feature_extractor import FeatureExtractor
from src.ai_service.service_manager import AIServiceManager
from src.database.connection import DatabaseConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Position:
    x: float
    y: float
    z: float


@dataclass
class DrawLine:
    positions: List[Position]
    width: float
    color: Optional[Dict[str, float]]


@dataclass
class DrawingData:
    draw_lines: List[DrawLine]
    center: Position


class ShapeRecognitionTester:
    def __init__(self):
        self.drawings_repository = DrawingsRepository()
        self.shape_repository = ShapeRepository()
        self.features_repository = FeaturesRepository()
        self.results_repository = ResultsRepository()
        self.result_details_repository = ResultDetailsRepository()
        self.feature_extractor = FeatureExtractor()

    async def setup(self):
        """AIサービスマネージャーの初期化"""
        self.ai_service_manager = await AIServiceManager.create()

    def _convert_to_drawing_data(self, db_data: Dict[str, Any]) -> DrawingData:
        """データベースから取得したデータを DrawingData 形式に変換"""
        draw_lines_data = (
            json.loads(db_data["draw_lines"])
            if isinstance(db_data["draw_lines"], str)
            else db_data["draw_lines"]
        )

        draw_lines = []
        for line in draw_lines_data:
            positions = [
                Position(x=float(pos["x"]), y=float(pos["y"]), z=float(pos["z"]))
                for pos in line["positions"]
            ]

            color = line.get("color")
            if color:
                color = {
                    "r": float(color["r"]),
                    "g": float(color["g"]),
                    "b": float(color["b"]),
                    "a": float(color.get("a", 1.0)),
                }

            draw_lines.append(
                DrawLine(positions=positions, width=float(line.get("width", 1.0)), color=color)
            )

        center = Position(
            x=float(db_data["center_x"]), y=float(db_data["center_y"]), z=float(db_data["center_z"])
        )

        return DrawingData(draw_lines=draw_lines, center=center)

    async def process_drawing(self, drawing_id: str) -> Optional[Dict[str, Any]]:
        try:
            # 描画データを取得
            db_drawing_data = await self.drawings_repository.get_drawing(drawing_id)
            if not db_drawing_data:
                logger.error(f"Drawing not found: {drawing_id}")
                return None

            # FeatureExtractor用のデータ形式に変換
            converted_data = self._convert_to_drawing_data(db_drawing_data)

            # 特徴量を抽出
            features = self.feature_extractor.extract_features(converted_data)

            # 特徴量を保存
            feature_id = str(uuid.uuid4())
            await self.features_repository.insert_features(
                {
                    "feature_id": feature_id,
                    "drawing_id": drawing_id,
                    "total_strokes": features["global_features"]["total_strokes"],
                    "total_points": features["global_features"]["total_points"],
                    "features": features,
                }
            )

            # シーンで利用可能な形状を取得
            shapes = await self.shape_repository.get_available_shapes(db_drawing_data["scene_id"])

            # drawing_dataをProtoメッセージとして作成
            from src.proto.drawing_pb2 import DrawingData, Vector3Proto, Line, Color

            drawing_data = DrawingData()
            drawing_data.drawing_id = drawing_id
            drawing_data.scene_id = db_drawing_data["scene_id"]
            drawing_data.draw_timestamp = db_drawing_data["draw_timestamp"]
            drawing_data.center.x = db_drawing_data["center_x"]
            drawing_data.center.y = db_drawing_data["center_y"]
            drawing_data.center.z = db_drawing_data["center_z"]
            drawing_data.use_ai = True
            drawing_data.client_id = db_drawing_data.get("client_id", "")

            draw_lines_data = (
                json.loads(db_drawing_data["draw_lines"])
                if isinstance(db_drawing_data["draw_lines"], str)
                else db_drawing_data["draw_lines"]
            )
            for line_data in draw_lines_data:
                line = Line()
                for pos_data in line_data["positions"]:
                    pos = Vector3Proto()
                    pos.x = pos_data["x"]
                    pos.y = pos_data["y"]
                    pos.z = pos_data["z"]
                    line.positions.append(pos)
                line.width = line_data.get("width", 1.0)
                if line_data.get("color"):
                    color = Color()
                    color.r = line_data["color"]["r"]
                    color.g = line_data["color"]["g"]
                    color.b = line_data["color"]["b"]
                    color.a = line_data["color"].get("a", 1.0)
                    line.color.CopyFrom(color)
                drawing_data.draw_lines.append(line)

            # AI処理を実行
            start_time = datetime.now()
            ai_result = await self.ai_service_manager.process_drawing(
                drawing_data, shapes, features
            )
            process_time = (datetime.now() - start_time).total_seconds() * 1000

            if not ai_result:
                logger.error("No AI result")
                return None

            # resultsテーブルに保存
            result_id = str(uuid.uuid4())
            await self.results_repository.insert_result(
                {
                    "result_id": result_id,
                    "drawing_id": drawing_id,
                    "shape_id": ai_result.shape_id,
                    "success": ai_result.success,
                }
            )

            # result_detailsテーブルに保存
            api_response = {
                "shape_id": ai_result.shape_id,
                "score": ai_result.score,
                "reasoning": ai_result.reasoning,
                "success": ai_result.success,
                "model_name": ai_result.model_name,
                "error_message": ai_result.error_message,
            }

            await self.result_details_repository.insert_detail(
                {
                    "result_id": result_id,
                    "drawing_id": drawing_id,
                    "scene_id": db_drawing_data["scene_id"],
                    "shape_id": ai_result.shape_id,
                    "success": ai_result.success,
                    "score": ai_result.score,
                    "reasoning": ai_result.reasoning,
                    "process_time_ms": int(process_time),
                    "model_name": ai_result.model_name,
                    "api_response": api_response,
                    "error_message": ai_result.error_message,
                    "client_id": db_drawing_data.get("client_id"),
                }
            )

            return {
                "result_id": result_id,
                "shape_id": ai_result.shape_id,
                "score": ai_result.score,
                "model": ai_result.model_name,
                "process_time_ms": int(process_time),
            }

        except Exception as e:
            logger.error(f"Error processing drawing {drawing_id}: {e}")
            raise


async def main():
    """メイン処理"""
    # コマンドライン引数からdrawing_idを取得
    import sys

    if len(sys.argv) != 2:
        print("Usage: python test_shape_recognition.py <drawing_id>")
        sys.exit(1)

    drawing_id = sys.argv[1]

    try:
        # テスター初期化
        tester = ShapeRecognitionTester()
        await tester.setup()

        # 指定されたdrawing_idの処理
        logger.info(f"Processing drawing: {drawing_id}")
        result = await tester.process_drawing(drawing_id)

        if result:
            logger.info(f"Result: {json.dumps(result, indent=2)}")
        else:
            logger.error(f"Failed to process drawing: {drawing_id}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # データベース接続をクローズ
        await DatabaseConnection.close_pool()


if __name__ == "__main__":
    asyncio.run(main())
