"""
Pinecone 客户端模块 - 负责初始化索引并写入向量
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any

from pinecone import Pinecone, ServerlessSpec

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


def init_pinecone_index() -> Any:
    """
    初始化 Pinecone，确保索引存在并返回 Index 对象

    说明：
    - 该项目统一使用新版 `pinecone` SDK（Pinecone class）
    - 不再使用已废弃的 `pinecone.init()` / `pinecone.Index()` 旧接口
    """
    if not PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY 未配置，无法连接 Pinecone。")

    pc = Pinecone(api_key=PINECONE_API_KEY)

    try:
        indexes = pc.list_indexes()
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if "401" in msg or "Unauthorized" in msg or "Invalid API Key" in msg:
            raise RuntimeError(
                "Pinecone 鉴权失败（401 / Invalid API Key）。请确认：\n"
                "- `.env` 里的 `PINECONE_API_KEY` 是 Pinecone 控制台最新的 API key（不要带多余空格/换行）\n"
                "- 该 key 属于你当前使用的 Pinecone 项目\n"
            ) from e
        raise RuntimeError(f"无法连接 Pinecone（list_indexes 失败）: {e}") from e

    # 兼容不同 SDK 返回结构
    if hasattr(indexes, "names"):
        index_names = list(indexes.names())
    else:
        try:
            index_names = [idx.name for idx in indexes]
        except Exception:  # noqa: BLE001
            index_names = []

    if PINECONE_INDEX_NAME not in index_names:
        logger.info(
            "Pinecone 索引不存在，正在创建：name=%s, dimension=%d, metric=%s",
            PINECONE_INDEX_NAME,
            PINECONE_DIMENSION,
            PINECONE_METRIC,
        )
        # 新版 SDK 需要显式提供 ServerlessSpec
        # 这里用 PINECONE_ENVIRONMENT 作为 region（例如 us-east-1），cloud 默认 aws
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=PINECONE_DIMENSION,
            metric=PINECONE_METRIC,
            spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT),
        )

    logger.info("连接 Pinecone 索引：%s", PINECONE_INDEX_NAME)
    return pc.Index(PINECONE_INDEX_NAME)


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


def upsert_vectors(index: Any, vectors: List[Dict[str, Any]], batch_size: int = 100) -> None:
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


