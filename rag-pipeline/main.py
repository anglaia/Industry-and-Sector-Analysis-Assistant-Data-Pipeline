"""
RAG 数据处理管道主入口
运行完整的两阶段处理流程
"""
import argparse
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from preprocessing import DocumentPreprocessor
from ingestion import VectorIngestion
from config import Config


def run_phase1():
    """运行 Phase 1: 文档预处理"""
    try:
        preprocessor = DocumentPreprocessor()
        preprocessor.run()
        return True
    except Exception as e:
        print(f"\n✗ Phase 1 失败: {str(e)}")
        return False


def run_phase2():
    """运行 Phase 2: 向量摄取"""
    try:
        ingestion = VectorIngestion()
        ingestion.run()
        return True
    except Exception as e:
        print(f"\n✗ Phase 2 失败: {str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='RAG 数据处理管道',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行完整流程
  python main.py --all
  
  # 只运行预处理
  python main.py --phase1
  
  # 只运行向量摄取
  python main.py --phase2
        """
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='运行完整的两阶段流程'
    )
    
    parser.add_argument(
        '--phase1',
        action='store_true',
        help='只运行 Phase 1: 文档预处理'
    )
    
    parser.add_argument(
        '--phase2',
        action='store_true',
        help='只运行 Phase 2: 向量摄取'
    )
    
    args = parser.parse_args()
    
    # 如果没有指定任何参数，显示帮助信息
    if not (args.all or args.phase1 or args.phase2):
        parser.print_help()
        return
    
    print("=" * 60)
    print("RAG 数据处理管道")
    print("=" * 60)
    print()
    
    # 运行指定的阶段
    if args.all:
        print("运行模式: 完整流程 (Phase 1 + Phase 2)\n")
        
        # Phase 1
        success = run_phase1()
        if not success:
            print("\n流程中断: Phase 1 失败")
            return
        
        print("\n" + "=" * 60 + "\n")
        
        # Phase 2
        success = run_phase2()
        if not success:
            print("\n流程中断: Phase 2 失败")
            return
        
        print("\n" + "=" * 60)
        print("✓ 完整流程执行成功!")
        print("=" * 60)
    
    elif args.phase1:
        print("运行模式: Phase 1 (文档预处理)\n")
        run_phase1()
    
    elif args.phase2:
        print("运行模式: Phase 2 (向量摄取)\n")
        
        # 检查 Phase 1 的输出文件是否存在
        if not Config.OUTPUT_JSONL.exists():
            print(f"✗ 错误: 找不到预处理输出文件: {Config.OUTPUT_JSONL}")
            print("请先运行 Phase 1 (--phase1) 或完整流程 (--all)")
            return
        
        run_phase2()


if __name__ == "__main__":
    main()

