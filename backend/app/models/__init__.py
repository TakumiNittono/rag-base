"""
データモデルモジュール（Lv2.5: 3テーブル分離設計）
===============================================
- files: ファイルメタデータ
- chunks: テキストチャンク
- embeddings: ベクトル表現
"""

from app.models.chunk import (
    Chunk,
    ChunkBase,
    ChunkCreate,
    ChunkWithFile,
    ChunkWithSimilarity,
)
from app.models.embedding import (
    Embedding,
    EmbeddingBase,
    EmbeddingCreate,
    EmbeddingWithChunk,
)
from app.models.file import File, FileCreate, FileListResponse, FileStatus, FileUpdate

__all__ = [
    # File
    "File",
    "FileCreate",
    "FileUpdate",
    "FileStatus",
    "FileListResponse",
    # Chunk
    "Chunk",
    "ChunkBase",
    "ChunkCreate",
    "ChunkWithFile",
    "ChunkWithSimilarity",
    # Embedding
    "Embedding",
    "EmbeddingBase",
    "EmbeddingCreate",
    "EmbeddingWithChunk",
]
