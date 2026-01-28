"""
配置管理（简化版 - 专注AI行业）
统一管理所有配置项
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings(BaseSettings):
    """应用配置（简化版）"""
    
    # 项目路径
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    
    # Pinecone 配置（必需）
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "industry-reports")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
    pinecone_dimension: int = int(os.getenv("PINECONE_DIMENSION", "3072"))
    
    # Google Gemini 配置（必需）
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    # 支持 "gemini-embedding-001" 或 "models/gemini-embedding-001"
    _raw_embedding_model: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001").strip()
    embedding_model: str = (
        _raw_embedding_model if _raw_embedding_model.startswith("models/") else f"models/{_raw_embedding_model}"
    )
    
    # 分块配置
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    top_k_results: int = int(os.getenv("TOP_K_RESULTS", "5"))
    
    # 爬虫配置
    scraper_user_agent: str = os.getenv("SCRAPER_USER_AGENT", "Mozilla/5.0 (Research Bot)")
    scraper_download_delay: float = float(os.getenv("SCRAPER_DOWNLOAD_DELAY", "3"))
    
    # 存储配置（简化）
    storage_base_path: Path = BASE_DIR / "storage"
    raw_files_path: Path = BASE_DIR / "storage" / "raw"
    processed_files_path: Path = BASE_DIR / "storage" / "processed"
    logs_path: Path = BASE_DIR / "storage" / "logs"
    
    # 文件大小限制
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    # 日志配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_retention_days: int = int(os.getenv("LOG_RETENTION_DAYS", "30"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略 .env 中未定义的字段
    
    def ensure_directories(self):
        """确保所有必要的目录存在（简化版）"""
        directories = [
            self.storage_base_path,
            self.logs_path,
            self.raw_files_path / "mckinsey_ai",
            self.processed_files_path,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_required_keys(self) -> bool:
        """验证必需的 API 密钥是否配置"""
        required_keys = {
            "Pinecone API Key": self.pinecone_api_key,
            "Google API Key": self.google_api_key,
        }
        
        missing_keys = [name for name, key in required_keys.items() if not key]
        
        if missing_keys:
            print(f"❌ 缺少必需的 API 密钥: {', '.join(missing_keys)}")
            print("请在 .env 文件中配置这些密钥")
            return False
        
        return True


# 创建全局配置实例
settings = Settings()

# 确保目录存在
settings.ensure_directories()

