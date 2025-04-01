# src/ai_service/services/google_ai.py

from enum import Enum
from typing import List, Dict, Optional
import logging
import json
from dataclasses import dataclass

import google.generativeai as genai

from src.ai_service.api_keys import API_KEYS
from src.ai_service.base import AIService
from src.proto.drawing_pb2 import ShapeRecognitionServer

logger = logging.getLogger(__name__)


class GoogleAIModel(Enum):
    """Google AIのモデル"""

    GEMINI20_FLASH = "gemini-2.0-flash-exp"
    GEMINI15_FLASH = "gemini-1.5-flash"
    GEMINI15_PRO = "gemini-1.5-pro"


@dataclass
class ModelConfig:
    """モデルの設定"""

    max_tokens: int = 250
    timeout: int = 5
    temperature: float = 0.7


class GoogleAIService(AIService):
    """Google AIのサービス"""

    MODELS_CONFIGS = {
        GoogleAIModel.GEMINI20_FLASH: ModelConfig(),
        GoogleAIModel.GEMINI15_FLASH: ModelConfig(),
        GoogleAIModel.GEMINI15_PRO: ModelConfig(),
    }

    @classmethod
    async def create(cls, api_key: str):
        """サービスを初期化
        Args:
            api_key (str): APIキー
        """
        return await cls.create_with_models(api_key, None)

    @classmethod
    async def create_with_models(cls, api_key: str, models: Optional[List[GoogleAIModel]] = None):
        """サービスを初期化

        Args:
            api_key (str): APIキー
            models (Optional[List[GoogleAIModel]]): 使用するモデルのリスト
        Returns:
            GoogleAIService: 初期化されたサービスインスタンス        
        """
        self = await super().create(api_key)
        self.current_model = None

        if not models or not self.api_key:
            self.enabled = False
            self.models = []
            return self

        genai.configure(api_key=self.api_key)
        self.enabled = True
        self.models = models
        self.model_configs = cls.MODELS_CONFIGS.copy()
        self.current_model = models[0]
        return self

    @property
    def model_name(self) -> str:
        """現在のモデル名を返す

        Returns:
            str: モデル名
        """
        model_name = self.current_model.value if self.current_model is not None else "unknown"
        return f"Google_{model_name}"

    async def call_ai_api(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """各モデルでAPIを呼び出し、最も確信度の高い結果を返す

        Args:
            system_prompt: システムプロンプト
            user_prompt: ユーザプロンプト
        Returns:
            str: AIからのレスポンス
        Raises:
            Exception: モデルの呼び出しに失敗した場合
        """
        if not self.enabled:
            return None

        for model in self.models:
            config = self.model_configs.get(model)
            if not config:
                continue

            try:
                self.current_model = model
                model_instance = genai.GenerativeModel(model.value)

                schema = {
                    "type": "object",
                    "properties": {
                        "shape_id": {"type": "string"},
                        "score": {"type": "integer"},
                        "reason": {"type": "string"},
                    },
                    "required": ["shape_id", "score", "reason"],
                }

                response = model_instance.generate_content(
                    [
                        {"role": "user", "parts": [system_prompt]},
                        {"role": "model", "parts": ["了解しました。"]},
                        {"role": "user", "parts": [user_prompt]},
                    ],
                    generation_config=genai.GenerationConfig(
                        temperature=config.temperature,
                        response_mime_type="application/json",
                        response_schema=schema,
                    ),
                )

                response_text = response.candidates[0].content.parts[0].text
                if response_text:
                    return response_text

            except Exception as e:
                logger.error(f"Error with model {model.value}: {str(e)}")
                continue

        return None

    async def parse_response(
        self, response: str, shape_infos: List[Dict[str, str]], result_id: str
    ) -> ShapeRecognitionServer:
        """レスポンスのパース処理

        Args:
            response: APIのレスポンス
            shape_infos: 図形情報
        Returns:
            パース結果
        Raises:
            ValueError: 解析エラー
        例外が発生した場合は、エラーメッセージを含むShapeRecognitionServerを返す
        """
        try:
            json_text = response.strip()
            result = json.loads(json_text)

            shape_info = next((s for s in shape_infos if s["shape_id"] == result["shape_id"]), None)

            if not shape_info:
                raise ValueError(f"Invalid shape ID: {result['shape_id']}")

            return ShapeRecognitionServer(
                success=True,
                result_id=result_id,
                shape_id=result["shape_id"],
                score=int(result["score"]),
                reasoning=result["reason"],
                model_name=self.model_name,
                api_response=json.dumps(result),
            )

        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return self.create_error_response(str(e))
