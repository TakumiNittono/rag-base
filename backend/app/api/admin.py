"""
Admin API
=========
管理者向けのファイル管理API
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Query, UploadFile
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.auth import check_admin, get_user_from_token
from app.core.exceptions import AppException, FileNotFoundError, InvalidFileTypeError, FileTooLargeError
from app.core.logging import get_logger
from app.models.file import File as FileModel, FileListResponse, FileStatus
from app.services.file_service import FileService
from app.services.rag_service import RAGService

logger = get_logger(__name__)
router = APIRouter()

# 対応ファイル形式
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}


def get_auth_token(request: Request) -> str:
    """
    Authorizationヘッダーからトークンを取得

    Args:
        request: FastAPIリクエスト

    Returns:
        str: JWTトークン

    Raises:
        HTTPException: トークンが存在しない場合
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(status_code=401, detail="認証トークンが提供されていません")
    return authorization


def verify_admin(token: str = Depends(get_auth_token)):
    """
    管理者認証デコレータ

    Args:
        token: JWTトークン

    Returns:
        User: 認証済み管理者ユーザー

    Raises:
        HTTPException: 認証・認可エラー
    """
    user = get_user_from_token(token)
    check_admin(user)
    return user


class DeleteFileRequest(BaseModel):
    """ファイル削除リクエスト"""

    file_id: UUID = Field(..., description="ファイルID")


class DeleteFileResponse(BaseModel):
    """ファイル削除レスポンス"""

    message: str = Field(..., description="メッセージ")
    file_id: UUID = Field(..., description="削除されたファイルID")


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user=Depends(verify_admin),
):
    """
    ファイルをアップロードし、RAG検索対象として登録

    Args:
        file: アップロードファイル
        user: 認証済み管理者ユーザー

    Returns:
        FileModel: アップロードされたファイル情報

    Raises:
        HTTPException: エラーが発生した場合
    """
    try:
        # ファイル形式チェック
        file_ext = None
        if file.filename:
            file_ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

        if file_ext not in ALLOWED_EXTENSIONS:
            raise InvalidFileTypeError(
                file_type=file_ext or "不明",
                allowed_types=list(ALLOWED_EXTENSIONS),
            )

        # ファイルサイズチェック
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > get_settings().max_file_size:
            raise FileTooLargeError(
                file_size=file_size,
                max_size=get_settings().max_file_size,
            )

        logger.info(f"ファイルアップロード開始: {file.filename} ({file_size} bytes) by {user.email}")

        # File Service初期化
        file_service = FileService()

        # ファイル作成（Storage保存 + DB登録）
        file_model = await file_service.create_file(
            file_content=file_content,
            file_name=file.filename or "unknown",
            file_size=file_size,
            mime_type=file.content_type,
        )

        # RAG Service初期化
        rag_service = RAGService()

        # ファイル取り込み（テキスト抽出、チャンキング、Embedding生成）
        # 非同期で実行（バックグラウンド処理として）
        try:
            chunk_count, embedding_count = await rag_service.ingest_file(
                file_content=file_content,
                file_name=file.filename or "unknown",
                file_id=str(file_model.id),
            )
            logger.info(
                f"ファイル取り込み成功: {file_model.id} "
                f"(chunks: {chunk_count}, embeddings: {embedding_count})"
            )
        except Exception as e:
            logger.error(f"ファイル取り込みエラー: {str(e)}", exc_info=True)
            # エラー時はステータスが'error'に更新される（RAG Service内で処理）

        return file_model

    except (InvalidFileTypeError, FileTooLargeError) as e:
        logger.warning(f"ファイルアップロードエラー: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except AppException as e:
        logger.error(f"アプリケーションエラー: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="ファイルアップロードに失敗しました")


@router.get("/files", response_model=FileListResponse)
async def list_files(
    status: Optional[FileStatus] = Query(None, description="ステータスでフィルタ"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    user=Depends(verify_admin),
):
    """
    アップロード済みファイルの一覧を取得

    Args:
        status: ステータスでフィルタ（オプション）
        limit: 取得件数
        offset: オフセット
        user: 認証済み管理者ユーザー

    Returns:
        FileListResponse: ファイル一覧

    Raises:
        HTTPException: エラーが発生した場合
    """
    try:
        file_service = FileService()
        files, total = await file_service.list_files(
            status=status,
            limit=limit,
            offset=offset,
        )

        return FileListResponse(files=files, total=total)

    except Exception as e:
        logger.error(f"ファイル一覧取得エラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="ファイル一覧の取得に失敗しました")


@router.post("/delete", response_model=DeleteFileResponse)
async def delete_file(
    request_body: DeleteFileRequest,
    user=Depends(verify_admin),
):
    """
    ファイルを削除

    Args:
        request_body: ファイル削除リクエスト
        user: 認証済み管理者ユーザー

    Returns:
        DeleteFileResponse: 削除結果

    Raises:
        HTTPException: エラーが発生した場合
    """
    try:
        logger.info(f"ファイル削除開始: {request_body.file_id} by {user.email}")

        file_service = FileService()
        await file_service.delete_file(request_body.file_id)

        return DeleteFileResponse(
            message="ファイルが削除されました",
            file_id=request_body.file_id,
        )

    except FileNotFoundError as e:
        logger.warning(f"ファイル削除エラー: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except AppException as e:
        logger.error(f"アプリケーションエラー: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="ファイル削除に失敗しました")

