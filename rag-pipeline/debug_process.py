"""
调试处理流程 - 找出卡住的原因
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from preprocessing import DocumentPreprocessor
import time


def debug_process():
    """调试处理流程"""
    print("=" * 60)
    print("调试处理流程")
    print("=" * 60)
    
    preprocessor = DocumentPreprocessor()
    
    # 加载数据集
    print("\n1. 加载数据集...")
    df = preprocessor.load_dataset()
    
    print(f"\n2. 开始处理前 5 条记录...")
    print(f"DataFrame 类型: {type(df)}")
    print(f"DataFrame 长度: {len(df)}")
    
    # 测试迭代
    print("\n3. 测试 df.iterrows()...")
    count = 0
    start_time = time.time()
    
    try:
        for idx, row in df.iterrows():
            count += 1
            print(f"  处理第 {idx} 行... (count={count})")
            
            # 处理这一行
            documents = preprocessor.process_row(row, idx)
            print(f"    -> 生成 {len(documents)} 个文档块")
            
            if count >= 5:
                print(f"\n✓ 成功处理前 5 条记录")
                break
            
            # 检查是否卡住
            elapsed = time.time() - start_time
            if elapsed > 10:
                print(f"\n⚠️  警告: 处理 {count} 条记录用了 {elapsed:.1f} 秒")
                break
    
    except Exception as e:
        print(f"\n✗ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    elapsed = time.time() - start_time
    print(f"\n处理 {count} 条记录用时: {elapsed:.2f} 秒")
    print(f"平均每条: {elapsed/count:.2f} 秒")


if __name__ == "__main__":
    debug_process()

