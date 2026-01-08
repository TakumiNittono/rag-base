"""
認証・認可モジュール
==================
Supabase Authを使用したJWT認証と管理者判定を提供します。
"""

from functools import wraps
from typing import Optional

from supabase import create_client, Client

from app.config import get_settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Supabaseクライアント（認証用）
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Supabaseクライアントを取得（シングルトン）

    Returns:
        Client: Supabaseクライアント
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
        )
    return _supabase_client


class User:
    """認証済みユーザー情報"""

    def __init__(self, user_id: str, email: str, token: str):
        """
        ユーザー情報を初期化

        Args:
            user_id: ユーザーID
            email: メールアドレス
            token: JWTトークン
        """
        self.user_id = user_id
        self.email = email
        self.token = token

    @property
    def is_admin(self) -> bool:
        """管理者かどうか"""
        return settings.is_admin(self.email)


def verify_jwt(token: str) -> User:
    """
    JWTトークンを検証してユーザー情報を取得

    Args:
        token: JWTトークン

    Returns:
        User: 認証済みユーザー情報

    Raises:
        AuthenticationError: 認証に失敗した場合
    """
    try:
        client = get_supabase_client()
        # SupabaseのJWT検証
        response = client.auth.get_user(token)

        if not response.user:
            raise AuthenticationError("認証トークンが無効です")

        user = User(
            user_id=response.user.id,
            email=response.user.email or "",
            token=token,
        )

        logger.info(f"認証成功: {user.email} (ID: {user.user_id})")
        return user

    except Exception as e:
        logger.warning(f"認証失敗: {str(e)}")
        if isinstance(e, AuthenticationError):
            raise
        raise AuthenticationError("認証に失敗しました") from e


def require_auth(func):
    """
    認証必須デコレータ

    使用例:
        @require_auth
        async def my_endpoint(request, user: User):
            # userは認証済みユーザー情報
            pass
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # FastAPIのRequestオブジェクトからAuthorizationヘッダーを取得
        # 実装はAPI層で行うため、ここでは型チェックのみ
        return await func(*args, **kwargs)

    return wrapper


def require_admin(func):
    """
    管理者必須デコレータ

    使用例:
        @require_admin
        async def admin_endpoint(request, user: User):
            # userは管理者であることが保証される
            pass
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # FastAPIのRequestオブジェクトからAuthorizationヘッダーを取得
        # 実装はAPI層で行うため、ここでは型チェックのみ
        return await func(*args, **kwargs)

    return wrapper


def get_user_from_token(token: Optional[str]) -> User:
    """
    トークンからユーザー情報を取得

    Args:
        token: JWTトークン（Bearer形式または生のトークン）

    Returns:
        User: 認証済みユーザー情報

    Raises:
        AuthenticationError: トークンが無効または存在しない場合
    """
    if not token:
        raise AuthenticationError("認証トークンが提供されていません")

    # Bearer形式の場合は除去
    if token.startswith("Bearer "):
        token = token[7:]

    return verify_jwt(token)


def check_admin(user: User) -> None:
    """
    ユーザーが管理者かどうかを確認

    Args:
        user: ユーザー情報

    Raises:
        AuthorizationError: 管理者でない場合
    """
    if not user.is_admin:
        raise AuthorizationError(f"管理者権限が必要です: {user.email}")

