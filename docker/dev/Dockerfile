FROM python:3.9-slim

# Poetryのインストール
RUN pip install poetry

WORKDIR /app

# pyproject.tomlのみをコピー
COPY pyproject.toml poetry.lock ./

# ソースコード用ディレクトリの作成
RUN mkdir src

# ソースコードのコピー
COPY src/ ./src/

# Poetry設定とインストール
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

EXPOSE 50051

CMD ["python", "main.py"]