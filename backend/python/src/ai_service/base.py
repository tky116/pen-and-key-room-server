# src/ai_service/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time
import uuid
import traceback
import logging

from src.proto.drawing_pb2 import DrawingData, ShapeRecognitionServer
from src.database.repositories.results_repository import ResultsRepository
from src.database.repositories.result_details_repository import ResultDetailsRepository
from src.database.repositories.error_logs_repository import ErrorLogsRepository
from src.ai_service.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class AIService(ABC):
    api_key: str
    prompt_manager: PromptManager
    results_repository: ResultsRepository
    result_details_repository: ResultDetailsRepository
    error_logs_repository: ErrorLogsRepository

    @classmethod
    async def create(cls, api_key: str):
        self = cls.__new__(cls)
        self.api_key = api_key
        self.prompt_manager = PromptManager()
        self.results_repository = ResultsRepository()
        self.result_details_repository = ResultDetailsRepository()
        self.error_logs_repository = ErrorLogsRepository()
        return self

    def prepare_prompt(
        self, drawing: DrawingData, shape_infos: List[Dict[str, str]], lang: str = "ja"
    ) -> Dict[str, str]:
        """ プロンプトの準備

        Args:
            drawing (DrawingData): 描画データ
            shape_infos (List[Dict[str, str]]): 形状情報
            lang (str, optional): 言語. Defaults to "ja".
        Returns:
            Dict[str, str]: システムプロンプトとユーザープロンプト
        """
        drawing_info = self.prompt_manager.prepare_drawing_info(drawing)
        return {
            "system": self.prompt_manager.create_system_prompt(shape_infos, lang),
            "user": self.prompt_manager.create_data_prompt(drawing_info),
        }

    @abstractmethod
    async def call_ai_api(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """ AI APIを呼び出す抽象メソッド

        Args:
            system_prompt (str): システムプロンプト
            user_prompt (str): ユーザープロンプト
        Returns:
            Optional[str]: APIのレスポンス
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """ AI モデルの識別子を返す抽象メソッド

        Returns:
            str: モデル名
        """
        pass

    async def recognize_shape(
        self,
        drawing: DrawingData, 
        shape_infos: List[Dict[str, str]],
        features: Dict[str, Any]
    ) -> ShapeRecognitionServer:
        """ 形状認識の実行

        Args:
            drawing (DrawingData): 描画データ
            shape_infos (List[Dict[str, str]]): 形状情報
            features (Dict[str, Any]): 特徴量データ
        Returns:
            ShapeRecognitionServer: AI判定結果を表すメッセージ（サーバー）
        Raises:
            Exception: エラーが発生した場合
        例外が発生した場合は、エラーメッセージを含むShapeRecognitionServerを返す
        """
        start_time = time.time()
        result_id = str(uuid.uuid4())

        try:
            # 描画情報と特徴量を含めてプロンプトを準備
            drawing_info = self.prompt_manager.prepare_drawing_info(drawing, features)
            system_prompt = self.prompt_manager.create_system_prompt(shape_infos)
            user_prompt = self.prompt_manager.create_data_prompt(drawing_info)

            # AI APIを呼び出し
            response = await self.call_ai_api(system_prompt, user_prompt)
            if not response:
                return self.create_error_response("No response from AI service")

            # レスポンスをパース
            result = await self.parse_response(response, shape_infos, result_id)
            if not result:
                return self.create_error_response("Failed to parse response")

            # 結果をデータベースに保存
            await self.results_repository.insert_result({
                "result_id": result_id,
                "drawing_id": drawing.drawing_id,
                "shape_id": result.shape_id,
                "success": True
            })

            await self.result_details_repository.insert_detail({
                "result_id": result_id,
                "drawing_id": drawing.drawing_id,
                "scene_id": drawing.scene_id,
                "shape_id": result.shape_id,
                "success": True,
                "score": result.score,
                "reasoning": result.reasoning,
                "process_time_ms": int((time.time() - start_time) * 1000),
                "model_name": self.model_name,
                "api_response": response,
                "error_message": "",
                "client_id": drawing.client_id
            })

            return result

        except Exception as e:
            error_id = str(uuid.uuid4())
            await self.error_logs_repository.insert_error_log({
                "error_id": error_id,
                "result_id": result_id,
                "drawing_id": drawing.drawing_id,
                "scene_id": drawing.scene_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "stack_trace": traceback.format_exc(),
            })
            logger.error(f"Error in recognize_shape: {e}")
            return self.create_error_response(str(e), error_id)

    @abstractmethod
    async def parse_response(
        self, response: str, shape_infos: List[Dict[str, str]], result_id: str
    ) -> ShapeRecognitionServer:
        """ レスポンスのパースの抽象メソッド

        Args:
            response (str): APIのレスポンス
            shape_infos (List[Dict[str, str]]): 形状情報
            result_id (str): 結果ID
        Returns:
            ShapeRecognitionServer: AI判定結果を表すメッセージ（サーバー）
        """
        pass

    def create_error_response(
        self, message: str, error_id: Optional[str] = None
    ) -> ShapeRecognitionServer:
        """ エラーレスポンスの作成

        Args:
            message (str): エラーメッセージ
            error_id (Optional[str], optional): エラーID. Defaults to None.
        Returns:
            ShapeRecognitionServer: AI判定結果を表すメッセージ（サーバー）
        """
        return ShapeRecognitionServer(
            success=False,
            result_id=error_id if error_id else str(uuid.uuid4()),
            error_message=message
        )
