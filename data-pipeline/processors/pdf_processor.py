"""
PDF 处理器
复用 backend-ai 的 PDF 处理逻辑
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional
from utils.logger import logger


class PDFProcessor:
    """
    PDF 文本提取器
    与 backend-ai/app/services/pdf_service.py 功能相同
    """
    
    def __init__(self):
        """初始化 PDF 处理器"""
        self.logger = logger
    
    def extract_text(self, pdf_path: str) -> str:
        """
        从 PDF 提取文本
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            提取的文本内容
        """
        try:
            doc = fitz.open(pdf_path)
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                if text.strip():
                    text_parts.append(text)
            
            doc.close()
            
            full_text = '\n\n'.join(text_parts)
            self.logger.info(f"Extracted {len(full_text)} characters from {Path(pdf_path).name}")
            
            return full_text
            
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise
    
    def extract_metadata(self, pdf_path: str) -> dict:
        """
        提取 PDF 元数据
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            元数据字典
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            page_count = len(doc)
            doc.close()
            
            return {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'page_count': page_count
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {pdf_path}: {e}")
            return {}
    
    def is_valid_pdf(self, pdf_path: str) -> bool:
        """
        检查是否为有效的 PDF 文件
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            是否有效
        """
        try:
            doc = fitz.open(pdf_path)
            is_valid = len(doc) > 0
            doc.close()
            return is_valid
        except:
            return False
    
    def extract_with_validation(self, pdf_path: str, min_length: int = 100) -> Optional[str]:
        """
        提取文本并验证
        
        Args:
            pdf_path: PDF 文件路径
            min_length: 最小文本长度
            
        Returns:
            提取的文本，如果不符合要求则返回 None
        """
        if not self.is_valid_pdf(pdf_path):
            self.logger.warning(f"Invalid PDF: {pdf_path}")
            return None
        
        text = self.extract_text(pdf_path)
        
        if len(text.strip()) < min_length:
            self.logger.warning(f"Extracted text too short ({len(text)} chars): {pdf_path}")
            return None
        
        return text

