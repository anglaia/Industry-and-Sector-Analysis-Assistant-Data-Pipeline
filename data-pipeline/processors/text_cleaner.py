"""
文本清洗器
清理和标准化文本内容
"""
import re
from typing import Optional
from utils.logger import logger


class TextCleaner:
    """文本清洗和标准化"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符（保留基本标点）
        text = re.sub(r'[^\w\s\.,;:!?\'"-]', '', text)
        
        # 移除多余的换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 去除首尾空白
        text = text.strip()
        
        return text
    
    @staticmethod
    def remove_urls(text: str) -> str:
        """移除 URL"""
        return re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    @staticmethod
    def remove_emails(text: str) -> str:
        """移除邮箱地址"""
        return re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """标准化空白字符"""
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        
        # 移除空行
        lines = [line for line in lines if line]
        
        return '\n\n'.join(lines)
    
    @staticmethod
    def remove_page_numbers(text: str) -> str:
        """移除页码"""
        # 移除单独一行的数字（可能是页码）
        text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
        return text
    
    @staticmethod
    def remove_headers_footers(text: str) -> str:
        """
        尝试移除页眉页脚
        
        注意：这是一个启发式方法，可能不完全准确
        """
        lines = text.split('\n')
        
        if len(lines) < 10:
            return text
        
        # 检查是否有重复出现的行（可能是页眉页脚）
        from collections import Counter
        line_counts = Counter(lines)
        
        # 移除出现次数过多的短行
        cleaned_lines = []
        for line in lines:
            if len(line) < 50 and line_counts[line] > 3:
                continue  # 跳过可能的页眉页脚
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def clean_pdf_text(text: str) -> str:
        """
        专门用于清理 PDF 提取的文本
        
        Args:
            text: PDF 提取的原始文本
            
        Returns:
            清理后的文本
        """
        # 移除 URL 和邮箱
        text = TextCleaner.remove_urls(text)
        text = TextCleaner.remove_emails(text)
        
        # 移除页码
        text = TextCleaner.remove_page_numbers(text)
        
        # 标准化空白
        text = TextCleaner.normalize_whitespace(text)
        
        # 基础清理
        text = TextCleaner.clean_text(text)
        
        return text
    
    @staticmethod
    def extract_sentences(text: str) -> list:
        """
        将文本分割成句子
        
        Args:
            text: 文本
            
        Returns:
            句子列表
        """
        # 简单的句子分割（基于标点符号）
        sentences = re.split(r'[.!?]+', text)
        
        # 清理和过滤
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 10000) -> str:
        """
        截断文本到指定长度
        
        Args:
            text: 文本
            max_length: 最大长度
            
        Returns:
            截断后的文本
        """
        if len(text) <= max_length:
            return text
        
        # 尝试在句子边界截断
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period > max_length * 0.8:  # 如果找到的句号位置较靠后
            return truncated[:last_period + 1]
        
        return truncated + '...'

