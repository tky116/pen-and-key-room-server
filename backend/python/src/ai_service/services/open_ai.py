# src/ai_service/services/open_ai.py

import logging
import json
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass

from openai import OpenAI

from src.ai_service.api_keys import API_KEYS
from src.ai_service.base import AIService
from src.proto.drawing_pb2 import ShapeRecognitionServer

logger = logging.getLogger(__name__)


class OpenAIModel(Enum):
    """OpenAIのモデル"""

    GPT4o = "chatgpt-4o-latest"
    GPT4oMINI = "gpt-4o-mini"
    GPT4oTURBO = "gpt-4-turbo"
    GPT35TURBO = "gpt-3.5-turbo-0125"


@dataclass
class ModelConfig:
    """モデルの設定"""

    max_tokens: int = 250
    timeout: int = 5
    temperature: float = 1.0


class OpenAIService(AIService):
    """OpenAIのサービス"""
    MODELS_CONFIGS = {
        OpenAIModel.GPT4o: ModelConfig(),
        OpenAIModel.GPT4oMINI: ModelConfig(),
        OpenAIModel.GPT4oTURBO: ModelConfig(),
        OpenAIModel.GPT35TURBO: ModelConfig(),
    }

    @classmethod
    async def create(cls, api_key: str):
        """サービスを初期化
        Args:
            api_key (str): APIキー
        """
        return await cls.create_with_models(api_key, None)

    @classmethod
    async def create_with_models(cls, api_key: str, models: Optional[List[OpenAIModel]] = None):
        """サービスを初期化

        Args:
            api_key (str): APIキー
            models (Optional[List[OpenAIModel]]): 使用するモデルのリスト
        Returns:
            OpenAIService: 初期化されたサービスインスタンス
        """
        self = await super().create(api_key)
        self.current_model = None

        if not models or not self.api_key:
            self.enabled = False
            self.models = []
            return self

        self.client = OpenAI(api_key=self.api_key)
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
        return f"OpenAI_{model_name}"

    async def call_ai_api(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """各モデルでAPIを呼び出し、最も確信度の高い結果を返す

        Args:
            system_prompt: システムプロンプト
            user_prompt: ユーザプロンプト
        Returns:
            APIの結果
        Raises:
            Exception: モデルの呼び出しに失敗した場合
        例外が発生した場合はNoneを返す
        """
        if not self.enabled:
            return None

        # 各モデルでAPIを呼び出し、最も確信度の高い結果を返す
        for model in self.models:
            config = self.model_configs.get(model)
            if not config:
                continue
            try:
                self.current_model = model
                completion = self.client.chat.completions.create(
                    model=model.value,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    timeout=config.timeout,
                )
                return completion.choices[0].message.content

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
