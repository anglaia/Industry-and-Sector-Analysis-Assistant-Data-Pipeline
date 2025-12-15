"""
本地存储模块 - 将chunks保存为JSONL格式
"""
import json
import logging
from pathlib import Path
from typing import List, Optional

from core.models import Chunk
from processing.metadata_builder import build_metadata
from config.settings import LOCAL_STORE_DIR

logger = logging.getLogger(__name__)


def save_chunks_to_jsonl(chunks: List[Chunk], file_id: str, output_dir: Optional[Path] = None) -> Path:
    """
    将chunks保存为JSONL格式文件
    
    Args:
        chunks: Chunk对象列表
        file_id: 文档的file_id，用于生成文件名
        output_dir: 输出目录，如果为None则使用默认的LOCAL_STORE_DIR
        
    Returns:
        Path: 保存的文件路径
    """
    if output_dir is None:
        output_dir = LOCAL_STORE_DIR
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名
    from core.utils import sanitize_filename
    safe_file_id = sanitize_filename(file_id)
    output_file = output_dir / f"{safe_file_id}_chunks.jsonl"
    
    # 写入JSONL文件
    with open(output_file, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            # 构建记录（暂时没有embedding values）
            record = {
                "id": chunk.chunk_id or f"{chunk.file_id}_chunk_{chunk.chunk_index}",
                "metadata": build_metadata(chunk)
                # 注意：values字段在步骤2中暂时不包含，因为还没有生成embedding
            }
            
            # 写入一行JSON
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    logger.info(f"成功保存 {len(chunks)} 个chunks到 {output_file}")
    return output_file


def load_chunks_from_jsonl(jsonl_path: Path) -> List[dict]:
    """
    从JSONL文件加载chunks（用于调试或后续处理）
    
    Args:
        jsonl_path: JSONL文件路径
        
    Returns:
        List[dict]: 包含chunk记录的字典列表
    """
    chunks = []
    
    if not jsonl_path.exists():
        logger.warning(f"JSONL文件不存在: {jsonl_path}")
        return chunks
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            try:
                record = json.loads(line.strip())
                chunks.append(record)
            except json.JSONDecodeError as e:
                logger.error(f"解析第 {line_num} 行时出错: {e}")
                continue
    
    logger.info(f"从 {jsonl_path} 加载了 {len(chunks)} 个chunks")
    return chunks

