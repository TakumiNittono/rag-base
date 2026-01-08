"""
RAG Service（Lv2.5: 3テーブル分離設計）
======================================
RAG処理のビジネスロジックを提供します。
- ファイル取り込み（テキスト抽出、チャンキング、Embedding生成）
- ベクトル検索
- LLM回答生成
"""

import mimetypes
from pathlib import Path
from typing import Optional

import pdfplumber
from llama_index.core import Document, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from openai import OpenAI as OpenAIClient

from app.config import get_settings
from app.core.exceptions import (
    EmbeddingError,
    ExtractionError,
    InvalidFileTypeError,
    LLMError,
    NoResultsError,
)
from app.core.logging import get_logger
from app.models.chunk import ChunkCreate, ChunkWithSimilarity
from app.models.embedding import EmbeddingCreate
from app.models.file import FileStatus
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.services.file_service import FileService

logger = get_logger(__name__)
settings = get_settings()

# LlamaIndex設定
Settings.embed_model = OpenAIEmbedding(
    model=settings.embedding_model,
    api_key=settings.openai_api_key,
)
Settings.llm = OpenAI(
    model=settings.chat_model,
    api_key=settings.openai_api_key,
    temperature=0.7,
    max_tokens=1000,
)

# OpenAIクライアント（Embedding生成用）
_openai_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """OpenAIクライアントを取得（シングルトン）"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient(api_key=settings.openai_api_key)
    return _openai_client


class RAGService:
    """RAG Service（Lv2.5: 3テーブル分離設計）"""

    def __init__(self):
        self.file_service = FileService()
        self.chunk_repo = ChunkRepository()
        self.embedding_repo = EmbeddingRepository()
        self.chunker = SentenceSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separator="\n\n",
        )

    async def ingest_file(
        self,
        file_content: bytes,
        file_name: str,
        file_id: str,
    ) -> tuple[int, int]:
        """
        ファイルを取り込み（Lv2.5: chunksとembeddingsを分離して保存）

        Args:
            file_content: ファイル内容（バイト）
            file_name: ファイル名
            file_id: ファイルID（UUID文字列）

        Returns:
            tuple[int, int]: (チャンク数, Embedding数)

        Raises:
            InvalidFileTypeError: 未対応のファイル形式
            ExtractionError: テキスト抽出失敗
            EmbeddingError: Embedding生成失敗
        """
        from uuid import UUID

        file_uuid = UUID(file_id)

        try:
            # 1. ファイルステータスを'indexing'に更新
            await self.file_service.update_file_status(
                file_uuid,
                status=FileStatus.INDEXING,
            )

            # 2. テキスト抽出
            text = self._extract_text(file_content, file_name)

            if not text or not text.strip():
                raise ExtractionError("テキストが抽出できませんでした")

            # 3. チャンキング
            documents = [Document(text=text)]
            nodes = self.chunker.get_nodes_from_documents(documents)

            if not nodes:
                raise ExtractionError("チャンクが生成できませんでした")

            # 4. chunksテーブルに保存
            chunks_data = [
                ChunkCreate(
                    file_id=file_uuid,
                    content=node.text,
                    chunk_index=i,
                    token_count=None,  # 将来実装
                )
                for i, node in enumerate(nodes)
            ]

            chunks = await self.chunk_repo.create_batch(chunks_data)
            chunk_count = len(chunks)

            logger.info(f"チャンク作成成功: {chunk_count}個 (file_id: {file_id})")

            # 5. Embedding生成（バッチ処理）
            embeddings_data = []
            for chunk in chunks:
                try:
                    embedding = await self._generate_embedding(chunk.content)
                    embeddings_data.append(
                        EmbeddingCreate(
                            chunk_id=chunk.id,
                            embedding=embedding,
                            model_name=settings.embedding_model,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Embedding生成失敗（チャンク {chunk.id}）: {str(e)}")
                    # 個別のEmbedding生成失敗は警告のみ（他のチャンクは続行）

            # 6. embeddingsテーブルに保存
            if embeddings_data:
                embeddings = await self.embedding_repo.create_batch(embeddings_data)
                embedding_count = len(embeddings)
            else:
                embedding_count = 0

            logger.info(f"Embedding作成成功: {embedding_count}個 (file_id: {file_id})")

            # 7. ファイルステータスを'indexed'に更新
            await self.file_service.update_file_counts(
                file_uuid,
                chunk_count=chunk_count,
                embedding_count=embedding_count,
            )
            await self.file_service.update_file_status(
                file_uuid,
                status=FileStatus.INDEXED,
            )

            return chunk_count, embedding_count

        except (InvalidFileTypeError, ExtractionError, EmbeddingError) as e:
            # エラー時はステータスを'error'に更新
            try:
                await self.file_service.update_file_status(
                    file_uuid,
                    status=FileStatus.ERROR,
                    error_message=str(e),
                )
            except Exception:
                pass
            raise
        except Exception as e:
            logger.error(f"ファイル取り込みエラー: {str(e)}")
            # 予期しないエラー
            try:
                await self.file_service.update_file_status(
                    file_uuid,
                    status=FileStatus.ERROR,
                    error_message=f"予期しないエラー: {str(e)}",
                )
            except Exception:
                pass
            raise ExtractionError(f"ファイル取り込みに失敗しました: {str(e)}") from e

    def _extract_text(self, file_content: bytes, file_name: str) -> str:
        """
        ファイルからテキストを抽出

        Args:
            file_content: ファイル内容（バイト）
            file_name: ファイル名

        Returns:
            str: 抽出されたテキスト

        Raises:
            InvalidFileTypeError: 未対応のファイル形式
            ExtractionError: テキスト抽出失敗
        """
        # ファイル拡張子を取得
        file_ext = Path(file_name).suffix.lower()

        # ファイル形式に応じてテキスト抽出
        if file_ext == ".txt":
            return self._extract_text_txt(file_content)
        elif file_ext == ".md":
            return self._extract_text_txt(file_content)  # MarkdownもUTF-8テキストとして扱う
        elif file_ext == ".pdf":
            return self._extract_text_pdf(file_content)
        else:
            raise InvalidFileTypeError(
                file_type=file_ext,
                allowed_types=[".txt", ".md", ".pdf"],
            )

    def _extract_text_txt(self, file_content: bytes) -> str:
        """テキストファイルからテキストを抽出"""
        try:
            # UTF-8でデコードを試行
            return file_content.decode("utf-8")
        except UnicodeDecodeError:
            # Shift-JISでデコードを試行
            try:
                return file_content.decode("shift-jis")
            except UnicodeDecodeError:
                # EUC-JPでデコードを試行
                try:
                    return file_content.decode("euc-jp")
                except UnicodeDecodeError:
                    raise ExtractionError("テキストファイルのエンコーディングが判別できませんでした")

    def _extract_text_pdf(self, file_content: bytes) -> str:
        """PDFファイルからテキストを抽出"""
        try:
            import io

            pdf_file = io.BytesIO(file_content)
            text_parts = []

            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            if not text_parts:
                raise ExtractionError("PDFからテキストが抽出できませんでした（画像のみの可能性があります）")

            return "\n\n".join(text_parts)

        except Exception as e:
            raise ExtractionError(f"PDFテキスト抽出に失敗しました: {str(e)}") from e

    async def _generate_embedding(self, text: str) -> list[float]:
        """
        Embeddingを生成

        Args:
            text: テキスト

        Returns:
            list[float]: Embeddingベクトル（1536次元）

        Raises:
            EmbeddingError: Embedding生成失敗
        """
        try:
            client = get_openai_client()
            response = client.embeddings.create(
                model=settings.embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            raise EmbeddingError(f"Embedding生成に失敗しました: {str(e)}") from e

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ) -> list[ChunkWithSimilarity]:
        """
        ベクトル類似検索を実行（Lv2.5: embeddingsテーブルで検索）

        Args:
            query: 質問文
            top_k: 取得するチャンク数（デフォルト: 設定値）
            similarity_threshold: 類似度閾値（オプション）

        Returns:
            list[ChunkWithSimilarity]: 類似度順にソートされたチャンク一覧

        Raises:
            EmbeddingError: 質問のEmbedding生成失敗
            NoResultsError: 検索結果が0件
        """
        top_k = top_k or settings.top_k

        try:
            # 1. 質問文のEmbedding生成
            query_embedding = await self._generate_embedding(query)

            # 2. ベクトル類似検索（embeddingsテーブルで検索）
            results = await self.embedding_repo.search_similar(
                query_embedding=query_embedding,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )

            if not results:
                raise NoResultsError("検索結果が見つかりませんでした")

            logger.info(f"ベクトル検索成功: {len(results)}件")

            return results

        except NoResultsError:
            raise
        except Exception as e:
            logger.error(f"ベクトル検索エラー: {str(e)}")
            raise EmbeddingError(f"ベクトル検索に失敗しました: {str(e)}") from e

    async def generate_answer(
        self,
        query: str,
        contexts: list[ChunkWithSimilarity],
    ) -> str:
        """
        LLMで回答を生成

        Args:
            query: 質問文
            contexts: 検索結果（コンテキスト）

        Returns:
            str: 生成された回答

        Raises:
            LLMError: LLM呼び出し失敗
        """
        try:
            # プロンプト構築
            context_text = "\n\n".join(
                [f"[{i+1}] {ctx.content}" for i, ctx in enumerate(contexts)]
            )

            prompt = f"""以下のコンテキスト情報を基に、ユーザーの質問に回答してください。

コンテキスト:
{context_text}

質問: {query}

回答:"""

            # LLM呼び出し
            llm = Settings.llm
            response = await llm.acomplete(prompt)

            answer = str(response).strip()

            logger.info(f"LLM回答生成成功: {len(answer)}文字")

            return answer

        except Exception as e:
            logger.error(f"LLM回答生成エラー: {str(e)}")
            raise LLMError(f"LLM回答生成に失敗しました: {str(e)}") from e

