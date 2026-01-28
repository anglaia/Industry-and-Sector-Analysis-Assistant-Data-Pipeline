"""爬虫模块（简化版 - 只保留Playwright爬虫）"""
from .mckinsey_playwright_scraper import McKinseyPlaywrightScraper
from .playwright_base_scraper import PlaywrightBaseScraper

__all__ = ['McKinseyPlaywrightScraper', 'PlaywrightBaseScraper']

