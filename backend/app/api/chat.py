"""
Chat API
========
RAG検索を実行するエンドポイント
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.auth import get_user_from_token
from app.core.exceptions import AppException, NoResultsError
from app.core.logging import get_logger
from app.services.rag_service import RAGService

logger = get_logger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    """チャットリクエスト"""

    message: str = Field(..., min_length=1, max_length=2000, description="質問文")


class ChatResponse(BaseModel):
    """チャットレスポンス"""

    answer: str = Field(..., description="回答")
    sources: list[dict] = Field(default_factory=list, description="参考にしたチャンクの情報")


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


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request_body: ChatRequest,
    token: str = Depends(get_auth_token),
):
    """
    RAG検索を実行し、回答を生成

    Args:
        request_body: チャットリクエスト
        token: JWTトークン

    Returns:
        ChatResponse: 回答と参考情報

    Raises:
        HTTPException: エラーが発生した場合
    """
    try:
        # 認証
        user = get_user_from_token(token)
        logger.info(f"チャットリクエスト: {user.email} - {request_body.message[:50]}...")

        # RAG Service初期化
        rag_service = RAGService()

        # ベクトル検索
        contexts = await rag_service.retrieve(
            query=request_body.message,
            top_k=None,  # デフォルト値を使用
        )

        # LLMで回答生成
        answer = await rag_service.generate_answer(
            query=request_body.message,
            contexts=contexts,
        )

        # ソース情報を構築
        sources = [
            {
                "file_id": str(ctx.file_id),
                "file_name": ctx.file_name,
                "chunk_id": str(ctx.id),
                "content": ctx.content[:200] + "..." if len(ctx.content) > 200 else ctx.content,
                "similarity": ctx.similarity,
            }
            for ctx in contexts
        ]

        return ChatResponse(answer=answer, sources=sources)

    except NoResultsError as e:
        logger.warning(f"検索結果なし: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except AppException as e:
        logger.error(f"アプリケーションエラー: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="内部サーバーエラーが発生しました")

