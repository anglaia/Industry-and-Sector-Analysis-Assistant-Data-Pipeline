"""
数据模型定义 - 只定义类和字段，不包含复杂逻辑
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Document:
    """
    文档级模型 - 统一管理一个PDF的整体信息
    """
    # 核心属性
    file_id: str  # 逻辑文件ID，如 "Deloitte_AI_Report_2024"
    industry: str  # 行业分类，如 "AI", "general"
    source_file: str  # 原始文件名，如 "Deloitte_AI_Report_2024.pdf"
    local_path: str  # 本地文件路径
    
    # 引用/外部属性
    s3_url: Optional[str] = None  # 上传到S3后的URL
    
    # 推荐属性
    title: Optional[str] = None
    year: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None
    collection_date: Optional[str] = None
    date: Optional[str] = None  # 发布日期
    
    # 运行时属性
    num_pages: Optional[int] = None  # PDF总页数
    session_id: Optional[str] = None  # 用户上传时的会话ID（可选）
    
    # 其他可选字段
    doc_id: Optional[str] = None  # 文档ID（如果与file_id不同）


@dataclass
class Page:
    """
    页级模型 - 保存每一页的原始和清洗后文本
    """
    file_id: str  # 所属文档的file_id
    page_number: int  # 页码（从1开始）
    raw_text: str  # 原始提取的文本
    clean_text: Optional[str] = None  # 清洗后的文本


@dataclass
class Chunk:
    """
    Chunk模型 - 表示一个最终要向量化和入库的文本段落单位
    """
    # 核心必需字段（4个）
    file_id: str  # 来源于Document
    industry: str  # 来源于Document
    chunk_index: int  # 在当前文件内的递增索引（从0或1开始）
    text: str  # chunk的文本内容
    
    # 引用必需字段（3个）
    page_number: int  # 主要页码（单页chunk=该页，跨页chunk=起始页）
    s3_url: Optional[str] = None  # 来自Document
    source_file: str  # 来自Document.source_file
    
    # 跨页字段（可选，但强烈建议写上）
    page_start: Optional[int] = None  # 起始页码
    page_end: Optional[int] = None  # 结束页码
    
    # 推荐字段
    title: Optional[str] = None
    year: Optional[str] = None
    author: Optional[str] = None
    
    # 其他可选字段
    doc_id: Optional[str] = None
    date: Optional[str] = None
    source: Optional[str] = None
    collection_date: Optional[str] = None
    language: Optional[str] = None
    session_id: Optional[str] = None
    
    # 技术字段
    chunk_id: Optional[str] = None  # 如 "Deloitte_AI_Report_2024_chunk_5"


@dataclass
class EmbeddingRecord:
    """
    向量记录模型 - 专门表示可以直接写入Pinecone的一条记录
    """
    id: str  # chunk ID，如 "Deloitte_AI_Report_2024_chunk_5"
    values: List[float]  # embedding向量
    metadata: Dict[str, Any]  # 按schema打平好的字典，包含所有核心/引用/推荐字段


@dataclass
class ProcessingStats:
    """
    处理统计信息
    """
    file_id: str
    total_pages: int = 0
    total_chunks: int = 0
    processing_start_time: Optional[datetime] = None
    processing_end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)

