# 開発作業手順書

このドキュメントは、RAGシステムの開発を進めるための詳細な作業手順を記載しています。

## 📋 目次

1. [開発環境準備](#開発環境準備)
2. [Day 1: 基盤構築](#day-1-基盤構築)
3. [Day 2: データ層・サービス層](#day-2-データ層サービス層)
4. [Day 3: API層実装](#day-3-api層実装)
5. [Day 4: フロントエンド実装](#day-4-フロントエンド実装)
6. [Day 5: デプロイ・動作確認](#day-5-デプロイ動作確認)

---

## 開発環境準備

### 1. リポジトリセットアップ

```bash
# リポジトリクローン
git clone https://github.com/TakumiNittono/rag-base.git
cd rag-base

# ブランチ作成
git checkout -b develop
```

### 2. Supabaseセットアップ

1. **プロジェクト作成**
   - https://supabase.com にアクセス
   - 新規プロジェクト作成
   - リージョン: `ap-northeast-1`（東京）を推奨

2. **データベーススキーマ作成**
   - Dashboard → SQL Editor
   - `migrations/001_initial_schema.sql`を実行
   - 実行結果を確認

3. **Storage設定**
   - Dashboard → Storage → Buckets
   - New bucket作成
     - 名前: `documents`
     - Public: 無効
   - Policies設定:
     ```sql
     -- 認証済みユーザーのみアップロード可能
     CREATE POLICY "Authenticated users can upload"
     ON storage.objects FOR INSERT
     TO authenticated
     WITH CHECK (bucket_id = 'documents');

     -- 認証済みユーザーのみ読み取り可能
     CREATE POLICY "Authenticated users can read"
     ON storage.objects FOR SELECT
     TO authenticated
     USING (bucket_id = 'documents');
     ```

4. **認証設定**
   - Dashboard → Authentication → Settings
   - Email認証を有効化
   - パスワード要件: 最小8文字

### 3. 環境変数設定

```bash
cd backend
cp env.example .env
```

`.env`ファイルを編集して実際の値を設定:

```bash
# Supabase設定（Dashboard → Settings → APIから取得）
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# データベース設定（Dashboard → Settings → Database → Connection string）
DB_HOST=db.xxxxx.supabase.co
DB_PASSWORD=your-password

# OpenAI APIキー
OPENAI_API_KEY=sk-...

# 管理者メールアドレス
ADMIN_EMAILS=your-email@example.com
```

### 4. 仮想環境セットアップ

```bash
cd backend

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 動作確認
python -c "from app.config import get_settings; print(get_settings())"
```

---

## Day 1: 基盤構築

### 目標

- プロジェクト構造の作成
- 設定管理の実装
- 例外処理の実装
- 認証・認可の実装

### 作業手順

#### ステップ1: プロジェクト構造作成

```bash
cd backend

# ディレクトリ作成
mkdir -p app/{config,core,models,repositories,services,api}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p migrations

# __init__.py作成
touch app/__init__.py
touch app/config/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/repositories/__init__.py
touch app/services/__init__.py
touch app/api/__init__.py
```

#### ステップ2: 設定管理実装

**ファイル**: `backend/app/config/settings.py`

要件定義書の「12. 環境変数・設定」を参照して実装。

**確認事項**:
- [ ] 環境変数が正しく読み込まれる
- [ ] 型チェックが機能する
- [ ] バリデーションが動作する

**テスト**:
```bash
python -c "from app.config import get_settings; s = get_settings(); print(s.supabase_url)"
```

#### ステップ3: 例外定義実装

**ファイル**: `backend/app/core/exceptions.py`

要件定義書の「13. エラーハンドリング」を参照して実装。

**実装する例外クラス**:
- `AppException`（基底クラス）
- `AuthenticationError`
- `AuthorizationError`
- `InvalidRequestError`
- `FileNotFoundError`
- `InvalidFileTypeError`
- `FileTooLargeError`
- `ExtractionError`
- `EmbeddingError`
- `NoResultsError`
- `LLMError`
- `DatabaseError`
- `StorageError`

**確認事項**:
- [ ] すべての例外クラスが定義されている
- [ ] HTTPステータスコードがマッピングされている
- [ ] エラーコードが定義されている

#### ステップ4: ロギング実装

**ファイル**: `backend/app/core/logging.py`

**実装内容**:
- ロガー設定
- フォーマット設定
- ログレベル設定

**確認事項**:
- [ ] ログが正しく出力される
- [ ] ログレベルが環境変数から読み込まれる

#### ステップ5: 認証・認可実装

**ファイル**: `backend/app/core/auth.py`

**実装内容**:
- JWT検証関数
- 管理者判定関数
- 認証デコレータ
- 管理者チェックデコレータ

**確認事項**:
- [ ] JWTトークンが正しく検証される
- [ ] 管理者判定が正しく動作する
- [ ] デコレータが正しく動作する

**テスト**:
```python
# テスト用JWTトークンで検証
from app.core.auth import verify_jwt, is_admin

token = "test-token"
user = verify_jwt(token)
print(user.email)
print(is_admin(user.email))
```

### Day 1 完了チェックリスト

- [ ] プロジェクト構造が作成されている
- [ ] 設定管理が実装されている
- [ ] 例外定義が実装されている
- [ ] ロギングが実装されている
- [ ] 認証・認可が実装されている
- [ ] 各モジュールがインポートできる

---

## Day 2: データ層・サービス層

### 目標

- データモデルの定義
- Repositoryの実装
- Storage Serviceの実装
- File Serviceの実装
- RAG Serviceの実装

### 作業手順

#### ステップ1: データモデル定義

**ファイル**: `backend/app/models/file.py`, `backend/app/models/chunk.py`

**実装内容**:
- `File`モデル（Pydantic）
- `Chunk`モデル（Pydantic）
- バリデーション

**確認事項**:
- [ ] モデルが正しく定義されている
- [ ] バリデーションが動作する

#### ステップ2: Repository実装

**ファイル**: `backend/app/repositories/file_repository.py`, `backend/app/repositories/chunk_repository.py`

**実装内容**:
- データベース接続設定
- CRUD操作
- ベクトル検索

**確認事項**:
- [ ] データベース接続が成功する
- [ ] CRUD操作が正しく動作する
- [ ] ベクトル検索が正しく動作する

**テスト**:
```python
from app.repositories.file_repository import FileRepository

repo = FileRepository()
files = repo.list_files()
print(files)
```

#### ステップ3: Storage Service実装

**ファイル**: `backend/app/services/storage_service.py`

**実装内容**:
- Supabase Storage接続
- ファイルアップロード
- ファイル削除
- ファイル取得

**確認事項**:
- [ ] ファイルアップロードが成功する
- [ ] ファイル削除が成功する
- [ ] エラーハンドリングが正しい

#### ステップ4: File Service実装

**ファイル**: `backend/app/services/file_service.py`

**実装内容**:
- ファイルアップロード処理
- ファイル削除処理
- ステータス管理

**確認事項**:
- [ ] ファイルアップロードの一連の流れが動作する
- [ ] ファイル削除の一連の流れが動作する
- [ ] エラーハンドリングが正しい

#### ステップ5: RAG Service実装

**ファイル**: `backend/app/services/rag_service.py`

**実装内容**:
- テキスト抽出（PDF/TXT/MD）
- チャンキング
- Embedding生成
- ベクトル検索
- LLM呼び出し

**確認事項**:
- [ ] テキスト抽出が正しく動作する
- [ ] チャンキングが正しく動作する
- [ ] Embedding生成が成功する
- [ ] ベクトル検索が正しく動作する
- [ ] LLM呼び出しが成功する

**テスト**:
```python
from app.services.rag_service import RAGService

rag = RAGService()

# ファイル取り込みテスト
rag.ingest_file("test.txt", "file-id")

# 検索テスト
results = rag.retrieve("テスト質問", top_k=5)
print(results)

# 回答生成テスト
answer = rag.generate_answer("テスト質問", results)
print(answer)
```

### Day 2 完了チェックリスト

- [ ] データモデルが定義されている
- [ ] Repositoryが実装されている
- [ ] Storage Serviceが実装されている
- [ ] File Serviceが実装されている
- [ ] RAG Serviceが実装されている
- [ ] 各サービスが正しく動作する

---

## Day 3: API層実装

### 目標

- Health APIの実装
- Chat APIの実装
- Admin APIの実装

### 作業手順

#### ステップ1: Azure Functions設定

**ファイル**: `backend/host.json`

```json
{
  "version": "2.0",
  "logging": {
    "logLevel": {
      "default": "Information"
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
```

**ファイル**: `backend/function_app.py`

FastAPIアプリケーションのエントリーポイント。

#### ステップ2: Health API実装

**ファイル**: `backend/app/api/health.py`

**実装内容**:
- GET `/api/health`
- 認証不要
- システム状態を返す

**確認事項**:
- [ ] エンドポイントが正しく動作する
- [ ] レスポンスが正しい形式

**テスト**:
```bash
curl http://localhost:7071/api/health
```

#### ステップ3: Chat API実装

**ファイル**: `backend/app/api/chat.py`

**実装内容**:
- POST `/api/chat`
- JWT認証必須
- RAG検索実行
- 回答を返す

**確認事項**:
- [ ] 認証が正しく動作する
- [ ] RAG検索が正しく動作する
- [ ] エラーハンドリングが正しい

**テスト**:
```bash
curl -X POST http://localhost:7071/api/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "テスト質問"}'
```

#### ステップ4: Admin API実装

**ファイル**: `backend/app/api/admin.py`

**実装内容**:
- POST `/api/admin/upload` - ファイルアップロード
- GET `/api/admin/files` - ファイル一覧
- POST `/api/admin/delete` - ファイル削除

**確認事項**:
- [ ] 管理者チェックが正しく動作する
- [ ] ファイルアップロードが正しく動作する
- [ ] ファイル一覧取得が正しく動作する
- [ ] ファイル削除が正しく動作する

**テスト**:
```bash
# ファイルアップロード
curl -X POST http://localhost:7071/api/admin/upload \
  -H "Authorization: Bearer <admin-token>" \
  -F "file=@test.txt"

# ファイル一覧
curl http://localhost:7071/api/admin/files \
  -H "Authorization: Bearer <admin-token>"

# ファイル削除
curl -X POST http://localhost:7071/api/admin/delete \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"file_id": "uuid"}'
```

### Day 3 完了チェックリスト

- [ ] Health APIが実装されている
- [ ] Chat APIが実装されている
- [ ] Admin APIが実装されている
- [ ] すべてのAPIが正しく動作する
- [ ] エラーハンドリングが正しい

---

## Day 4: フロントエンド実装

### 目標

- ログイン画面の実装
- チャット画面の実装
- 管理画面の実装

### 作業手順

#### ステップ1: プロジェクト構造作成

```bash
cd frontend
mkdir -p css js
```

#### ステップ2: 共通CSS実装

**ファイル**: `frontend/css/style.css`

BootstrapまたはカスタムCSSを実装。

#### ステップ3: 認証機能実装

**ファイル**: `frontend/js/auth.js`

**実装内容**:
- Supabase Auth接続
- ログイン処理
- ログアウト処理
- 認証状態チェック

#### ステップ4: ログイン画面実装

**ファイル**: `frontend/login.html`

**実装内容**:
- Email/Password入力フォーム
- ログイン処理
- エラー表示
- リダイレクト処理

**確認事項**:
- [ ] ログインが成功する
- [ ] エラーが正しく表示される
- [ ] リダイレクトが正しく動作する

#### ステップ5: チャット画面実装

**ファイル**: `frontend/index.html`, `frontend/js/chat.js`

**実装内容**:
- メッセージ入力欄
- 送信ボタン
- 会話履歴表示
- API呼び出し
- 回答表示

**確認事項**:
- [ ] メッセージ送信が成功する
- [ ] 回答が正しく表示される
- [ ] エラーが正しく表示される
- [ ] ローディング表示が動作する

#### ステップ6: 管理画面実装

**ファイル**: `frontend/admin.html`, `frontend/js/admin.js`

**実装内容**:
- ファイルアップロードUI
- ファイル一覧表示
- ファイル削除機能
- ステータス表示

**確認事項**:
- [ ] ファイルアップロードが成功する
- [ ] ファイル一覧が正しく表示される
- [ ] ファイル削除が成功する
- [ ] ステータスが正しく表示される

### Day 4 完了チェックリスト

- [ ] ログイン画面が実装されている
- [ ] チャット画面が実装されている
- [ ] 管理画面が実装されている
- [ ] すべての画面が正しく動作する
- [ ] エラーハンドリングが正しい

---

## Day 5: デプロイ・動作確認

### 目標

- Azure Functionsデプロイ
- Azure Static Web Appsデプロイ
- 動作確認

### 作業手順

#### ステップ1: Azure Functionsデプロイ準備

```bash
# Azure CLIでログイン
az login

# リソースグループ作成（初回のみ）
az group create --name rag-system-rg --location japaneast

# Storage Account作成（初回のみ）
az storage account create \
  --name ragstorage \
  --resource-group rag-system-rg \
  --location japaneast \
  --sku Standard_LRS

# Function App作成（初回のみ）
az functionapp create \
  --resource-group rag-system-rg \
  --consumption-plan-location japaneast \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name rag-system-api \
  --storage-account ragstorage
```

#### ステップ2: 環境変数設定

```bash
# 環境変数を一括設定
az functionapp config appsettings set \
  --name rag-system-api \
  --resource-group rag-system-rg \
  --settings \
    SUPABASE_URL="<url>" \
    SUPABASE_ANON_KEY="<key>" \
    # ... その他の環境変数
```

または`.env`ファイルから読み込み:

```bash
# .envファイルをJSON形式に変換して設定
# （手動で設定する方が確実）
```

#### ステップ3: Azure Functionsデプロイ

```bash
cd backend

# デプロイ
func azure functionapp publish rag-system-api

# デプロイ確認
func azure functionapp list-functions rag-system-api
```

#### ステップ4: Azure Static Web Appsデプロイ

```bash
# Static Web App作成（初回のみ）
az staticwebapp create \
  --name rag-system-web \
  --resource-group rag-system-rg \
  --location japaneast \
  --sku Free

# デプロイ
cd frontend
swa deploy
```

またはGitHub Actionsを使用（推奨）:

1. GitHubリポジトリにpush
2. `.github/workflows/azure-static-web-apps-<name>.yml`が自動生成
3. 自動デプロイが実行される

#### ステップ5: 動作確認

**API確認**:
```bash
# Health Check
curl https://rag-system-api.azurewebsites.net/api/health

# Chat API（認証トークンが必要）
curl -X POST https://rag-system-api.azurewebsites.net/api/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "テスト"}'
```

**フロントエンド確認**:
- ブラウザでStatic Web AppのURLにアクセス
- ログイン → チャット → 管理画面の順に確認

### Day 5 完了チェックリスト

- [ ] Azure Functionsがデプロイされている
- [ ] Azure Static Web Appsがデプロイされている
- [ ] 環境変数が正しく設定されている
- [ ] APIが正しく動作する
- [ ] フロントエンドが正しく動作する
- [ ] エラーログを確認

---

## トラブルシューティング

### よくある問題

#### 1. デプロイエラー

**症状**: `func azure functionapp publish`でエラー

**解決方法**:
- Azure CLIでログインしているか確認
- Function App名が正しいか確認
- リソースグループが存在するか確認

#### 2. 環境変数が読み込まれない

**症状**: デプロイ後、環境変数が設定されていない

**解決方法**:
```bash
# 環境変数を確認
az functionapp config appsettings list \
  --name rag-system-api \
  --resource-group rag-system-rg

# 環境変数を再設定
az functionapp config appsettings set \
  --name rag-system-api \
  --resource-group rag-system-rg \
  --settings KEY=VALUE
```

#### 3. CORSエラー

**症状**: フロントエンドからAPI呼び出し時にCORSエラー

**解決方法**:
- Azure FunctionsのCORS設定を確認
- `ALLOWED_ORIGINS`環境変数を確認
- Static Web AppのURLを許可リストに追加

---

## 次のステップ

実装完了後:

1. **テスト追加**
   - 単体テスト
   - 統合テスト
   - E2Eテスト

2. **パフォーマンス最適化**
   - データベースクエリ最適化
   - キャッシュ実装
   - 非同期処理

3. **監視・ログ**
   - Application Insights設定
   - エラートラッキング
   - パフォーマンス監視

---

**最終更新**: 2024-01-01

