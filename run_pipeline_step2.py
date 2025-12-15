"""
步骤2测试脚本 - 单文件PDF处理到本地JSONL
顺序：先将原始 PDF 上传到 S3（如果已配置），然后再进行：
PDF提取 -> 文本清洗 -> 切块 -> 元数据构建 -> 本地存储
仍不包含：向量生成、Pinecone写入
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.models import Document
from core.utils import generate_file_id
from processing.pdf_extractor import extract_pages
from processing.text_cleaner import clean_pages
from processing.chunker import chunk_pages
from io.local_store import save_chunks_to_jsonl
from ingestion.s3_uploader import upload_pdf_to_s3
from config.settings import LOG_FILE, LOG_LEVEL, S3_BUCKET_NAME

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def process_single_pdf(
    pdf_path: str,
    industry: str = "general",
    title: Optional[str] = None,
    year: Optional[str] = None,
    **kwargs
) -> None:
    """
    处理单个PDF文件（步骤2：到本地JSONL）
    
    Args:
        pdf_path: PDF文件路径
        industry: 行业分类
        title: 文档标题（可选）
        year: 发布年份（可选）
        **kwargs: 其他Document字段
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        logger.error(f"PDF文件不存在: {pdf_path}")
        return
    
    logger.info(f"开始处理PDF: {pdf_path}")
    
    # 1. 创建Document对象
    file_id = generate_file_id(str(pdf_path))
    document = Document(
        file_id=file_id,
        industry=industry,
        source_file=pdf_path.name,
        local_path=str(pdf_path),
        title=title,
        year=year,
        **kwargs
    )
    
    logger.info(f"文档信息: file_id={file_id}, industry={industry}")
    
    try:
        # 1.5 先上传到 S3（如果配置了 S3_BUCKET_NAME）
        if S3_BUCKET_NAME:
            logger.info("步骤1: 将原始 PDF 上传到 S3...")
            s3_url = upload_pdf_to_s3(document)
            if s3_url:
                logger.info(f"S3 URL: {s3_url}")
            else:
                logger.warning("PDF 上传到 S3 失败或已跳过，将继续使用本地文件进行处理。")
        else:
            logger.info("未配置 S3_BUCKET_NAME，跳过上传到 S3，直接使用本地 PDF 进行处理。")

        # 2. 提取PDF页面
        logger.info("步骤2: 提取PDF页面...")
        pages = extract_pages(document)
        if not pages:
            logger.warning(f"未能从PDF中提取任何页面: {pdf_path}")
            return
        
        # 3. 清洗文本
        logger.info("步骤3: 清洗文本...")
        cleaned_pages = clean_pages(pages)
        
        # 4. 切块
        logger.info("步骤4: 切分文本块...")
        chunks = chunk_pages(cleaned_pages, document)
        if not chunks:
            logger.warning(f"未能生成任何chunks: {pdf_path}")
            return
        
        # 5. 保存到本地JSONL
        logger.info("步骤5: 保存到本地JSONL...")
        output_file = save_chunks_to_jsonl(chunks, file_id)
        
        logger.info(f"✅ 处理完成！")
        logger.info(f"   - 总页数: {document.num_pages}")
        logger.info(f"   - 总chunks: {len(chunks)}")
        logger.info(f"   - 输出文件: {output_file}")
        
    except Exception as e:
        logger.error(f"处理PDF时出错: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # 示例用法
    if len(sys.argv) < 2:
        print("用法: python run_pipeline_step2.py <pdf_path> [industry] [title] [year]")
        print("\n示例:")
        print('  python run_pipeline_step2.py "data/report.pdf" "AI" "AI Report 2024" "2024"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    industry = sys.argv[2] if len(sys.argv) > 2 else "general"
    title = sys.argv[3] if len(sys.argv) > 3 else None
    year = sys.argv[4] if len(sys.argv) > 4 else None
    
    process_single_pdf(
        pdf_path=pdf_path,
        industry=industry,
        title=title,
        year=year
    )

