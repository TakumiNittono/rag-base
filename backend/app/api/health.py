"""
Health API
==========
システムのヘルスチェックエンドポイント
"""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    ヘルスチェック

    Returns:
        dict: システム状態
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }

