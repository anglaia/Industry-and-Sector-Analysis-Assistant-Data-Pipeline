"""
使用示例：展示如何在代码中使用各个模块
"""
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from preprocessing import DocumentPreprocessor
from ingestion import VectorIngestion
from config import Config


def example_full_pipeline():
    """示例：运行完整的管道"""
    print("示例 1: 运行完整的 RAG 管道")
    print("=" * 60)
    
    # Phase 1: 预处理
    print("\n[Phase 1] 文档预处理")
    preprocessor = DocumentPreprocessor()
    preprocessor.run()
    
    # Phase 2: 向量摄取
    print("\n[Phase 2] 向量摄取")
    ingestion = VectorIngestion()
    ingestion.run()
    
    print("\n✓ 完整管道执行成功!")


def example_custom_preprocessing():
    """示例：自定义预处理流程"""
    print("示例 2: 自定义预处理")
    print("=" * 60)
    
    preprocessor = DocumentPreprocessor()
    
    # 加载数据集
    df = preprocessor.load_dataset()
    
    # 处理单行数据
    sample_row = df.iloc[0]
    documents = preprocessor.process_row(sample_row, 0)
    
    print(f"\n处理结果示例：")
    for doc in documents[:2]:  # 只显示前两个块
        print(f"\nID: {doc['id']}")
        print(f"文本: {doc['text'][:100]}...")
        print(f"元数据: {doc['metadata']}")


def example_custom_chunking():
    """示例：自定义文本分块"""
    print("示例 3: 自定义文本分块")
    print("=" * 60)
    
    preprocessor = DocumentPreprocessor()
    
    # 测试文本
    test_text = """
    Artificial intelligence is transforming the world. Machine learning algorithms 
    are becoming more sophisticated every day. Deep learning has revolutionized 
    computer vision and natural language processing. The future of AI is bright 
    and full of possibilities.
    """
    
    # 使用不同的分块参数
    chunks_small = preprocessor.chunk_text(test_text, chunk_size=100, overlap=20)
    chunks_large = preprocessor.chunk_text(test_text, chunk_size=200, overlap=50)
    
    print(f"\n小块（100 字符，重叠 20）：{len(chunks_small)} 块")
    for i, chunk in enumerate(chunks_small):
        print(f"  块 {i+1}: {chunk[:50]}...")
    
    print(f"\n大块（200 字符，重叠 50）：{len(chunks_large)} 块")
    for i, chunk in enumerate(chunks_large):
        print(f"  块 {i+1}: {chunk[:50]}...")


def example_embedding_generation():
    """示例：生成嵌入向量"""
    print("示例 4: 生成嵌入向量")
    print("=" * 60)
    
    try:
        ingestion = VectorIngestion()
        
        # 测试文本
        test_texts = [
            "Artificial intelligence is changing the world.",
            "Machine learning algorithms are powerful tools.",
            "Deep learning enables complex pattern recognition."
        ]
        
        print("\n正在生成嵌入向量...")
        embeddings = ingestion.generate_embeddings(test_texts)
        
        print(f"\n✓ 成功生成 {len(embeddings)} 个嵌入向量")
        print(f"向量维度: {len(embeddings[0])}")
        print(f"第一个向量的前 10 个值: {embeddings[0][:10]}")
        
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        print("提示: 确保已设置 GEMINI_API_KEY 环境变量")


def example_read_processed_data():
    """示例：读取已处理的数据"""
    print("示例 5: 读取 JSONL 数据")
    print("=" * 60)
    
    import json
    
    input_path = Config.OUTPUT_JSONL
    
    if not input_path.exists():
        print(f"\n✗ 文件不存在: {input_path}")
        print("请先运行 Phase 1 预处理")
        return
    
    print(f"\n正在读取: {input_path}")
    
    # 读取前 5 条记录
    with open(input_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 5:
                break
            doc = json.loads(line)
            print(f"\n记录 {i+1}:")
            print(f"  ID: {doc['id']}")
            print(f"  文本: {doc['text'][:80]}...")
            print(f"  行业: {doc['metadata']['industry']}")
            print(f"  年份: {doc['metadata']['year']}")
            print(f"  标题: {doc['metadata']['title']}")


def main():
    """主函数"""
    examples = {
        '1': ('运行完整管道', example_full_pipeline),
        '2': ('自定义预处理', example_custom_preprocessing),
        '3': ('自定义文本分块', example_custom_chunking),
        '4': ('生成嵌入向量', example_embedding_generation),
        '5': ('读取已处理数据', example_read_processed_data),
    }
    
    print("\nRAG 管道使用示例")
    print("=" * 60)
    print("\n可用示例:")
    for key, (desc, _) in examples.items():
        print(f"  {key}. {desc}")
    print()
    
    choice = input("请选择示例编号 (1-5) 或按 Enter 退出: ").strip()
    
    if choice in examples:
        _, func = examples[choice]
        print()
        func()
    elif choice:
        print("无效的选择")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

