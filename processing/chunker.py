"""
文本切块模块 - 将清洗后的文本切分成chunks，支持跨页处理
"""
import logging
from typing import List, Tuple

from core.models import Page, Chunk, Document
from core.utils import generate_chunk_id
from config.settings import (
    CHUNK_MAX_CHARS,
    CHUNK_OVERLAP_CHARS,
    CHUNK_ALLOW_CROSS_PAGE
)

logger = logging.getLogger(__name__)


def chunk_pages(pages: List[Page], document: Document) -> List[Chunk]:
    """
    将页面文本切分成chunks
    
    Args:
        pages: 清洗后的Page对象列表
        document: Document对象，用于获取file_id、industry等信息
        
    Returns:
        List[Chunk]: Chunk对象列表，每个chunk包含文本、页码等信息
    """
    if not pages:
        logger.warning(f"文档 {document.file_id} 没有可切分的页面")
        return []
    
    chunks: List[Chunk] = []
    chunk_index = 0
    
    # 策略：先按页切分，然后合并小段
    # 这样可以更好地跟踪页码信息
    
    if CHUNK_ALLOW_CROSS_PAGE:
        # 允许跨页：将所有页的文本合并后切分
        chunks = _chunk_with_cross_page(pages, document, chunk_index)
    else:
        # 不允许跨页：每页独立切分
        chunks = _chunk_per_page(pages, document, chunk_index)
    
    logger.info(
        f"文档 {document.file_id} 切分成 {len(chunks)} 个chunks "
        f"(最大长度={CHUNK_MAX_CHARS}, 重叠={CHUNK_OVERLAP_CHARS})"
    )
    
    return chunks


def _chunk_with_cross_page(pages: List[Page], document: Document, start_index: int) -> List[Chunk]:
    """
    允许跨页的切分策略
    """
    chunks: List[Chunk] = []
    chunk_index = start_index
    
    # 第一步：将每页文本按段落/句子切分成小段
    page_segments: List[Tuple[str, int, int]] = []  # (text, page_start, page_end)
    
    for page in pages:
        if not page.clean_text or not page.clean_text.strip():
            continue
        
        # 按段落切分（双换行分隔）
        paragraphs = [p.strip() for p in page.clean_text.split('\n\n') if p.strip()]
        
        for para in paragraphs:
            # 如果段落太长，进一步按句子切分
            if len(para) > CHUNK_MAX_CHARS:
                sentences = _split_into_sentences(para)
                for sent in sentences:
                    if sent.strip():
                        page_segments.append((sent.strip(), page.page_number, page.page_number))
            else:
                page_segments.append((para, page.page_number, page.page_number))
    
    # 第二步：合并小段成chunks（考虑最大长度和重叠）
    current_chunk_text = ""
    current_page_start = None
    current_page_end = None
    
    for segment_text, seg_page_start, seg_page_end in page_segments:
        # 如果当前chunk为空，初始化
        if not current_chunk_text:
            current_chunk_text = segment_text
            current_page_start = seg_page_start
            current_page_end = seg_page_end
            continue
        
        # 尝试添加新段落到当前chunk
        potential_text = current_chunk_text + "\n\n" + segment_text
        
        if len(potential_text) <= CHUNK_MAX_CHARS:
            # 可以添加
            current_chunk_text = potential_text
            current_page_end = seg_page_end
        else:
            # 当前chunk已满，保存并开始新chunk
            chunk = _create_chunk(
                document=document,
                chunk_index=chunk_index,
                text=current_chunk_text,
                page_start=current_page_start,
                page_end=current_page_end
            )
            chunks.append(chunk)
            chunk_index += 1
            
            # 开始新chunk（考虑重叠）
            overlap_text = _get_overlap_text(current_chunk_text, CHUNK_OVERLAP_CHARS)
            current_chunk_text = overlap_text + "\n\n" + segment_text if overlap_text else segment_text
            current_page_start = seg_page_start
            current_page_end = seg_page_end
    
    # 保存最后一个chunk
    if current_chunk_text:
        chunk = _create_chunk(
            document=document,
            chunk_index=chunk_index,
            text=current_chunk_text,
            page_start=current_page_start,
            page_end=current_page_end
        )
        chunks.append(chunk)
    
    return chunks


def _chunk_per_page(pages: List[Page], document: Document, start_index: int) -> List[Chunk]:
    """
    不允许跨页的切分策略 - 每页独立切分
    """
    chunks: List[Chunk] = []
    chunk_index = start_index
    
    for page in pages:
        if not page.clean_text or not page.clean_text.strip():
            continue
        
        page_text = page.clean_text.strip()
        
        # 如果页面文本很短，直接作为一个chunk
        if len(page_text) <= CHUNK_MAX_CHARS:
            chunk = _create_chunk(
                document=document,
                chunk_index=chunk_index,
                text=page_text,
                page_start=page.page_number,
                page_end=page.page_number
            )
            chunks.append(chunk)
            chunk_index += 1
        else:
            # 页面文本较长，需要切分
            page_chunks = _split_long_text(
                text=page_text,
                document=document,
                page_number=page.page_number,
                start_index=chunk_index
            )
            chunks.extend(page_chunks)
            chunk_index += len(page_chunks)
    
    return chunks


def _split_long_text(text: str, document: Document, page_number: int, start_index: int) -> List[Chunk]:
    """
    将长文本切分成多个chunks（单页内）
    """
    chunks: List[Chunk] = []
    chunk_index = start_index
    
    # 按段落切分
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    current_chunk_text = ""
    
    for para in paragraphs:
        if not current_chunk_text:
            current_chunk_text = para
            continue
        
        potential_text = current_chunk_text + "\n\n" + para
        
        if len(potential_text) <= CHUNK_MAX_CHARS:
            current_chunk_text = potential_text
        else:
            # 保存当前chunk
            chunk = _create_chunk(
                document=document,
                chunk_index=chunk_index,
                text=current_chunk_text,
                page_start=page_number,
                page_end=page_number
            )
            chunks.append(chunk)
            chunk_index += 1
            
            # 开始新chunk（考虑重叠）
            overlap_text = _get_overlap_text(current_chunk_text, CHUNK_OVERLAP_CHARS)
            current_chunk_text = overlap_text + "\n\n" + para if overlap_text else para
    
    # 保存最后一个chunk
    if current_chunk_text:
        chunk = _create_chunk(
            document=document,
            chunk_index=chunk_index,
            text=current_chunk_text,
            page_start=page_number,
            page_end=page_number
        )
        chunks.append(chunk)
    
    return chunks


def _split_into_sentences(text: str) -> List[str]:
    """
    将文本按句子切分（简单实现）
    """
    # 简单的句子分隔符
    sentence_endings = r'[.!?。！？]\s+'
    import re
    sentences = re.split(sentence_endings, text)
    return [s.strip() for s in sentences if s.strip()]


def _get_overlap_text(text: str, overlap_chars: int) -> str:
    """
    获取文本末尾的overlap部分
    """
    if len(text) <= overlap_chars:
        return text
    
    # 从末尾取overlap_chars个字符
    overlap = text[-overlap_chars:]
    # 尝试在句子或单词边界截断
    # 简单实现：找到第一个空格或换行
    first_space = overlap.find('\n')
    if first_space == -1:
        first_space = overlap.find(' ')
    if first_space > 0:
        overlap = overlap[first_space + 1:]
    
    return overlap.strip()


def _create_chunk(
    document: Document,
    chunk_index: int,
    text: str,
    page_start: int,
    page_end: int
) -> Chunk:
    """
    创建Chunk对象
    """
    # 确定page_number（主要页码 = page_start）
    page_number = page_start
    
    # 生成chunk_id
    chunk_id = generate_chunk_id(document.file_id, chunk_index)
    
    chunk = Chunk(
        # 核心必需字段
        file_id=document.file_id,
        industry=document.industry,
        chunk_index=chunk_index,
        text=text,
        
        # 引用必需字段
        page_number=page_number,
        s3_url=document.s3_url,
        source_file=document.source_file,
        
        # 跨页字段
        page_start=page_start,
        page_end=page_end,
        
        # 推荐字段
        title=document.title,
        year=document.year,
        author=document.author,
        
        # 其他可选字段
        doc_id=document.doc_id,
        date=document.date,
        source=document.source,
        collection_date=document.collection_date,
        language=document.language,
        session_id=document.session_id,
        
        # 技术字段
        chunk_id=chunk_id
    )
    
    return chunk

