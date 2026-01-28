# Industry and Sector Analysis Assistant - Data Pipeline

这是一个专门用于处理PDF文件、提取文本、切块向量化并上传到Pinecone的ETL数据管道。

## 📋 目录

- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [详细设置步骤](#详细设置步骤)
- [使用方法](#使用方法)
- [配置说明](#配置说明)
- [数据模型](#数据模型)
- [常见问题](#常见问题)

## 📁 项目结构

```
.
├── config/                 # 配置模块
│   ├── __init__.py
│   └── settings.py         # 统一配置文件
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── models.py          # 数据模型定义
│   └── utils.py           # 通用工具函数
├── ingestion/              # 数据摄取模块
│   ├── __init__.py
│   └── s3_uploader.py     # S3上传功能
├── processing/             # 数据处理模块
│   ├── __init__.py
│   ├── pdf_extractor.py   # PDF文本提取
│   ├── text_cleaner.py     # 文本清洗
│   ├── chunker.py          # 文本切块
│   └── metadata_builder.py # 元数据构建
├── embedding/              # 向量生成模块
│   ├── __init__.py
│   └── embedder.py         # Embedding生成（Gemini）
├── vector_store/           # 向量存储模块
│   ├── __init__.py
│   └── pinecone_client.py  # Pinecone客户端
├── io/                     # IO模块
│   ├── __init__.py
│   └── local_store.py      # 本地JSONL存储
├── data/                   # 输入数据目录（自动创建）
├── output/                 # 输出目录（自动创建）
│   └── local_store/        # JSONL文件存储
├── logs/                   # 日志目录（自动创建）
├── run_pipeline_step2.py   # 步骤2脚本（到JSONL）
├── run_pipeline_full.py    # 完整端到端脚本
├── .env.example            # 环境变量示例文件
├── requirements.txt        # 依赖包列表
└── README.md               # 本文件
```

## 🚀 快速开始

### 1. 克隆项目并安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，填入你的API密钥和配置
# Windows用户可以直接复制 .env.example 为 .env 并编辑
```

### 3. 运行管道

**方式1：仅处理到本地JSONL（步骤2）**
```bash
python run_pipeline_step2.py "data/report.pdf" "AI" "AI Report 2024" "2024"
```

**方式2：完整端到端处理（步骤2 + 向量化 + Pinecone）**
```bash
python run_pipeline_full.py "data/report.pdf" "AI" "AI Report 2024" "2024"
```

## ⚙️ 详细设置步骤

### 步骤1：安装Python依赖

确保你的Python版本 >= 3.10：

```bash
python --version  # 应该显示 Python 3.10.x 或更高版本
pip install -r requirements.txt
```

**依赖包说明：**
- `pdfplumber`: PDF文本提取（优先使用）
- `pypdf`: PDF文本提取（备选方案）
- `boto3`: AWS S3上传功能
- `pinecone-client`: Pinecone向量数据库客户端
- `google-generativeai`: Google Gemini Embedding API
- `pyyaml`: YAML配置文件解析（可选）

### 步骤2：配置AWS S3（可选）

如果你需要使用S3上传功能：

1. **创建S3存储桶**
   - 登录AWS控制台
   - 创建S3存储桶，记录存储桶名称和区域

2. **获取AWS凭证**
   - 方式1：使用IAM用户访问密钥（推荐用于生产环境）
     - 创建IAM用户，授予S3读写权限
     - 获取Access Key ID和Secret Access Key
   - 方式2：使用AWS CLI配置的默认凭证（推荐用于开发环境）
     ```bash
     aws configure
     ```

3. **配置环境变量**
   在 `.env` 文件中设置：
   ```bash
   S3_BUCKET_NAME=your-bucket-name
   S3_REGION=us-east-1
   S3_PREFIX=documents/
   # 如果使用IAM用户凭证，取消注释并填入：
   # AWS_ACCESS_KEY_ID=your-access-key-id
   # AWS_SECRET_ACCESS_KEY=your-secret-access-key
   ```

**注意：** 如果不配置S3，管道仍可运行，但不会上传PDF到S3，chunks的metadata中`s3_url`字段将为`None`。

### 步骤3：配置Google Gemini API（必需，如果要用embedding功能）

1. **获取Gemini API密钥**
   - 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
   - 创建新的API密钥
   - 复制API密钥

2. **配置环境变量**
   在 `.env` 文件中设置：
   ```bash
   EMBEDDING_PROVIDER=gemini
   EMBEDDING_API_KEY=your-gemini-api-key
   EMBEDDING_MODEL=gemini-embedding-001  # 默认模型（也支持 models/ 前缀）
   ```

3. **确认向量维度**
   - Gemini `gemini-embedding-001` 模型的向量维度是 **3072**
   - 确保 `PINECONE_DIMENSION=3072`（在Pinecone配置中）

### 步骤4：配置Pinecone（必需，如果要用Pinecone功能）

1. **创建Pinecone账户**
   - 访问 [Pinecone官网](https://www.pinecone.io/)
   - 注册账户并登录

2. **获取API密钥**
   - 在Pinecone控制台获取API密钥
   - 记录你的环境（environment）名称（旧版本API需要）

3. **配置环境变量**
   在 `.env` 文件中设置：
   ```bash
   PINECONE_API_KEY=your-pinecone-api-key
   PINECONE_ENVIRONMENT=us-east-1  # 旧版本API需要，新版本Serverless不需要
   PINECONE_INDEX_NAME=industry-analysis
   PINECONE_DIMENSION=3072  # 必须与embedding模型匹配！
   PINECONE_METRIC=cosine
   ```

4. **确认向量维度匹配**
   - **重要：** `PINECONE_DIMENSION` 必须与embedding模型的输出维度一致
   - Gemini `gemini-embedding-001`: 3072
   - OpenAI `text-embedding-ada-002`: 1536
   - 如果不匹配，Pinecone会拒绝写入向量

### 步骤5：准备PDF文件

将你的PDF文件放在 `data/` 目录下（或任何可访问的路径）：

```bash
# 创建data目录（如果不存在）
mkdir -p data

# 将PDF文件复制到data目录
cp your-report.pdf data/
```

## 📖 使用方法

### 方式1：步骤2 - 仅处理到本地JSONL

这个脚本会：
1. ✅ 上传PDF到S3（如果配置了）
2. ✅ 提取PDF文本
3. ✅ 清洗文本
4. ✅ 切分成chunks
5. ✅ 构建metadata
6. ✅ 保存到本地JSONL文件

**不会执行：**
- ❌ 生成向量
- ❌ 写入Pinecone

```bash
python run_pipeline_step2.py <pdf_path> [industry] [title] [year]
```

**示例：**
```bash
python run_pipeline_step2.py "data/report.pdf" "AI" "AI Report 2024" "2024"
```

**输出：**
- JSONL文件：`output/local_store/{file_id}_chunks.jsonl`
- 日志文件：`logs/pipeline.log`

### 方式2：完整端到端处理

这个脚本会执行**所有步骤**：
1. ✅ 上传PDF到S3（如果配置了）
2. ✅ 提取PDF文本
3. ✅ 清洗文本
4. ✅ 切分成chunks
5. ✅ 构建metadata
6. ✅ 生成向量（Gemini）
7. ✅ 写入Pinecone

```bash
python run_pipeline_full.py <pdf_path> [industry] [title] [year]
```

**示例：**
```bash
python run_pipeline_full.py "data/report.pdf" "AI" "AI Report 2024" "2024"
```

**输出：**
- JSONL文件：`output/local_store/{file_id}_chunks.jsonl`
- Pinecone索引：向量已写入
- 日志文件：`logs/pipeline.log`

### 方式3：批量处理多个PDF

这个脚本会扫描指定目录下的所有 PDF 文件，并逐个执行端到端处理。

```bash
python run_pipeline_batch.py --input_dir "data" --industry "education"
```

**示例：**
```bash
python run_pipeline_batch.py --input_dir "data" --industry "finance" --year "2024"
```

**参数说明**
- `--input_dir`（可选）：包含 PDF 文件的目录路径，默认 `"data"`
- `--industry`（可选）：行业分类，默认 `"education"`
- `--year`（可选）：文档年份，默认 `None`

**输出：**
- 对每个文件执行完整处理流程
- 汇总成功/失败统计
- 日志文件：`logs/pipeline.log`

### 参数说明

- `pdf_path`（必需）：PDF文件的路径
- `industry`（可选）：行业分类，默认 `"general"`
- `title`（可选）：文档标题
- `year`（可选）：发布年份

## 🔧 配置说明

所有配置都在 `config/settings.py` 中，可以通过环境变量覆盖。

### PDF处理配置

- `CHUNK_MAX_CHARS`: 每个chunk的最大字符数（默认1000）
- `CHUNK_OVERLAP_CHARS`: chunk之间的重叠字符数（默认200）
- `CHUNK_ALLOW_CROSS_PAGE`: 是否允许跨页chunk（默认true）

### 文本清洗配置

- `CLEAN_REMOVE_HEADERS`: 是否移除页眉（默认true）
- `CLEAN_REMOVE_FOOTERS`: 是否移除页脚（默认true）
- `CLEAN_REMOVE_ADS`: 是否移除广告（默认true）
- `CLEAN_REMOVE_CONTACTS`: 是否移除联系方式（默认true）

### Embedding配置

- `EMBEDDING_PROVIDER`: 提供商（默认"gemini"）
- `EMBEDDING_BATCH_SIZE`: 批量大小（默认32）
- `EMBEDDING_MAX_RETRIES`: 最大重试次数（默认3）

## 📊 数据模型

### Document（文档级）

- `file_id`: 文件标识符（自动生成）
- `industry`: 行业分类
- `source_file`: 原始文件名
- `local_path`: 本地文件路径
- `s3_url`: S3 URL（上传后填充）
- 其他可选字段：`title`, `year`, `author`, `language` 等

### Page（页级）

- `file_id`: 所属文档ID
- `page_number`: 页码（从1开始）
- `raw_text`: 原始提取的文本
- `clean_text`: 清洗后的文本

### Chunk（块级）

**核心必需字段（4个）：**
- `file_id`: 文件标识符
- `industry`: 行业分类
- `chunk_index`: 分块索引
- `text`: 文本内容

**引用功能必需字段（3个）：**
- `page_number`: PDF页码
- `s3_url`: S3文件URL
- `source_file`: 原始文件名

**跨页字段（可选）：**
- `page_start`: 起始页码
- `page_end`: 结束页码

**推荐字段（可选）：**
- `title`: 文档标题
- `year`: 发布年份
- `author`: 作者

### Pinecone向量格式

每条向量在Pinecone中的结构：

```python
{
    "id": "Deloitte_AI_Report_2024_chunk_5",
    "values": [0.34, 0.56, ...],  # 768维向量（Gemini embedding-001）
    "metadata": {
        "file_id": "Deloitte_AI_Report_2024",
        "industry": "AI",
        "chunk_index": 5,
        "text": "AI technology is transforming...",
        "page_number": 12,
        "s3_url": "https://s3.amazonaws.com/bucket/Deloitte_AI_Report_2024.pdf",
        "source_file": "Deloitte_AI_Report_2024.pdf",
        # ... 其他可选字段
    }
}
```

## ❓ 常见问题

### Q1: 如何跳过S3上传？

不设置 `S3_BUCKET_NAME` 环境变量即可。管道会跳过S3上传步骤，但chunks的metadata中`s3_url`将为`None`。

### Q2: 向量维度不匹配怎么办？

确保 `PINECONE_DIMENSION` 与你的embedding模型输出维度一致：
- Gemini `embedding-001`: 768
- OpenAI `text-embedding-ada-002`: 1536

### Q3: Pinecone初始化失败？

检查：
1. `PINECONE_API_KEY` 是否正确
2. 如果使用旧版本API，`PINECONE_ENVIRONMENT` 是否正确
3. 网络连接是否正常

### Q4: Gemini API调用失败？

检查：
1. `EMBEDDING_API_KEY` 是否正确
2. API配额是否用完
3. 网络连接是否正常

### Q5: PDF提取失败？

确保：
1. 已安装 `pdfplumber` 或 `pypdf`
2. PDF文件没有损坏
3. PDF文件路径正确

### Q6: 如何批量处理多个PDF？

可以使用提供的批量处理脚本 `run_pipeline_batch.py`：

```bash
python run_pipeline_batch.py --input_dir "data" --industry "education"
```

该脚本会自动扫描指定目录下的所有 PDF 文件并进行处理。

## 📝 注意事项

1. **环境变量优先级**：环境变量会覆盖 `config/settings.py` 中的默认值
2. **日志文件**：所有日志都会写入 `logs/pipeline.log`，同时也会输出到控制台
3. **错误处理**：如果某个步骤失败，会记录错误日志，但不会中断整个流程（某些关键步骤除外）
4. **S3上传**：如果S3中已存在同名文件，默认不会覆盖（除非设置 `overwrite=True`）
5. **Pinecone索引**：如果索引不存在，会自动创建；如果已存在，会直接使用

## 🔄 下一步

- [ ] 支持更多embedding提供商（OpenAI等）
- [x] 支持批量处理多个PDF
- [ ] 添加进度条显示
- [ ] 支持从JSONL恢复处理流程
- [ ] 添加单元测试

## 📄 许可证

本项目仅供学习和研究使用。
