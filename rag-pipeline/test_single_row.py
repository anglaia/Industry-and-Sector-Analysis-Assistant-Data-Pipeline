"""
测试单条数据处理 - 快速诊断问题
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from preprocessing import DocumentPreprocessor


def test_single_row():
    """测试处理单条记录"""
    print("=" * 60)
    print("测试单条数据处理")
    print("=" * 60)
    
    preprocessor = DocumentPreprocessor()
    
    # 加载数据集
    print("\n1. 加载数据集...")
    df = preprocessor.load_dataset()
    
    if len(df) == 0:
        print("✗ 数据集为空")
        return
    
    # 测试第一条记录
    print("\n2. 测试处理第一条记录...")
    first_row = df.iloc[0]
    
    print(f"\n原始数据:")
    print(f"  Article Header: {first_row.get('Article Header', 'N/A')}")
    print(f"  Article Body 长度: {len(str(first_row.get('Article Body', '')))} 字符")
    print(f"  Published Date: {first_row.get('Published Date', 'N/A')}")
    print(f"  URL: {first_row.get('URL', 'N/A')}")
    
    try:
        print("\n3. 开始处理...")
        documents = preprocessor.process_row(first_row, 0)
        
        print(f"\n✓ 处理成功！生成了 {len(documents)} 个文档块")
        
        if documents:
            print(f"\n第一个文档块:")
            doc = documents[0]
            print(f"  ID: {doc['id']}")
            print(f"  标题: {doc['metadata']['title']}")
            print(f"  年份: {doc['metadata']['year']}")
            print(f"  文本长度: {len(doc['text'])} 字符")
            print(f"  文本预览: {doc['text'][:200]}...")
        
    except Exception as e:
        print(f"\n✗ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_single_row()

