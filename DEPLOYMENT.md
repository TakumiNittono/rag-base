# デプロイ手順書

## 📋 目次

1. [前提条件](#前提条件)
2. [Supabaseセットアップ](#supabaseセットアップ)
3. [Azure Functionsデプロイ](#azure-functionsデプロイ)
4. [Azure Static Web Appsデプロイ](#azure-static-web-appsデプロイ)
5. [環境変数設定](#環境変数設定)
6. [動作確認](#動作確認)
7. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

### 必要なアカウント・ツール

- **Azureアカウント**（有効なサブスクリプション）
- **Supabaseアカウント**（無料プラン可）
- **OpenAI APIキー**
- **Azure CLI**（インストール済み）
- **Azure Functions Core Tools**（インストール済み）
- **Git**（インストール済み）

### Azure CLIログイン

```bash
az login
az account set --subscription <subscription-id>
```

---

## Supabaseセットアップ

### 1. プロジェクト作成

1. [Supabase Dashboard](https://supabase.com/dashboard)にアクセス
2. 「New Project」をクリック
3. プロジェクト情報を入力:
   - **Name**: rag-system（任意）
   - **Database Password**: 強力なパスワードを設定（メモしておく）
   - **Region**: 日本（ap-northeast-1）を推奨
4. プロジェクト作成を待つ（2-3分）

### 2. データベーススキーマ作成

1. Supabase Dashboard → **SQL Editor**を開く
2. `migrations/001_initial_schema.sql`の内容をコピー
3. SQL Editorに貼り付けて実行
4. 実行結果を確認（エラーがないことを確認）

### 3. Storage設定

1. Supabase Dashboard → **Storage**を開く
2. **New bucket**をクリック
3. バケット情報を入力:
   - **Name**: `documents`
   - **Public bucket**: 無効（チェックを外す）
4. **Create bucket**をクリック

#### Storageポリシー設定

SQL Editorで以下を実行:

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

-- 認証済みユーザーのみ削除可能
CREATE POLICY "Authenticated users can delete"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'documents');
```

### 4. 認証設定

1. Supabase Dashboard → **Authentication** → **Settings**
2. **Email認証**を有効化
3. **Password requirements**:
   - Minimum length: 8
   - その他はデフォルトのまま

### 5. APIキー取得

1. Supabase Dashboard → **Settings** → **API**
2. 以下の値をメモ:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - **service_role key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`（⚠️ 機密情報）

### 6. データベース接続情報取得

1. Supabase Dashboard → **Settings** → **Database**
2. **Connection string** → **URI**をコピー
3. パスワード部分を実際のパスワードに置き換え

---

## Azure Functionsデプロイ

### 1. リソースグループ作成

```bash
az group create \
  --name rag-system-rg \
  --location japaneast
```

### 2. Storage Account作成

```bash
az storage account create \
  --name ragstorage$(date +%s) \
  --resource-group rag-system-rg \
  --location japaneast \
  --sku Standard_LRS
```

**注意**: `ragstorage`の後にタイムスタンプを追加（一意性のため）

### 3. Function App作成

```bash
# Storage Account名を取得
STORAGE_ACCOUNT=$(az storage account list \
  --resource-group rag-system-rg \
  --query "[0].name" -o tsv)

# Function App作成（Linux OSを明示的に指定）
az functionapp create \
  --resource-group rag-system-rg \
  --consumption-plan-location japaneast \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux \
  --name rag-system-api-$(date +%s) \
  --storage-account $STORAGE_ACCOUNT
```

**注意**: 
- Function App名は一意である必要があります
- `--os-type Linux`を指定することで、Pythonランタイムが正しく認識されます

### 4. 環境変数設定

環境変数の設定で`value: null`になる場合は、以下の方法を試してください。

#### 方法1: 個別に設定（確実な方法）

```bash
FUNCTION_APP_NAME="rag-system-api-xxxxx"  # 実際のFunction App名に置き換え

# 各環境変数を個別に設定
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group rag-system-rg \
  --settings SUPABASE_URL="https://xxxxx.supabase.co"

az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group rag-system-rg \
  --settings SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# ... 以下、同様に各環境変数を設定
```

#### 方法2: スクリプトを使用（推奨）

```bash
# .envファイルから環境変数を設定
cd /Users/takuminittono/Desktop/ragstudy/rag-base
./scripts/set-env-vars-from-file.sh rag-system-api-xxxxx rag-system-rg
```

#### 方法3: Azure Portalから設定

1. Azure Portal → Function App → **Configuration** → **Application settings**
2. **+ New application setting**をクリック
3. 各環境変数を個別に追加

**注意**: 複数行のコマンドで`value: null`になる場合は、個別に設定するか、Azure Portalから設定してください

### 5. Azure Functionsデプロイ（独立したFunction Appとして）

**重要**: Azure Static Web AppsのAPI機能（100MB制限）ではなく、独立したAzure Functionsとしてデプロイします。

```bash
FUNCTION_APP_NAME="rag-system-api-xxxxx"  # 実際のFunction App名に置き換え

# 依存関係をインストール（仮想環境で）
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Azure Functionsにデプロイ
func azure functionapp publish $FUNCTION_APP_NAME

# デプロイ確認
func azure functionapp list-functions $FUNCTION_APP_NAME
```

**デプロイ後のURL確認**:
```bash
echo "API URL: https://${FUNCTION_APP_NAME}.azurewebsites.net/api"
```

このURLをフロントエンドの`window.API_BASE_URL`に設定してください。

### 6. CORS設定

```bash
az functionapp cors add \
  --name $FUNCTION_APP_NAME \
  --resource-group rag-system-rg \
  --allowed-origins "https://your-static-web-app.azurestaticapps.net"
```

---

## Azure Static Web Appsデプロイ

### 方法1: GitHub Actions（推奨）

1. **GitHubリポジトリにプッシュ**

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/TakumiNittono/rag-base.git
git push -u origin main
```

2. **Static Web App作成**

```bash
az staticwebapp create \
  --name rag-system-web \
  --resource-group rag-system-rg \
  --location japaneast \
  --sku Free \
  --source https://github.com/TakumiNittono/rag-base \
  --branch main \
  --app-location frontend
  # 注意: api-locationは指定しない（独立したAzure Functionsとしてデプロイ）
```

3. **GitHub Actionsが自動実行される**
   - `.github/workflows/azure-static-web-apps.yml`が自動生成されるか、手動で作成
   - Azure Portal → Static Web App → **Manage deployment token**でトークンを取得
   - GitHubリポジトリの**Settings** → **Secrets and variables** → **Actions**で`AZURE_STATIC_WEB_APPS_API_TOKEN`を設定
   - デプロイが完了するまで待つ（5-10分）

**重要**: Azure Functionsは独立してデプロイする必要があります（サイズ制限のため）

### 方法2: SWA CLI（手動デプロイ）

```bash
# SWA CLIインストール
npm install -g @azure/static-web-apps-cli

# デプロイ
cd frontend
swa deploy \
  --app-location . \
  --api-location ../backend \
  --deployment-token <deployment-token>
```

**Deployment Token取得方法**:
1. Azure Portal → Static Web App → **Manage deployment token**
2. トークンをコピー

### 3. フロントエンド設定更新

デプロイ後、Static Web AppのURLを取得:

```bash
az staticwebapp show \
  --name rag-system-web \
  --resource-group rag-system-rg \
  --query defaultHostname -o tsv
```

各HTMLファイルの設定を更新:

```javascript
window.SUPABASE_URL = 'https://xxxxx.supabase.co';
window.SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
window.API_BASE_URL = 'https://rag-system-api-xxxxx.azurewebsites.net/api';
window.ADMIN_EMAILS = 'admin@example.com';
```

---

## 環境変数設定

### 本番環境変数チェックリスト

- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_ANON_KEY`
- [ ] `SUPABASE_SERVICE_ROLE_KEY`
- [ ] `SUPABASE_STORAGE_BUCKET`
- [ ] `DB_HOST`
- [ ] `DB_PORT`
- [ ] `DB_NAME`
- [ ] `DB_USER`
- [ ] `DB_PASSWORD`
- [ ] `OPENAI_API_KEY`
- [ ] `EMBEDDING_MODEL`
- [ ] `CHAT_MODEL`
- [ ] `CHUNK_SIZE`
- [ ] `CHUNK_OVERLAP`
- [ ] `TOP_K`
- [ ] `ADMIN_EMAILS`
- [ ] `LOG_LEVEL`
- [ ] `ALLOWED_ORIGINS`
- [ ] `API_TIMEOUT`
- [ ] `MAX_FILE_SIZE`
- [ ] `ENVIRONMENT`

### 環境変数を一括設定する方法

`.env`ファイルから読み込んで設定する場合:

```bash
# .envファイルの内容をJSON形式に変換して設定
# （手動で設定する方が確実）
```

---

## 動作確認

### 1. APIヘルスチェック

```bash
curl https://rag-system-api-xxxxx.azurewebsites.net/api/health
```

**期待結果**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 2. フロントエンドアクセス

ブラウザでStatic Web AppのURLにアクセス:
```
https://rag-system-web.azurestaticapps.net
```

### 3. ログイン機能確認

1. `/login.html`にアクセス
2. テストユーザーでログイン
3. `/index.html`にリダイレクトされることを確認

### 4. チャット機能確認

1. チャット画面で質問を入力
2. 回答が表示されることを確認
3. ソース情報が表示されることを確認

### 5. 管理画面確認

1. 管理者アカウントでログイン
2. `/admin.html`にアクセス
3. ファイルアップロードをテスト
4. ファイル一覧が表示されることを確認
5. ファイル削除をテスト

### 6. ログ確認

```bash
# Azure Functionsログ
az functionapp log tail \
  --name rag-system-api-xxxxx \
  --resource-group rag-system-rg

# Static Web Appログ
az staticwebapp show \
  --name rag-system-web \
  --resource-group rag-system-rg
```

---

## トラブルシューティング

### 問題1: APIが404エラーを返す

**原因**: ルーティング設定の問題

**解決方法**:
- `function_app.py`のルーター設定を確認
- Azure Functionsの`host.json`を確認

### 問題2: CORSエラー

**原因**: CORS設定が正しくない

**解決方法**:
```bash
az functionapp cors show \
  --name rag-system-api-xxxxx \
  --resource-group rag-system-rg

# 必要に応じて追加
az functionapp cors add \
  --name rag-system-api-xxxxx \
  --resource-group rag-system-rg \
  --allowed-origins "https://rag-system-web.azurestaticapps.net"
```

### 問題3: 認証エラー

**原因**: JWTトークンが無効

**解決方法**:
- Supabaseの設定を確認
- フロントエンドの`SUPABASE_URL`と`SUPABASE_ANON_KEY`を確認

### 問題4: データベース接続エラー

**原因**: 接続情報が間違っている

**解決方法**:
- 環境変数の`DB_HOST`、`DB_PASSWORD`を確認
- Supabase Dashboardで接続文字列を確認

### 問題5: ファイルアップロードが失敗する

**原因**: Storageポリシーが設定されていない

**解決方法**:
- Supabase Dashboard → Storage → Policiesを確認
- 上記のStorageポリシー設定を実行

### 問題6: Pythonランタイムエラー（Windows OSエラー）

**原因**: Azure CLIがOSを誤認識している

**解決方法**:
- `--os-type Linux`を明示的に指定
- リージョンを`japaneast`に指定（Linuxプランが利用可能）

```bash
az functionapp create \
  --resource-group rag-system-rg \
  --consumption-plan-location japaneast \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux \
  --name rag-system-api-$(date +%s) \
  --storage-account $STORAGE_ACCOUNT
```

### 問題7: "The size of the function content was too large" エラー

**原因**: Azure Static Web AppsのAPI機能には100MBの制限があります。LlamaIndexなどの大きな依存関係を含むアプリケーションには適していません。

**解決方法**:
1. Azure Static Web Appsの`--api-location`オプションを使用しない
2. 独立したAzure Functionsとしてデプロイする（上記の手順5を参照）
3. GitHub Actionsワークフローの`api_location`を空にする
4. フロントエンドの`window.API_BASE_URL`を独立したAzure FunctionsのURLに設定する

**確認事項**:
- `.github/workflows/azure-static-web-apps.yml`の`api_location`が空になっているか
- `az staticwebapp create`コマンドで`--api-location`を指定していないか
- フロントエンドのHTMLファイルで`window.API_BASE_URL`が正しく設定されているか

---

## デプロイ後の確認事項

- [ ] APIヘルスチェックが成功
- [ ] ログイン機能が動作
- [ ] チャット機能が動作
- [ ] ファイルアップロードが動作
- [ ] ファイル一覧が表示される
- [ ] ファイル削除が動作
- [ ] エラーログに異常がない

---

**デプロイ完了！**
