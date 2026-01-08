"""
例外定義
========
アプリケーション全体で使用するカスタム例外クラスを定義します。
各例外はHTTPステータスコードとエラーコードを持ちます。
"""

from typing import Any, Optional


class AppException(Exception):
    """
    アプリケーション例外の基底クラス

    すべてのカスタム例外はこのクラスを継承します。
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        例外を初期化

        Args:
            message: エラーメッセージ（ユーザー向け）
            error_code: エラーコード
            status_code: HTTPステータスコード
            details: エラーの詳細情報（開発者向け）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """例外を辞書形式に変換"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            }
        }


# ============================================
# 認証・認可関連の例外
# ============================================


class AuthenticationError(AppException):
    """認証エラー（401）"""

    def __init__(self, message: str = "認証が必要です", details: Optional[dict[str, Any]] = None):
        super().__init__(message, "AUTH_REQUIRED", 401, details)


class AuthorizationError(AppException):
    """認可エラー（403）"""

    def __init__(self, message: str = "権限がありません", details: Optional[dict[str, Any]] = None):
        super().__init__(message, "FORBIDDEN", 403, details)


# ============================================
# リクエスト関連の例外
# ============================================


class InvalidRequestError(AppException):
    """無効なリクエストエラー（400）"""

    def __init__(self, message: str = "リクエストが不正です", details: Optional[dict[str, Any]] = None):
        super().__init__(message, "INVALID_REQUEST", 400, details)


# ============================================
# ファイル関連の例外
# ============================================


class FileNotFoundError(AppException):
    """ファイル不存在エラー（404）"""

    def __init__(self, file_id: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        message = f"ファイルが見つかりません: {file_id}" if file_id else "ファイルが見つかりません"
        super().__init__(message, "FILE_NOT_FOUND", 404, details)


class InvalidFileTypeError(AppException):
    """無効なファイル形式エラー（400）"""

    def __init__(
        self,
        file_type: Optional[str] = None,
        allowed_types: Optional[list[str]] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        message = f"サポートされていないファイル形式です: {file_type}"
        if allowed_types:
            message += f" (対応形式: {', '.join(allowed_types)})"
        super().__init__(message, "INVALID_FILE_TYPE", 400, details)


class FileTooLargeError(AppException):
    """ファイルサイズ超過エラー（400）"""

    def __init__(self, file_size: int, max_size: int, details: Optional[dict[str, Any]] = None):
        message = f"ファイルサイズが制限を超えています: {file_size} bytes (最大: {max_size} bytes)"
        super().__init__(message, "FILE_TOO_LARGE", 400, details)


# ============================================
# 処理関連の例外
# ============================================


class ExtractionError(AppException):
    """テキスト抽出エラー（500）"""

    def __init__(self, message: str = "テキスト抽出に失敗しました", details: Optional[dict[str, Any]] = None):
        super().__init__(message, "EXTRACTION_FAILED", 500, details)


class EmbeddingError(AppException):
    """Embedding生成エラー（500）"""

    def __init__(self, message: str = "Embedding生成に失敗しました", details: Optional[dict[str, Any]] = None):
        super().__init__(message, "EMBEDDING_FAILED", 500, details)


class NoResultsError(AppException):
    """検索結果なしエラー（404）"""

    def __init__(self, message: str = "検索結果が見つかりませんでした", details: Optional[dict[str, Any]] = None):
        super().__init__(message, "NO_RESULTS", 404, details)


class LLMError(AppException):
    """LLM APIエラー（500）"""

    def __init__(self, message: str = "LLM API呼び出しに失敗しました", details: Optional[dict[str, Any]] = None):
        super().__init__(message, "LLM_ERROR", 500, details)


# ============================================
# インフラ関連の例外
# ============================================


class DatabaseError(AppException):
    """データベースエラー（500）"""

    def __init__(self, message: str = "データベースエラーが発生しました", details: Optional[dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", 500, details)


class StorageError(AppException):
    """ストレージエラー（500）"""

    def __init__(self, message: str = "ストレージエラーが発生しました", details: Optional[dict[str, Any]] = None):
        super().__init__(message, "STORAGE_ERROR", 500, details)

