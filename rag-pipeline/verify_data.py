"""
快速验证脚本 - 检查处理后的数据是否正确
"""
import json
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import Config


def verify_jsonl():
    """验证 JSONL 文件内容"""
    jsonl_path = Config.OUTPUT_JSONL
    
    if not jsonl_path.exists():
        print(f"✗ 文件不存在: {jsonl_path}")
        print("请先运行: python main.py --phase1")
        return
    
    print("=" * 60)
    print("验证 JSONL 数据")
    print("=" * 60)
    
    # 读取前几条记录
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 3:  # 只显示前 3 条
                break
            
            doc = json.loads(line)
            
            print(f"\n记录 {i+1}:")
            print(f"  ID: {doc['id']}")
            print(f"  标题: {doc['metadata']['title']}")
            print(f"  行业: {doc['metadata']['industry']}")
            print(f"  年份: {doc['metadata']['year']}")
            print(f"  URL: {doc['metadata']['source_url'][:50]}..." if doc['metadata']['source_url'] else "  URL: (无)")
            print(f"  文本长度: {len(doc['text'])} 字符")
            print(f"  文本预览: {doc['text'][:150]}...")
    
    # 统计信息
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f)
    
    print("\n" + "=" * 60)
    print(f"✓ 总共 {total_lines} 个文档块")
    print("=" * 60)
    
    # 检查是否有空内容
    empty_count = 0
    placeholder_count = 0
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            doc = json.loads(line)
            if not doc['text'] or doc['text'] == 'nan':
                empty_count += 1
            if doc['text'].startswith('Document '):
                placeholder_count += 1
    
    if empty_count > 0:
        print(f"⚠️  警告: 发现 {empty_count} 个空文本块")
    
    if placeholder_count > 0:
        print(f"⚠️  警告: 发现 {placeholder_count} 个占位符文本（'Document X'）")
        print("   这表示数据没有正确提取，请检查列名映射")
    else:
        print("✓ 所有文本块都包含真实内容")


def verify_source_data():
    """验证源数据集"""
    print("\n" + "=" * 60)
    print("验证源数据集")
    print("=" * 60)
    
    try:
        from preprocessing import DocumentPreprocessor
        
        preprocessor = DocumentPreprocessor()
        df = preprocessor.load_dataset()
        
        print(f"\n数据集信息:")
        print(f"  总行数: {len(df)}")
        print(f"  列名: {df.columns.tolist()}")
        
        # 显示第一行数据（检查内容）
        if len(df) > 0:
            print(f"\n第一行数据示例:")
            first_row = df.iloc[0]
            for col in df.columns:
                value = str(first_row[col])
                if len(value) > 100:
                    value = value[:100] + "..."
                print(f"  {col}: {value}")
        
    except Exception as e:
        print(f"✗ 加载数据集失败: {str(e)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='验证 RAG 管道数据')
    parser.add_argument('--source', action='store_true', help='验证源数据集')
    parser.add_argument('--processed', action='store_true', help='验证处理后的 JSONL')
    
    args = parser.parse_args()
    
    if not (args.source or args.processed):
        # 默认验证处理后的数据
        verify_jsonl()
    else:
        if args.source:
            verify_source_data()
        if args.processed:
            verify_jsonl()

