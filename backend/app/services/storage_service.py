"""
Storage Service
==============
Supabase Storageへのファイル操作を提供します。
"""

from uuid import UUID, uuid4

from supabase import create_client, Client

from app.config import get_settings
from app.core.exceptions import StorageError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Supabaseクライアント（Storage用）
_storage_client: Client | None = None


def get_storage_client() -> Client:
    """
    Supabase Storageクライアントを取得（シングルトン）

    Returns:
        Client: Supabaseクライアント
    """
    global _storage_client
    if _storage_client is None:
        _storage_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,  # Storage操作にはService Role Keyが必要
        )
    return _storage_client


class StorageService:
    """Storage Service"""

    def __init__(self):
        self.client = get_storage_client()
        self.bucket_name = settings.supabase_storage_bucket

    def upload_file(self, file_content: bytes, file_name: str, file_id: UUID) -> str:
        """
        ファイルをアップロード

        Args:
            file_content: ファイル内容（バイト）
            file_name: ファイル名
            file_id: ファイルID

        Returns:
            str: Storage内のパス

        Raises:
            StorageError: アップロードに失敗した場合
        """
        try:
            # パス構造: documents/{file_id}/{file_name}
            storage_path = f"{file_id}/{file_name}"

            # ファイルアップロード
            response = self.client.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": "application/octet-stream"},
            )

            logger.info(f"ファイルアップロード成功: {storage_path}")
            return storage_path

        except Exception as e:
            logger.error(f"ファイルアップロードエラー: {str(e)}")
            raise StorageError(f"ファイルのアップロードに失敗しました: {str(e)}") from e

    def delete_file(self, storage_path: str) -> None:
        """
        ファイルを削除

        Args:
            storage_path: Storage内のパス

        Raises:
            StorageError: 削除に失敗した場合
        """
        try:
            # パスからファイル名を抽出
            # storage_path形式: {file_id}/{file_name}
            self.client.storage.from_(self.bucket_name).remove([storage_path])

            logger.info(f"ファイル削除成功: {storage_path}")

        except Exception as e:
            logger.error(f"ファイル削除エラー: {str(e)}")
            raise StorageError(f"ファイルの削除に失敗しました: {str(e)}") from e

    def get_file_url(self, storage_path: str) -> str:
        """
        ファイルの公開URLを取得

        Args:
            storage_path: Storage内のパス

        Returns:
            str: ファイルのURL

        Raises:
            StorageError: URL取得に失敗した場合
        """
        try:
            response = self.client.storage.from_(self.bucket_name).get_public_url(storage_path)
            return response
        except Exception as e:
            logger.error(f"ファイルURL取得エラー: {str(e)}")
            raise StorageError(f"ファイルURLの取得に失敗しました: {str(e)}") from e

    def file_exists(self, storage_path: str) -> bool:
        """
        ファイルが存在するか確認

        Args:
            storage_path: Storage内のパス

        Returns:
            bool: ファイルが存在する場合True

        Raises:
            StorageError: 確認に失敗した場合
        """
        try:
            files = self.client.storage.from_(self.bucket_name).list(path=storage_path)
            return len(files) > 0
        except Exception as e:
            logger.error(f"ファイル存在確認エラー: {str(e)}")
            raise StorageError(f"ファイルの存在確認に失敗しました: {str(e)}") from e

