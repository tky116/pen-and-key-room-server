# src/database/connection.py

import os
import aiomysql
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    _pool: Optional[aiomysql.Pool] = None

    @classmethod
    async def get_pool(cls) -> aiomysql.Pool:
        """ コネクションプールを取得する """
        if cls._pool is None:
            try:
                cls._pool = await aiomysql.create_pool(
                    host=os.getenv("DB_HOST", "mysql"),
                    port=3306,
                    db=os.getenv("DB_NAME", "vrdb01"),
                    user=os.getenv("DB_USER", "db_user"),
                    password=os.getenv("DB_PASSWORD", "db_pass"),
                    maxsize=5,
                    autocommit=True
                )
            except Exception as e:
                logger.error(f"Failed to create connection pool: {e}")
                raise
        return cls._pool

    @classmethod
    async def execute_query(cls, query: str, params: tuple = None):
        """ クエリを実行する """
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    @classmethod
    async def close_pool(cls):
        """ コネクションプールをクローズする """
        if cls._pool:
            cls._pool.close()
            await cls._pool.wait_closed()
            cls._pool = None
