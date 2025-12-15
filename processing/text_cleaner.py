"""
文本清洗模块 - 删除广告、页眉页脚、联系方式等无关内容
"""
import re
import logging
from typing import List

from core.models import Page
from config.settings import (
    CLEAN_REMOVE_HEADERS,
    CLEAN_REMOVE_FOOTERS,
    CLEAN_REMOVE_ADS,
    CLEAN_REMOVE_CONTACTS
)

logger = logging.getLogger(__name__)


def clean_pages(pages: List[Page]) -> List[Page]:
    """
    清洗页面文本，移除广告、页眉页脚、联系方式等
    
    Args:
        pages: 原始Page对象列表
        
    Returns:
        List[Page]: 清洗后的Page对象列表（clean_text字段已填充）
    """
    cleaned_pages: List[Page] = []
    
    for page in pages:
        cleaned_text = page.raw_text
        
        # 应用各种清洗规则
        if CLEAN_REMOVE_HEADERS:
            cleaned_text = _remove_headers(cleaned_text, page)
        
        if CLEAN_REMOVE_FOOTERS:
            cleaned_text = _remove_footers(cleaned_text, page)
        
        if CLEAN_REMOVE_ADS:
            cleaned_text = _remove_ads(cleaned_text)
        
        if CLEAN_REMOVE_CONTACTS:
            cleaned_text = _remove_contacts(cleaned_text)
        
        # 清理多余空白
        cleaned_text = _normalize_whitespace(cleaned_text)
        
        # 创建新的Page对象，填充clean_text
        cleaned_page = Page(
            file_id=page.file_id,
            page_number=page.page_number,
            raw_text=page.raw_text,
            clean_text=cleaned_text
        )
        cleaned_pages.append(cleaned_page)
    
    logger.info(f"完成 {len(pages)} 页的文本清洗")
    return cleaned_pages


def _remove_headers(text: str, page: Page) -> str:
    """
    移除页眉
    策略：通常页眉在文本开头，包含文档标题、报告名称等
    """
    lines = text.split('\n')
    if len(lines) < 2:
        return text
    
    # 移除前1-2行（可能是页眉）
    # 如果前几行很短且包含常见页眉关键词，则移除
    header_keywords = ['报告', 'report', '年度', 'annual', '季度', 'quarter']
    cleaned_lines = []
    skip_header = True
    
    for i, line in enumerate(lines[:3]):  # 只检查前3行
        line_lower = line.lower().strip()
        if line_lower and len(line_lower) > 10:  # 如果行较长，可能不是页眉
            skip_header = False
            break
        if any(keyword in line_lower for keyword in header_keywords):
            continue  # 跳过包含页眉关键词的行
    
    if skip_header:
        cleaned_lines = lines[1:]  # 移除第一行
    else:
        cleaned_lines = lines
    
    return '\n'.join(cleaned_lines)


def _remove_footers(text: str, page: Page) -> str:
    """
    移除页脚
    策略：页脚通常在文本末尾，包含页码、版权信息等
    """
    lines = text.split('\n')
    if len(lines) < 2:
        return text
    
    # 移除最后1-2行（可能是页脚）
    footer_keywords = ['页', 'page', 'copyright', '版权所有', 'confidential']
    cleaned_lines = []
    skip_footer = True
    
    for line in lines[-3:]:  # 检查最后3行
        line_lower = line.lower().strip()
        # 如果行很短且只包含数字（可能是页码），或包含页脚关键词
        if line_lower and (line_lower.isdigit() or any(keyword in line_lower for keyword in footer_keywords)):
            continue
        if len(line_lower) > 10:  # 如果行较长，可能不是页脚
            skip_footer = False
            break
    
    if skip_footer:
        cleaned_lines = lines[:-1]  # 移除最后一行
    else:
        cleaned_lines = lines
    
    return '\n'.join(cleaned_lines)


def _remove_ads(text: str) -> str:
    """
    移除广告内容
    策略：识别常见的广告关键词和模式
    """
    # 广告关键词列表
    ad_keywords = [
        '广告', 'advertisement', 'ad', 'sponsored',
        '立即购买', 'buy now', 'click here', '了解更多'
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line_lower = line.lower().strip()
        # 如果行包含广告关键词，跳过
        if any(keyword in line_lower for keyword in ad_keywords):
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def _remove_contacts(text: str) -> str:
    """
    移除联系方式
    策略：识别邮箱、电话、网址等联系方式
    """
    # 邮箱模式
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # 电话模式（简化版）
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    # URL模式
    url_pattern = r'https?://[^\s]+|www\.[^\s]+'
    
    # 移除匹配的联系方式
    text = re.sub(email_pattern, '', text)
    text = re.sub(phone_pattern, '', text)
    text = re.sub(url_pattern, '', text)
    
    return text


def _normalize_whitespace(text: str) -> str:
    """
    规范化空白字符
    - 将多个连续空白字符（空格、制表符、换行）合并为单个空格或换行
    - 移除行首行尾空白
    """
    # 将多个连续空白字符替换为单个空格
    text = re.sub(r'[ \t]+', ' ', text)
    # 将多个连续换行替换为最多两个换行
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 移除行首行尾空白
    lines = [line.strip() for line in text.split('\n')]
    # 移除空行
    lines = [line for line in lines if line]
    
    return '\n'.join(lines)

