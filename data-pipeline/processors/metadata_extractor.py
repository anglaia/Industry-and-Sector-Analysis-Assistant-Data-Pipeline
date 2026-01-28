"""
元数据提取器
从文件名、内容等提取结构化元数据
"""
import re
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from utils.logger import logger


class MetadataExtractor:
    """从文档提取元数据"""
    
    # 行业关键词映射
    INDUSTRY_KEYWORDS = {
        'Technology': [
            'software', 'hardware', 'AI', 'artificial intelligence',
            'cloud', 'semiconductor', 'tech', 'digital', 'computing',
            'internet', 'mobile', 'app', 'platform'
        ],
        'Healthcare': [
            'healthcare', 'health', 'medical', 'pharmaceutical', 'pharma',
            'biotech', 'hospital', 'clinical', 'patient', 'drug', 'therapy'
        ],
        'Finance': [
            'banking', 'bank', 'insurance', 'investment', 'fintech',
            'financial', 'capital', 'credit', 'asset', 'portfolio', 'trading'
        ],
        'Manufacturing': [
            'manufacturing', 'factory', 'production', 'automotive', 'auto',
            'industrial', 'machinery', 'assembly', 'supply chain'
        ],
        'Retail': [
            'retail', 'store', 'shopping', 'consumer', 'e-commerce',
            'merchandise', 'sales', 'customer'
        ],
        'Energy': [
            'energy', 'oil', 'gas', 'renewable', 'solar', 'wind',
            'electricity', 'power', 'utility'
        ]
    }
    
    @staticmethod
    def extract_from_filename(filename: str) -> Dict[str, Optional[str]]:
        """
        从文件名提取元数据
        
        Args:
            filename: 文件名
            
        Returns:
            元数据字典
        """
        metadata = {
            'original_filename': filename,
            'year': None,
            'company': None,
            'report_type': None
        }
        
        # 提取年份（4位数字）
        year_match = re.search(r'(20\d{2})', filename)
        if year_match:
            metadata['year'] = year_match.group(1)
        
        # 提取公司名称（股票代码）
        ticker_match = re.search(r'\b([A-Z]{2,5})\b', filename)
        if ticker_match:
            metadata['company'] = ticker_match.group(1)
        
        # 提取报告类型
        if '10-K' in filename.upper():
            metadata['report_type'] = '10-K'
        elif '10-Q' in filename.upper():
            metadata['report_type'] = '10-Q'
        elif 'annual' in filename.lower():
            metadata['report_type'] = 'Annual Report'
        elif 'quarterly' in filename.lower():
            metadata['report_type'] = 'Quarterly Report'
        
        return metadata
    
    @staticmethod
    def extract_industry_from_text(text: str, top_n: int = 3) -> list:
        """
        从文本内容推断行业
        
        Args:
            text: 文本内容
            top_n: 返回前 N 个最匹配的行业
            
        Returns:
            行业列表
        """
        text_lower = text.lower()
        
        # 计算每个行业的关键词出现次数
        industry_scores = {}
        
        for industry, keywords in MetadataExtractor.INDUSTRY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # 使用词边界匹配，避免部分匹配
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                matches = re.findall(pattern, text_lower)
                score += len(matches)
            
            if score > 0:
                industry_scores[industry] = score
        
        # 按分数排序
        sorted_industries = sorted(
            industry_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 返回前 N 个
        return [industry for industry, score in sorted_industries[:top_n]]
    
    @staticmethod
    def extract_date_from_text(text: str) -> Optional[str]:
        """
        从文本提取日期
        
        Args:
            text: 文本内容
            
        Returns:
            日期字符串（YYYY-MM-DD 格式），如果未找到返回 None
        """
        # 尝试多种日期格式
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if '-' in pattern:
                        year, month, day = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif '/' in pattern:
                        month, day, year = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:  # Month name format
                        month_name, day, year = match.groups()
                        month_num = datetime.strptime(month_name, '%B').month
                        return f"{year}-{month_num:02d}-{int(day):02d}"
                except:
                    continue
        
        return None
    
    @staticmethod
    def extract_author_from_text(text: str) -> Optional[str]:
        """
        从文本提取作者
        
        Args:
            text: 文本内容
            
        Returns:
            作者名称，如果未找到返回 None
        """
        # 查找常见的作者标识
        author_patterns = [
            r'Author[s]?:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'By\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Written by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, text[:2000])  # 只搜索前2000个字符
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def build_metadata(
        file_path: Path,
        text: Optional[str] = None,
        additional_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        综合构建元数据
        
        Args:
            file_path: 文件路径
            text: 文本内容（可选）
            additional_metadata: 额外的元数据（可选）
            
        Returns:
            完整的元数据字典
        """
        metadata = {
            'source': 'automated_collection',
            'collected_at': datetime.now().isoformat(),
        }
        
        # 从文件名提取
        filename_metadata = MetadataExtractor.extract_from_filename(file_path.name)
        metadata.update(filename_metadata)
        
        # 从文本内容提取
        if text:
            # 截取前5000字符用于元数据提取（提高性能）
            text_sample = text[:5000]
            
            # 推断行业
            industries = MetadataExtractor.extract_industry_from_text(text_sample)
            if industries:
                metadata['industry'] = industries[0]  # 使用最匹配的行业
                metadata['industries'] = industries  # 保存所有匹配的行业
            
            # 提取日期
            if not metadata.get('year'):
                date_str = MetadataExtractor.extract_date_from_text(text_sample)
                if date_str:
                    metadata['date'] = date_str
                    metadata['year'] = date_str[:4]
            
            # 提取作者
            author = MetadataExtractor.extract_author_from_text(text_sample)
            if author:
                metadata['author'] = author
        
        # 合并额外的元数据
        if additional_metadata:
            metadata.update(additional_metadata)
        
        logger.debug(f"Extracted metadata for {file_path.name}: {metadata}")
        return metadata

