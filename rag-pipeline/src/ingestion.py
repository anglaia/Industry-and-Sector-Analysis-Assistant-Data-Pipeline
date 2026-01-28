"""
向量摄取模块 (Phase 2)
功能：
1. 读取本地 JSONL 文件
2. 使用 Gemini API 生成嵌入向量
3. 上传到 Pinecone 向量数据库
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Generator

import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec

from config import Config


class VectorIngestion:
    """向量摄取器"""
    
    def __init__(self):
        """初始化向量摄取器"""
        self.config = Config
        
        # 验证配置
        self.config.validate()
        
        # 初始化 Gemini
        self._init_gemini()
        
        # 初始化 Pinecone
        self._init_pinecone()
    
    def _init_gemini(self):
        """初始化 Gemini API"""
        print("正在初始化 Gemini API...")
        try:
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            print("✓ Gemini API 初始化成功")
        except Exception as e:
            print(f"✗ Gemini API 初始化失败: {str(e)}")
            raise
    
    def _init_pinecone(self):
        """初始化 Pinecone 客户端和索引"""
        print("正在初始化 Pinecone...")
        try:
            # 初始化 Pinecone 客户端
            self.pc = Pinecone(api_key=self.config.PINECONE_API_KEY)
            
            # 获取或创建索引
            index_name = self.config.PINECONE_INDEX_NAME
            
            # 检查索引是否存在
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if index_name not in existing_indexes:
                print(f"索引 '{index_name}' 不存在，正在创建...")
                self.pc.create_index(
                    name=index_name,
                    dimension=self.config.EMBEDDING_DIMENSION,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=self.config.PINECONE_ENVIRONMENT or 'us-east-1'
                    )
                )
                print(f"✓ 索引 '{index_name}' 创建成功")
            else:
                print(f"✓ 索引 '{index_name}' 已存在")
            
            # 连接到索引
            self.index = self.pc.Index(index_name)
            print(f"✓ Pinecone 初始化成功")
            
        except Exception as e:
            print(f"✗ Pinecone 初始化失败: {str(e)}")
            raise
    
    def read_jsonl_batches(self, file_path: Path, batch_size: int = None) -> Generator[List[Dict], None, None]:
        """
        批量读取 JSONL 文件
        
        Args:
            file_path: JSONL 文件路径
            batch_size: 批量大小
            
        Yields:
            List[Dict]: 批量文档列表
        """
        if batch_size is None:
            batch_size = self.config.BATCH_SIZE
        
        batch = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    batch.append(doc)
                    
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
            
            # 返回最后一批
            if batch:
                yield batch
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        使用 Gemini API 生成嵌入向量（批量处理）
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        try:
            embeddings = []
            
            # 批量生成嵌入（Gemini 支持批量请求）
            print(f"      正在生成 {len(texts)} 个嵌入向量...")
            
            for i, text in enumerate(texts):
                # 显示详细进度
                if i % 10 == 0 or i == 0:
                    print(f"        进度: {i+1}/{len(texts)}")
                
                try:
                    result = genai.embed_content(
                        model=self.config.EMBEDDING_MODEL,
                        content=text,
                        task_type="retrieval_document"
                    )
                    embeddings.append(result['embedding'])
                    
                    # 短暂延迟避免速率限制
                    if i > 0 and i % 10 == 0:
                        time.sleep(0.1)
                        
                except Exception as api_error:
                    print(f"        警告: 第 {i+1} 个文本生成失败: {str(api_error)}")
                    # 使用零向量作为后备
                    embeddings.append([0.0] * self.config.EMBEDDING_DIMENSION)
            
            print(f"      ✓ 嵌入向量生成完成")
            return embeddings
            
        except Exception as e:
            print(f"✗ 生成嵌入向量失败: {str(e)}")
            raise
    
    def prepare_pinecone_payload(self, documents: List[Dict], embeddings: List[List[float]]) -> List[Dict]:
        """
        准备 Pinecone 上传的数据格式
        
        Args:
            documents: 原始文档列表
            embeddings: 嵌入向量列表
            
        Returns:
            List[Dict]: Pinecone 格式的数据列表
        """
        vectors = []
        
        for doc, embedding in zip(documents, embeddings):
            # 将 text 移动到 metadata 中
            metadata = doc['metadata'].copy()
            metadata['text'] = doc['text']  # 重要：将文本内容移到 metadata 中供 RAG 使用
            
            vector = {
                "id": doc['id'],
                "values": embedding,
                "metadata": metadata
            }
            vectors.append(vector)
        
        return vectors
    
    def upsert_to_pinecone(self, vectors: List[Dict]):
        """
        上传向量到 Pinecone
        
        Args:
            vectors: Pinecone 格式的向量列表
        """
        try:
            # 批量上传
            self.index.upsert(vectors=vectors)
            
        except Exception as e:
            print(f"✗ 上传到 Pinecone 失败: {str(e)}")
            raise
    
    def process_batch(self, batch: List[Dict]) -> int:
        """
        处理一批文档
        
        Args:
            batch: 文档批次
            
        Returns:
            int: 成功处理的文档数量
        """
        try:
            # 提取文本
            texts = [doc['text'] for doc in batch]
            print(f"      提取了 {len(texts)} 个文本")
            
            # 生成嵌入向量
            embeddings = self.generate_embeddings(texts)
            
            # 准备 Pinecone 数据
            print(f"      准备 Pinecone 数据...")
            vectors = self.prepare_pinecone_payload(batch, embeddings)
            
            # 上传到 Pinecone
            print(f"      上传到 Pinecone...")
            self.upsert_to_pinecone(vectors)
            print(f"      ✓ 上传完成")
            
            return len(batch)
            
        except Exception as e:
            print(f"\n      ✗ 处理批次出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0
    
    def run(self, input_path: Path = None):
        """
        运行完整的向量摄取流程
        
        Args:
            input_path: JSONL 文件路径，默认使用配置中的路径
        """
        print("=" * 60)
        print("Phase 2: 向量摄取")
        print("=" * 60)
        
        if input_path is None:
            input_path = self.config.OUTPUT_JSONL
        
        # 检查文件是否存在
        if not input_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
        
        print(f"正在读取: {input_path}")
        
        # 统计总行数（用于进度条）
        total_lines = sum(1 for _ in open(input_path, 'r', encoding='utf-8'))
        print(f"总共 {total_lines} 个文档块需要处理")
        
        # 批量处理
        processed_count = 0
        batch_count = 0
        start_time = time.time()
        
        print(f"\n开始处理...")
        
        for batch in self.read_jsonl_batches(input_path):
            batch_count += 1
            
            try:
                # 显示当前批次信息
                print(f"  批次 {batch_count}: 处理 {len(batch)} 个文档块...")
                
                count = self.process_batch(batch)
                processed_count += count
                
                # 显示进度
                progress = (processed_count / total_lines) * 100
                elapsed = time.time() - start_time
                avg_time = elapsed / processed_count if processed_count > 0 else 0
                remaining = (total_lines - processed_count) * avg_time
                
                print(f"    ✓ 完成 {processed_count}/{total_lines} ({progress:.1f}%) - 预计剩余: {remaining/60:.1f} 分钟")
                
                # 添加短暂延迟以避免 API 速率限制
                time.sleep(1)
                
            except Exception as e:
                print(f"\n  ⚠️  警告: 批次 {batch_count} 处理失败: {str(e)}")
                print(f"    跳过这个批次，继续处理...")
                continue
        
        print(f"\n✓ Phase 2 完成!")
        print(f"成功处理: {processed_count}/{total_lines} 个文档块")
        print(f"索引名称: {self.config.PINECONE_INDEX_NAME}")
        
        # 显示索引统计
        try:
            stats = self.index.describe_index_stats()
            print(f"索引统计: {stats}")
        except Exception as e:
            print(f"无法获取索引统计: {str(e)}")


def main():
    """主函数"""
    ingestion = VectorIngestion()
    ingestion.run()


if __name__ == "__main__":
    main()

