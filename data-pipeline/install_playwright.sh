#!/bin/bash
# Playwright 安装脚本 (Linux/Mac)
# 用于安装 Playwright 浏览器驱动

echo "============================================================"
echo "Playwright 浏览器驱动安装脚本"
echo "============================================================"
echo ""

echo "[步骤 1/2] 检查 Playwright 包..."
if python -c "import playwright; print(f'✅ Playwright 版本: {playwright.__version__}')" 2>/dev/null; then
    echo "✅ Playwright 已安装"
else
    echo "❌ Playwright 未安装"
    echo "正在安装 Playwright..."
    pip install playwright==1.40.0
fi

echo ""
echo "[步骤 2/2] 安装 Chromium 浏览器驱动..."
python -m playwright install chromium

echo ""
echo "============================================================"
if [ $? -eq 0 ]; then
    echo "✅ 安装完成！"
    echo ""
    echo "现在可以运行以下命令测试:"
    echo "  python test_playwright_scraper.py"
    echo "  python run_scrapers.py --source mckinsey --limit 2 --no-headless"
else
    echo "❌ 安装失败！"
    echo ""
    echo "可能的原因:"
    echo "1. 权限不足"
    echo "2. 网络连接问题"
    echo ""
    echo "建议:"
    echo "- 使用 sudo 运行此脚本"
    echo "- 检查网络连接"
fi
echo "============================================================"

