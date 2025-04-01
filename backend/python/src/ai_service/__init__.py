# src/ai_service/__init__.py

from typing import Optional, List
from enum import Enum
import logging

from src.ai_service.api_keys import API_KEYS
from src.ai_service.services.open_ai import OpenAIService, OpenAIModel
from src.ai_service.services.google_ai import GoogleAIService, GoogleAIModel
from src.ai_service.services.anthropic_ai import AnthropicAIService, AnthropicModel
from src.ai_service.services.mistral_ai import MistralAIService, MistralAIModel
from src.ai_service.base import AIService

logger = logging.getLogger(__name__)


class AIServiceType(Enum):
    OPENAI = "openai"
    GOOGLEAI = "googleai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"


async def create_ai_service(service_type: AIServiceType, models: Optional[List[Enum]] = None) -> Optional[AIService]:
    """AIサービスの作成

    Args:
        service_type (AIServiceType): 使用するAIサービスの種類
        models (Optional[List[Enum]], optional): 使用するモデルのリスト

    Returns:
        Optional[AIService]: AIサービスのインスタンス
    """
    try:
        if service_type == AIServiceType.OPENAI:
            api_key = API_KEYS.get('OPENAI_API_KEY')
            return await OpenAIService.create_with_models(api_key, models)

        elif service_type == AIServiceType.GOOGLEAI:
            api_key = API_KEYS.get('GOOGLE_API_KEY')
            return await GoogleAIService.create_with_models(api_key, models)

        elif service_type == AIServiceType.ANTHROPIC:
            api_key = API_KEYS.get('ANTHROPIC_API_KEY')
            return await AnthropicAIService.create_with_models(api_key, models)

        elif service_type == AIServiceType.MISTRAL:
            api_key = API_KEYS.get('MISTRAL_API_KEY')
            return await MistralAIService.create_with_models(api_key, models)

    except ValueError as e:
        logger.error(f"Failed to initialize {service_type.value}: {str(e)}")
        return None

    return None


# 使用例：
# # Gemini 1.5 Proを使用するGoogleAIサービスの作成
# google_service = await create_ai_service(
#     AIServiceType.GOOGLEAI,
#     [GoogleAIModel.GEMINI15PRO]
# )
#
# # Claude-3 Opusを使用するAnthropicサービスの作成
# anthropic_service = await create_ai_service(
#     AIServiceType.ANTHROPIC,
#     [AnthropicModel.CLAUDE3OPUS]
# )
