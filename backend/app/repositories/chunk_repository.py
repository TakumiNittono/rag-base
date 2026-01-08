"""
チャンクRepository（Lv2.5: 3テーブル分離設計）
============================================
chunksテーブルへのデータアクセスを提供します。
"""

from typing import Optional
from uuid import UUID

import asyncpg
from asyncpg import Pool

from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.models.chunk import Chunk, ChunkCreate
from app.repositories.file_repository import get_db_pool

logger = get_logger(__name__)


class ChunkRepository:
    """チャンクRepository"""

    async def create(self, chunk_data: ChunkCreate) -> Chunk:
        """
        チャンクを作成

        Args:
            chunk_data: チャンクデータ

        Returns:
            Chunk: 作成されたチャンク

        Raises:
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO chunks (file_id, content, chunk_index, token_count)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id, created_at
                    """,
                    chunk_data.file_id,
                    chunk_data.content,
                    chunk_data.chunk_index,
                    chunk_data.token_count,
                )

                return Chunk(
                    id=row["id"],
                    file_id=chunk_data.file_id,
                    content=chunk_data.content,
                    chunk_index=chunk_data.chunk_index,
                    token_count=chunk_data.token_count,
                    created_at=row["created_at"],
                )
        except Exception as e:
            logger.error(f"チャンク作成エラー: {str(e)}")
            raise DatabaseError("チャンクの作成に失敗しました") from e

    async def create_batch(self, chunks_data: list[ChunkCreate]) -> list[Chunk]:
        """
        チャンクを一括作成

        Args:
            chunks_data: チャンクデータのリスト

        Returns:
            list[Chunk]: 作成されたチャンクのリスト

        Raises:
            DatabaseError: データベースエラー
        """
        if not chunks_data:
            return []

        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                # 一括INSERT
                values = [
                    (
                        chunk.file_id,
                        chunk.content,
                        chunk.chunk_index,
                        chunk.token_count,
                    )
                    for chunk in chunks_data
                ]

                rows = await conn.fetch(
                    """
                    INSERT INTO chunks (file_id, content, chunk_index, token_count)
                    SELECT * FROM unnest($1::uuid[], $2::text[], $3::int[], $4::int[])
                    RETURNING id, file_id, content, chunk_index, token_count, created_at
                    """,
                    [v[0] for v in values],
                    [v[1] for v in values],
                    [v[2] for v in values],
                    [v[3] for v in values],
                )

                return [
                    Chunk(
                        id=row["id"],
                        file_id=row["file_id"],
                        content=row["content"],
                        chunk_index=row["chunk_index"],
                        token_count=row["token_count"],
                        created_at=row["created_at"],
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"チャンク一括作成エラー: {str(e)}")
            raise DatabaseError("チャンクの一括作成に失敗しました") from e

    async def get_by_id(self, chunk_id: UUID) -> Optional[Chunk]:
        """
        チャンクIDでチャンクを取得

        Args:
            chunk_id: チャンクID

        Returns:
            Optional[Chunk]: チャンク情報（存在しない場合はNone）

        Raises:
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM chunks WHERE id = $1",
                    chunk_id,
                )

                if not row:
                    return None

                return Chunk(
                    id=row["id"],
                    file_id=row["file_id"],
                    content=row["content"],
                    chunk_index=row["chunk_index"],
                    token_count=row["token_count"],
                    created_at=row["created_at"],
                )
        except Exception as e:
            logger.error(f"チャンク取得エラー: {str(e)}")
            raise DatabaseError("チャンクの取得に失敗しました") from e

    async def get_by_file_id(self, file_id: UUID) -> list[Chunk]:
        """
        ファイルIDでチャンク一覧を取得

        Args:
            file_id: ファイルID

        Returns:
            list[Chunk]: チャンク一覧

        Raises:
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM chunks
                    WHERE file_id = $1
                    ORDER BY chunk_index ASC
                    """,
                    file_id,
                )

                return [
                    Chunk(
                        id=row["id"],
                        file_id=row["file_id"],
                        content=row["content"],
                        chunk_index=row["chunk_index"],
                        token_count=row["token_count"],
                        created_at=row["created_at"],
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"チャンク一覧取得エラー: {str(e)}")
            raise DatabaseError("チャンク一覧の取得に失敗しました") from e

    async def delete_by_file_id(self, file_id: UUID) -> int:
        """
        ファイルIDでチャンクを削除（CASCADEでembeddingsも削除される）

        Args:
            file_id: ファイルID

        Returns:
            int: 削除されたチャンク数

        Raises:
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM chunks WHERE file_id = $1",
                    file_id,
                )
                # "DELETE N" の形式から数値を抽出
                deleted_count = int(result.split()[-1])
                return deleted_count
        except Exception as e:
            logger.error(f"チャンク削除エラー: {str(e)}")
            raise DatabaseError("チャンクの削除に失敗しました") from e

