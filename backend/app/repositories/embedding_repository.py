"""
Embedding Repository（Lv2.5: 3テーブル分離設計）
===============================================
embeddingsテーブルへのデータアクセスとベクトル検索を提供します。
"""

from typing import Optional
from uuid import UUID

import asyncpg
from asyncpg import Pool

from app.config import get_settings
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.models.chunk import ChunkWithSimilarity
from app.models.embedding import Embedding, EmbeddingCreate
from app.repositories.file_repository import get_db_pool

logger = get_logger(__name__)
settings = get_settings()


class EmbeddingRepository:
    """Embedding Repository"""

    async def create(self, embedding_data: EmbeddingCreate) -> Embedding:
        """
        Embeddingを作成

        Args:
            embedding_data: Embeddingデータ

        Returns:
            Embedding: 作成されたEmbedding

        Raises:
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO embeddings (chunk_id, embedding, model_name)
                    VALUES ($1, $2::vector, $3)
                    RETURNING id, created_at
                    """,
                    embedding_data.chunk_id,
                    embedding_data.embedding,
                    embedding_data.model_name,
                )

                return Embedding(
                    id=row["id"],
                    chunk_id=embedding_data.chunk_id,
                    embedding=embedding_data.embedding,
                    model_name=embedding_data.model_name,
                    created_at=row["created_at"],
                )
        except Exception as e:
            logger.error(f"Embedding作成エラー: {str(e)}")
            raise DatabaseError("Embeddingの作成に失敗しました") from e

    async def create_batch(self, embeddings_data: list[EmbeddingCreate]) -> list[Embedding]:
        """
        Embeddingを一括作成

        Args:
            embeddings_data: Embeddingデータのリスト

        Returns:
            list[Embedding]: 作成されたEmbeddingのリスト

        Raises:
            DatabaseError: データベースエラー
        """
        if not embeddings_data:
            return []

        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                # 一括INSERT（pgvectorのvector型を使用）
                embeddings = []
                for emb_data in embeddings_data:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO embeddings (chunk_id, embedding, model_name)
                        VALUES ($1, $2::vector, $3)
                        RETURNING id, chunk_id, embedding, model_name, created_at
                        """,
                        emb_data.chunk_id,
                        emb_data.embedding,
                        emb_data.model_name,
                    )
                    embeddings.append(
                        Embedding(
                            id=row["id"],
                            chunk_id=row["chunk_id"],
                            embedding=list(row["embedding"]),  # vector型をlistに変換
                            model_name=row["model_name"],
                            created_at=row["created_at"],
                        )
                    )

                return embeddings
        except Exception as e:
            logger.error(f"Embedding一括作成エラー: {str(e)}")
            raise DatabaseError("Embeddingの一括作成に失敗しました") from e

    async def get_by_chunk_id(self, chunk_id: UUID, model_name: Optional[str] = None) -> Optional[Embedding]:
        """
        チャンクIDでEmbeddingを取得

        Args:
            chunk_id: チャンクID
            model_name: モデル名（オプション、デフォルトは設定値）

        Returns:
            Optional[Embedding]: Embedding情報（存在しない場合はNone）

        Raises:
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            model = model_name or settings.embedding_model

            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM embeddings
                    WHERE chunk_id = $1 AND model_name = $2
                    """,
                    chunk_id,
                    model,
                )

                if not row:
                    return None

                return Embedding(
                    id=row["id"],
                    chunk_id=row["chunk_id"],
                    embedding=list(row["embedding"]),  # vector型をlistに変換
                    model_name=row["model_name"],
                    created_at=row["created_at"],
                )
        except Exception as e:
            logger.error(f"Embedding取得エラー: {str(e)}")
            raise DatabaseError("Embeddingの取得に失敗しました") from e

    async def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        model_name: Optional[str] = None,
        similarity_threshold: Optional[float] = None,
    ) -> list[ChunkWithSimilarity]:
        """
        ベクトル類似検索を実行（Lv2.5: embeddingsテーブルで検索）

        Args:
            query_embedding: 質問のEmbedding（1536次元）
            top_k: 取得するチャンク数
            model_name: モデル名（オプション、デフォルトは設定値）
            similarity_threshold: 類似度閾値（オプション、0.0-1.0）

        Returns:
            list[ChunkWithSimilarity]: 類似度順にソートされたチャンク一覧

        Raises:
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            model = model_name or settings.embedding_model

            async with pool.acquire() as conn:
                # pgvectorのコサイン類似度検索
                # 1 - (embedding <=> query_embedding) で類似度を計算
                query = """
                    SELECT 
                        c.id AS chunk_id,
                        c.content,
                        c.chunk_index,
                        c.file_id,
                        f.file_name,
                        e.id AS embedding_id,
                        1 - (e.embedding <=> $1::vector) AS similarity
                    FROM embeddings e
                    JOIN chunks c ON e.chunk_id = c.id
                    JOIN files f ON c.file_id = f.id
                    WHERE f.status = 'indexed'
                      AND e.model_name = $2
                """

                params = [query_embedding, model]

                # 類似度閾値がある場合は追加
                if similarity_threshold is not None:
                    query += " AND (1 - (e.embedding <=> $1::vector)) >= $3"
                    params.append(similarity_threshold)

                query += """
                    ORDER BY e.embedding <=> $1::vector
                    LIMIT $4
                """
                params.append(top_k)

                rows = await conn.fetch(query, *params)

                return [
                    ChunkWithSimilarity(
                        id=row["chunk_id"],
                        file_id=row["file_id"],
                        content=row["content"],
                        chunk_index=row["chunk_index"],
                        token_count=None,
                        created_at=None,  # 検索結果には不要
                        file_name=row["file_name"],
                        similarity=float(row["similarity"]),
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"ベクトル検索エラー: {str(e)}")
            raise DatabaseError("ベクトル検索に失敗しました") from e

    async def delete_by_chunk_id(self, chunk_id: UUID) -> int:
        """
        チャンクIDでEmbeddingを削除

        Args:
            chunk_id: チャンクID

        Returns:
            int: 削除されたEmbedding数

        Raises:
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM embeddings WHERE chunk_id = $1",
                    chunk_id,
                )
                deleted_count = int(result.split()[-1])
                return deleted_count
        except Exception as e:
            logger.error(f"Embedding削除エラー: {str(e)}")
            raise DatabaseError("Embeddingの削除に失敗しました") from e

    async def count_by_file_id(self, file_id: UUID, model_name: Optional[str] = None) -> int:
        """
        ファイルIDでEmbedding数を取得

        Args:
            file_id: ファイルID
            model_name: モデル名（オプション）

        Returns:
            int: Embedding数

        Raises:
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                if model_name:
                    count = await conn.fetchval(
                        """
                        SELECT COUNT(*)
                        FROM embeddings e
                        JOIN chunks c ON e.chunk_id = c.id
                        WHERE c.file_id = $1 AND e.model_name = $2
                        """,
                        file_id,
                        model_name,
                    )
                else:
                    count = await conn.fetchval(
                        """
                        SELECT COUNT(*)
                        FROM embeddings e
                        JOIN chunks c ON e.chunk_id = c.id
                        WHERE c.file_id = $1
                        """,
                        file_id,
                    )

                return count or 0
        except Exception as e:
            logger.error(f"Embedding数取得エラー: {str(e)}")
            raise DatabaseError("Embedding数の取得に失敗しました") from e

