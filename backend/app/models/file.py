"""
ファイルモデル（Lv2.5: 3テーブル分離設計）
=========================================
filesテーブルのデータモデル定義
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FileStatus(str, Enum):
    """ファイルの処理ステータス"""

    UPLOADED = "uploaded"
    INDEXING = "indexing"
    INDEXED = "indexed"
    ERROR = "error"


class FileBase(BaseModel):
    """ファイルの基本モデル"""

    file_name: str = Field(..., description="ファイル名")
    storage_path: str = Field(..., description="Supabase Storage内のパス")
    file_size: Optional[int] = Field(None, description="ファイルサイズ（バイト）")
    mime_type: Optional[str] = Field(None, description="MIMEタイプ")
    status: FileStatus = Field(default=FileStatus.UPLOADED, description="処理ステータス")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    chunk_count: int = Field(default=0, description="チャンク数")
    embedding_count: int = Field(default=0, description="Embedding生成済みチャンク数")


class FileCreate(FileBase):
    """ファイル作成用モデル"""

    pass


class FileUpdate(BaseModel):
    """ファイル更新用モデル"""

    status: Optional[FileStatus] = None
    error_message: Optional[str] = None
    chunk_count: Optional[int] = None
    embedding_count: Optional[int] = None


class File(FileBase):
    """ファイルモデル（読み取り用）"""

    id: UUID = Field(..., description="ファイルID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """ファイル一覧レスポンス"""

    files: list[File] = Field(..., description="ファイル一覧")
    total: int = Field(..., description="総件数")

