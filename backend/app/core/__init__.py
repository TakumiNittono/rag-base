"""
コアモジュール
=============
アプリケーション全体で使用される共通機能を提供します。
- 例外処理
- 認証・認可
- ロギング
"""

from app.core.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    EmbeddingError,
    ExtractionError,
    FileNotFoundError,
    FileTooLargeError,
    InvalidFileTypeError,
    InvalidRequestError,
    LLMError,
    NoResultsError,
    StorageError,
)
from app.core.logging import get_logger, setup_logging

__all__ = [
    # 例外
    "AppException",
    "AuthenticationError",
    "AuthorizationError",
    "InvalidRequestError",
    "FileNotFoundError",
    "InvalidFileTypeError",
    "FileTooLargeError",
    "ExtractionError",
    "EmbeddingError",
    "NoResultsError",
    "LLMError",
    "DatabaseError",
    "StorageError",
    # ロギング
    "get_logger",
    "setup_logging",
]
