"""
配置文件 - 统一管理所有配置项
"""
import os
from pathlib import Path
from typing import Optional

# 尝试加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"已加载环境变量文件: {env_path}")
except ImportError:
    # 如果没有安装python-dotenv，跳过
    pass

# ==================== 项目路径配置 ====================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOCAL_STORE_DIR = OUTPUT_DIR / "local_store"
LOGS_DIR = PROJECT_ROOT / "logs"

# 确保目录存在
for dir_path in [DATA_DIR, OUTPUT_DIR, LOCAL_STORE_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ==================== S3 配置 ====================
S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME", None)
S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
S3_PREFIX: str = os.getenv("S3_PREFIX", "documents/")
AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", None)

# ==================== Pinecone 配置 ====================
PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY", None)
PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "industry-analysis")
PINECONE_DIMENSION: int = int(os.getenv("PINECONE_DIMENSION", "3072"))  # 默认3072（gemini-embedding-001）
PINECONE_METRIC: str = os.getenv("PINECONE_METRIC", "cosine")

# ==================== Embedding API 配置 ====================
# 支持 Gemini / OpenAI / 其他
EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "gemini")  # "gemini" | "openai" | "other"
EMBEDDING_API_KEY: Optional[str] = os.getenv("EMBEDDING_API_KEY", None)
# Gemini 模型名：
# - 既支持 "gemini-embedding-001"（无前缀），也支持 "models/gemini-embedding-001"
_raw_embedding_model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001").strip()
EMBEDDING_MODEL: str = (
    _raw_embedding_model if _raw_embedding_model.startswith("models/") else f"models/{_raw_embedding_model}"
)
EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
EMBEDDING_MAX_RETRIES: int = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))

# ==================== PDF 处理配置 ====================
# Chunk 切块参数
CHUNK_MAX_CHARS: int = int(os.getenv("CHUNK_MAX_CHARS", "1000"))  # 每个chunk最大字符数
CHUNK_OVERLAP_CHARS: int = int(os.getenv("CHUNK_OVERLAP_CHARS", "200"))  # chunk之间的重叠字符数
CHUNK_ALLOW_CROSS_PAGE: bool = os.getenv("CHUNK_ALLOW_CROSS_PAGE", "true").lower() == "true"

# 文本清洗配置
CLEAN_REMOVE_HEADERS: bool = True
CLEAN_REMOVE_FOOTERS: bool = True
CLEAN_REMOVE_ADS: bool = True
CLEAN_REMOVE_CONTACTS: bool = True

# ==================== 文档配置文件路径 ====================
DOCUMENTS_CONFIG_PATH = PROJECT_ROOT / "documents_config.yaml"

# ==================== 日志配置 ====================
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "pipeline.log"

