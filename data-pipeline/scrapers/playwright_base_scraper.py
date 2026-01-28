"""
基于 Playwright 的爬虫基类
使用真实浏览器来绕过反爬虫机制
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import time
from utils.logger import logger
from utils.file_utils import FileUtils


class PlaywrightBaseScraper(ABC):
    """
    基于 Playwright 的基础爬虫类
    使用真实浏览器来爬取网站
    """
    
    def __init__(
        self,
        name: str,
        base_url: str,
        delay: float = 3.0,
        headless: bool = True,
        browser_type: str = "chromium"  # chromium, firefox, webkit
    ):
        """
        初始化 Playwright 爬虫
        
        Args:
            name: 爬虫名称
            base_url: 基础 URL
            delay: 请求延迟（秒）
            headless: 是否无头模式
            browser_type: 浏览器类型
        """
        self.name = name
        self.base_url = base_url
        self.delay = delay
        self.headless = headless
        self.browser_type = browser_type
        
        # Playwright 对象
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        logger.info(f"Initialized Playwright scraper: {self.name}")
    
    def start(self):
        """启动浏览器"""
        try:
            self.playwright = sync_playwright().start()
            
            # 选择浏览器
            if self.browser_type == "firefox":
                browser_launcher = self.playwright.firefox
            elif self.browser_type == "webkit":
                browser_launcher = self.playwright.webkit
            else:
                browser_launcher = self.playwright.chromium
            
            # 启动浏览器
            self.browser = browser_launcher.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            # 创建上下文（模拟真实浏览器环境）
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                }
            )
            
            # 创建页面
            self.page = self.context.new_page()
            
            # 隐藏 webdriver 特征
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // 覆盖 plugins 和 languages
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Chrome 特征
                window.chrome = {
                    runtime: {}
                };
            """)
            
            logger.info(f"Browser started: {self.browser_type}")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise
    
    def handle_cookie_popup(self, timeout: int = 5000):
        """
        处理常见的 Cookie 弹窗
        
        Args:
            timeout: 等待超时时间（毫秒）
        """
        if not self.page:
            return
        
        # 常见的 Cookie 同意按钮选择器
        cookie_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button:has-text("I agree")',
            'button:has-text("同意")',
            '#onetrust-accept-btn-handler',
            '#accept-recommended-btn-handler',
            '.cookie-consent-accept',
            '[aria-label*="Accept"]',
            '[id*="accept"]',
        ]
        
        for selector in cookie_selectors:
            try:
                button = self.page.locator(selector).first
                if button.is_visible(timeout=timeout):
                    logger.info(f"🍪 Found cookie popup, clicking: {selector}")
                    button.click(timeout=timeout)
                    time.sleep(1)
                    logger.info("✅ Cookie popup dismissed")
                    return
            except Exception:
                continue
        
        logger.debug("No cookie popup found (this is OK)")
    
    def get_page(self, url: str, wait_selector: Optional[str] = None, max_retries: int = 3, wait_for_network_idle: bool = False) -> bool:
        """
        访问页面
        
        Args:
            url: 页面 URL
            wait_selector: 等待的选择器（可选）
            max_retries: 最大重试次数
            wait_for_network_idle: 是否等待网络空闲（默认 False，因为很多网站会一直有后台请求）
            
        Returns:
            是否成功
        """
        if not self.page:
            self.start()
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to {url} (attempt {attempt + 1}/{max_retries})")
                
                # 导航到页面，等待 load 事件即可
                response = self.page.goto(url, wait_until='load', timeout=60000)
                
                if response and response.status >= 400:
                    logger.warning(f"Got status {response.status} for {url}")
                    if attempt < max_retries - 1:
                        time.sleep(self.delay * (attempt + 1))
                        continue
                    return False
                
                logger.info(f"Page loaded with status {response.status if response else 'unknown'}")
                
                # 等待指定选择器
                if wait_selector:
                    logger.info(f"Waiting for selector: {wait_selector}")
                    self.page.wait_for_selector(wait_selector, timeout=10000)
                
                # 可选：等待网络空闲（大多数情况不需要）
                if wait_for_network_idle:
                    try:
                        self.page.wait_for_load_state('networkidle', timeout=10000)
                    except Exception as e:
                        logger.debug(f"Network idle timeout (this is usually OK): {e}")
                else:
                    # 简单等待一下让页面渲染
                    time.sleep(2)
                
                # 礼貌性延迟
                time.sleep(self.delay)
                
                logger.info(f"✅ Successfully loaded: {url}")
                return True
                
            except Exception as e:
                logger.warning(f"Failed to load {url} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = self.delay * (attempt + 2)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to load {url} after {max_retries} attempts")
                    return False
        
        return False
    
    def scroll_page(self, scroll_times: int = 3):
        """
        滚动页面以加载动态内容
        
        Args:
            scroll_times: 滚动次数
        """
        if not self.page:
            return
        
        for i in range(scroll_times):
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            logger.debug(f"Scrolled page {i + 1}/{scroll_times}")
    
    def get_html(self) -> str:
        """
        获取当前页面的 HTML
        
        Returns:
            HTML 内容
        """
        if not self.page:
            return ""
        return self.page.content()
    
    def download_file(self, url: str, save_path: Path) -> bool:
        """
        下载文件
        
        Args:
            url: 文件 URL
            save_path: 保存路径
            
        Returns:
            是否成功
        """
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用 page 的下载功能
            with self.page.expect_download() as download_info:
                self.page.goto(url)
            
            download = download_info.value
            download.save_as(save_path)
            
            file_size = FileUtils.get_file_size_mb(save_path)
            logger.info(f"Downloaded {url} to {save_path} ({file_size:.2f} MB)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            if save_path.exists():
                save_path.unlink()
            return False
    
    def take_screenshot(self, save_path: Path, full_page: bool = True):
        """
        截图
        
        Args:
            save_path: 保存路径
            full_page: 是否全页截图
        """
        if not self.page:
            return
        
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            self.page.screenshot(path=str(save_path), full_page=full_page)
            logger.info(f"Screenshot saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
    
    @abstractmethod
    def scrape(self, max_items: Optional[int] = None) -> List[Dict]:
        """
        执行爬取（由子类实现）
        
        Args:
            max_items: 最大爬取数量
            
        Returns:
            爬取的数据列表
        """
        pass
    
    def save_results(self, results: List[Dict], output_file: Path):
        """
        保存爬取结果到 JSON 文件
        
        Args:
            results: 结果列表
            output_file: 输出文件路径
        """
        import json
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(results)} results to {output_file}")
    
    def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            
            logger.info(f"Closed Playwright scraper: {self.name}")
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()

