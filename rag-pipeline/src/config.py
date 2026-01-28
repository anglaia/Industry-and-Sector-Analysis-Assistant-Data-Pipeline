"""
配置管理模块
用于加载和管理环境变量和配置参数
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """配置类，用于管理所有配置参数"""
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rag-news-index")
    
    # Kaggle Dataset 配置
    DATASET_NAME = "deepanshudalal09/mit-ai-news-published-till-2023"
    
    # 文件路径
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    OUTPUT_JSONL = DATA_DIR / "processed_data.jsonl"
    
    # 数据处理配置
    CHUNK_SIZE = 512  # 每个文本块的最大字符数
    CHUNK_OVERLAP = 50  # 文本块之间的重叠字符数
    BATCH_SIZE = 20  # Pinecone 批量上传的大小（减小以提高稳定性）
    
    # Gemini 嵌入模型配置
    # 既支持无前缀，也支持 "models/..." 前缀
    _RAW_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001").strip()
    EMBEDDING_MODEL = (
        _RAW_EMBEDDING_MODEL
        if _RAW_EMBEDDING_MODEL.startswith("models/")
        else f"models/{_RAW_EMBEDDING_MODEL}"
    )
    EMBEDDING_DIMENSION = int(os.getenv("PINECONE_DIMENSION", "3072"))  # gemini-embedding-001 的维度
    
    @classmethod
    def validate(cls):
        """验证必需的配置是否已设置"""
        required_vars = {
            "GEMINI_API_KEY": cls.GEMINI_API_KEY,
            "PINECONE_API_KEY": cls.PINECONE_API_KEY,
            "PINECONE_ENVIRONMENT": cls.PINECONE_ENVIRONMENT,
        }
        
        missing = [key for key, value in required_vars.items() if not value]
        
        if missing:
            raise ValueError(
                f"缺少必需的环境变量: {', '.join(missing)}\n"
                f"请在 .env 文件中设置这些变量"
            )
    
    @classmethod
    def setup_directories(cls):
        """创建必需的目录"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)

