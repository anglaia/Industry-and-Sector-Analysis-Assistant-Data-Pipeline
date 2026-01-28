"""
McKinsey Insights 爬虫 (Playwright 版本 - 两阶段模式)
阶段一：收割机 - 收集所有文章URL
阶段二：加工厂 - 爬取每篇文章的完整内容
"""
from typing import List, Dict, Optional
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
import re
from .playwright_base_scraper import PlaywrightBaseScraper
from utils.logger import logger
from utils.file_utils import FileUtils
from config.settings import settings
from datetime import datetime


class McKinseyPlaywrightScraper(PlaywrightBaseScraper):
    """
    McKinsey Insights 爬虫（Playwright 版本）
    
    使用真实浏览器来绕过反爬虫机制
    注意：此爬虫仅用于教育和研究目的
    请遵守网站的 robots.txt 和服务条款
    """
    
    def __init__(self, headless: bool = True):
        super().__init__(
            name="McKinsey Insights (Playwright)",
            base_url="https://www.mckinsey.com",
            delay=3.0,  # 礼貌性延迟
            headless=headless,
            browser_type="chromium"
        )
        
        # 输出目录
        self.output_dir = settings.raw_files_path / "mckinsey_reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def scrape(self, max_items: Optional[int] = 10) -> List[Dict]:
        """
        两阶段爬取 McKinsey 报告
        
        阶段一：收集文章URL列表
        阶段二：爬取每篇文章的完整内容
        
        Args:
            max_items: 最大爬取数量
            
        Returns:
            报告信息列表
        """
        # 启动浏览器
        if not self.page:
            self.start()
        
        # 🌾 阶段一：收割机 - 收集文章URL
        logger.info("=" * 60)
        logger.info("🌾 阶段一：收割机 - 收集文章URL列表")
        logger.info("=" * 60)
        
        article_urls = self._collect_article_urls(max_items)
        
        if not article_urls:
            logger.error("❌ 没有找到任何文章链接")
            return []
        
        logger.info(f"✅ 收集到 {len(article_urls)} 个文章链接")
        
        # 🏭 阶段二：加工厂 - 爬取完整内容
        logger.info("")
        logger.info("=" * 60)
        logger.info("🏭 阶段二：加工厂 - 爬取文章完整内容")
        logger.info("=" * 60)
        
        results = []
        for i, url in enumerate(article_urls, 1):
            logger.info(f"\n📖 [{i}/{len(article_urls)}] 处理文章: {url}")
            
            article_data = self._scrape_article_detail(url)
            if article_data:
                results.append(article_data)
                logger.info(f"✅ 成功爬取: {article_data['title'][:50]}...")
            else:
                logger.warning(f"⚠️  跳过文章: {url}")
            
            # 礼貌性延迟
            if i < len(article_urls):
                time.sleep(self.delay)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"🎉 完成！成功爬取 {len(results)}/{len(article_urls)} 篇文章")
        logger.info("=" * 60)
        
        return results
    
    def _collect_article_urls(self, max_items: int) -> List[str]:
        """
        阶段一：从列表页收集文章URL
        
        Args:
            max_items: 最大收集数量
            
        Returns:
            文章URL列表
        """
        insights_url = urljoin(self.base_url, "/featured-insights")
        
        logger.info(f"⏳ 访问列表页: {insights_url}")
        
        # 访问列表页
        if not self.get_page(insights_url):
            logger.error("❌ 无法加载列表页")
            return []
        
        logger.info("✅ 列表页加载成功")
        
        # 🍪 处理 Cookie 弹窗
        logger.info("🍪 检查并处理 Cookie 弹窗...")
        self.handle_cookie_popup()
        time.sleep(2)
        
        # 📜 滚动页面加载更多内容
        logger.info("📜 滚动页面加载更多文章...")
        self.scroll_page(scroll_times=5)
        time.sleep(2)
        
        # 保存调试信息
        screenshot_path = self.output_dir / "stage1_article_list.png"
        self.take_screenshot(screenshot_path)
        logger.info(f"📸 保存截图: {screenshot_path}")
        
        # 获取 HTML
        html = self.get_html()
        if not html or len(html) < 1000:
            logger.error(f"❌ 页面内容异常: {len(html)} bytes")
            return []
        
        # 保存 HTML 用于调试
        html_path = self.output_dir / "stage1_page.html"
        html_path.write_text(html, encoding='utf-8')
        logger.info(f"💾 保存HTML: {html_path}")
        
        # 解析文章链接
        soup = BeautifulSoup(html, 'lxml')
        article_urls = self._extract_article_urls(soup, max_items)
        
        return article_urls
    
    def _extract_article_urls(self, soup: BeautifulSoup, max_items: int) -> List[str]:
        """
        从页面中提取文章详情页URL
        
        Args:
            soup: BeautifulSoup 对象
            max_items: 最大提取数量
            
        Returns:
            文章URL列表
        """
        urls = set()
        
        # 查找所有链接
        all_links = soup.find_all('a', href=True)
        logger.info(f"🔍 页面中共有 {len(all_links)} 个链接")
        
        for link in all_links:
            href = link.get('href', '')
            
            # 过滤出文章链接
            # McKinsey 文章URL通常包含这些模式
            if any(pattern in href for pattern in [
                '/featured-insights/',
                '/our-insights/',
                '/industries/',
                '/business-functions/',
                '/capabilities/'
            ]):
                # 排除非文章链接
                if any(skip in href for skip in [
                    '#', 'javascript:', 'mailto:', 
                    '.pdf', '.jpg', '.png', '.svg',
                    '/search', '/subscribe', '/careers'
                ]):
                    continue
                
                # 构建完整URL
                full_url = urljoin(self.base_url, href)
                
                # 确保是 McKinsey 域名
                if 'mckinsey.com' in full_url:
                    urls.add(full_url)
        
        # 转为列表并限制数量
        url_list = list(urls)[:max_items * 3]  # 多收集一些，因为有些可能无效
        
        logger.info(f"✅ 找到 {len(url_list)} 个候选文章链接")
        
        # 只返回需要的数量
        return url_list[:max_items]
    
    def _scrape_article_detail(self, url: str) -> Optional[Dict]:
        """
        阶段二：爬取单篇文章的完整内容
        
        Args:
            url: 文章详情页URL
            
        Returns:
            清洗后的文章数据
        """
        try:
            # 访问文章页面
            if not self.get_page(url):
                logger.error(f"❌ 无法加载文章: {url}")
                return None
            
            # 处理可能的 Cookie 弹窗
            self.handle_cookie_popup()
            time.sleep(1)
            
            # 等待内容加载
            time.sleep(2)
            
            # 获取HTML
            html = self.get_html()
            if not html or len(html) < 500:
                logger.error(f"❌ 文章内容太短: {len(html)} bytes")
                return None
            
            # 解析内容
            soup = BeautifulSoup(html, 'lxml')
            
            # 提取并清洗数据
            article_data = self._extract_and_clean_article(soup, url)
            
            return article_data
            
        except Exception as e:
            logger.error(f"❌ 爬取文章失败 {url}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def _extract_and_clean_article(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """
        提取并清洗文章数据
        
        Args:
            soup: BeautifulSoup 对象
            url: 文章URL
            
        Returns:
            清洗后的文章数据
        """
        try:
            # 🏷️ 提取标题
            title = self._extract_title(soup)
            if not title or title == "No Title":
                logger.warning("⚠️  未找到标题")
                return None
            
            # 📅 提取日期
            date = self._extract_date(soup)
            
            # ✍️ 提取作者
            authors = self._extract_authors(soup)
            
            # 📝 提取正文（重点！）
            content = self._extract_clean_content(soup)
            
            if not content or len(content) < 100:
                logger.warning(f"⚠️  正文内容太短: {len(content)} 字符")
                return None
            
            # 🏷️ 提取标签
            tags = self._extract_tags(soup)
            
            # 📊 构建数据
            article_data = {
                'title': title,
                'url': url,
                'date': date,
                'authors': authors,
                'content': content,
                'tags': tags,
                'source': 'McKinsey Insights',
                'scraped_at': datetime.now().isoformat(),
                'content_length': len(content),
                'word_count': len(content.split())
            }
            
            logger.info(f"📊 文章统计: {len(content)} 字符, {article_data['word_count']} 单词")
            
            return article_data
            
        except Exception as e:
            logger.error(f"❌ 提取数据失败: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        selectors = [
            'h1.article-title',
            'h1[class*="hero"]',
            'h1[class*="title"]',
            'h1',
            '[data-component*="headline"] h1',
            '[class*="headline"] h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 5:
                    return title
        
        return "No Title"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """提取日期"""
        # 查找 time 标签
        time_elem = soup.find('time')
        if time_elem:
            return time_elem.get('datetime', time_elem.get_text(strip=True))
        
        # 查找包含日期的元素
        date_patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
        ]
        
        text = soup.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return ""
    
    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        """提取作者"""
        authors = []
        
        # 常见的作者选择器
        author_selectors = [
            '[class*="author"]',
            '[data-component*="author"]',
            '.byline'
        ]
        
        for selector in author_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                # 过滤掉太短或太长的文本
                if text and 3 < len(text) < 50 and 'by' not in text.lower():
                    authors.append(text)
        
        return list(set(authors))[:5]  # 去重并限制数量
    
    def _extract_clean_content(self, soup: BeautifulSoup) -> str:
        """
        提取并清洗正文内容
        
        这是最重要的函数！确保提取高质量的正文
        """
        # 移除不需要的元素
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # 尝试查找文章正文容器
        content_selectors = [
            'article',
            '[class*="article-body"]',
            '[class*="content-body"]',
            '[data-component*="body"]',
            '[class*="rich-text"]',
            'main',
        ]
        
        content_container = None
        for selector in content_selectors:
            container = soup.select_one(selector)
            if container:
                content_container = container
                break
        
        if not content_container:
            # 如果找不到容器，使用整个body
            content_container = soup.find('body')
        
        if not content_container:
            return ""
        
        # 提取所有段落
        paragraphs = []
        for p in content_container.find_all(['p', 'h2', 'h3', 'h4', 'li']):
            text = p.get_text(strip=True)
            
            # 过滤掉太短的段落和导航文本
            if len(text) > 20 and not any(skip in text.lower() for skip in [
                'cookie', 'subscribe', 'sign up', 'download', 'share',
                'related', 'read more', 'learn more'
            ]):
                paragraphs.append(text)
        
        # 合并段落
        content = '\n\n'.join(paragraphs)
        
        # 清理多余空白
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r' {2,}', ' ', content)
        
        return content.strip()
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """提取标签/行业分类"""
        tags = []
        
        tag_selectors = [
            '[class*="tag"]',
            '[class*="topic"]',
            '[class*="category"]',
            '[data-component*="tag"]'
        ]
        
        for selector in tag_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                if text and 2 < len(text) < 30:
                    tags.append(text)
        
        return list(set(tags))[:10]  # 去重并限制数量


# 使用示例
if __name__ == "__main__":
    scraper = McKinseyPlaywrightScraper(headless=False)
    
    try:
        # 爬取前 3 篇文章
        results = scraper.scrape(max_items=3)
        
        # 保存结果
        output_file = settings.processed_files_path / f"mckinsey_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        scraper.save_results(results, output_file)
        
        print(f"\n✅ 成功爬取 {len(results)} 篇文章")
        print(f"📁 保存到: {output_file}")
        
        # 显示统计
        if results:
            total_chars = sum(r['content_length'] for r in results)
            total_words = sum(r['word_count'] for r in results)
            print(f"\n📊 总计: {total_chars:,} 字符, {total_words:,} 单词")
        
    finally:
        scraper.close()
