# RAG 数据处理管道

基于 Python 的 RAG (Retrieval-Augmented Generation) 数据摄取管道，用于处理 MIT AI News 数据集并构建向量数据库。

## 架构概览

该管道分为两个独立的阶段：

### Phase 1: 文档预处理（本地）
- 从 Kaggle 加载数据集
- 清洗和规范化文本
- 分块处理长文档
- 保存为结构化 JSONL 格式

### Phase 2: 向量摄取
- 读取本地 JSONL 文件
- 使用 Gemini API 生成嵌入向量
- 批量上传到 Pinecone 向量数据库

## 技术栈

- **Python**: 3.10+
- **数据源**: Kaggle Dataset (`deepanshudalal09/mit-ai-news-published-till-2023`)
- **嵌入模型**: Google Gemini API (`google-generativeai`)
- **向量数据库**: Pinecone
- **数据处理**: Pandas, JSONL
- **环境管理**: python-dotenv

## 项目结构

```
rag-pipeline/
├── src/
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── preprocessing.py   # Phase 1: 文档预处理
│   └── ingestion.py       # Phase 2: 向量摄取
├── data/                  # 数据目录（自动创建）
│   └── processed_data.jsonl
├── main.py                # 主入口
├── requirements.txt       # 依赖包
├── .env                   # 环境变量（需要创建）
└── .env.example           # 环境变量示例
```

## 安装

### 1. 克隆项目

```bash
cd rag-pipeline
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
GEMINI_API_KEY=your_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=rag-news-index
```

## 使用方法

### 运行完整流程（推荐）

```bash
python main.py --all
```

这将依次运行 Phase 1 和 Phase 2。

### 单独运行某个阶段

```bash
# 只运行 Phase 1（文档预处理）
python main.py --phase1

# 只运行 Phase 2（向量摄取）
python main.py --phase2
```

### 查看帮助

```bash
python main.py --help
```

## 数据格式

### JSONL 格式（Phase 1 输出）

```json
{
  "id": "doc_000001_chunk_00",
  "text": "The operational profit increased by 15% due to...",
  "metadata": {
    "industry": "AI/Technology",
    "year": 2023,
    "doc_id": "doc_000001",
    "title": "MIT AI News: Q3 Report",
    "source_url": "https://..."
  }
}
```

### Pinecone 格式（Phase 2 上传）

```json
{
  "id": "doc_000001_chunk_00",
  "values": [0.12, -0.05, ...],
  "metadata": {
    "industry": "AI/Technology",
    "year": 2023,
    "doc_id": "doc_000001",
    "title": "MIT AI News: Q3 Report",
    "source_url": "https://...",
    "text": "The operational profit increased by 15% due to..."
  }
}
```

## 配置参数

可以在 `src/config.py` 中调整以下参数：

- `CHUNK_SIZE`: 文本块大小（默认 512 字符）
- `CHUNK_OVERLAP`: 文本块重叠（默认 50 字符）
- `BATCH_SIZE`: Pinecone 批量上传大小（默认 100）
- `EMBEDDING_MODEL`: Gemini 嵌入模型（默认 `gemini-embedding-001`，也支持 `models/` 前缀）
- `EMBEDDING_DIMENSION`: 嵌入向量维度（默认 3072）

## 错误处理

管道包含完善的错误处理：

- **API 调用失败**: 自动捕获并报告错误，继续处理其他数据
- **数据验证**: 在每个阶段验证必需的字段
- **批处理容错**: 单个批次失败不会影响整个流程
- **进度显示**: 使用 tqdm 显示实时处理进度

## 注意事项

1. **API 速率限制**: 代码中已添加延迟以避免触发 API 速率限制
2. **大数据集**: 对于大型数据集，建议分批处理
3. **存储空间**: 确保有足够的磁盘空间存储 JSONL 文件
4. **API 配额**: 注意 Gemini 和 Pinecone 的 API 使用配额

## 故障排查

### Kaggle 认证问题

如果遇到 Kaggle 认证错误，请确保：
1. 已安装 `kagglehub` 包
2. 已在 Kaggle 网站上接受数据集的使用条款

### Pinecone 索引问题

如果索引创建失败：
1. 检查 Pinecone API 密钥是否正确
2. 确认 Pinecone 环境设置正确
3. 确保账户有创建索引的权限

### Gemini API 问题

如果嵌入生成失败：
1. 验证 Gemini API 密钥
2. 检查 API 配额
3. 确认网络连接正常

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系项目维护者。

