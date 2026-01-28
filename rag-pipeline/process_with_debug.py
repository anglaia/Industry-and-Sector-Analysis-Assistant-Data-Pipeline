"""
带详细调试信息的处理脚本
"""
import sys
import json
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from preprocessing import DocumentPreprocessor
from config import Config


def process_with_debug():
    """带调试信息的处理"""
    print("=" * 60)
    print("Phase 1: 文档预处理 (带调试)")
    print("=" * 60)
    
    preprocessor = DocumentPreprocessor()
    
    # 创建必要的目录
    Config.setup_directories()
    
    # 加载数据集
    preprocessor.load_dataset()
    df = preprocessor.df
    
    print(f"\n正在处理数据集...")
    all_documents = []
    
    total = len(df)
    start_time = time.time()
    last_time = start_time
    
    # 使用 iloc 而不是 iterrows
    for i in range(total):
        try:
            current_time = time.time()
            elapsed = current_time - last_time
            
            # 如果单条记录处理超过 5 秒，发出警告
            if i > 0 and elapsed > 5:
                print(f"  ⚠️  警告: 第 {i-1} 条记录处理用时 {elapsed:.1f} 秒")
            
            row = df.iloc[i]
            
            # 显示当前处理的记录信息
            if i < 5 or i % 10 == 0:
                title = str(row.get('Article Header', ''))[:50]
                print(f"  [{i}/{total}] 正在处理: {title}...")
            
            documents = preprocessor.process_row(row, i)
            all_documents.extend(documents)
            
            last_time = current_time
            
            # 每 50 条显示一次进度
            if (i + 1) % 50 == 0:
                elapsed_total = time.time() - start_time
                avg_time = elapsed_total / (i + 1)
                remaining = (total - i - 1) * avg_time
                print(f"  处理进度: {i + 1}/{total} ({(i + 1)/total*100:.1f}%) - 预计剩余: {remaining/60:.1f} 分钟")
            
        except Exception as e:
            print(f"\n✗ 处理第 {i} 行时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    # 保存为 JSONL
    output_path = Config.OUTPUT_JSONL
    print(f"\n正在保存到 {output_path}...")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for doc in all_documents:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
        
        print(f"✓ 成功保存 {len(all_documents)} 个文档块到 {output_path}")
        
        total_time = time.time() - start_time
        print(f"\n总用时: {total_time/60:.1f} 分钟")
        print(f"平均每条: {total_time/total:.2f} 秒")
        
    except Exception as e:
        print(f"✗ 保存文件失败: {str(e)}")
        raise


if __name__ == "__main__":
    process_with_debug()

