"""
通用工具函数
"""
import re
from pathlib import Path
from typing import Optional
from datetime import datetime


def generate_file_id(file_path: str) -> str:
    """
    根据文件路径生成file_id
    例如: "Deloitte_AI_Report_2024.pdf" -> "Deloitte_AI_Report_2024"
    """
    file_name = Path(file_path).stem  # 获取不带扩展名的文件名
    # 规范化：移除特殊字符，保留字母、数字、下划线、连字符
    file_id = re.sub(r'[^\w\-]', '_', file_name)
    return file_id


def generate_chunk_id(file_id: str, chunk_index: int) -> str:
    """
    生成chunk ID
    例如: "Deloitte_AI_Report_2024", 5 -> "Deloitte_AI_Report_2024_chunk_5"
    """
    return f"{file_id}_chunk_{chunk_index}"


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    """
    # 移除或替换不安全字符
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return sanitized


def get_current_timestamp() -> str:
    """
    获取当前时间戳字符串
    """
    return datetime.now().isoformat()

