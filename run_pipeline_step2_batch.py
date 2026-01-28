"""
批量处理脚本 - 步骤2（不上传到Pinecone）
批量处理多个PDF文件：上传到S3 -> 提取 -> 清洗 -> 切块 -> 保存到本地JSONL
不上传到Pinecone向量数据库
"""
import logging
import sys
import argparse
from pathlib import Path
from typing import Optional, List

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.models import Document
from core.utils import generate_file_id
from processing.pdf_extractor import extract_pages
from processing.text_cleaner import clean_pages
from processing.chunker import chunk_pages
from data_io.local_store import save_chunks_to_jsonl
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
) -> bool:
    """
    处理单个PDF文件（步骤2：到本地JSONL，不上传到Pinecone）
    
    Args:
        pdf_path: PDF文件路径
        industry: 行业分类
        title: 文档标题（可选）
        year: 发布年份（可选）
        **kwargs: 其他Document字段
    
    Returns:
        bool: 处理是否成功
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        logger.error(f"PDF文件不存在: {pdf_path}")
        return False
    
    logger.info(f"开始处理PDF: {pdf_path}")
    
    # 1. 创建Document对象
    file_id = generate_file_id(str(pdf_path))
    document = Document(
        file_id=file_id,
        industry=industry,
        source_file=pdf_path.name,
        local_path=str(pdf_path),
        title=title or pdf_path.stem,
        year=year,
        **kwargs
    )
    
    logger.info(f"文档信息: file_id={file_id}, industry={industry}, title={document.title}")
    
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
            return False
        
        # 3. 清洗文本
        logger.info("步骤3: 清洗文本...")
        cleaned_pages = clean_pages(pages)
        
        # 4. 切块
        logger.info("步骤4: 切分文本块...")
        chunks = chunk_pages(cleaned_pages, document)
        if not chunks:
            logger.warning(f"未能生成任何chunks: {pdf_path}")
            return False
        
        # 5. 保存到本地JSONL
        logger.info("步骤5: 保存到本地JSONL...")
        output_file = save_chunks_to_jsonl(chunks, file_id)
        
        logger.info(f"✅ 处理完成！")
        logger.info(f"   - 总页数: {document.num_pages}")
        logger.info(f"   - 总chunks: {len(chunks)}")
        logger.info(f"   - 输出文件: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"处理PDF时出错: {e}", exc_info=True)
        return False


def process_batch(
    input_paths: List[str],
    industry: str = "general",
    year: Optional[str] = None,
    title_prefix: Optional[str] = None
) -> None:
    """
    批量处理PDF文件
    
    Args:
        input_paths: PDF文件路径列表（可以是文件或目录）
        industry: 默认行业分类
        year: 默认年份
        title_prefix: 标题前缀（可选）
    """
    pdf_files = []
    
    # 收集所有PDF文件
    for input_path in input_paths:
        path = Path(input_path)
        if not path.exists():
            logger.warning(f"路径不存在，跳过: {path}")
            continue
        
        if path.is_file() and path.suffix.lower() == '.pdf':
            pdf_files.append(path)
        elif path.is_dir():
            # 递归查找所有PDF文件
            found_pdfs = list(path.rglob("*.pdf"))
            pdf_files.extend(found_pdfs)
            logger.info(f"在目录 {path} 中找到 {len(found_pdfs)} 个PDF文件")
        else:
            logger.warning(f"不是有效的PDF文件或目录，跳过: {path}")
    
    if not pdf_files:
        logger.error("未找到任何PDF文件")
        return
    
    # 去重
    pdf_files = list(set(pdf_files))
    pdf_files.sort()
    
    logger.info("=" * 60)
    logger.info(f"开始批量处理，共 {len(pdf_files)} 个PDF文件")
    logger.info(f"默认行业: {industry}")
    if year:
        logger.info(f"默认年份: {year}")
    logger.info("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        logger.info("-" * 60)
        logger.info(f"正在处理第 {i}/{len(pdf_files)} 个文件: {pdf_file.name}")
        
        # 生成标题
        title = pdf_file.stem
        if title_prefix:
            title = f"{title_prefix} - {title}"
        
        success = process_single_pdf(
            pdf_path=str(pdf_file),
            industry=industry,
            title=title,
            year=year
        )
        
        if success:
            success_count += 1
            logger.info(f"✅ 成功处理: {pdf_file.name}")
        else:
            fail_count += 1
            logger.error(f"❌ 处理失败: {pdf_file.name}")
    
    logger.info("=" * 60)
    logger.info("批量处理完成！")
    logger.info(f"成功: {success_count}/{len(pdf_files)}")
    logger.info(f"失败: {fail_count}/{len(pdf_files)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="批量处理PDF文件（步骤2：不上传到Pinecone）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 处理单个文件
  python run_pipeline_step2_batch.py "data/report.pdf" --industry "AI" --title "AI Report 2024" --year "2024"
  
  # 处理目录下所有PDF
  python run_pipeline_step2_batch.py data/ --industry "AI" --year "2024"
  
  # 处理多个文件/目录
  python run_pipeline_step2_batch.py "data/file1.pdf" "data/file2.pdf" "data/subdir/" --industry "AI"
        """
    )
    
    parser.add_argument(
        "input_paths",
        nargs="+",
        help="PDF文件路径或包含PDF文件的目录（可指定多个）"
    )
    parser.add_argument(
        "--industry",
        type=str,
        default="general",
        help="文档所属行业 (默认: general)"
    )
    parser.add_argument(
        "--year",
        type=str,
        default=None,
        help="文档年份 (可选)"
    )
    parser.add_argument(
        "--title-prefix",
        type=str,
        default=None,
        help="标题前缀 (可选，会添加到文件名前)"
    )
    
    args = parser.parse_args()
    
    process_batch(
        input_paths=args.input_paths,
        industry=args.industry,
        year=args.year,
        title_prefix=args.title_prefix
    )
