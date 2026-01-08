"""
RAG System Backend Application
=============================
ファイルベースのRAG検索システムのバックエンドアプリケーション。

モジュール構成:
- config: 設定管理
- core: 共通機能（認証、例外、ロギング）
- models: データモデル（Lv2.5: files, chunks, embeddings）
- repositories: データアクセス層
- services: ビジネスロジック層
- api: APIエンドポイント
"""

__version__ = "1.0.0"
