"""
AI RAG 快速构建工具（简化版）
专注于AI行业文章的采集和向量化

使用示例:
    python run_ai_rag.py --articles 10
    python run_ai_rag.py --articles 20 --no-headless  # 显示浏览器
    python run_ai_rag.py --preview-only  # 只预览不上传
"""
import argparse
from pathlib import Path
from datetime import datetime
from scrapers.mckinsey_playwright_scraper import McKinseyPlaywrightScraper
from ingest.batch_processor import BatchProcessor
from utils.logger import logger
from config.settings import settings
import json

# AI 关键词列表（用于过滤）
AI_KEYWORDS = [
    "artificial intelligence", "AI", "machine learning", "deep learning",
    "neural network", "generative AI", "large language model", "LLM",
    "GPT", "transformer", "computer vision", "natural language processing",
    "reinforcement learning", "AI ethics", "AI strategy", "AI implementation"
]


def is_ai_relevant(text: str, threshold: int = 2) -> bool:
    """
    检查文章是否与AI相关
    
    Args:
        text: 文章文本
        threshold: 至少包含多少个AI关键词
        
    Returns:
        是否与AI相关
    """
    if not text:
        return False
    
    text_lower = text.lower()
    count = sum(1 for keyword in AI_KEYWORDS if keyword.lower() in text_lower)
    return count >= threshold


def filter_ai_articles(articles: list) -> list:
    """
    过滤出与AI相关的文章
    
    Args:
        articles: 文章列表
        
    Returns:
        过滤后的文章列表
    """
    filtered = []
    
    for article in articles:
        # 检查标题和内容
        title = article.get('title', '')
        content = article.get('content', '')
        full_text = f"{title} {content}"
        
        if is_ai_relevant(full_text):
            filtered.append(article)
            logger.info(f"✅ AI相关: {title[:60]}...")
        else:
            logger.debug(f"⏭️  跳过非AI文章: {title[:60]}...")
    
    return filtered


def run_scraping(max_articles: int, headless: bool = True, ai_filter: bool = True):
    """
    运行爬虫采集AI文章
    
    Args:
        max_articles: 最大文章数
        headless: 是否无头模式
        ai_filter: 是否启用AI过滤
        
    Returns:
        采集到的文章列表
    """
    logger.info("=" * 70)
    logger.info("🔍 步骤 1/2: 开始爬取McKinsey AI文章")
    logger.info("=" * 70)
    
    scraper = McKinseyPlaywrightScraper(headless=headless)
    
    try:
        # 爬取文章
        articles = scraper.scrape(max_items=max_articles)
        
        if not articles:
            logger.error("❌ 未找到任何文章")
            return []
        
        logger.info(f"✅ 爬取到 {len(articles)} 篇文章")
        
        # AI过滤
        if ai_filter:
            logger.info("\n🎯 应用AI关键词过滤...")
            articles = filter_ai_articles(articles)
            logger.info(f"✅ 过滤后剩余 {len(articles)} 篇AI相关文章")
        
        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = settings.processed_files_path / f"mckinsey_ai_{timestamp}.json"
        scraper.save_results(articles, output_file)
        logger.info(f"💾 结果已保存到: {output_file.name}")
        
        return articles
        
    finally:
        scraper.close()


def run_ingestion(articles: list, preview_only: bool = False):
    """
    运行向量化并上传到Pinecone
    
    Args:
        articles: 文章列表
        preview_only: 仅预览，不实际上传
        
    Returns:
        摄取结果
    """
    if not articles:
        logger.warning("⚠️  没有文章需要处理")
        return None
    
    logger.info("\n" + "=" * 70)
    logger.info("🚀 步骤 2/2: 向量化处理并上传到Pinecone")
    logger.info("=" * 70)
    
    if preview_only:
        logger.info("📋 预览模式 - 只显示统计信息，不上传")
        total_chars = sum(len(a.get('content', '')) for a in articles)
        logger.info(f"📊 统计:")
        logger.info(f"   - 文章数: {len(articles)}")
        logger.info(f"   - 总字符数: {total_chars:,}")
        logger.info(f"   - 预计chunks: ~{total_chars // 2000}")
        return None
    
    # 准备文档数据
    documents = []
    for i, article in enumerate(articles, 1):
        content = article.get('content', '')
        if not content or len(content) < 200:
            logger.warning(f"⏭️  跳过内容过短的文章: {article.get('title', 'Unknown')[:50]}")
            continue
        
        doc_data = {
            'text': content,
            'file_id': f"mckinsey_ai_{datetime.now().strftime('%Y%m%d')}_{i}",
            'industry': 'AI',
            'metadata': {
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'author': article.get('author', ''),
                'date': article.get('date', ''),
                'source': 'McKinsey AI',
                'collection_date': datetime.now().isoformat()
            }
        }
        documents.append(doc_data)
    
    if not documents:
        logger.error("❌ 没有有效的文档可以处理")
        return None
    
    logger.info(f"📦 准备处理 {len(documents)} 篇文章...")
    
    # 批量摄取
    try:
        processor = BatchProcessor()
        result = processor.ingester.ingest_batch(documents)
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ 完成！RAG库已更新")
        logger.info("=" * 70)
        logger.info(f"📊 摄取统计:")
        logger.info(f"   - 总文章数: {result['total']}")
        logger.info(f"   - 成功: {result['successful']}")
        logger.info(f"   - 失败: {result['failed']}")
        logger.info(f"   - 总chunks: {result['total_chunks']}")
        logger.info(f"\n🎉 你现在可以在backend-ai中查询这些AI行业内容了!")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 摄取失败: {e}", exc_info=True)
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI RAG 快速构建工具 - 专注于AI行业文章采集和向量化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 采集10篇AI文章并上传
  python run_ai_rag.py --articles 10
  
  # 采集20篇文章，显示浏览器（调试用）
  python run_ai_rag.py --articles 20 --no-headless
  
  # 只预览不上传
  python run_ai_rag.py --articles 5 --preview-only
  
  # 关闭AI过滤，采集所有文章
  python run_ai_rag.py --articles 15 --no-filter
        """
    )
    
    parser.add_argument(
        '--articles',
        type=int,
        default=10,
        help='采集文章数量 (默认: 10)'
    )
    
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='显示浏览器窗口（用于调试）'
    )
    
    parser.add_argument(
        '--preview-only',
        action='store_true',
        help='只预览统计信息，不上传到Pinecone'
    )
    
    parser.add_argument(
        '--no-filter',
        action='store_true',
        help='关闭AI关键词过滤，采集所有McKinsey文章'
    )
    
    args = parser.parse_args()
    
    # 验证API密钥
    if not settings.validate_required_keys():
        logger.error("❌ 请先配置 PINECONE_API_KEY 和 GOOGLE_API_KEY")
        return 1
    
    # 显示配置
    logger.info("=" * 70)
    logger.info("🤖 AI RAG 快速构建工具")
    logger.info("=" * 70)
    logger.info(f"📝 配置:")
    logger.info(f"   - 采集数量: {args.articles} 篇")
    logger.info(f"   - 浏览器模式: {'可见' if not args.no_headless else '无头'}")
    logger.info(f"   - AI过滤: {'开启' if not args.no_filter else '关闭'}")
    logger.info(f"   - 预览模式: {'是' if args.preview_only else '否'}")
    logger.info(f"   - Pinecone索引: {settings.pinecone_index_name}")
    logger.info("")
    
    try:
        # 步骤1: 爬取文章
        articles = run_scraping(
            max_articles=args.articles,
            headless=not args.no_headless,
            ai_filter=not args.no_filter
        )
        
        if not articles:
            logger.error("❌ 未采集到任何文章，退出")
            return 1
        
        # 步骤2: 向量化并上传
        result = run_ingestion(articles, preview_only=args.preview_only)
        
        if result or args.preview_only:
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  用户中断操作")
        return 1
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

