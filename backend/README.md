# RAG System Backend

## セットアップ

### 1. 仮想環境作成

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 依存関係インストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数設定

```bash
cp env.example .env
# .envファイルを編集して実際の値を設定
```

### 4. ローカル実行

```bash
func start
```

## デプロイ

```bash
func azure functionapp publish <function-app-name>
```

詳細は [`../DEPLOYMENT.md`](../DEPLOYMENT.md) を参照してください。

