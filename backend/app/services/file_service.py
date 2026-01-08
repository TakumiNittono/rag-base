"""
File Service
===========
ファイル管理のビジネスロジックを提供します。
"""

from uuid import UUID, uuid4

from app.core.exceptions import FileNotFoundError, StorageError
from app.core.logging import get_logger
from app.models.file import File, FileCreate, FileStatus, FileUpdate
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.file_repository import FileRepository
from app.services.storage_service import StorageService

logger = get_logger(__name__)


class FileService:
    """File Service"""

    def __init__(self):
        self.file_repo = FileRepository()
        self.chunk_repo = ChunkRepository()
        self.embedding_repo = EmbeddingRepository()
        self.storage_service = StorageService()

    async def create_file(
        self,
        file_content: bytes,
        file_name: str,
        file_size: int,
        mime_type: str | None = None,
    ) -> File:
        """
        ファイルを作成（Storageに保存 + DBにメタデータ登録）

        Args:
            file_content: ファイル内容（バイト）
            file_name: ファイル名
            file_size: ファイルサイズ（バイト）
            mime_type: MIMEタイプ（オプション）

        Returns:
            File: 作成されたファイル情報

        Raises:
            StorageError: Storage保存に失敗した場合
        """
        file_id = uuid4()

        try:
            # 1. Storageにファイルをアップロード
            storage_path = self.storage_service.upload_file(
                file_content=file_content,
                file_name=file_name,
                file_id=file_id,
            )

            # 2. DBにメタデータを登録
            file_data = FileCreate(
                file_name=file_name,
                storage_path=storage_path,
                file_size=file_size,
                mime_type=mime_type,
                status=FileStatus.UPLOADED,
            )

            file = await self.file_repo.create(file_data)

            logger.info(f"ファイル作成成功: {file.id} ({file_name})")
            return file

        except Exception as e:
            # エラー時はStorageからファイルを削除（クリーンアップ）
            try:
                storage_path = f"{file_id}/{file_name}"
                self.storage_service.delete_file(storage_path)
            except Exception:
                pass  # クリーンアップ失敗は無視

            raise

    async def get_file(self, file_id: UUID) -> File:
        """
        ファイルを取得

        Args:
            file_id: ファイルID

        Returns:
            File: ファイル情報

        Raises:
            FileNotFoundError: ファイルが見つからない場合
        """
        return await self.file_repo.get_by_id(file_id)

    async def list_files(
        self,
        status: FileStatus | None = None,
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
        """
        return await self.file_repo.list_files(status=status, limit=limit, offset=offset)

    async def update_file_status(
        self,
        file_id: UUID,
        status: FileStatus,
        error_message: str | None = None,
    ) -> File:
        """
        ファイルのステータスを更新

        Args:
            file_id: ファイルID
            status: 新しいステータス
            error_message: エラーメッセージ（エラー時のみ）

        Returns:
            File: 更新されたファイル情報

        Raises:
            FileNotFoundError: ファイルが見つからない場合
        """
        update_data = FileUpdate(
            status=status,
            error_message=error_message,
        )
        return await self.file_repo.update(file_id, update_data)

    async def update_file_counts(
        self,
        file_id: UUID,
        chunk_count: int | None = None,
        embedding_count: int | None = None,
    ) -> File:
        """
        ファイルのチャンク数・Embedding数を更新

        Args:
            file_id: ファイルID
            chunk_count: チャンク数（オプション）
            embedding_count: Embedding数（オプション）

        Returns:
            File: 更新されたファイル情報

        Raises:
            FileNotFoundError: ファイルが見つからない場合
        """
        update_data = FileUpdate(
            chunk_count=chunk_count,
            embedding_count=embedding_count,
        )
        return await self.file_repo.update(file_id, update_data)

    async def delete_file(self, file_id: UUID) -> None:
        """
        ファイルを削除（Storage + DB + chunks + embeddings）

        Args:
            file_id: ファイルID

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            StorageError: Storage削除に失敗した場合
        """
        # 1. ファイル情報を取得（Storageパスを取得するため）
        file = await self.file_repo.get_by_id(file_id)

        try:
            # 2. Storageからファイルを削除
            try:
                self.storage_service.delete_file(file.storage_path)
            except StorageError as e:
                logger.warning(f"Storage削除エラー（続行）: {str(e)}")
                # Storage削除失敗は警告のみ（DB削除は続行）

            # 3. DBからファイルを削除（CASCADEでchunksとembeddingsも削除される）
            await self.file_repo.delete(file_id)

            logger.info(f"ファイル削除成功: {file_id}")

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"ファイル削除エラー: {str(e)}")
            raise

