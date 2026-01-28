# Playwright 爬虫使用指南

## 📋 简介

由于 McKinsey 网站有反爬虫机制，普通的 `requests` 库无法访问。因此我们使用 **Playwright** 来模拟真实浏览器进行爬取。

## 🚀 安装 Playwright 浏览器

在使用 Playwright 爬虫之前，需要先安装浏览器驱动：

```bash
# 1. 确保已安装 playwright 包（已在 requirements.txt 中）
pip install playwright==1.40.0

# 2. 安装浏览器驱动（首次使用必须执行）
python -m playwright install chromium

# 可选：安装所有浏览器
python -m playwright install
```

### Windows 特别说明
在 Windows 上可能需要管理员权限：
```powershell
# 以管理员身份运行 PowerShell
python -m playwright install chromium
```

## 📖 使用方法

### 方法 1: 使用命令行脚本（推荐）

```bash
# 基本用法（默认使用 Playwright，无头模式）
python run_scrapers.py --source mckinsey --limit 5

# 显示浏览器窗口（用于调试）
python run_scrapers.py --source mckinsey --limit 5 --no-headless

# 爬取更多文章
python run_scrapers.py --source mckinsey --limit 10
```

### 方法 2: 测试脚本

```bash
# 运行测试脚本（会显示浏览器窗口）
python test_playwright_scraper.py
```

### 方法 3: 在代码中使用

```python
from scrapers.mckinsey_playwright_scraper import McKinseyPlaywrightScraper
from config.settings import settings

# 创建爬虫实例
scraper = McKinseyPlaywrightScraper(headless=True)

try:
    # 爬取文章
    results = scraper.scrape(max_items=5)
    
    # 保存结果
    output_file = settings.processed_files_path / "mckinsey_articles.json"
    scraper.save_results(results, output_file)
    
    print(f"成功爬取 {len(results)} 篇文章")
    
finally:
    scraper.close()
```

## ⚙️ 配置选项

### 爬虫参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `headless` | 是否无头模式（不显示浏览器） | `True` |
| `max_items` | 最大爬取文章数量 | `10` |
| `delay` | 请求间隔延迟（秒） | `5.0` |
| `browser_type` | 浏览器类型 | `chromium` |

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--source mckinsey` | 指定爬取 McKinsey | 必需 |
| `--limit N` | 爬取数量限制 | `--limit 10` |
| `--no-headless` | 显示浏览器窗口 | `--no-headless` |

## 🎯 功能特性

### ✅ 已实现

1. **真实浏览器模拟** - 使用 Playwright 模拟真实 Chrome 浏览器
2. **反爬虫绕过** - 隐藏 webdriver 特征，添加真实浏览器指纹
3. **自动滚动** - 自动滚动页面加载动态内容
4. **智能重试** - 失败自动重试，增加延迟
5. **截图调试** - 自动保存页面截图用于调试
6. **完整数据提取** - 提取标题、日期、作者、内容、标签等

### 📊 提取的数据

每篇文章包含以下字段：
```json
{
  "title": "文章标题",
  "url": "文章链接",
  "date": "发布日期",
  "authors": ["作者1", "作者2"],
  "content": "文章内容（前5000字符）",
  "industries": ["行业标签1", "行业标签2"],
  "pdf_url": "PDF下载链接（如果有）",
  "source": "McKinsey Insights",
  "scraped_at": "爬取时间"
}
```

## 🐛 调试技巧

### 1. 显示浏览器窗口
```bash
python run_scrapers.py --source mckinsey --limit 2 --no-headless
```

### 2. 查看截图
爬虫会自动保存截图到：
```
data-pipeline/storage/raw/mckinsey_reports/debug_insights_page.png
```

### 3. 查看日志
日志文件位置：
```
data-pipeline/storage/logs/data_pipeline_YYYY-MM-DD.log
```

### 4. 测试网络连接
```bash
python test_mckinsey_connection.py
```

## ⚠️ 常见问题

### Q1: 提示 "playwright not installed"
**解决方案：**
```bash
python -m playwright install chromium
```

### Q2: 爬取失败或超时
**可能原因：**
- 网络连接不稳定
- 网站临时不可访问
- 反爬虫机制升级

**解决方案：**
1. 增加延迟时间（修改 `delay` 参数）
2. 使用 VPN 或代理
3. 减少爬取数量
4. 使用 `--no-headless` 查看浏览器行为

### Q3: Windows 上权限错误
**解决方案：**
以管理员身份运行 PowerShell

### Q4: 找不到浏览器驱动
**解决方案：**
```bash
# 重新安装浏览器驱动
python -m playwright install --force chromium
```

## 📝 注意事项

1. **合法性**: 此爬虫仅用于教育和研究目的，请遵守网站的服务条款和 robots.txt
2. **频率限制**: 使用较大的延迟（5秒以上），避免对服务器造成压力
3. **礼貌性**: 不要进行大规模爬取，建议单次爬取不超过 20 篇文章
4. **数据使用**: 爬取的数据仅供学习研究使用，不得用于商业目的

## 🔧 高级配置

### 使用代理
```python
scraper = McKinseyPlaywrightScraper(headless=True)
scraper.context = scraper.browser.new_context(
    proxy={"server": "http://proxy-server:port"}
)
```

### 修改浏览器类型
```python
# 使用 Firefox
scraper = McKinseyPlaywrightScraper(headless=True)
scraper.browser_type = "firefox"
```

### 增加等待时间
修改 `scrapers/mckinsey_playwright_scraper.py` 中的 `delay` 参数：
```python
super().__init__(
    name="McKinsey Insights (Playwright)",
    base_url="https://www.mckinsey.com",
    delay=10.0,  # 增加到 10 秒
    ...
)
```

## 📚 参考资源

- [Playwright 官方文档](https://playwright.dev/python/)
- [Playwright 反爬虫技巧](https://playwright.dev/python/docs/emulation)
- [项目 QUICKSTART](./QUICKSTART.md)

