# src/grpc/grpc_server.py

import asyncio
import uuid
import grpc
import grpc.aio
from concurrent import futures
import logging
from datetime import datetime

from src.proto.drawing_pb2 import (
    ShapeRecognitionClient,
    UploadResponse,
    HealthCheckResponse
)
from src.proto.drawing_pb2 import ShapeRecognitionServer
from src.proto.drawing_pb2_grpc import (
    DrawingServiceServicer,
    add_DrawingServiceServicer_to_server
)
from src.database.repositories.drawings_repository import DrawingsRepository
from src.database.repositories.shape_repository import ShapeRepository
from src.database.repositories.features_repository import FeaturesRepository
from src.features.feature_extractor import FeatureExtractor
from src.ai_service.service_manager import AIServiceManager

logger = logging.getLogger(__name__)


class GrpcService(DrawingServiceServicer):
    """描画データのアップロードと処理を行うgRPCサービス"""

    drawings_repository: DrawingsRepository
    shape_repository: ShapeRepository
    features_repository: FeaturesRepository
    ai_service_manager: AIServiceManager
    start_time: datetime

    @classmethod
    async def create(cls):
        self = cls.__new__(cls)
        self.drawings_repository = DrawingsRepository()
        self.shape_repository = ShapeRepository()
        self.features_repository = FeaturesRepository()
        self.ai_service_manager = await AIServiceManager.create()
        self.start_time = datetime.now()
        return self

    async def CheckHealth(self, request, context):
        """サーバーのヘルスチェックを実行"""
        logger.info("ヘルスチェックリクエストを受信")
        return HealthCheckResponse(
            status=HealthCheckResponse.ServingStatus.SERVING,
            message="gRPC server is running"
        )

    async def UploadDrawing(self, request, context):
        """ 描画データをアップロード """
        try:
            drawing_data = self._convert_request_to_dict(request)
            saved_id = await self.drawings_repository.insert_drawings(drawing_data)
            return UploadResponse(success=True, message="", upload_id=saved_id)
        except Exception as e:
            logger.error(f"Error uploading drawing: {e}")
            return UploadResponse(success=False, message=f"Error: {str(e)}", upload_id="")

    async def ProcessDrawing(self, request, context) -> ShapeRecognitionClient:
        """ 描画データの処理を実行

        Args:
            request (DrawingRequest): gRPCリクエスト
            context: gRPCコンテキスト
        Returns:
            ShapeRecognitionClient: クライアントのレスポンス
        """
        try:
            if not request.use_ai:
                return None

            # 特徴量を生成
            feature_extractor = FeatureExtractor()
            features = feature_extractor.extract_features(request)

            # 特徴量保存とAI処理を並行実行
            feature_id = str(uuid.uuid4())
            save_task = self.features_repository.insert_features({
                "feature_id": feature_id,
                "drawing_id": request.drawing_id,
                "total_strokes": features["global_features"]["total_strokes"],
                "total_points": features["global_features"]["total_points"],
                "features": features  # 全特徴量をJSONとして保存
            })

            shapes = await self.shape_repository.get_available_shapes(request.scene_id)
            ai_task: ShapeRecognitionServer = self.ai_service_manager.process_drawing(
                request,
                shapes,
                features,
            )

            # 両方の処理を待機
            ai_result, _ = await asyncio.gather(ai_task, save_task)

            logger.info(f"AI Result: {ai_result}")

            if not ai_result:
                return ShapeRecognitionClient(
                    success=False,
                    prefab_name="Unknown",
                    error_message="No valid results"
                    )

            # shape_idに対応する形状情報を取得
            shape_info = await self.shape_repository.get_shape_info_by_id(ai_result.shape_id)

            # shape_idに対応する形状情報が見つからない場合
            if not shape_info:
                logger.error(f"Shape info not found for shape_id: {ai_result.shape_id}")
                return ShapeRecognitionClient(
                    success=False,
                    drawing_id=request.drawing_id,
                    prefab_name="Unknown",
                    error_message="Shape info not found for the recognized shape"
                )

            # ケース1: AIの処理に成功しScoreも閾値以上
            if ai_result.success and ai_result.score >= shape_info["threshold"]:
                return ShapeRecognitionClient(
                    success=True,
                    drawing_id=request.drawing_id,
                    prefab_name=shape_info["prefab_name"],
                    error_message=""
                )
            # ケース2: AIの処理に成功したがScoreが閾値以下
            elif ai_result.success:
                return ShapeRecognitionClient(
                    success=True,
                    drawing_id=request.drawing_id,
                    prefab_name="Unknown",
                    error_message=f"Recognized but below threshold. Score: {ai_result.score}, Required: {shape_info['threshold']}"
                )
            # ケース3: AIの処理に失敗
            else:
                return ShapeRecognitionClient(
                    success=False,
                    drawing_id=request.drawing_id,
                    prefab_name="Unknown",
                    error_message=ai_result.error_message
                )

        except Exception as e:
            logger.error(f"Error processing drawing: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")
            return None

    def _convert_request_to_dict(self, request):
        """ gRPCリクエストをデータベース保存用の辞書に変換

        Args:
            request (DrawingRequest): gRPCリクエスト
        """
        return {
            "drawing_id": request.drawing_id,
            "scene_id": request.scene_id,
            "draw_timestamp": request.draw_timestamp,
            "draw_lines": [
                {
                    "positions": [{"x": pos.x, "y": pos.y, "z": pos.z} for pos in line.positions],
                    "width": line.width,
                    "color": {"r": line.color.r, "g": line.color.g, "b": line.color.b, "a": line.color.a} if line.color else None,
                }
                for line in request.draw_lines
            ],
            "center_x": request.center.x,
            "center_y": request.center.y,
            "center_z": request.center.z,
            "use_ai": request.use_ai,
            "client_id": request.client_id,
            "client_info": {
                "type": request.client_info.type,
                "device_id": request.client_info.device_id,
                "device_name": request.client_info.device_name,
                "system_info": request.client_info.system_info,
                "app_version": request.client_info.app_version,
            },
            "metadata": dict(request.metadata)
        }


async def start_grpc_server():
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
        ],
    )

    service = await GrpcService.create()
    add_DrawingServiceServicer_to_server(service, server)

    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)

    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()
    logger.info("gRPC server started successfully")

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("gRPC server stopping...")
        await server.stop(0)
        logger.info("gRPC server stopped")
