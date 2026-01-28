"""
本地 data/ -> Pinecone（跳过 S3 上传）

用途：
- 你已经把原始 PDF 传过 S3 了，这次只想用本地文件重新抽取/切块/embedding（3072）并 upsert 到新索引。

示例：
  # 扫描 data/ 下所有 pdf（递归），写入 Pinecone
  python run_local_data_to_pinecone.py --input-dir data --recursive

  # 只跑前 5 个文件做验证
  python run_local_data_to_pinecone.py --input-dir data --recursive --max-files 5

  # 如果你想在 metadata 里保留可引用的 s3_url（不上传，只拼接）
  python run_local_data_to_pinecone.py --input-dir data --recursive --s3-bucket your-bucket --s3-prefix documents/
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from core.models import Document, Chunk
from core.utils import generate_file_id
from processing.pdf_extractor import extract_pages
from processing.text_cleaner import clean_pages
from processing.chunker import chunk_pages
from processing.metadata_builder import build_metadata
from embedding.embedder import get_embeddings_for_chunks
from vector_store.pinecone_client import init_pinecone_index, build_pinecone_vectors, upsert_vectors
from config.settings import LOG_FILE, LOG_LEVEL


logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def _make_file_id(pdf_path: Path, input_dir: Path, strategy: str) -> str:
    if strategy == "path_hash":
        return generate_file_id(str(pdf_path))
    if strategy == "filename":
        return pdf_path.stem
    if strategy == "relative_path":
        rel = pdf_path.resolve().relative_to(input_dir.resolve())
        # 用 '_' 避免 pinecone id/metadata 里出现路径分隔符
        return str(rel).replace("/", "_").replace("\\", "_").rsplit(".", 1)[0]
    raise ValueError(f"未知 id-strategy: {strategy}")


def _maybe_build_s3_url(s3_bucket: Optional[str], s3_prefix: str, filename: str) -> Optional[str]:
    if not s3_bucket:
        return None
    prefix = (s3_prefix or "").lstrip("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    return f"https://{s3_bucket}.s3.amazonaws.com/{prefix}{filename}"


def process_single_pdf_local_to_pinecone(
    pdf_path: Path,
    *,
    input_dir: Path,
    id_strategy: str,
    industry: str,
    year: Optional[str],
    title_prefix: Optional[str],
    s3_bucket: Optional[str],
    s3_prefix: str,
    extra_doc_fields: Dict[str, Any],
) -> None:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    file_id = _make_file_id(pdf_path, input_dir, id_strategy)
    title = pdf_path.stem
    if title_prefix:
        title = f"{title_prefix} - {title}"

    # 注意：这里不会上传 S3；如果你想 citations 可用，可以通过 s3_bucket/s3_prefix 拼接一个 url 写进 metadata
    s3_url = _maybe_build_s3_url(s3_bucket, s3_prefix, pdf_path.name)

    document = Document(
        file_id=file_id,
        industry=industry,
        source_file=pdf_path.name,
        local_path=str(pdf_path),
        title=title,
        year=year,
        s3_url=s3_url,
        **extra_doc_fields,
    )

    logger.info("开始处理: %s (file_id=%s)", pdf_path.name, file_id)

    # 1) PDF -> pages
    pages = extract_pages(document)
    if not pages:
        logger.warning("未能从 PDF 中提取任何页面: %s", pdf_path)
        return

    # 2) clean
    cleaned_pages = clean_pages(pages)

    # 3) chunk
    chunks: list[Chunk] = chunk_pages(cleaned_pages, document)
    if not chunks:
        logger.warning("未能生成任何 chunks: %s", pdf_path)
        return

    # 4) metadata（id -> metadata）
    chunks_metadata: Dict[str, Dict[str, Any]] = {}
    for chunk in chunks:
        chunk_id = chunk.chunk_id or f"{chunk.file_id}_chunk_{chunk.chunk_index}"
        chunks_metadata[chunk_id] = build_metadata(chunk)

    # 5) embedding
    embedding_records = get_embeddings_for_chunks(chunks)
    if not embedding_records:
        logger.warning("未生成任何向量，跳过写入: %s", pdf_path)
        return

    # 6) upsert
    index = init_pinecone_index()
    vectors = build_pinecone_vectors(embedding_records, chunks_metadata)
    upsert_vectors(index, vectors)

    logger.info("✅ 完成: %s (chunks=%d, vectors=%d)", pdf_path.name, len(chunks), len(vectors))


def main() -> int:
    parser = argparse.ArgumentParser(description="本地 data/ -> Pinecone（跳过 S3 上传）")
    parser.add_argument("--input-dir", type=str, default="data", help="包含 PDF 的目录（默认 data）")
    parser.add_argument("--recursive", action="store_true", help="递归扫描子目录")
    parser.add_argument("--max-files", type=int, default=None, help="最多处理多少个文件（用于测试）")
    parser.add_argument("--industry", type=str, default="education", help="行业标签（默认 education）")
    parser.add_argument("--year", type=str, default=None, help="年份（可选）")
    parser.add_argument("--title-prefix", type=str, default=None, help="标题前缀（可选）")
    parser.add_argument(
        "--id-strategy",
        type=str,
        default="path_hash",
        choices=["path_hash", "filename", "relative_path"],
        help="file_id 生成策略：path_hash(默认)/filename/relative_path",
    )
    parser.add_argument("--s3-bucket", type=str, default=None, help="不上传，仅用于拼接 metadata 里的 s3_url（可选）")
    parser.add_argument("--s3-prefix", type=str, default="", help="不上传，仅用于拼接 s3_url 的前缀（可选）")

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        logger.error("输入目录不存在或不是目录: %s", input_dir)
        return 1

    pdf_files = list(input_dir.rglob("*.pdf")) if args.recursive else list(input_dir.glob("*.pdf"))
    pdf_files = sorted({p.resolve() for p in pdf_files})

    if not pdf_files:
        logger.warning("未找到任何 PDF: %s", input_dir)
        return 0

    if args.max_files:
        pdf_files = pdf_files[: args.max_files]

    logger.info("将处理 %d 个 PDF，写入 Pinecone。", len(pdf_files))

    # 预留：如果你想补充 Document 其它字段，可以在这里统一注入
    extra_doc_fields: Dict[str, Any] = {}

    success = 0
    failed = 0
    for i, pdf_path in enumerate(pdf_files, 1):
        logger.info("-" * 60)
        logger.info("[%d/%d] %s", i, len(pdf_files), pdf_path.name)
        try:
            process_single_pdf_local_to_pinecone(
                pdf_path,
                input_dir=input_dir,
                id_strategy=args.id_strategy,
                industry=args.industry,
                year=args.year,
                title_prefix=args.title_prefix,
                s3_bucket=args.s3_bucket,
                s3_prefix=args.s3_prefix,
                extra_doc_fields=extra_doc_fields,
            )
            success += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            logger.error("处理失败: %s (%s)", pdf_path, exc, exc_info=True)

    logger.info("=" * 60)
    logger.info("完成：成功 %d，失败 %d", success, failed)
    logger.info("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

