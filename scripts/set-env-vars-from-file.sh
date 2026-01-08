#!/bin/bash
# .envファイルから環境変数を読み込んで設定
# 使用方法: ./scripts/set-env-vars-from-file.sh <function-app-name> <resource-group> [.env-file-path]

FUNCTION_APP_NAME=$1
RESOURCE_GROUP=$2
ENV_FILE=${3:-backend/.env}

if [ -z "$FUNCTION_APP_NAME" ] || [ -z "$RESOURCE_GROUP" ]; then
  echo "使用方法: $0 <function-app-name> <resource-group> [.env-file-path]"
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "エラー: .envファイルが見つかりません: $ENV_FILE"
  exit 1
fi

echo ".envファイルから環境変数を読み込んでいます: $ENV_FILE"

# .envファイルを読み込んで、azコマンド用の形式に変換
SETTINGS=""

while IFS='=' read -r key value; do
  # コメント行と空行をスキップ
  [[ "$key" =~ ^#.*$ ]] && continue
  [[ -z "$key" ]] && continue
  
  # 前後の空白とクォートを削除
  key=$(echo "$key" | xargs)
  value=$(echo "$value" | xargs | sed "s/^['\"]//;s/['\"]$//")
  
  # 空の値はスキップ
  [[ -z "$value" ]] && continue
  
  # 設定に追加
  if [ -z "$SETTINGS" ]; then
    SETTINGS="$key=\"$value\""
  else
    SETTINGS="$SETTINGS $key=\"$value\""
  fi
done < "$ENV_FILE"

if [ -z "$SETTINGS" ]; then
  echo "警告: .envファイルに有効な設定が見つかりませんでした"
  exit 1
fi

echo "環境変数を設定しています..."
az functionapp config appsettings set \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings $SETTINGS

echo "環境変数の設定が完了しました。"

