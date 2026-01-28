"""
批量处理器
协调 PDF 处理、文本清洗和数据摄取
"""
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
from processors.pdf_processor import PDFProcessor
from processors.text_cleaner import TextCleaner
from processors.metadata_extractor import MetadataExtractor
from ingest.pinecone_ingester import PineconeIngester
from utils.logger import logger
from utils.file_utils import FileUtils
from config.settings import settings


class BatchProcessor:
    """
    批量文档处理器
    
    工作流程：
    1. 扫描目录获取 PDF 文件
    2. 提取文本
    3. 清洗文本
    4. 提取元数据
    5. 摄取到 Pinecone
    """
    
    def __init__(self):
        """初始化批量处理器"""
        self.pdf_processor = PDFProcessor()
        self.text_cleaner = TextCleaner()
        self.metadata_extractor = MetadataExtractor()
        self.ingester = PineconeIngester()
        self.logger = logger
        
        self.logger.info("BatchProcessor initialized")
    
    def process_directory(
        self,
        directory: Path,
        industry: str,
        recursive: bool = True,
        pattern: str = "*.pdf"
    ) -> Dict:
        """
        处理目录中的所有文件
        
        Args:
            directory: 目录路径
            industry: 行业分类
            recursive: 是否递归处理子目录
            pattern: 文件匹配模式
            
        Returns:
            处理结果统计
        """
        if not directory.exists():
            self.logger.error(f"Directory does not exist: {directory}")
            return {'error': 'Directory not found'}
        
        # 查找文件
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        
        self.logger.info(f"Found {len(files)} files in {directory}")
        
        if not files:
            return {'total': 0, 'message': 'No files found'}
        
        # 处理文件
        documents = []
        
        for file_path in tqdm(files, desc="Processing files"):
            try:
                doc_data = self.process_single_file(file_path, industry)
                if doc_data:
                    documents.append(doc_data)
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
        
        # 批量摄取
        if documents:
            result = self.ingester.ingest_batch(documents)
            return result
        else:
            return {'total': 0, 'message': 'No documents processed successfully'}
    
    def process_single_file(
        self,
        file_path: Path,
        industry: Optional[str] = None,
        additional_metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            industry: 行业分类（如果未提供，尝试自动推断）
            additional_metadata: 额外的元数据
            
        Returns:
            处理后的文档数据，失败返回 None
        """
        self.logger.info(f"Processing file: {file_path.name}")
        
        # 1. 验证文件
        if not self.pdf_processor.is_valid_pdf(str(file_path)):
            self.logger.warning(f"Invalid PDF file: {file_path}")
            return None
        
        # 检查文件大小
        file_size_mb = FileUtils.get_file_size_mb(file_path)
        if file_size_mb > settings.max_file_size_mb:
            self.logger.warning(f"File too large ({file_size_mb:.2f} MB): {file_path}")
            return None
        
        # 2. 提取文本
        try:
            raw_text = self.pdf_processor.extract_text(str(file_path))
        except Exception as e:
            self.logger.error(f"Failed to extract text from {file_path}: {e}")
            return None
        
        # 验证文本长度
        if len(raw_text.strip()) < 100:
            self.logger.warning(f"Extracted text too short: {file_path}")
            return None
        
        # 3. 清洗文本
        cleaned_text = self.text_cleaner.clean_pdf_text(raw_text)
        
        # 4. 提取元数据
        metadata = self.metadata_extractor.build_metadata(
            file_path=file_path,
            text=cleaned_text[:5000],  # 只用前5000字符
            additional_metadata=additional_metadata
        )
        
        # 5. 确定行业
        if not industry:
            # 尝试从元数据推断
            industry = metadata.get('industry', 'Unknown')
        
        # 6. 生成文件 ID
        file_id = file_path.stem  # 使用文件名（不含扩展名）
        
        # 7. 准备返回数据
        doc_data = {
            'text': cleaned_text,
            'file_id': file_id,
            'industry': industry,
            'metadata': metadata
        }
        
        self.logger.info(f"✅ Processed {file_path.name}: {len(cleaned_text)} chars, industry={industry}")
        return doc_data
    
    def process_file_list(
        self,
        file_paths: List[Path],
        industry: str
    ) -> Dict:
        """
        处理文件列表
        
        Args:
            file_paths: 文件路径列表
            industry: 行业分类
            
        Returns:
            处理结果统计
        """
        documents = []
        
        for file_path in tqdm(file_paths, desc="Processing files"):
            try:
                doc_data = self.process_single_file(file_path, industry)
                if doc_data:
                    documents.append(doc_data)
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
        
        # 批量摄取
        if documents:
            result = self.ingester.ingest_batch(documents)
            return result
        else:
            return {'total': 0, 'message': 'No documents processed successfully'}
    
    def process_with_industry_detection(
        self,
        directory: Path,
        recursive: bool = True
    ) -> Dict:
        """
        处理目录中的文件，自动检测行业分类
        
        Args:
            directory: 目录路径
            recursive: 是否递归
            
        Returns:
            处理结果统计
        """
        if recursive:
            files = list(directory.rglob("*.pdf"))
        else:
            files = list(directory.glob("*.pdf"))
        
        self.logger.info(f"Found {len(files)} files in {directory}")
        
        documents = []
        
        for file_path in tqdm(files, desc="Processing files with auto-detection"):
            try:
                # 不指定行业，让系统自动推断
                doc_data = self.process_single_file(file_path, industry=None)
                if doc_data:
                    documents.append(doc_data)
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
        
        # 批量摄取
        if documents:
            result = self.ingester.ingest_batch(documents)
            return result
        else:
            return {'total': 0, 'message': 'No documents processed successfully'}


# 使用示例
if __name__ == "__main__":
    processor = BatchProcessor()
    
    # 示例：处理 SEC 报告目录
    sec_dir = settings.raw_files_path / "sec_filings"
    if sec_dir.exists():
        result = processor.process_directory(
            directory=sec_dir,
            industry="Technology",
            recursive=False
        )
        
        print(f"\nProcessing Results:")
        print(f"Total: {result.get('total', 0)}")
        print(f"Successful: {result.get('successful', 0)}")
        print(f"Failed: {result.get('failed', 0)}")
        print(f"Total chunks: {result.get('total_chunks', 0)}")

