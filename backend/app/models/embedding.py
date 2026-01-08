"""
Embeddingモデル（Lv2.5: 3テーブル分離設計）
==========================================
embeddingsテーブルのデータモデル定義
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EmbeddingBase(BaseModel):
    """Embeddingの基本モデル"""

    chunk_id: UUID = Field(..., description="対応するチャンクのID")
    embedding: list[float] = Field(..., description="ベクトル表現（1536次元）")
    model_name: str = Field(
        default="text-embedding-3-small",
        description="Embeddingモデル名",
    )

    @Field.validator("embedding")
    @classmethod
    def validate_embedding_dimension(cls, v: list[float]) -> list[float]:
        """Embeddingの次元数を検証"""
        if len(v) != 1536:
            raise ValueError(f"Embeddingの次元数は1536である必要があります（実際: {len(v)}）")
        return v


class EmbeddingCreate(EmbeddingBase):
    """Embedding作成用モデル"""

    pass


class Embedding(EmbeddingBase):
    """Embeddingモデル（読み取り用）"""

    id: UUID = Field(..., description="Embedding ID")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        from_attributes = True


class EmbeddingWithChunk(Embedding):
    """チャンク情報を含むEmbeddingモデル"""

    chunk_content: str = Field(..., description="チャンクのテキスト内容")
    chunk_index: int = Field(..., description="チャンクのインデックス")
    file_id: UUID = Field(..., description="ファイルID")
    file_name: str = Field(..., description="ファイル名")

