"""
Repositoryモジュール（Lv2.5: 3テーブル分離設計）
==============================================
データアクセス層の実装。
"""

from app.repositories.chunk_repository import ChunkRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.file_repository import FileRepository

__all__ = [
    "FileRepository",
    "ChunkRepository",
    "EmbeddingRepository",
]
