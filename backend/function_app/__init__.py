"""
Azure Functions エントリーポイント
==================================
FastAPIアプリケーションをAzure Functionsで実行するためのエントリーポイント
"""

import asyncio
import logging
from typing import Callable

import azure.functions as func
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.logging import setup_logging
from app.api import health, chat, admin

# ロギング設定
setup_logging()
logger = logging.getLogger(__name__)

# 設定取得（エラーハンドリング付き）
try:
    settings = get_settings()
    allowed_origins = settings.allowed_origins_list
except Exception as e:
    logger.warning(f"設定の読み込みに失敗しました（デフォルト値を使用）: {str(e)}")
    allowed_origins = ["*"]  # デフォルトで全てのオリジンを許可

# FastAPIアプリケーション作成
app = FastAPI(
    title="RAG System API",
    description="ファイルベースのRAG検索システムAPI",
    version="1.0.0",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録（Azure Functionsの/apiプレフィックスが自動的に追加されるため、ここでは/apiを追加しない）
# route: "{*route}"の場合、/api/healthへのリクエストは/healthとしてFastAPIアプリに渡される
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """
    Azure Functions HTTPトリガー

    Args:
        req: HTTPリクエスト
        context: 関数コンテキスト

    Returns:
        func.HttpResponse: HTTPレスポンス
    """
    return func.AsgiMiddleware(app).handle(req, context)
