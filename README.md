# RAGシステム 開発ガイド

## 📋 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [前提条件](#前提条件)
3. [セットアップ手順](#セットアップ手順)
4. [開発フロー](#開発フロー)
5. [実装順序](#実装順序)
6. [各ステップの詳細](#各ステップの詳細)
7. [テスト方法](#テスト方法)
8. [デプロイ手順](#デプロイ手順)
9. [トラブルシューティング](#トラブルシューティング)

---

## プロジェクト概要

ファイルベースのRAG（Retrieval-Augmented Generation）検索システムです。

- **管理者**: ファイルのアップロード・削除・管理
- **一般ユーザー**: 自然言語で質問してRAG検索

詳細は [`きそ.md`](./きそ.md) を参照してください。

---

## 前提条件

### 必要なツール

- **Python 3.11以上**
- **Node.js 18以上**（フロントエンド開発用）
- **Git**
- **Azure Functions Core Tools v4**
  ```bash
  npm install -g azure-functions-core-tools@4 --unsafe-perm true
  ```

### 必要なアカウント・サービス

- **Supabaseアカウント**（無料プラン可）
- **OpenAI APIキー**
- **Azureアカウント**（デプロイ時）

---

## セットアップ手順

### ステップ1: リポジトリクローン

```bash
git clone <repository-url>
cd rag-base
```

### ステップ2: Supabaseプロジェクト作成

1. [Supabase](https://supabase.com)にアクセス
2. 新規プロジェクト作成
3. プロジェクト設定をメモ:
   - Project URL
   - Anon Key
   - Service Role Key
   - Database Password

### ステップ3: データベースセットアップ

1. Supabase Dashboard → SQL Editorを開く
2. `migrations/001_initial_schema.sql`を実行
3. Storage → Buckets → New bucket
   - バケット名: `documents`
   - Public: 無効
   - ポリシー: 認証済みユーザーのみアクセス可能

### ステップ4: バックエンド環境構築

```bash
cd backend

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp env.example .env
# .envファイルを編集して実際の値を設定
```

`.env`ファイルの設定例:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=documents

DB_HOST=db.your-project.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-db-password

OPENAI_API_KEY=sk-your-openai-api-key

EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o-mini
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K=5

ADMIN_EMAILS=admin@example.com

LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:7071
API_TIMEOUT=30
MAX_FILE_SIZE=10485760
ENVIRONMENT=development
```

### ステップ5: フロントエンド環境構築

```bash
cd frontend

# ローカルサーバー起動（例）
python -m http.server 3000
# または
npx serve .
```

### ステップ6: 動作確認

```bash
# バックエンド起動
cd backend
func start

# 別ターミナルでフロントエンド起動
cd frontend
python -m http.server 3000
```

ブラウザで `http://localhost:3000` にアクセスして確認。

---

## 開発フロー

### 1. ブランチ作成

```bash
git checkout -b feature/<機能名>
# 例: git checkout -b feature/chat-api
```

### 2. 実装

要件定義書（`きそ.md`）を参照しながら実装。

### 3. テスト

```bash
# バックエンドテスト
cd backend
pytest

# フロントエンドは手動テスト
```

### 4. コミット

```bash
git add .
git commit -m "feat: <機能名>を実装"
```

### 5. プッシュ・プルリクエスト

```bash
git push origin feature/<機能名>
```

---

## 実装順序

### Phase 1: 基盤構築（Day 1）

1. ✅ プロジェクト構造作成
2. ✅ 設定管理（config/settings.py）
3. ✅ 例外定義（core/exceptions.py）
4. ✅ ロギング設定（core/logging.py）
5. ✅ 認証・認可（core/auth.py）

### Phase 2: データ層（Day 1-2）

1. ✅ データモデル定義（models/）
2. ✅ Repository実装（repositories/）
3. ✅ データベース接続設定

### Phase 3: サービス層（Day 2-3）

1. ✅ Storage Service（ファイル保存）
2. ✅ File Service（ファイル管理）
3. ✅ RAG Service（RAG処理）

### Phase 4: API層（Day 3）

1. ✅ Health API
2. ✅ Chat API
3. ✅ Admin API（upload, files, delete）

### Phase 5: フロントエンド（Day 4）

1. ✅ ログイン画面
2. ✅ チャット画面
3. ✅ 管理画面

### Phase 6: デプロイ（Day 5）

1. ✅ Azure Functionsデプロイ
2. ✅ Azure Static Web Appsデプロイ
3. ✅ 動作確認

---

## 各ステップの詳細

### Phase 1: 基盤構築

#### 1.1 プロジェクト構造作成

```bash
mkdir -p backend/app/{config,core,models,repositories,services,api}
mkdir -p backend/tests/{unit,integration,fixtures}
mkdir -p backend/migrations
mkdir -p frontend/{css,js}
```

#### 1.2 設定管理実装

**ファイル**: `backend/app/config/settings.py`

- Pydantic Settingsを使用
- 環境変数から読み込み
- 型安全な設定管理

#### 1.3 例外定義実装

**ファイル**: `backend/app/core/exceptions.py`

- カスタム例外クラス定義
- エラーコード定義
- HTTPステータスコードマッピング

#### 1.4 認証・認可実装

**ファイル**: `backend/app/core/auth.py`

- JWT検証
- 管理者判定
- デコレータ実装

### Phase 2: データ層

#### 2.1 データモデル定義

**ファイル**: `backend/app/models/file.py`, `backend/app/models/chunk.py`

- Pydanticモデル定義
- バリデーション

#### 2.2 Repository実装

**ファイル**: `backend/app/repositories/file_repository.py`, `backend/app/repositories/chunk_repository.py`

- データベースアクセス
- CRUD操作
- トランザクション管理

### Phase 3: サービス層

#### 3.1 Storage Service

**ファイル**: `backend/app/services/storage_service.py`

- Supabase Storage操作
- ファイルアップロード
- ファイル削除

#### 3.2 File Service

**ファイル**: `backend/app/services/file_service.py`

- ファイル管理ロジック
- ステータス管理
- エラーハンドリング

#### 3.3 RAG Service

**ファイル**: `backend/app/services/rag_service.py`

- テキスト抽出
- チャンキング
- Embedding生成
- ベクトル検索
- LLM呼び出し

### Phase 4: API層

#### 4.1 Health API

**ファイル**: `backend/app/api/health.py`

```python
@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}
```

#### 4.2 Chat API

**ファイル**: `backend/app/api/chat.py`

- POST `/api/chat`
- JWT認証必須
- RAG検索実行

#### 4.3 Admin API

**ファイル**: `backend/app/api/admin.py`

- POST `/api/admin/upload` - ファイルアップロード
- GET `/api/admin/files` - ファイル一覧
- POST `/api/admin/delete` - ファイル削除

### Phase 5: フロントエンド

#### 5.1 ログイン画面

**ファイル**: `frontend/login.html`

- Email/Password入力
- Supabase Auth連携
- エラーハンドリング

#### 5.2 チャット画面

**ファイル**: `frontend/index.html`, `frontend/js/chat.js`

- メッセージ入力
- API呼び出し
- 回答表示
- 会話履歴（セッション内）

#### 5.3 管理画面

**ファイル**: `frontend/admin.html`, `frontend/js/admin.js`

- ファイルアップロード
- ファイル一覧表示
- ファイル削除

---

## テスト方法

### バックエンドテスト

```bash
cd backend

# 全テスト実行
pytest

# 特定のテストファイル実行
pytest tests/unit/test_rag_service.py

# カバレッジ付き実行
pytest --cov=app --cov-report=html
```

### フロントエンドテスト

現時点では手動テストを推奨。

1. ログイン機能
2. チャット機能
3. ファイルアップロード
4. ファイル削除

### APIテスト

**Postman**または**curl**を使用:

```bash
# Health Check
curl http://localhost:7071/api/health

# Chat（認証トークンが必要）
curl -X POST http://localhost:7071/api/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "テスト質問"}'
```

---

## デプロイ手順

### 1. Azure Functionsデプロイ

```bash
# Azure CLIでログイン
az login

# Function App作成（初回のみ）
az functionapp create \
  --resource-group <resource-group> \
  --consumption-plan-location japaneast \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name <function-app-name> \
  --storage-account <storage-account-name>

# 環境変数設定
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings @.env

# デプロイ
cd backend
func azure functionapp publish <function-app-name>
```

### 2. Azure Static Web Appsデプロイ

```bash
# Static Web App作成（初回のみ）
az staticwebapp create \
  --name <static-web-app-name> \
  --resource-group <resource-group> \
  --location japaneast \
  --sku Free

# デプロイ
cd frontend
swa deploy
```

### 3. 動作確認

- [ ] APIヘルスチェック: `GET /api/health`
- [ ] ログイン機能
- [ ] チャット機能
- [ ] ファイルアップロード
- [ ] ファイル削除

---

## トラブルシューティング

### 問題1: データベース接続エラー

**症状**: `DATABASE_ERROR`が発生

**解決方法**:
1. `.env`の接続情報を確認
2. Supabase Dashboardで接続文字列を確認
3. ファイアウォール設定を確認

### 問題2: Azure Functionsが起動しない

**症状**: `func start`でエラー

**解決方法**:
```bash
# Azure Functions Core Toolsのバージョン確認
func --version

# 再インストール
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

### 問題3: CORSエラー

**症状**: フロントエンドからAPI呼び出し時にCORSエラー

**解決方法**:
1. `.env`の`ALLOWED_ORIGINS`を確認
2. Azure FunctionsのCORS設定を確認

### 問題4: ファイルアップロードが遅い

**症状**: アップロードに時間がかかる

**原因**: Embedding生成に時間がかかっている

**解決方法**:
- 非同期処理に変更（将来実装）
- バッチ処理で最適化

---

## 参考資料

- [要件定義書](./きそ.md)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [Supabase Documentation](https://supabase.com/docs)
- [Azure Functions Documentation](https://learn.microsoft.com/azure/azure-functions/)

---

## 開発チェックリスト

### 実装前

- [ ] 要件定義書を確認
- [ ] 環境変数を設定
- [ ] データベーススキーマを作成

### 実装中

- [ ] 型ヒントを記述
- [ ] エラーハンドリングを実装
- [ ] ログを出力
- [ ] コメントを記述

### 実装後

- [ ] テストを実行
- [ ] コードレビュー
- [ ] ドキュメント更新

---

## サポート

問題が発生した場合は、以下を確認してください:

1. 要件定義書（`きそ.md`）の該当セクション
2. ログファイル
3. エラーメッセージ

---

**最終更新**: 2024-01-01

