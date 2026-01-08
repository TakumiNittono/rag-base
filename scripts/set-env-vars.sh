#!/bin/bash
# 環境変数設定スクリプト
# 使用方法: ./scripts/set-env-vars.sh <function-app-name> <resource-group>

FUNCTION_APP_NAME=$1
RESOURCE_GROUP=$2

if [ -z "$FUNCTION_APP_NAME" ] || [ -z "$RESOURCE_GROUP" ]; then
  echo "使用方法: $0 <function-app-name> <resource-group>"
  exit 1
fi

echo "環境変数を設定しています..."

az functionapp config appsettings set \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings \
    SUPABASE_URL="${SUPABASE_URL:-https://your-project.supabase.co}" \
    SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY:-your-anon-key}" \
    SUPABASE_SERVICE_ROLE_KEY="${SUPABASE_SERVICE_ROLE_KEY:-your-service-role-key}" \
    SUPABASE_STORAGE_BUCKET="${SUPABASE_STORAGE_BUCKET:-documents}" \
    DB_HOST="${DB_HOST:-db.your-project.supabase.co}" \
    DB_PORT="${DB_PORT:-5432}" \
    DB_NAME="${DB_NAME:-postgres}" \
    DB_USER="${DB_USER:-postgres}" \
    DB_PASSWORD="${DB_PASSWORD:-your-db-password}" \
    OPENAI_API_KEY="${OPENAI_API_KEY:-sk-your-openai-api-key}" \
    EMBEDDING_MODEL="${EMBEDDING_MODEL:-text-embedding-3-small}" \
    CHAT_MODEL="${CHAT_MODEL:-gpt-4o-mini}" \
    CHUNK_SIZE="${CHUNK_SIZE:-500}" \
    CHUNK_OVERLAP="${CHUNK_OVERLAP:-50}" \
    TOP_K="${TOP_K:-5}" \
    ADMIN_EMAILS="${ADMIN_EMAILS:-admin@example.com}" \
    LOG_LEVEL="${LOG_LEVEL:-INFO}" \
    ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-https://your-static-web-app.azurestaticapps.net}" \
    API_TIMEOUT="${API_TIMEOUT:-30}" \
    MAX_FILE_SIZE="${MAX_FILE_SIZE:-10485760}" \
    ENVIRONMENT="${ENVIRONMENT:-production}"

echo "環境変数の設定が完了しました。"

