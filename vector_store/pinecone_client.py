"""
Pinecone 客户端模块 - 负责初始化索引并写入向量
"""
import logging
from typing import List, Dict, Any

import pinecone

from core.models import EmbeddingRecord
from processing.metadata_builder import build_metadata
from config.settings import (
    PINECONE_API_KEY,
    PINECONE_ENVIRONMENT,
    PINECONE_INDEX_NAME,
    PINECONE_DIMENSION,
    PINECONE_METRIC,
)

logger = logging.getLogger(__name__)


def init_pinecone_index() -> pinecone.Index:
    """
    初始化 Pinecone，确保索引存在并返回 Index 对象
    
    注意：Pinecone API 可能有两种版本：
    1. 旧版本：使用 environment 参数
    2. 新版本（Serverless）：不需要 environment，直接使用 API key
    """
    if not PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY 未配置，无法连接 Pinecone。")

    try:
        # 尝试新版本API（Serverless）
        pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
        indexes = pc.list_indexes()
        index_names = [idx.name for idx in indexes] if hasattr(indexes, '__iter__') else []
        
        if PINECONE_INDEX_NAME not in index_names:
            logger.info(
                "Pinecone 索引不存在，正在创建：name=%s, dimension=%d, metric=%s",
                PINECONE_INDEX_NAME,
                PINECONE_DIMENSION,
                PINECONE_METRIC,
            )
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=PINECONE_DIMENSION,
                metric=PINECONE_METRIC,
            )
        
        logger.info("连接 Pinecone 索引：%s", PINECONE_INDEX_NAME)
        return pc.Index(PINECONE_INDEX_NAME)
        
    except Exception as e:
        # 如果新版本API失败，尝试旧版本API
        logger.warning(f"尝试新版本API失败，使用旧版本API: {e}")
        try:
            pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
            
            if PINECONE_INDEX_NAME not in pinecone.list_indexes():
                logger.info(
                    "Pinecone 索引不存在，正在创建：name=%s, dimension=%d, metric=%s",
                    PINECONE_INDEX_NAME,
                    PINECONE_DIMENSION,
                    PINECONE_METRIC,
                )
                pinecone.create_index(
                    name=PINECONE_INDEX_NAME,
                    dimension=PINECONE_DIMENSION,
                    metric=PINECONE_METRIC,
                )
            
            logger.info("连接 Pinecone 索引：%s", PINECONE_INDEX_NAME)
            return pinecone.Index(PINECONE_INDEX_NAME)
        except Exception as e2:
            raise RuntimeError(f"无法初始化 Pinecone: {e2}") from e2


def build_pinecone_vectors(
    records: List[EmbeddingRecord], chunks_metadata: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    将 EmbeddingRecord + 预先构建的 metadata 组合成 Pinecone upsert 所需的向量列表

    Args:
        records: 向量记录列表
        chunks_metadata: 以 id 为键的 metadata 字典
    """
    vectors: List[Dict[str, Any]] = []

    for rec in records:
        metadata = chunks_metadata.get(rec.id)
        if not metadata:
            # 如果没有找到对应 metadata，可以选择跳过或仅使用 values
            logger.warning("未找到 id=%s 对应的 metadata，跳过该向量。", rec.id)
            continue

        vectors.append(
            {
                "id": rec.id,
                "values": rec.values,
                "metadata": metadata,
            }
        )

    return vectors


def upsert_vectors(index: pinecone.Index, vectors: List[Dict[str, Any]], batch_size: int = 100) -> None:
    """
    将向量批量写入 Pinecone
    """
    if not vectors:
        logger.info("没有需要写入 Pinecone 的向量。")
        return

    logger.info("开始向 Pinecone 写入向量，总数=%d", len(vectors))

    for start in range(0, len(vectors), batch_size):
        end = min(start + batch_size, len(vectors))
        batch = vectors[start:end]
        logger.info("Pinecone upsert，batch=%d-%d", start, end)
        index.upsert(vectors=batch)

    logger.info("Pinecone upsert 完成。")


