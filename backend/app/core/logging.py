"""
ロギング設定
===========
アプリケーション全体で使用するロギング設定を提供します。
"""

import logging
import sys
from typing import Optional

from app.config import get_settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    ロギングを設定

    Args:
        log_level: ログレベル（Noneの場合は設定から読み込み）
    """
    settings = get_settings()
    level = log_level or settings.log_level

    # ログレベルを設定
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # ログフォーマット設定
    if settings.is_development:
        # 開発環境: 詳細なフォーマット
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    else:
        # 本番環境: シンプルなフォーマット
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ロギング設定
    logging.basicConfig(
        level=numeric_level,
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # 外部ライブラリのログレベルを調整
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("llama_index").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    ロガーを取得

    Args:
        name: ロガー名（通常は__name__）

    Returns:
        logging.Logger: ロガーインスタンス
    """
    return logging.getLogger(name)

