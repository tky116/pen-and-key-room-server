.PHONY: setup proto clean \
        dev-build dev-up dev-down dev-ps dev-logs dev-db dev-bash \
        prod-build prod-up prod-down prod-ps prod-logs prod-db prod-bash

# Proto生成
proto:
	@echo "Generating proto files..."
	cd backend/python/src && \
	poetry run python -m grpc_tools.protoc \
		--python_out=. \
		--grpc_python_out=. \
		--proto_path=. \
		proto/drawing.proto && \
	sed -i 's/from proto/from src.proto/g' proto/drawing_pb2_grpc.py

# セットアップ
# 開発環境と本番環境の両方をセットアップ
setup: dev-setup prod-setup
	@echo "Installing Poetry..."
	curl -sSL https://install.python-poetry.org | python3 -
	cd backend/python && poetry install

# 開発環境のみセットアップ
dev-setup:
	@echo "Setting up development environment..."
	@sudo mkdir -p ./mysql/data
	@sudo chown -R 999:999 ./mysql/data

# 本番環境のみセットアップ
prod-setup:
	@echo "Setting up production environment..."
	@sudo mkdir -p /var/lib/mysql/vracademy
	@sudo chown -R 999:999 /var/lib/mysql/vracademy

# 開発環境
dev-build:
	docker compose -f docker/dev/docker-compose.yml build

dev-up:
	docker compose -f docker/dev/docker-compose.yml up -d

dev-down:
	docker compose -f docker/dev/docker-compose.yml down

dev-ps:
	docker compose -f docker/dev/docker-compose.yml ps

dev-logs:
	docker compose -f docker/dev/docker-compose.yml logs -f

dev-logs-server:
	docker compose -f docker/dev/docker-compose.yml logs -f server

dev-logs-db:
	docker compose -f docker/dev/docker-compose.yml logs -f mysql

dev-logs-web:
	docker compose -f docker/dev/docker-compose.yml logs -f nginx

dev-db:
	docker compose -f docker/dev/docker-compose.yml exec mysql mysql -u db_user -p

dev-bash:
	docker compose -f docker/dev/docker-compose.yml exec server bash

# 本番環境
prod-build:
	docker compose --env-file .env -f docker/prod/docker-compose.yml build

prod-up:
	docker compose --env-file .env -f docker/prod/docker-compose.yml up -d

prod-down:
	docker compose --env-file .env -f docker/prod/docker-compose.yml down

prod-ps:
	docker compose --env-file .env -f docker/prod/docker-compose.yml ps

prod-logs:
	docker compose --env-file .env -f docker/prod/docker-compose.yml logs -f

prod-logs-server:
	docker compose -f docker/prod/docker-compose.yml logs -f server

prod-logs-db:
	docker compose -f docker/prod/docker-compose.yml logs -f mysql

prod-logs-web:
	docker compose -f docker/prod/docker-compose.yml logs -f nginx

prod-db:
	docker compose -f docker/prod/docker-compose.yml exec mysql mysql -u db_user -p

prod-bash:
	docker compose -f docker/prod/docker-compose.yml exec server bash

# クリーンアップ
# 開発環境と本番環境の両方をクリーンアップ
clean:
	find . -type d -name "__pycache__" -exec sudo rm -rf {} +
	find . -type f -name "*.pyc" -delete
	docker compose -f docker/dev/docker-compose.yml down -v
	docker compose -f docker/prod/docker-compose.yml down -v
	sudo rm -rf ./mysql/data/*  # MySQLのデータディレクトリをクリーン

# 開発環境のみクリーンアップ
dev-clean:
	find . -type d -name "__pycache__" -exec sudo rm -rf {} +
	find . -type f -name "*.pyc" -delete
	docker compose -f docker/dev/docker-compose.yml down -v
	sudo rm -rf ./mysql/data/dev/*

# 本番環境のみクリーンアップ
prod-clean:
	docker compose -f docker/prod/docker-compose.yml down -v
	sudo rm -rf /var/lib/mysql/vracademy/*

# ヘルプ
help:
	@echo "Available commands:"
	@echo "Development:"
	@echo "  dev-build  - Build development environment"
	@echo "  dev-up     - Start development environment"
	@echo "  dev-down   - Stop development environment"
	@echo "  dev-ps     - Show development container status"
	@echo "  dev-logs   - Show development logs"
	@echo "  dev-db     - Connect to development database"
	@echo "  dev-bash   - Enter development server container"
	@echo ""
	@echo "Production:"
	@echo "  prod-build - Build production environment"
	@echo "  prod-up    - Start production environment"
	@echo "  prod-down  - Stop production environment"
	@echo "  prod-ps    - Show production container status"
	@echo "  prod-logs  - Show production logs"
	@echo "  prod-db    - Connect to production database"
	@echo "  prod-bash  - Enter production server container"
	@echo ""
	@echo "Other:"
	@echo "  setup      - Install dependencies"
	@echo "  proto      - Generate proto files"
	@echo "  clean      - Clean up generated files and volumes"