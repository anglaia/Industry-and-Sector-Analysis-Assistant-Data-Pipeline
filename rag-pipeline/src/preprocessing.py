"""
文档预处理模块 (Phase 1)
功能：
1. 从 Kaggle 加载数据集
2. 清洗和预处理文本
3. 分块处理
4. 保存为 JSONL 格式
"""
import json
import re
import os
import pandas as pd
import kagglehub
from pathlib import Path
from typing import List, Dict

from config import Config


class DocumentPreprocessor:
    """文档预处理器"""
    
    def __init__(self):
        """初始化预处理器"""
        self.config = Config
        self.df = None
        
    def load_dataset(self) -> pd.DataFrame:
        """
        从 Kaggle 加载数据集
        
        Returns:
            pd.DataFrame: 加载的数据集
        """
        print("正在从 Kaggle 加载数据集...")
        try:
            # 首先下载数据集到本地
            print("正在下载数据集...")
            path = kagglehub.dataset_download(self.config.DATASET_NAME)
            print(f"✓ 数据集已下载到: {path}")
            
            # 查找数据集中的 CSV 文件
            csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
            
            if not csv_files:
                raise FileNotFoundError("数据集中未找到 CSV 文件")
            
            # 加载第一个 CSV 文件
            csv_path = os.path.join(path, csv_files[0])
            print(f"正在加载文件: {csv_files[0]}")
            
            self.df = pd.read_csv(csv_path)
            
            print(f"✓ 成功加载数据集，共 {len(self.df)} 条记录")
            print(f"数据集列: {self.df.columns.tolist()}")
            print(f"前 5 条记录:\n{self.df.head()}")
            return self.df
            
        except Exception as e:
            print(f"✗ 加载数据集失败: {str(e)}")
            raise
    
    def clean_text(self, text: str) -> str:
        """
        清洗文本
        - 移除多余空白
        - 移除特殊字符（保留基本标点）
        - 规范化空格
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清洗后的文本
        """
        if not isinstance(text, str):
            return ""
        
        # 移除 HTML 标签（简化版，避免灾难性回溯）
        text = re.sub(r'<[^>]{1,200}>', '', text)
        
        # 移除 URL（简化版，更高效）
        text = re.sub(r'https?://\S+', '', text)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除前后空白
        text = text.strip()
        
        return text
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        将长文本分割成多个文本块（简化版，性能优化）
        
        Args:
            text: 输入文本
            chunk_size: 每个块的最大字符数
            overlap: 块之间的重叠字符数
            
        Returns:
            List[str]: 文本块列表
        """
        if chunk_size is None:
            chunk_size = self.config.CHUNK_SIZE
        if overlap is None:
            overlap = self.config.CHUNK_OVERLAP
            
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            
            if chunk:
                chunks.append(chunk)
            
            # 移动到下一个位置，考虑重叠
            if end >= len(text):
                break
            start = end - overlap
        
        return chunks
    
    def process_row(self, row: pd.Series, row_idx: int) -> List[Dict]:
        """
        处理单行数据，生成多个文本块
        
        Args:
            row: DataFrame 的一行
            row_idx: 行索引
            
        Returns:
            List[Dict]: 处理后的文档块列表
        """
        # 根据 MIT AI News 数据集的实际列名进行字段映射
        # Article Header -> title
        # Article Body -> content
        
        # 提取字段
        title = row.get('Article Header', '') or row.get('title', '') or f"Document {row_idx}"
        content = row.get('Article Body', '') or row.get('text', '') or row.get('content', '')
        date = row.get('Published Date', '') or row.get('date', '') or row.get('published_date', '')
        url = row.get('Url', '') or row.get('URL', '') or row.get('url', '') or row.get('link', '') or ""
        
        # 清洗文本
        title = self.clean_text(str(title))
        content = self.clean_text(str(content))
        
        # 如果内容为空，跳过这条记录
        if not content or content == 'nan':
            return []
        
        # 提取年份
        year = self._extract_year(date)
        
        # 只对文章内容进行分块（不包含标题）
        chunks = self.chunk_text(content)
        
        # 生成文档 ID
        doc_id = f"doc_{row_idx:06d}"
        
        # 为每个块创建结构化数据
        documents = []
        for chunk_idx, chunk_text in enumerate(chunks):
            doc = {
                "id": f"{doc_id}_chunk_{chunk_idx:02d}",
                "text": chunk_text,
                "metadata": {
                    "industry": "AI/Technology",  # MIT AI News 默认为 AI/Technology
                    "year": year,
                    "doc_id": doc_id,
                    "title": title,
                    "source_url": url,
                }
            }
            documents.append(doc)
        
        return documents
    
    def _extract_year(self, date_str: str) -> int:
        """
        从日期字符串中提取年份
        
        Args:
            date_str: 日期字符串
            
        Returns:
            int: 年份，如果无法提取则返回 2023
        """
        if not date_str:
            return 2023
        
        # 尝试提取四位数年份
        year_match = re.search(r'\b(19|20)\d{2}\b', str(date_str))
        if year_match:
            return int(year_match.group())
        
        return 2023  # 默认年份
    
    def process_and_save(self, output_path: Path = None):
        """
        处理整个数据集并保存为 JSONL
        
        Args:
            output_path: 输出文件路径，默认使用配置中的路径
        """
        if self.df is None:
            raise ValueError("数据集尚未加载，请先调用 load_dataset()")
        
        if output_path is None:
            output_path = self.config.OUTPUT_JSONL
        
        print(f"\n正在处理数据集...")
        all_documents = []
        
        total = len(self.df)
        
        # 使用简单的进度显示（避免 tqdm 在某些环境下的问题）
        for idx, row in self.df.iterrows():
            try:
                documents = self.process_row(row, idx)
                all_documents.extend(documents)
                
                # 每处理 50 条显示一次进度
                if (idx + 1) % 50 == 0 or idx == 0:
                    print(f"  处理进度: {idx + 1}/{total} ({(idx + 1)/total*100:.1f}%)")
                
            except Exception as e:
                print(f"\n警告: 处理第 {idx} 行时出错: {str(e)}")
                continue
        
        # 保存为 JSONL
        print(f"\n正在保存到 {output_path}...")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for doc in all_documents:
                    f.write(json.dumps(doc, ensure_ascii=False) + '\n')
            
            print(f"✓ 成功保存 {len(all_documents)} 个文档块到 {output_path}")
            
        except Exception as e:
            print(f"✗ 保存文件失败: {str(e)}")
            raise
    
    def run(self):
        """运行完整的预处理流程"""
        print("=" * 60)
        print("Phase 1: 文档预处理 (本地)")
        print("=" * 60)
        
        # 创建必要的目录
        self.config.setup_directories()
        
        # 加载数据集
        self.load_dataset()
        
        # 处理并保存
        self.process_and_save()
        
        print("\n✓ Phase 1 完成!")
        print(f"输出文件: {self.config.OUTPUT_JSONL}")


def main():
    """主函数"""
    preprocessor = DocumentPreprocessor()
    preprocessor.run()


if __name__ == "__main__":
    main()

