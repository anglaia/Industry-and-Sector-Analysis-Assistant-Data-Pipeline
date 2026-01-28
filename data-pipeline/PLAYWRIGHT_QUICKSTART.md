# 🚀 快速开始 - Playwright 爬虫

## ⚠️ 重要提示

McKinsey 网站有反爬虫机制，普通 requests 无法访问。**必须使用 Playwright 版本！**

## 📦 第一步：安装 Playwright 浏览器

### Windows:
```powershell
# 双击运行安装脚本
install_playwright.bat

# 或手动运行
python -m playwright install chromium
```

### Linux/Mac:
```bash
# 添加执行权限并运行
chmod +x install_playwright.sh
./install_playwright.sh

# 或手动运行
python -m playwright install chromium
```

## 🎯 第二步：运行爬虫

### 1. 快速测试（显示浏览器窗口，爬取2篇）
```bash
python run_scrapers.py --source mckinsey --limit 2 --no-headless
```

### 2. 正式运行（无头模式，爬取5篇）
```bash
python run_scrapers.py --source mckinsey --limit 5
```

### 3. 运行测试脚本
```bash
python test_playwright_scraper.py
```

## 📊 查看结果

爬取的数据保存在：
```
storage/processed/mckinsey_playwright_YYYYMMDD_HHMMSS.json
```

调试截图保存在：
```
storage/raw/mckinsey_reports/debug_insights_page.png
```

## 📖 详细文档

查看完整使用指南：[docs/PLAYWRIGHT_GUIDE.md](docs/PLAYWRIGHT_GUIDE.md)

## ❓ 常见问题

### Q: 提示找不到 playwright
**A:** 先安装浏览器驱动：
```bash
python -m playwright install chromium
```

### Q: 爬取失败
**A:** 
1. 使用 `--no-headless` 查看浏览器实际行为
2. 检查网络连接
3. 增加延迟时间（修改代码中的 `delay` 参数）

### Q: 想看到爬虫运行过程
**A:** 添加 `--no-headless` 参数：
```bash
python run_scrapers.py --source mckinsey --limit 2 --no-headless
```

## 🎬 使用演示

```bash
# 1. 安装浏览器驱动
python -m playwright install chromium

# 2. 测试爬虫（显示浏览器）
python run_scrapers.py --source mckinsey --limit 2 --no-headless

# 3. 正式爬取（后台运行）
python run_scrapers.py --source mckinsey --limit 10
```

## 📝 注意事项

- ✅ **推荐爬取数量**: 2-10 篇（避免对服务器造成压力）
- ✅ **延迟设置**: 默认5秒，建议不要小于3秒
- ✅ **合法使用**: 仅用于教育和研究目的
- ✅ **礼貌爬取**: 遵守网站 robots.txt 和服务条款

