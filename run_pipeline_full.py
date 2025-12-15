"""
完整管道脚本 - 单文件端到端：
1）上传 PDF 到 S3
2）PDF 提取 + 清洗 + 切块
3）生成向量（Gemini）
4）写入 Pinecone
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from core.models import Document, Chunk
from core.utils import generate_file_id
from processing.pdf_extractor import extract_pages
from processing.text_cleaner import clean_pages
from processing.chunker import chunk_pages
from processing.metadata_builder import build_metadata
from ingestion.s3_uploader import upload_pdf_to_s3
from embedding.embedder import get_embeddings_for_chunks
from vector_store.pinecone_client import (
    init_pinecone_index,
    build_pinecone_vectors,
    upsert_vectors,
)
from config.settings import LOG_FILE, LOG_LEVEL, S3_BUCKET_NAME

# 日志配置
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def process_single_pdf_end_to_end(
    pdf_path: str,
    industry: str = "general",
    title: Optional[str] = None,
    year: Optional[str] = None,
    **kwargs: Dict[str, Any],
) -> None:
    """
    单文件端到端处理：PDF -> S3 -> chunks -> embeddings -> Pinecone
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        logger.error("PDF 文件不存在: %s", pdf_path)
        return

    logger.info("开始端到端处理 PDF: %s", pdf_path)

    # 1. 创建 Document
    file_id = generate_file_id(str(pdf_path))
    document = Document(
        file_id=file_id,
        industry=industry,
        source_file=pdf_path.name,
        local_path=str(pdf_path),
        title=title,
        year=year,
        **kwargs,
    )

    logger.info("文档信息: file_id=%s, industry=%s", file_id, industry)

    try:
        # 2. 先上传 S3
        if S3_BUCKET_NAME:
            logger.info("步骤1: 上传 PDF 到 S3...")
            s3_url = upload_pdf_to_s3(document)
            if s3_url:
                logger.info("S3 URL: %s", s3_url)
            else:
                logger.warning("上传到 S3 失败或跳过，将继续本地处理。")
        else:
            logger.info("未配置 S3_BUCKET_NAME，跳过上传到 S3。")

        # 3. PDF -> Pages
        logger.info("步骤2: 提取 PDF 页面...")
        pages = extract_pages(document)
        if not pages:
            logger.warning("未能从 PDF 中提取任何页面: %s", pdf_path)
            return

        # 4. 清洗
        logger.info("步骤3: 清洗文本...")
        cleaned_pages = clean_pages(pages)

        # 5. 切块
        logger.info("步骤4: 切分文本块...")
        chunks: list[Chunk] = chunk_pages(cleaned_pages, document)
        if not chunks:
            logger.warning("未能生成任何 chunks: %s", pdf_path)
            return

        # 6. 生成 metadata（先构建一个 id -> metadata 映射）
        logger.info("步骤5: 构建 metadata...")
        chunks_metadata: Dict[str, Dict[str, Any]] = {}
        for chunk in chunks:
            chunk_id = chunk.chunk_id or f"{chunk.file_id}_chunk_{chunk.chunk_index}"
            meta = build_metadata(chunk)
            chunks_metadata[chunk_id] = meta

        # 7. 生成向量
        logger.info("步骤6: 生成向量（Embedding）...")
        embedding_records = get_embeddings_for_chunks(chunks)
        if not embedding_records:
            logger.warning("未生成任何向量，流程结束。")
            return

        # 将 metadata 填入 EmbeddingRecord（便于调试）
        for rec in embedding_records:
            if rec.id in chunks_metadata:
                rec.metadata = chunks_metadata[rec.id]

        # 8. 初始化 Pinecone 并写入
        logger.info("步骤7: 初始化 Pinecone 索引...")
        index = init_pinecone_index()

        logger.info("步骤8: 准备 Pinecone 向量 payload...")
        vectors = build_pinecone_vectors(embedding_records, chunks_metadata)

        logger.info("步骤9: 向 Pinecone 写入向量...")
        upsert_vectors(index, vectors)

        logger.info("✅ 端到端处理完成！")
        logger.info("   - 总页数: %s", document.num_pages)
        logger.info("   - 总 chunks: %d", len(chunks))
        logger.info("   - 总向量: %d", len(vectors))

    except Exception as exc:  # noqa: BLE001
        logger.error("端到端处理 PDF 时出错: %s", exc, exc_info=True)
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python run_pipeline_full.py <pdf_path> [industry] [title] [year]")
        print("\n示例:")
        print('  python run_pipeline_full.py "data/report.pdf" "AI" "AI Report 2024" "2024"')
        sys.exit(1)

    pdf_path = sys.argv[1]
    industry = sys.argv[2] if len(sys.argv) > 2 else "general"
    title = sys.argv[3] if len(sys.argv) > 3 else None
    year = sys.argv[4] if len(sys.argv) > 4 else None

    process_single_pdf_end_to_end(
        pdf_path=pdf_path,
        industry=industry,
        title=title,
        year=year,
    )


