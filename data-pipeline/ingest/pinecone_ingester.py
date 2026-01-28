"""
Pinecone 数据摄取器
将处理后的文档写入 Pinecone 向量数据库
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any

# 添加 backend-ai 到路径，以便复用代码
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "backend-ai"))

try:
    from app.services.rag_service import RAGService
    BACKEND_AI_AVAILABLE = True
except ImportError:
    BACKEND_AI_AVAILABLE = False
    RAGService = None

# 如果无法导入 backend-ai，则自己实现
if not BACKEND_AI_AVAILABLE:
    import tiktoken
    from pinecone import Pinecone, ServerlessSpec
    import google.generativeai as genai
    from config.settings import settings
    
    class RAGService:
        """备用的 RAG Service 实现"""
        
        def __init__(self):
            from utils.logger import logger
            self.logger = logger
            self.chunk_size = settings.chunk_size
            self.chunk_overlap = settings.chunk_overlap
            
            # 初始化 tokenizer
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except:
                self.tokenizer = None
            
            # 初始化 Gemini
            genai.configure(api_key=settings.google_api_key)
            
            # 初始化 Pinecone
            self.pc = Pinecone(api_key=settings.pinecone_api_key)
            self.index_name = settings.pinecone_index_name
            
            # 确保索引存在
            self._ensure_index_exists()
            
            # 连接到索引
            self.index = self.pc.Index(self.index_name)
            
            self.logger.info(f"RAG Service initialized (backup implementation)")
        
        def _ensure_index_exists(self):
            """确保 Pinecone 索引存在"""
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                self.logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=getattr(settings, "pinecone_dimension", 3072),
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.pinecone_environment
                    )
                )
        
        def chunk_text(self, text: str) -> List[str]:
            """分块文本"""
            if not text.strip():
                return []
            
            if self.tokenizer:
                tokens = self.tokenizer.encode(text)
                chunks = []
                
                start = 0
                while start < len(tokens):
                    end = start + self.chunk_size
                    chunk_tokens = tokens[start:end]
                    chunk_text = self.tokenizer.decode(chunk_tokens)
                    chunks.append(chunk_text)
                    start = end - self.chunk_overlap
                
                return chunks
            else:
                # 字符级别分块
                chunk_size_chars = self.chunk_size * 4
                overlap_chars = self.chunk_overlap * 4
                
                chunks = []
                start = 0
                while start < len(text):
                    end = start + chunk_size_chars
                    chunks.append(text[start:end])
                    start = end - overlap_chars
                
                return chunks
        
        def generate_embedding(self, text: str) -> List[float]:
            """生成嵌入"""
            result = genai.embed_content(
                model=settings.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        
        def ingest_document(
            self,
            text: str,
            file_id: str,
            industry: str,
            metadata: Optional[Dict[str, Any]] = None
        ) -> int:
            """摄取文档"""
            from app.services.rag_service import sanitize_id
            
            chunks = self.chunk_text(text)
            
            if not chunks:
                raise ValueError("No chunks generated from text")
            
            self.logger.info(f"Processing {len(chunks)} chunks for {file_id}")
            
            vectors = []
            for idx, chunk in enumerate(chunks):
                embedding = self.generate_embedding(chunk)
                
                chunk_metadata = {
                    "file_id": file_id,
                    "industry": industry,
                    "chunk_index": idx,
                    "text": chunk[:1000],
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                safe_file_id = sanitize_id(file_id)
                vector_id = f"{safe_file_id}_chunk_{idx}"
                
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": chunk_metadata
                })
            
            # 批量上传
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            self.logger.info(f"Successfully ingested {len(chunks)} chunks for {file_id}")
            return len(chunks)

from utils.logger import logger


class PineconeIngester:
    """
    Pinecone 摄取器
    负责将文档数据写入 Pinecone
    """
    
    def __init__(self):
        """初始化摄取器"""
        self.logger = logger
        
        try:
            self.rag_service = RAGService()
            self.logger.info("PineconeIngester initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    def ingest_single_document(
        self,
        text: str,
        file_id: str,
        industry: str,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        摄取单个文档
        
        Args:
            text: 文档文本
            file_id: 文件标识符
            industry: 行业分类
            metadata: 额外元数据
            
        Returns:
            处理的分块数量
        """
        try:
            chunks_processed = self.rag_service.ingest_document(
                text=text,
                file_id=file_id,
                industry=industry,
                metadata=metadata or {}
            )
            
            self.logger.info(f"✅ Ingested {file_id}: {chunks_processed} chunks")
            return chunks_processed
            
        except Exception as e:
            self.logger.error(f"❌ Failed to ingest {file_id}: {e}")
            raise
    
    def ingest_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量摄取多个文档
        
        Args:
            documents: 文档列表，每个文档应包含:
                - text: str
                - file_id: str
                - industry: str
                - metadata: dict (optional)
        
        Returns:
            摄取结果统计
        """
        total = len(documents)
        successful = 0
        failed = 0
        total_chunks = 0
        errors = []
        
        self.logger.info(f"Starting batch ingestion of {total} documents")
        
        for i, doc in enumerate(documents, 1):
            try:
                self.logger.info(f"Processing document {i}/{total}: {doc.get('file_id', 'unknown')}")
                
                chunks = self.ingest_single_document(
                    text=doc['text'],
                    file_id=doc['file_id'],
                    industry=doc.get('industry', 'Unknown'),
                    metadata=doc.get('metadata', {})
                )
                
                successful += 1
                total_chunks += chunks
                
            except Exception as e:
                failed += 1
                error_msg = f"{doc.get('file_id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(f"Failed to process document {i}: {e}")
        
        result = {
            'total': total,
            'successful': successful,
            'failed': failed,
            'total_chunks': total_chunks,
            'errors': errors
        }
        
        self.logger.info(f"Batch ingestion completed: {successful}/{total} successful, {total_chunks} total chunks")
        
        if errors:
            self.logger.warning(f"Errors encountered:\n" + "\n".join(errors))
        
        return result
    
    def verify_ingestion(self, file_id: str) -> bool:
        """
        验证文档是否已成功摄取
        
        Args:
            file_id: 文件标识符
            
        Returns:
            是否存在于数据库中
        """
        try:
            # 查询第一个分块
            from app.services.rag_service import sanitize_id
            safe_file_id = sanitize_id(file_id)
            vector_id = f"{safe_file_id}_chunk_0"
            
            result = self.rag_service.index.fetch(ids=[vector_id])
            
            exists = len(result.vectors) > 0
            self.logger.info(f"Verification for {file_id}: {'✅ Found' if exists else '❌ Not found'}")
            
            return exists
            
        except Exception as e:
            self.logger.error(f"Failed to verify {file_id}: {e}")
            return False

