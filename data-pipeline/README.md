# Data Pipeline - 自动化数据采集与 RAG 库构建

## 📋 项目简介

这是一个自动化的数据采集系统，用于从各种来源（API、网络爬虫）获取行业报告和文档，并将其处理后存储到 Pinecone 向量数据库中，为 RAG（检索增强生成）系统提供知识库。

## 🎯 核心功能

- ✅ **API 数据采集**: 从 SEC EDGAR、World Bank 等 API 获取结构化数据
- ✅ **网络爬虫**: 爬取 McKinsey、BCG 等咨询公司的公开报告
- ✅ **智能处理**: PDF 文本提取、数据清洗、元数据提取
- ✅ **批量摄取**: 将处理后的文档分块、嵌入并存储到 Pinecone
- ✅ **自动调度**: 定时任务自动运行数据采集
- ✅ **监控日志**: 完整的日志记录和错误追踪

## 📁 项目结构

```
data-pipeline/
├── README.md                    # 项目说明
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量示例
├── config/
│   ├── settings.py             # 配置管理
│   └── sources.yaml            # 数据源配置
├── scrapers/                   # 爬虫模块
│   ├── __init__.py
│   ├── base_scraper.py        # 基础爬虫类
│   ├── mckinsey_scraper.py    # McKinsey 爬虫
│   └── news_scraper.py        # 新闻爬虫
├── api_clients/                # API 客户端
│   ├── __init__.py
│   ├── sec_client.py          # SEC EDGAR API
│   ├── worldbank_client.py    # 世界银行 API
│   └── newsapi_client.py      # NewsAPI
├── processors/                 # 数据处理
│   ├── __init__.py
│   ├── pdf_processor.py       # PDF 处理
│   ├── text_cleaner.py        # 文本清洗
│   └── metadata_extractor.py  # 元数据提取
├── ingest/                     # 数据摄取
│   ├── __init__.py
│   ├── pinecone_ingester.py   # Pinecone 摄取
│   └── batch_processor.py     # 批量处理
├── scheduler/                  # 任务调度
│   ├── __init__.py
│   └── task_scheduler.py      # 定时任务
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── logger.py              # 日志配置
│   ├── rate_limiter.py        # 频率限制
│   └── file_utils.py          # 文件工具
├── storage/                    # 本地存储
│   ├── raw/                   # 原始文件
│   ├── processed/             # 处理后文件
│   └── logs/                  # 日志文件
├── tests/                      # 测试
│   ├── test_scrapers.py
│   └── test_processors.py
├── main.py                     # 主入口
├── run_scrapers.py            # 运行爬虫
└── run_batch_ingest.py        # 批量摄取

## 🚀 快速开始

### 1. 安装依赖

```bash
cd data-pipeline
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的 API 密钥
```

### 3. 运行数据采集

```bash
# 从 SEC API 获取数据
python run_scrapers.py --source sec --limit 10

# 运行爬虫
python run_scrapers.py --source mckinsey

# 批量摄取到 Pinecone
python run_batch_ingest.py --directory storage/raw/sec_filings
```

### 4. 启动定时任务

```bash
python main.py
```

## 📊 数据源

### API 数据源
- **SEC EDGAR**: 美国上市公司财报
- **World Bank**: 全球经济和行业数据
- **NewsAPI**: 实时新闻和行业动态
- **arXiv**: 学术论文和研究报告

### 爬虫数据源
- **McKinsey Insights**: 行业分析报告
- **BCG Perspectives**: 战略咨询报告
- **Deloitte Insights**: 行业洞察
- **行业新闻网站**: 实时资讯

## 🔧 配置说明

编辑 `config/sources.yaml` 来配置数据源：

```yaml
data_sources:
  sec:
    enabled: true
    frequency: daily
    industries:
      - Technology
      - Healthcare
      - Finance
```

## 📝 日志

日志文件保存在 `storage/logs/` 目录：
- `data_pipeline_YYYY-MM-DD.log`: 常规日志
- `errors_YYYY-MM-DD.log`: 错误日志

## 🤝 与 backend-ai 的集成

本项目与 `backend-ai` 共享 Pinecone 向量数据库：

```python
# 数据格式约定
metadata = {
    "file_id": "unique_id",
    "industry": "Technology",
    "year": "2024",
    "source": "automated_collection",  # 标识为自动采集
    "original_filename": "report.pdf",
    "author": "McKinsey",
    "chunk_index": 0,
    "text": "..."
}
```

## 📈 监控和维护

- 查看日志: `tail -f storage/logs/data_pipeline_*.log`
- 检查采集状态: `python utils/check_status.py`
- 清理旧文件: `python utils/cleanup.py --days 30`

## ⚠️ 注意事项

1. **遵守网站 robots.txt**: 爬虫必须遵守目标网站的爬取规则
2. **频率限制**: 避免过于频繁的请求，使用 rate limiter
3. **数据质量**: 定期检查采集的数据质量
4. **存储空间**: 注意本地存储空间使用情况

## 📚 相关文档

- [数据源配置指南](docs/DATA_SOURCES.md)
- [爬虫开发指南](docs/SCRAPER_GUIDE.md)
- [故障排除](docs/TROUBLESHOOTING.md)

## 🔗 相关项目

- [backend-ai](../backend-ai/): 主要的 API 服务
- [frontend](../frontend/): 用户界面

## 📄 许可证

本项目仅用于教育和研究目的。

