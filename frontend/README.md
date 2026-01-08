# RAG System Frontend

## セットアップ

### 1. 設定ファイル更新

各HTMLファイルの`<script>`タグ内で、以下の設定を実際の値に変更してください:

```javascript
window.SUPABASE_URL = 'https://xxxxx.supabase.co';
window.SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
window.API_BASE_URL = 'https://rag-system-api-xxxxx.azurewebsites.net/api';
window.ADMIN_EMAILS = 'admin@example.com';
```

### 2. ローカル実行

```bash
# Python HTTPサーバー
python -m http.server 3000

# または
npx serve .
```

### 3. ブラウザでアクセス

```
http://localhost:3000
```

## デプロイ

詳細は [`../DEPLOYMENT.md`](../DEPLOYMENT.md) を参照してください。

