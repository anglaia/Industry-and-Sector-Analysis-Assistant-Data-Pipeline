"""
元数据构建模块 - 为Chunk生成完整的metadata字典
"""
import logging
from typing import Dict, Any

from core.models import Chunk

logger = logging.getLogger(__name__)


def build_metadata(chunk: Chunk) -> Dict[str, Any]:
    """
    为Chunk构建完整的metadata字典，符合Pinecone的schema要求
    
    Args:
        chunk: Chunk对象
        
    Returns:
        Dict[str, Any]: 包含所有必需和可选字段的metadata字典
    """
    metadata: Dict[str, Any] = {}
    
    # ==================== 核心必需字段（4个）====================
    metadata["file_id"] = chunk.file_id
    metadata["industry"] = chunk.industry
    metadata["chunk_index"] = chunk.chunk_index
    metadata["text"] = chunk.text
    
    # ==================== 引用功能必需字段（3个）====================
    metadata["page_number"] = chunk.page_number
    if chunk.s3_url:
        metadata["s3_url"] = chunk.s3_url
    metadata["source_file"] = chunk.source_file
    
    # ==================== 跨页字段（可选，但强烈建议写上）====================
    if chunk.page_start is not None:
        metadata["page_start"] = chunk.page_start
    if chunk.page_end is not None:
        metadata["page_end"] = chunk.page_end
    
    # ==================== 推荐字段 ====================
    if chunk.title:
        metadata["title"] = chunk.title
    if chunk.year:
        metadata["year"] = chunk.year
    if chunk.author:
        metadata["author"] = chunk.author
    
    # ==================== 可选字段 ====================
    if chunk.doc_id:
        metadata["doc_id"] = chunk.doc_id
    if chunk.date:
        metadata["date"] = chunk.date
    if chunk.source:
        metadata["source"] = chunk.source
    if chunk.collection_date:
        metadata["collection_date"] = chunk.collection_date
    if chunk.language:
        metadata["language"] = chunk.language
    if chunk.session_id:
        metadata["session_id"] = chunk.session_id
    
    return metadata


def build_pinecone_payload(chunk: Chunk, embedding_values: list) -> Dict[str, Any]:
    """
    构建完整的Pinecone payload（包含id, values, metadata）
    
    注意：这个函数在步骤2中暂时不会用到（因为还没有embedding），
    但为了完整性，先定义在这里。
    
    Args:
        chunk: Chunk对象
        embedding_values: embedding向量值列表
        
    Returns:
        Dict[str, Any]: Pinecone payload字典
    """
    payload = {
        "id": chunk.chunk_id or f"{chunk.file_id}_chunk_{chunk.chunk_index}",
        "values": embedding_values,
        "metadata": build_metadata(chunk)
    }
    
    return payload

