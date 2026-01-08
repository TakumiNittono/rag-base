-- ============================================
-- RAG System 初期スキーマ（Lv2.5）
-- files + chunks + embeddings 3テーブル分離設計
-- ============================================

-- pgvector拡張を有効化
CREATE EXTENSION IF NOT EXISTS vector;

-- --------------------------------------------
-- filesテーブル: ファイルメタデータ
-- --------------------------------------------
CREATE TABLE files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_name TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  file_size BIGINT,
  mime_type TEXT,
  status TEXT NOT NULL DEFAULT 'uploaded',
  -- status: 'uploaded' | 'indexing' | 'indexed' | 'error'
  error_message TEXT,
  chunk_count INTEGER DEFAULT 0,
  embedding_count INTEGER DEFAULT 0,
  -- embedding_count: 実際にEmbeddingが生成されたチャンク数
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  CONSTRAINT status_check CHECK (status IN ('uploaded', 'indexing', 'indexed', 'error'))
);

-- --------------------------------------------
-- chunksテーブル: テキストチャンク（Embeddingは含まない）
-- --------------------------------------------
CREATE TABLE chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  -- chunk_index: ファイル内でのチャンクの順序（0始まり）
  token_count INTEGER,
  -- token_count: チャンクのトークン数（オプション、将来の最適化用）
  created_at TIMESTAMP DEFAULT now(),
  CONSTRAINT chunk_index_check CHECK (chunk_index >= 0)
);

-- --------------------------------------------
-- embeddingsテーブル: チャンクのベクトル表現
-- --------------------------------------------
CREATE TABLE embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  embedding VECTOR(1536) NOT NULL,
  -- 1536次元: text-embedding-3-small
  model_name TEXT NOT NULL DEFAULT 'text-embedding-3-small',
  -- model_name: Embeddingモデル名（将来のモデル変更に対応）
  created_at TIMESTAMP DEFAULT now(),
  CONSTRAINT unique_chunk_embedding UNIQUE (chunk_id, model_name)
  -- 1チャンクにつき1モデルで1つのEmbedding（将来のマルチモデル対応）
);

-- --------------------------------------------
-- インデックス作成
-- --------------------------------------------
-- filesテーブルのインデックス
CREATE INDEX idx_files_status ON files(status);
CREATE INDEX idx_files_created_at ON files(created_at DESC);

-- chunksテーブルのインデックス
CREATE INDEX idx_chunks_file_id ON chunks(file_id);
CREATE INDEX idx_chunks_file_id_index ON chunks(file_id, chunk_index);

-- embeddingsテーブルのインデックス
CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_model ON embeddings(model_name);
-- ベクトル検索用インデックス（ivfflat）
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- --------------------------------------------
-- コメント追加
-- --------------------------------------------
COMMENT ON TABLE files IS 'アップロードされたファイルのメタデータ';
COMMENT ON TABLE chunks IS 'ファイルを分割したテキストチャンク（Embeddingは別テーブル）';
COMMENT ON TABLE embeddings IS 'チャンクのベクトル表現（Embedding）';
COMMENT ON COLUMN files.status IS 'ファイルの処理ステータス: uploaded, indexing, indexed, error';
COMMENT ON COLUMN files.embedding_count IS '実際にEmbeddingが生成されたチャンク数';
COMMENT ON COLUMN chunks.chunk_index IS 'ファイル内でのチャンクの順序（0始まり）';
COMMENT ON COLUMN embeddings.model_name IS 'Embeddingモデル名（将来のモデル変更・比較に対応）';
COMMENT ON COLUMN embeddings.embedding IS 'ベクトル表現（1536次元、text-embedding-3-small）';

