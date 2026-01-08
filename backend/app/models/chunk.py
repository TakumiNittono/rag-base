"""
チャンクモデル（Lv2.5: 3テーブル分離設計）
=========================================
chunksテーブルのデータモデル定義（Embeddingは含まない）
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChunkBase(BaseModel):
    """チャンクの基本モデル"""

    file_id: UUID = Field(..., description="親ファイルのID")
    content: str = Field(..., description="チャンクのテキスト内容")
    chunk_index: int = Field(..., ge=0, description="ファイル内でのチャンクの順序（0始まり）")
    token_count: Optional[int] = Field(None, description="チャンクのトークン数")


class ChunkCreate(ChunkBase):
    """チャンク作成用モデル"""

    pass


class Chunk(ChunkBase):
    """チャンクモデル（読み取り用）"""

    id: UUID = Field(..., description="チャンクID")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        from_attributes = True


class ChunkWithFile(Chunk):
    """ファイル情報を含むチャンクモデル"""

    file_name: str = Field(..., description="ファイル名")


class ChunkWithSimilarity(ChunkWithFile):
    """類似度を含むチャンクモデル（検索結果用）"""

    similarity: float = Field(..., ge=0.0, le=1.0, description="類似度（0.0-1.0）")

