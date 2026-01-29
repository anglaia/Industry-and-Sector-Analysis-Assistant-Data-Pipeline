"""
批量处理管道脚本：
1）扫描指定目录下的所有 PDF 文件
2）对每个 PDF 文件执行端到端处理（上传 -> 提取 -> 清洗 -> 切块 -> 向量化 -> 存储）
3）默认行业设为 "education"
"""
import logging
import sys
import argparse
from pathlib import Path
from typing import Optional

# 导入单文件处理函数
from run_pipeline_full import process_single_pdf_end_to_end
from config.settings import LOG_FILE, LOG_LEVEL

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

def process_batch(
    input_dir: str,
    industry: str = "education",
    year: Optional[str] = None,
    max_files: Optional[int] = None,
) -> None:
    """
    批量处理指定目录下的所有 PDF 文件
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        logger.error("输入目录不存在: %s", input_path)
        return

    # 获取所有 PDF 文件
    pdf_files = list(input_path.glob("*.pdf"))

    # 如果设置了最大文件数，则裁剪列表
    if max_files is not None and max_files > 0:
        pdf_files = pdf_files[:max_files]
    
    if not pdf_files:
        logger.warning("在目录 %s 中未找到任何 PDF 文件", input_path)
        return

    logger.info("开始批量处理，共发现 %d 个 PDF 文件，默认行业: %s", len(pdf_files), industry)
    
    success_count = 0
    fail_count = 0

    for i, pdf_file in enumerate(pdf_files, 1):
        logger.info("-" * 50)
        logger.info("正在处理第 %d/%d 个文件: %s", i, len(pdf_files), pdf_file.name)
        
        try:
            # 默认使用文件名作为标题
            title = pdf_file.stem
            
            process_single_pdf_end_to_end(
                pdf_path=str(pdf_file),
                industry=industry,
                title=title,
                year=year
            )
            success_count += 1
            logger.info("成功处理文件: %s", pdf_file.name)
            
        except Exception as e:
            fail_count += 1
            logger.error("处理文件 %s 时发生错误: %s", pdf_file.name, e, exc_info=True)
            # 继续处理下一个文件
            continue

    logger.info("=" * 50)
    logger.info("批量处理完成！")
    logger.info("成功: %d", success_count)
    logger.info("失败: %d", fail_count)
    logger.info("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量处理 PDF 文件管道")
    parser.add_argument("--input_dir", type=str, default="data", help="包含 PDF 文件的输入目录 (默认: data)")
    parser.add_argument("--industry", type=str, default="education", help="文档所属行业 (默认: education)")
    parser.add_argument("--year", type=str, default=None, help="文档年份 (可选)")
    parser.add_argument("--max-files", type=int, default=None, help="最多处理的 PDF 文件数量 (默认: 不限制)")

    args = parser.parse_args()

    process_batch(
        input_dir=args.input_dir,
        industry=args.industry,
        year=args.year,
        max_files=args.max_files,
    )

