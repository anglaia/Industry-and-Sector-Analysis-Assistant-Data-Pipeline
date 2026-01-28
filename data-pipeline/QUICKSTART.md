# Data Pipeline 快速开始指南

## 🚀 5分钟上手

### 1. 安装依赖

```bash
cd data-pipeline
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入必要的 API 密钥
# 至少需要配置：
# - PINECONE_API_KEY
# - GOOGLE_API_KEY
```

### 3. 测试单个数据源

#### 选项 A: 从 SEC API 获取数据

```bash
# 下载 Apple, Microsoft, Google 的最新财报
python run_scrapers.py --source sec --tickers AAPL MSFT GOOGL --limit 3
```

#### 选项 B: 爬取 McKinsey 报告

```bash
# 爬取前 5 篇文章
python run_scrapers.py --source mckinsey --limit 5
```

#### 选项 C: 获取行业新闻

```bash
# 获取科技、医疗、金融行业最近7天的新闻
python run_scrapers.py --source news --industries Technology Healthcare Finance --days 7
```

### 4. 摄取到 Pinecone

```bash
# 处理并摄取 SEC 报告
python run_batch_ingest.py --directory storage/raw/sec_filings --industry Technology

# 或者使用自动行业检测
python run_batch_ingest.py --directory storage/raw/sec_filings --auto-detect
```

### 5. 启动定时任务

```bash
# 启动调度器（持续运行）
python main.py --mode schedule

# 或者运行单次任务
python main.py --mode once --task sec
```

---

## 📊 完整工作流程示例

### 场景：每日自动采集科技行业数据

```bash
# 1. 配置数据源（编辑 config/sources.yaml）
# 启用 SEC 和 NewsAPI

# 2. 启动调度器
python main.py --mode schedule

# 调度器将会：
# - 每天凌晨2点：从 SEC 下载新财报
# - 每天早上6点：获取行业新闻
# - 每周一凌晨3点：爬取 McKinsey 报告
# - 自动处理并摄取到 Pinecone
```

---

## 🔍 验证数据已摄取

可以通过 backend-ai 的 API 验证：

```bash
# 启动 backend-ai 服务器
cd ../backend-ai
python main.py

# 测试查询
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the key trends in technology sector?"}'
```

---

## 📝 常见任务

### 手动下载并处理单个公司的数据

```python
# 创建脚本 manual_process.py
from api_clients.sec_client import SECClient
from ingest.batch_processor import BatchProcessor
from config.settings import settings

# 1. 下载 Tesla 的财报
client = SECClient()
output_dir = settings.raw_files_path / "sec_filings"
client.bulk_download_filings(
    tickers=["TSLA"],
    form_types=["10-K"],
    limit_per_company=1,
    output_dir=output_dir
)

# 2. 处理并摄取
processor = BatchProcessor()
result = processor.process_directory(
    directory=output_dir,
    industry="Automotive",
    recursive=False
)

print(f"Processed {result['successful']} documents")
```

### 查看日志

```bash
# 实时查看日志
tail -f storage/logs/data_pipeline_*.log

# 查看错误日志
tail -f storage/logs/errors_*.log
```

### 清理旧文件

```bash
# 手动运行清理任务
python main.py --mode once --task cleanup
```

---

## 🛠️ 故障排除

### 问题：API 密钥错误

```bash
# 检查环境变量是否正确加载
python -c "from config.settings import settings; print(settings.pinecone_api_key[:10])"
```

### 问题：Pinecone 连接失败

```bash
# 测试 Pinecone 连接
python -c "from pinecone import Pinecone; pc = Pinecone(api_key='your_key'); print(pc.list_indexes())"
```

### 问题：PDF 提取失败

```bash
# 测试 PDF 处理
python -c "from processors.pdf_processor import PDFProcessor; p = PDFProcessor(); print(p.extract_text('path/to/file.pdf')[:100])"
```

---

## 📚 下一步

- 查看 [README.md](README.md) 了解完整功能
- 编辑 [config/sources.yaml](config/sources.yaml) 配置数据源
- 查看 [backend-ai/README.md](../backend-ai/README.md) 了解如何使用 RAG 系统

## 💡 提示

1. **从小规模开始**：先测试单个数据源，确保流程正常
2. **监控日志**：定期查看日志，确保任务正常运行
3. **调整频率**：根据需要修改 `config/sources.yaml` 中的调度时间
4. **数据质量**：定期检查摄取的数据质量，调整清洗规则

---

**需要帮助？** 查看日志文件或联系项目维护者。

