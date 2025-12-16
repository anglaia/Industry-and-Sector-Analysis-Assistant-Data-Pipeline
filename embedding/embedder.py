"""
Embedding 模块 - 调用外部 API（默认 Gemini）为 Chunk 生成向量
"""
import logging
from typing import List

from core.models import Chunk, EmbeddingRecord
from config.settings import (
    EMBEDDING_PROVIDER,
    EMBEDDING_API_KEY,
    EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MAX_RETRIES,
)

logger = logging.getLogger(__name__)


def get_embeddings_for_chunks(chunks: List[Chunk]) -> List[EmbeddingRecord]:
    """
    为一组 Chunk 生成向量
    """
    if not chunks:
        return []

    if not EMBEDDING_API_KEY:
        raise RuntimeError("EMBEDDING_API_KEY 未配置，无法生成向量。")

    if EMBEDDING_PROVIDER.lower() == "gemini":
        return _embed_with_gemini(chunks)
    else:
        raise NotImplementedError(
            f"当前仅实现 provider='gemini'，但配置为: {EMBEDDING_PROVIDER}"
        )


def _embed_with_gemini(chunks: List[Chunk]) -> List[EmbeddingRecord]:
    """
    使用 Google Gemini Embedding API 生成向量
    """
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise ImportError(
            "缺少 google-generativeai 依赖，请先安装：pip install google-generativeai"
        ) from exc

    genai.configure(api_key=EMBEDDING_API_KEY)

    records: List[EmbeddingRecord] = []
    texts = [chunk.text for chunk in chunks]

    # 分批调用
    for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        end = min(start + EMBEDDING_BATCH_SIZE, len(texts))
        batch_chunks = chunks[start:end]
        batch_texts = texts[start:end]

        for attempt in range(1, EMBEDDING_MAX_RETRIES + 1):
            try:
                logger.info(
                    "调用 Gemini 生成向量，batch=%d-%d, attempt=%d",
                    start,
                    end,
                    attempt,
                )
                
                # 使用 Gemini Embedding API
                # 注意：Gemini的embedding API可能需要使用不同的方法
                # 这里使用google-generativeai库的标准方法
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=batch_texts,
                    task_type="retrieval_document"  # 文档检索任务
                )
                
                # 处理返回结果
                # Gemini API返回格式：{"embeddings": [[...], [...]]} 或直接是列表
                if isinstance(result, dict):
                    embeddings_list = result.get("embedding", result.get("embeddings", []))
                else:
                    embeddings_list = result if isinstance(result, list) else [result]
                
                # 如果返回的是单个列表（所有embeddings在一个列表中）
                if len(embeddings_list) == len(batch_chunks):
                    # 每个元素是一个向量
                    for chunk, emb_values in zip(batch_chunks, embeddings_list):
                        if isinstance(emb_values, dict):
                            values = emb_values.get("values", emb_values)
                        else:
                            values = emb_values
                        
                        record = EmbeddingRecord(
                            id=chunk.chunk_id or f"{chunk.file_id}_chunk_{chunk.chunk_index}",
                            values=values,
                            metadata={},  # metadata 由上层模块补齐
                        )
                        records.append(record)
                else:
                    raise ValueError(
                        f"返回的 embedding 数量与输入不一致: {len(embeddings_list)} != {len(batch_chunks)}"
                    )

                break  # 当前 batch 成功，跳出重试循环
            except Exception as exc:  # noqa: BLE001
                logger.warning("Gemini 向量生成失败（尝试 %d/%d）：%s", attempt, EMBEDDING_MAX_RETRIES, exc)
                if attempt == EMBEDDING_MAX_RETRIES:
                    logger.error("Gemini 多次重试仍失败，放弃该批次。", exc_info=True)
                    # 为保持整体流程不中断，可以选择跳过这一批
                    continue

    return records


