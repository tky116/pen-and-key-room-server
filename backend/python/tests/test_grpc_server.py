# tests/grpc/test_grpc_server.py

import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

from src.proto.drawing_pb2 import GeneratedObject
from src.proto.drawing_pb2 import (
    DrawingData, ClientInfo, Vector3Proto, Line, Color
    )
from src.grpc_server import GrpcService


class TestGrpcService:
    @pytest.fixture
    def mock_ai_service_manager(self):
        mock_manager = AsyncMock()
        mock_manager.process_drawing.return_value = GeneratedObject(
            success=True,
            object_id=str(uuid.uuid4()),
            shape_id="test_shape",
            prefab_name="test_prefab",
            score=0.95,
            reasoning="Test reasoning"
        )
        return mock_manager

    @pytest.fixture
    def grpc_service(self, mock_drawings_repository, mock_ai_service_manager):
        """GrpcServiceのインスタンスを作成"""
        service = GrpcService()
        service.repository = mock_drawings_repository
        service.ai_service_manager = mock_ai_service_manager
        return service

    @pytest.fixture
    def mock_drawings_repository(self):
        """ モック化されたDrawingsRepositoryを作成 """
        mock_repo = MagicMock()
        # check_connectionメソッドを追加
        mock_repo.check_connection.return_value = True
        # insert_drawingsメソッドを追加
        mock_repo.insert_drawings.return_value = str(uuid.uuid4())
        # insert_resultメソッドを追加
        mock_repo.insert_result.return_value = str(uuid.uuid4())

        return mock_repo

    @pytest.fixture
    def mock_scene_repository(self):
        """ モック化されたSceneRepositoryを作成 """
        mock_repo = MagicMock()
        mock_repo.get_scene_by_id.return_value = {
            "id": "test_scene",
            "name_ja": "テストシーン",
        }
        return mock_repo

    @pytest.fixture
    def grpc_service(self, mock_drawings_repository):
        """ GrpcServiceのインスタンスを作成 """
        # リポジトリを直接注入
        service = GrpcService()
        service.repository = mock_drawings_repository
        return service

    @pytest.fixture
    def sample_drawing_data(self):
        """ テスト用の描画データを生成 """
        return DrawingData(
            uuid=str(uuid.uuid4()),
            timestamp=1705708800000,
            scene_id="test_scene",  # 存在するシーンIDを指定
            client_id="test_client",
            client_info=ClientInfo(
                type=ClientInfo.ClientType.DEVELOPMENT,
                device_id="test_device",
                device_name="Test Device",
                system_info="Test System",
                app_version="1.0.0",
            ),
            center=Vector3Proto(x=0.0, y=0.0, z=0.0),
            draw_lines=[
                Line(
                    positions=[Vector3Proto(x=0.0, y=0.0, z=0.0)],
                    width=0.1,
                    color=Color(r=1.0, g=0.0, b=0.0, a=1.0),
                )
            ],
            metadata={"tag": "test"},
            ai_processing=True,
        )

    @pytest.mark.asyncio
    async def test_upload_drawing_success(
        self,
        grpc_service,
        mock_drawings_repository,
        mock_scene_repository,
        sample_drawing_data
    ):
        """ 描画データのアップロード成功テスト
        - アップロードリクエストが成功すること
        - 描画データがデータベースに正常に保存されること
        - アップロード時に一意のIDが返されること
        """
        mock_context = AsyncMock()

        # シーンリポジトリのモック化
        with patch(
            "src.database.repositories.scene_repository.SceneRepository",
            return_value=mock_scene_repository,
        ):
            response = await grpc_service.UploadDrawing(
                sample_drawing_data,
                mock_context
                )

            assert response.success is True
            assert response.upload_id != ""
            mock_drawings_repository.insert_drawings.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_drawing_success(
        self, grpc_service, mock_drawings_repository, sample_drawing_data
    ):
        """ 描画データの処理成功テスト
        - AI処理が正常に実行されること
        - 処理結果のGeneratedObjectが返されること
        - 推論された形状タイプが正確であること
        - 信頼度スコアが期待値に近いこと
        """
        mock_context = AsyncMock()

        response = await grpc_service.ProcessDrawing(
            sample_drawing_data,
            mock_context
            )

        assert response.success is True
        assert response.shape_id == "test_shape"
        assert pytest.approx(response.score, 0.05) == 0.95

    @pytest.mark.asyncio
    async def test_process_drawing_ai_processing_disabled(
        self, grpc_service, sample_drawing_data
    ):
        """ AI処理が無効な場合のテスト
        - AI処理がスキップされること
        - メソッドが何も返さないこと（Noneを返すこと）
        """
        mock_context = AsyncMock()
        sample_drawing_data.ai_processing = False

        response = await grpc_service.ProcessDrawing(
            sample_drawing_data,
            mock_context
            )

        assert response is None

    @pytest.mark.asyncio
    async def test_process_drawing_with_ai(
            self,
            grpc_service,
            sample_drawing_data
            ):
        """実際のAI処理を含む描画データの処理テスト
        - AI処理が正常に実行されること
        - AIが適切な形状を認識すること
        - 結果がデータベースに保存されること
        """
        mock_context = AsyncMock()

        response = await grpc_service.ProcessDrawing(
            sample_drawing_data,
            mock_context
            )

        assert response.success is True
        assert response.shape_id in ["円・丸", "四角", "三角"]  # 期待される形状
        assert 0 <= response.score <= 100
        assert response.reasoning != ""

    @pytest.mark.asyncio
    async def test_process_drawing_ai_error(
            self,
            grpc_service,
            sample_drawing_data
            ):
        """ AI処理エラー時のテスト """
        mock_context = AsyncMock()

        # モックを設定
        mock_ai_service_manager = AsyncMock()
        mock_ai_service_manager.process_drawing.return_value = None
        grpc_service.ai_service_manager = mock_ai_service_manager

        response = await grpc_service.ProcessDrawing(
            sample_drawing_data,
            mock_context
            )
        assert response.success is False
