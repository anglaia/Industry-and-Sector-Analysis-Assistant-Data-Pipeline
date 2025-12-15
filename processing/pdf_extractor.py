"""
PDF文本提取模块 - 从PDF文件中提取每一页的文本
"""
import logging
from pathlib import Path
from typing import List, Optional

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    try:
        from pypdf import PdfReader
        PYPDF_AVAILABLE = True
    except ImportError:
        PYPDF_AVAILABLE = False

from core.models import Document, Page

logger = logging.getLogger(__name__)


def extract_pages(document: Document) -> List[Page]:
    """
    从PDF文档中提取每一页的文本
    
    Args:
        document: Document对象，包含local_path等信息
        
    Returns:
        List[Page]: 包含所有页的Page对象列表
        
    Raises:
        ImportError: 如果没有安装pdfplumber或pypdf
        FileNotFoundError: 如果PDF文件不存在
        Exception: PDF解析过程中的其他错误
    """
    if not Path(document.local_path).exists():
        raise FileNotFoundError(f"PDF文件不存在: {document.local_path}")
    
    pages: List[Page] = []
    
    # 优先使用pdfplumber（更准确）
    if PDFPLUMBER_AVAILABLE:
        pages = _extract_with_pdfplumber(document)
    elif PYPDF_AVAILABLE:
        pages = _extract_with_pypdf(document)
    else:
        raise ImportError(
            "需要安装pdfplumber或pypdf库。"
            "运行: pip install pdfplumber 或 pip install pypdf"
        )
    
    # 更新Document的页数
    document.num_pages = len(pages)
    logger.info(f"成功提取 {document.file_id} 的 {len(pages)} 页")
    
    return pages


def _extract_with_pdfplumber(document: Document) -> List[Page]:
    """使用pdfplumber提取文本"""
    pages: List[Page] = []
    
    with pdfplumber.open(document.local_path) as pdf:
        for page_num, pdf_page in enumerate(pdf.pages, start=1):
            try:
                text = pdf_page.extract_text()
                if text is None:
                    text = ""
                
                page = Page(
                    file_id=document.file_id,
                    page_number=page_num,
                    raw_text=text.strip()
                )
                pages.append(page)
            except Exception as e:
                logger.warning(f"提取第 {page_num} 页时出错: {e}")
                # 即使出错也创建一个空页
                pages.append(Page(
                    file_id=document.file_id,
                    page_number=page_num,
                    raw_text=""
                ))
    
    return pages


def _extract_with_pypdf(document: Document) -> List[Page]:
    """使用pypdf提取文本（备用方案）"""
    pages: List[Page] = []
    
    reader = PdfReader(document.local_path)
    total_pages = len(reader.pages)
    
    for page_num in range(1, total_pages + 1):
        try:
            page_obj = reader.pages[page_num - 1]
            text = page_obj.extract_text()
            if text is None:
                text = ""
            
            page = Page(
                file_id=document.file_id,
                page_number=page_num,
                raw_text=text.strip()
            )
            pages.append(page)
        except Exception as e:
            logger.warning(f"提取第 {page_num} 页时出错: {e}")
            pages.append(Page(
                file_id=document.file_id,
                page_number=page_num,
                raw_text=""
            ))
    
    return pages

