# AI RAG Pipeline（简化版）

> **专注于AI行业**的快速RAG库构建工具  
> 学生演示项目 - 简单、快速、有效

## 🎯 项目定位

这是一个**专门为AI行业设计**的简化数据采集管道，用于快速构建RAG（检索增强生成）知识库。

**核心特点：**
- ✅ **聚焦AI行业** - 只采集AI相关的高质量文章
- ✅ **快速启动** - 30秒内完成采集和向量化
- ✅ **简单易用** - 一个命令搞定所有操作
- ✅ **适合演示** - 清晰的进度显示和实时反馈

## 📋 功能概览

### **数据源**
- **McKinsey AI Insights** - 麦肯锡AI行业分析报告（主要数据源）

### **处理流程**
```
爬取AI文章 → AI关键词过滤 → 文本提取清洗 → 智能分块 → Gemini嵌入 → Pinecone存储
```

### **与现有系统集成**
- 与 `backend-ai` 共享 Pinecone 向量数据库
- 统一的嵌入模型（Google Gemini）
- 兼容的元数据格式

## 🚀 快速开始

### 1. 安装依赖

```bash
cd data-pipeline
pip install -r requirements.txt

# 安装 Playwright 浏览器
python -m playwright install chromium
```

### 2. 配置环境变量

创建 `.env` 文件：
```bash
# 必需的API密钥
PINECONE_API_KEY=your_pinecone_key
GOOGLE_API_KEY=your_google_key

# Pinecone配置
PINECONE_INDEX_NAME=industry-reports
PINECONE_ENVIRONMENT=us-west1-gcp

# 可选配置
CHUNK_SIZE=500
CHUNK_OVERLAP=50
LOG_LEVEL=INFO
```

### 3. 运行（一键完成）

```bash
# 采集10篇AI文章并上传到Pinecone
python run_ai_rag.py --articles 10
```

**就这么简单！** 🎉

## 💻 使用示例

### 基础用法
```bash
# 采集10篇AI文章（默认）
python run_ai_rag.py --articles 10
```

### 高级选项
```bash
# 采集20篇文章
python run_ai_rag.py --articles 20

# 显示浏览器窗口（调试用）
python run_ai_rag.py --articles 10 --no-headless

# 只预览统计信息，不上传
python run_ai_rag.py --articles 5 --preview-only

# 关闭AI过滤，采集所有McKinsey文章
python run_ai_rag.py --articles 15 --no-filter
```

### 查看帮助
```bash
python run_ai_rag.py --help
```

## 📊 运行效果

```
======================================================================
🤖 AI RAG 快速构建工具
======================================================================
📝 配置:
   - 采集数量: 10 篇
   - 浏览器模式: 无头
   - AI过滤: 开启
   - Pinecone索引: industry-reports

======================================================================
🔍 步骤 1/2: 开始爬取McKinsey AI文章
======================================================================
✅ [1/10] The economic potential of generative AI...
✅ [2/10] AI at scale: Lessons from leading companies...
...
✅ 爬取到 10 篇文章
🎯 应用AI关键词过滤...
✅ 过滤后剩余 8 篇AI相关文章

======================================================================
🚀 步骤 2/2: 向量化处理并上传到Pinecone
======================================================================
处理文章: 100%|████████████████████| 8/8 [00:15<00:00]

======================================================================
✅ 完成！RAG库已更新
======================================================================
📊 摄取统计:
   - 总文章数: 8
   - 成功: 8
   - 失败: 0
   - 总chunks: 127

🎉 你现在可以在backend-ai中查询这些AI行业内容了!
```

## 📁 简化后的项目结构

```
data-pipeline/
├── config/                  # 配置文件
│   ├── settings.py         # 简化的设置（只保留核心配置）
│   └── sources.yaml        # AI数据源配置
│
├── scrapers/               # 爬虫模块
│   ├── mckinsey_playwright_scraper.py  # McKinsey AI爬虫
│   └── playwright_base_scraper.py      # 爬虫基类
│
├── processors/             # 数据处理
│   ├── pdf_processor.py    # PDF处理
│   └── text_cleaner.py     # 文本清洗
│
├── ingest/                 # 数据摄取
│   ├── pinecone_ingester.py  # Pinecone上传
│   └── batch_processor.py    # 批量处理
│
├── utils/                  # 工具模块
│   ├── logger.py
│   ├── rate_limiter.py
│   └── file_utils.py
│
├── storage/                # 数据存储
│   ├── processed/          # 处理后的JSON
│   └── logs/               # 日志文件
│
├── run_ai_rag.py          # 主入口脚本（一键运行）
├── requirements.txt        # 精简的依赖列表
├── .env                    # 环境变量
└── README.md              # 本文件
```

## 🎨 AI关键词过滤

系统会自动过滤包含以下AI关键词的文章：

```python
AI_KEYWORDS = [
    "artificial intelligence", "AI", "machine learning", 
    "deep learning", "neural network", "generative AI", 
    "large language model", "LLM", "GPT", "transformer",
    "computer vision", "natural language processing",
    "reinforcement learning", "AI ethics", "AI strategy"
]
```

只有包含至少2个关键词的文章才会被采集，确保内容与AI高度相关。

## ⚙️ 配置说明

### 必需的API密钥
- `PINECONE_API_KEY` - Pinecone向量数据库（免费版足够）
- `GOOGLE_API_KEY` - Google Gemini嵌入模型（免费额度充足）

### 可选配置
- `CHUNK_SIZE` - 文本分块大小（默认：500 tokens）
- `CHUNK_OVERLAP` - 分块重叠（默认：50 tokens）
- `LOG_LEVEL` - 日志级别（默认：INFO）

## 🔄 与 backend-ai 集成

数据pipeline采集的内容会自动同步到 `backend-ai`：

```
data-pipeline (采集)  →  Pinecone (存储)  →  backend-ai (查询)
```

### 共享配置
- 相同的 Pinecone Index
- 相同的嵌入模型（Gemini embedding-001）
- 统一的元数据格式

### 元数据格式
```python
{
    "file_id": "mckinsey_ai_20241128_1",
    "industry": "AI",
    "title": "The economic potential of generative AI",
    "url": "https://...",
    "source": "McKinsey AI",
    "collection_date": "2024-11-28T10:30:00"
}
```

## 📈 性能指标

- **采集速度**: ~2-3秒/篇文章
- **向量化速度**: ~1-2秒/chunk
- **10篇文章总耗时**: ~30-45秒
- **内存占用**: <500MB

## ❓ 常见问题

### Q: 为什么只有McKinsey一个数据源？
A: 为了演示项目的简洁性，专注于单一高质量来源。McKinsey的AI内容质量高、结构清晰，非常适合RAG演示。

### Q: 如何添加更多数据源？
A: 可以参考 `mckinsey_playwright_scraper.py` 创建新的爬虫类。但建议先验证现有功能。

### Q: 浏览器自动化失败怎么办？
A: 使用 `--no-headless` 参数查看浏览器窗口，检查网页加载情况。确保网络连接正常。

### Q: API密钥从哪里获取？
A: 
- Pinecone: https://www.pinecone.io/ （免费版足够）
- Google AI: https://makersuite.google.com/app/apikey （免费）

## 🔗 相关文档

- [配置详解](config/sources.yaml) - AI数据源配置
- [Playwright快速开始](PLAYWRIGHT_QUICKSTART.md) - 爬虫调试指南
- [Backend-AI集成](../backend-ai/README.md) - 查询接口使用

## 📝 变更日志

### v2.0 - 简化版（当前版本）
- ✅ 删除SEC、NewsAPI等非AI数据源
- ✅ 删除复杂的调度器系统
- ✅ 合并多个脚本为单一入口
- ✅ 精简依赖包（从30+减到12个）
- ✅ 专注AI行业关键词过滤
- ✅ 优化用户体验和反馈

### v1.0 - 完整版
- 支持多数据源（SEC, McKinsey, NewsAPI等）
- 完整的调度系统
- 复杂的元数据提取

## 🤝 适用场景

✅ **适合：**
- 学生演示项目
- AI行业快速原型
- RAG系统概念验证
- 教学和学习用途

❌ **不适合：**
- 生产环境大规模采集
- 多行业复杂场景
- 需要定时调度的持续运行

## 📄 许可证

本项目仅用于教育和研究目的。请遵守数据源网站的使用条款和 robots.txt。

---

**维护者**: Your Team  
**最后更新**: 2024-11-28  
**版本**: 2.0 (简化版)

---

## 🎓 演示提示

如果你要向导师演示这个项目：

1. **准备阶段** (5分钟前)
   - 确保 `.env` 已配置
   - 运行一次测试确保正常工作
   - 准备 `--preview-only` 模式的截图

2. **演示流程** (3分钟)
   - 展示简化的项目结构
   - 运行 `python run_ai_rag.py --articles 5`
   - 强调AI关键词过滤机制
   - 展示Pinecone中的数据

3. **亮点说明**
   - "我们简化了架构，专注于AI行业"
   - "从原来的30+个依赖减少到12个"
   - "一个命令30秒完成全流程"
   - "与backend-ai无缝集成"

祝演示成功！🎉

