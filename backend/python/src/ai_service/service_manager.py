# src/ai_service/service_manager.py

from enum import Enum
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union

from src.proto.drawing_pb2 import ShapeRecognitionServer

from src.ai_service.api_keys import API_KEYS
from src.ai_service.base import AIService
from src.ai_service.services.open_ai import OpenAIService, OpenAIModel
from src.ai_service.services.google_ai import GoogleAIService, GoogleAIModel
from src.ai_service.services.anthropic_ai import AnthropicAIService, AnthropicModel
from src.ai_service.services.mistral_ai import MistralAIService, MistralAIModel

logger = logging.getLogger(__name__)


class DrawingGroup(Enum):
    GROUP_A = "A"
    GROUP_B = "B"
    GROUP_BOTH = "BOTH"


class AIServiceManager:
    """複数のAIサービスを管理するクラス"""

    async def __init__(self):
        self.services: Dict[DrawingGroup, AIService] = {}

        # Aグループのサービスを初期化（gpt-3.5-turbo-0125）
        self.services[DrawingGroup.GROUP_A] = await OpenAIService.create_with_models(
            API_KEYS.get("OPENAI_API_KEY"), [OpenAIModel.GPT35TURBO]
        )

        # Bグループのサービスを初期化（gemini-1.5-pro）
        self.services[DrawingGroup.GROUP_B] = await GoogleAIService.create_with_models(
            API_KEYS.get("GOOGLE_API_KEY"), [GoogleAIModel.GEMINI15_PRO]
        )

        # BOTHグループのサービスを初期化（mistral-large-latest）
        self.services[DrawingGroup.GROUP_BOTH] = await MistralAIService.create_with_models(
            API_KEYS.get("MISTRAL_API_KEY"), [MistralAIModel.MINISTRAL_LARGE]
        )

        logger.info("Initialized services:")
        for group, service in self.services.items():
            logger.info(f"Group {group.value}: {service.model_name}")

    @classmethod
    async def create(cls):
        self = cls.__new__(cls)
        await self.__init__()
        return self

    @staticmethod
    def _calculate_point_density(features: Dict[str, Any]) -> float:
        """特徴量からpoint_densityを計算

        Args:
            features (Dict[str, Any]): 特徴量データ
        Returns:
            float: point_densityの値
        """
        total_points = features.get("total_points", 0)
        stroke_length = features.get("stroke_length", 0)

        if stroke_length > 0:
            return total_points / stroke_length
        return 0

    @staticmethod
    def prepare_features(features: Dict[str, Any]) -> Dict[str, Any]:
        """特徴量データの前処理
        Args:
            features (Dict[str, Any]): 特徴量データ
        Returns:
            Dict[str, Any]: 前処理された特徴量データ
        """
        enhanced_features = features.copy()
        # point_densityを計算
        enhanced_features["point_density"] = AIServiceManager._calculate_point_density(features)
        return enhanced_features

    @staticmethod
    def classify_drawing(features: Dict[str, Any]) -> DrawingGroup:
        """
        特徴量に基づいてグループを分類
        - GROUP_A: gpt-3.5-turbo-0125（OKの判定に強い）
        - GROUP_B: gemini-1.5-pro（NGの判定に強い）
        - GROUP_BOTH: mistral-large-latest（両方の判定が安定）

        Args:
            features (Dict[str, Any]): 特徴量データ
        Returns:
            DrawingGroup: 分類されたグループ
        """
        global_features = features.get("global_features", {})
        strokes = features.get("strokes", [])

        total_points = global_features.get("total_points", 0)
        total_length = sum(stroke.get("total_length", 0) for stroke in strokes)
        point_density = total_points / total_length if total_length > 0 else 0
        total_strokes = global_features.get("total_strokes", 0)

        # mistral-large-latestで処理（安定した判定が必要な場合）
        if (6 < point_density < 82) and (4 <= total_strokes <= 16):
            return DrawingGroup.GROUP_BOTH
        # gemini-1.5-proで処理（NGの判定が重要な場合）
        elif point_density > 50 or total_strokes <= 2 or total_length < 0.2:
            return DrawingGroup.GROUP_B
        # それ以外はgpt-3.5-turbo-0125で処理（OKの判定が重要な場合）
        else:
            return DrawingGroup.GROUP_A

    async def process_drawing(
        self, drawing_data, shapes: List[dict], features: Dict[str, Any]
    ) -> Optional[ShapeRecognitionServer]:
        """描画データの処理実行

        Args:
            drawing_data: 描画データ
            shapes: 利用可能な形状
            features: 特徴量データ
        Returns:
            ShapeRecognitionServer: サーバーのレスポンス
        """
        try:
            # グループを判定
            group = self.classify_drawing(features)

            # 対応するサービスを取得
            service = self.services.get(group)
            if not service:
                logger.error(f"No service found for group {group}")
                return ShapeRecognitionServer(
                    success=False, error_message=f"No AI service configured for group {group.value}"
                )

            # 単一サービスでの処理
            result = await service.recognize_shape(drawing_data, shapes, features)
            return result
        except Exception as e:
            logger.error(f"Error in process_drawing: {e}")
            return ShapeRecognitionServer(
                success=False,
                error_message=f"Error processing with {group.value} service: {str(e)}",
            )
