# src/ai_service/services/mistral_ai.py

import logging
import json
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

from src.ai_service.base import AIService
from src.proto.drawing_pb2 import ShapeRecognitionServer

logger = logging.getLogger(__name__)


class MistralAIModel(Enum):
    """Mistral AIのモデル"""

    MINISTRAL_LARGE = "mistral-large-latest"
    MINISTRAL_8B = "ministral-8b-latest"


@dataclass
class ModelConfig:
    """モデルの設定"""

    max_tokens: int = 250
    timeout: int = 5
    temperature: float = 0.7


class MistralAIService(AIService):
    """Mistral AIのサービス"""
    MODELS_CONFIGS = {
        MistralAIModel.MINISTRAL_LARGE: ModelConfig(),
        MistralAIModel.MINISTRAL_8B: ModelConfig(),
    }

    @classmethod
    async def create(cls, api_key: str):
        """サービスを初期化
        Args:
            api_key (str): APIキー
        """
        return await cls.create_with_models(api_key, None)

    @classmethod
    async def create_with_models(cls, api_key: str, models: Optional[List[MistralAIModel]] = None):
        """サービスを初期化

        Args:
            api_key (str): APIキー
            models (Optional[List[MistralAIModel]]): 使用するモデルのリスト
        Returns:
            MistralAIService: 初期化されたサービスインスタンス
        """
        self = await super().create(api_key)
        self.current_model = None

        if not models or not self.api_key:
            self.enabled = False
            self.models = []
            return self

        self.client = MistralClient(api_key=self.api_key)
        self.enabled = True
        self.models = models
        self.model_configs = cls.MODELS_CONFIGS.copy()
        return self

    @property
    def model_name(self) -> str:
        """現在のモデル名を返す

        Returns:
            str: モデル名
        """
        model_name = self.current_model.value if self.current_model is not None else "unknown"
        return f"Mistral_{model_name}"

    async def call_ai_api(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """AI APIを呼び出す

        Args:
            system_prompt (str): システムプロンプト
            user_prompt (str): ユーザープロンプト
        Returns:
            Optional[str]: AIからのレスポンス
        Raises:
            Exception: API呼び出し中のエラー
        例外が発生した場合はNoneを返す
        """
        if not self.enabled:
            return None

        for model in self.models:
            config = self.model_configs.get(model)
            if not config:
                continue

            try:
                self.current_model = model
                messages = [
                    ChatMessage(role="system", content=system_prompt),
                    ChatMessage(role="user", content=user_prompt),
                ]

                response = await self.client.chat(
                    model=model.value,
                    messages=messages,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )
                return response.choices[0].message.content

            except Exception as e:
                logger.error(f"Error with model {model.value}: {str(e)}")
                continue

        return None

    async def parse_response(
        self, response: str, shape_infos: List[Dict[str, str]], result_id: str
    ) -> ShapeRecognitionServer:
        """AIのレスポンスを解析して結果を返す"

        Args:
            response (str): AIからのレスポンス
            shape_infos (List[Dict[str, str]]): 形状情報のリスト
            result_id (str): 結果のID
        Returns:
            ShapeRecognitionServer: 解析結果
        Raises:
            ValueError: 形状IDが無効な場合
        例外が発生した場合はエラーレスポンスを返す
        """
        try:
            json_text = response.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()

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
