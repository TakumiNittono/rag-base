"""
ファイルRepository（Lv2.5: 3テーブル分離設計）
============================================
filesテーブルへのデータアクセスを提供します。
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

import asyncpg
from asyncpg import Pool

from app.config import get_settings
from app.core.exceptions import DatabaseError, FileNotFoundError
from app.core.logging import get_logger
from app.models.file import File, FileCreate, FileStatus, FileUpdate

logger = get_logger(__name__)
settings = get_settings()

# データベース接続プール
_db_pool: Optional[Pool] = None


async def get_db_pool() -> Pool:
    """
    データベース接続プールを取得（シングルトン）

    Returns:
        Pool: データベース接続プール
    """
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            settings.async_database_url.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=1,
            max_size=10,
        )
    return _db_pool


class FileRepository:
    """ファイルRepository"""

    async def create(self, file_data: FileCreate) -> File:
        """
        ファイルを作成

        Args:
            file_data: ファイルデータ

        Returns:
            File: 作成されたファイル

        Raises:
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO files (
                        file_name, storage_path, file_size, mime_type,
                        status, error_message, chunk_count, embedding_count
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id, created_at, updated_at
                    """,
                    file_data.file_name,
                    file_data.storage_path,
                    file_data.file_size,
                    file_data.mime_type,
                    file_data.status.value,
                    file_data.error_message,
                    file_data.chunk_count,
                    file_data.embedding_count,
                )

                return File(
                    id=row["id"],
                    file_name=file_data.file_name,
                    storage_path=file_data.storage_path,
                    file_size=file_data.file_size,
                    mime_type=file_data.mime_type,
                    status=FileStatus(row["status"]),
                    error_message=file_data.error_message,
                    chunk_count=file_data.chunk_count,
                    embedding_count=file_data.embedding_count,
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
        except Exception as e:
            logger.error(f"ファイル作成エラー: {str(e)}")
            raise DatabaseError("ファイルの作成に失敗しました") from e

    async def get_by_id(self, file_id: UUID) -> File:
        """
        ファイルIDでファイルを取得

        Args:
            file_id: ファイルID

        Returns:
            File: ファイル情報

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM files WHERE id = $1
                    """,
                    file_id,
                )

                if not row:
                    raise FileNotFoundError(str(file_id))

                return File(
                    id=row["id"],
                    file_name=row["file_name"],
                    storage_path=row["storage_path"],
                    file_size=row["file_size"],
                    mime_type=row["mime_type"],
                    status=FileStatus(row["status"]),
                    error_message=row["error_message"],
                    chunk_count=row["chunk_count"],
                    embedding_count=row["embedding_count"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"ファイル取得エラー: {str(e)}")
            raise DatabaseError("ファイルの取得に失敗しました") from e

    async def update(self, file_id: UUID, update_data: FileUpdate) -> File:
        """
        ファイルを更新

        Args:
            file_id: ファイルID
            update_data: 更新データ

        Returns:
            File: 更新されたファイル

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            # 更新フィールドを動的に構築
            updates = []
            values = []
            param_index = 1

            if update_data.status is not None:
                updates.append(f"status = ${param_index}")
                values.append(update_data.status.value)
                param_index += 1

            if update_data.error_message is not None:
                updates.append(f"error_message = ${param_index}")
                values.append(update_data.error_message)
                param_index += 1

            if update_data.chunk_count is not None:
                updates.append(f"chunk_count = ${param_index}")
                values.append(update_data.chunk_count)
                param_index += 1

            if update_data.embedding_count is not None:
                updates.append(f"embedding_count = ${param_index}")
                values.append(update_data.embedding_count)
                param_index += 1

            if not updates:
                # 更新する項目がない場合は現在のデータを返す
                return await self.get_by_id(file_id)

            # updated_atを更新
            updates.append(f"updated_at = ${param_index}")
            values.append(datetime.now())
            param_index += 1

            # file_idを追加
            values.append(file_id)

            query = f"""
                UPDATE files
                SET {', '.join(updates)}
                WHERE id = ${param_index}
                RETURNING *
            """

            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, *values)

                if not row:
                    raise FileNotFoundError(str(file_id))

                return File(
                    id=row["id"],
                    file_name=row["file_name"],
                    storage_path=row["storage_path"],
                    file_size=row["file_size"],
                    mime_type=row["mime_type"],
                    status=FileStatus(row["status"]),
                    error_message=row["error_message"],
                    chunk_count=row["chunk_count"],
                    embedding_count=row["embedding_count"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"ファイル更新エラー: {str(e)}")
            raise DatabaseError("ファイルの更新に失敗しました") from e

    async def list_files(
        self,
        status: Optional[FileStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[File], int]:
        """
        ファイル一覧を取得

        Args:
            status: ステータスでフィルタ（オプション）
            limit: 取得件数
            offset: オフセット

        Returns:
            tuple[list[File], int]: (ファイル一覧, 総件数)

        Raises:
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                # 総件数を取得
                if status:
                    total = await conn.fetchval(
                        "SELECT COUNT(*) FROM files WHERE status = $1",
                        status.value,
                    )
                else:
                    total = await conn.fetchval("SELECT COUNT(*) FROM files")

                # ファイル一覧を取得
                if status:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM files
                        WHERE status = $1
                        ORDER BY created_at DESC
                        LIMIT $2 OFFSET $3
                        """,
                        status.value,
                        limit,
                        offset,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM files
                        ORDER BY created_at DESC
                        LIMIT $1 OFFSET $2
                        """,
                        limit,
                        offset,
                    )

                files = [
                    File(
                        id=row["id"],
                        file_name=row["file_name"],
                        storage_path=row["storage_path"],
                        file_size=row["file_size"],
                        mime_type=row["mime_type"],
                        status=FileStatus(row["status"]),
                        error_message=row["error_message"],
                        chunk_count=row["chunk_count"],
                        embedding_count=row["embedding_count"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                    for row in rows
                ]

                return files, total
        except Exception as e:
            logger.error(f"ファイル一覧取得エラー: {str(e)}")
            raise DatabaseError("ファイル一覧の取得に失敗しました") from e

    async def delete(self, file_id: UUID) -> None:
        """
        ファイルを削除（CASCADEでchunksとembeddingsも削除される）

        Args:
            file_id: ファイルID

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            DatabaseError: データベースエラー
        """
        pool = await get_db_pool()
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM files WHERE id = $1",
                    file_id,
                )

                if result == "DELETE 0":
                    raise FileNotFoundError(str(file_id))
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"ファイル削除エラー: {str(e)}")
            raise DatabaseError("ファイルの削除に失敗しました") from e

