# 详细设置指南

本文档提供完整的环境配置步骤。

## 环境变量配置

创建 `.env` 文件（在项目根目录），内容如下：

```bash
# ==================== AWS S3 配置 ====================
# S3存储桶名称（必需，如果要用S3上传功能）
S3_BUCKET_NAME=your-bucket-name

# S3区域（可选，默认us-east-1）
S3_REGION=us-east-1

# S3对象前缀（可选，默认documents/）
S3_PREFIX=documents/

# AWS访问密钥（可选，如果不使用默认凭据）
# AWS_ACCESS_KEY_ID=your-access-key-id
# AWS_SECRET_ACCESS_KEY=your-secret-access-key

# ==================== Pinecone 配置 ====================
# Pinecone API密钥（必需，如果要用Pinecone功能）
PINECONE_API_KEY=your-pinecone-api-key

# Pinecone环境（旧版本API需要，新版本Serverless不需要）
PINECONE_ENVIRONMENT=us-east-1

# Pinecone索引名称（可选，默认industry-analysis）
PINECONE_INDEX_NAME=industry-analysis

# 向量维度（必需，必须与embedding模型匹配）
# Gemini gemini-embedding-001: 3072
# OpenAI text-embedding-ada-002: 1536
PINECONE_DIMENSION=3072

# 相似度度量（可选，默认cosine）
# 可选值: cosine, euclidean, dotproduct
PINECONE_METRIC=cosine

# ==================== Embedding API 配置 ====================
# Embedding提供商（可选，默认gemini）
# 当前支持: gemini
EMBEDDING_PROVIDER=gemini

# Embedding API密钥（必需，如果要用embedding功能）
EMBEDDING_API_KEY=your-gemini-api-key

# Embedding模型名称（可选，默认gemini-embedding-001）
# 支持写 "gemini-embedding-001" 或 "models/gemini-embedding-001"
EMBEDDING_MODEL=gemini-embedding-001

# 批量大小（可选，默认32）
EMBEDDING_BATCH_SIZE=32

# 最大重试次数（可选，默认3）
EMBEDDING_MAX_RETRIES=3

# ==================== PDF 处理配置 ====================
# Chunk最大字符数（可选，默认1000）
CHUNK_MAX_CHARS=1000

# Chunk重叠字符数（可选，默认200）
CHUNK_OVERLAP_CHARS=200

# 是否允许跨页chunk（可选，默认true）
CHUNK_ALLOW_CROSS_PAGE=true

# ==================== 日志配置 ====================
# 日志级别（可选，默认INFO）
# 可选值: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

## 步骤1：安装依赖

```bash
pip install -r requirements.txt
```

## 步骤2：配置AWS S3（可选）

### 2.1 创建S3存储桶

1. 登录 [AWS控制台](https://console.aws.amazon.com/)
2. 进入S3服务
3. 点击"创建存储桶"
4. 输入存储桶名称（例如：`my-documents-bucket`）
5. 选择区域（例如：`us-east-1`）
6. 完成创建

### 2.2 配置AWS凭证

**方式A：使用AWS CLI（推荐用于开发环境）**

```bash
# 安装AWS CLI（如果未安装）
# Windows: 下载并安装 https://aws.amazon.com/cli/
# Mac: brew install awscli
# Linux: sudo apt-get install awscli

# 配置凭证
aws configure
# 输入你的 Access Key ID
# 输入你的 Secret Access Key
# 输入默认区域（例如：us-east-1）
# 输入默认输出格式（例如：json）
```

**方式B：使用IAM用户凭证（推荐用于生产环境）**

1. 在AWS控制台创建IAM用户
2. 授予S3读写权限
3. 创建访问密钥
4. 在 `.env` 文件中填入：
   ```bash
   AWS_ACCESS_KEY_ID=your-access-key-id
   AWS_SECRET_ACCESS_KEY=your-secret-access-key
   ```

### 2.3 在.env中配置S3

```bash
S3_BUCKET_NAME=my-documents-bucket
S3_REGION=us-east-1
S3_PREFIX=documents/
```

## 步骤3：配置Google Gemini API（必需）

### 3.1 获取API密钥

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 登录你的Google账户
3. 点击"Create API Key"
4. 复制生成的API密钥

### 3.2 在.env中配置

```bash
EMBEDDING_PROVIDER=gemini
EMBEDDING_API_KEY=your-gemini-api-key-here
EMBEDDING_MODEL=gemini-embedding-001
```

**注意：** Gemini `gemini-embedding-001` 模型的向量维度是 **3072**，确保 Pinecone 配置中也使用 `PINECONE_DIMENSION=3072`。

## 步骤4：配置Pinecone（必需）

### 4.1 创建Pinecone账户

1. 访问 [Pinecone官网](https://www.pinecone.io/)
2. 注册账户并登录
3. 选择免费计划（Free tier）或付费计划

### 4.2 获取API密钥

1. 在Pinecone控制台，进入"API Keys"页面
2. 复制你的API密钥
3. 记录你的环境名称（如果是旧版本API）

### 4.3 在.env中配置

```bash
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENVIRONMENT=us-east-1  # 旧版本API需要，新版本Serverless不需要
PINECONE_INDEX_NAME=industry-analysis
PINECONE_DIMENSION=3072  # 必须与embedding模型匹配！
PINECONE_METRIC=cosine
```

**重要：** `PINECONE_DIMENSION` 必须与你的embedding模型输出维度一致：
- Gemini `gemini-embedding-001`: **3072**
- OpenAI `text-embedding-ada-002`: **1536**

## 步骤5：准备PDF文件

将你的PDF文件放在 `data/` 目录下：

```bash
# 创建data目录（如果不存在）
mkdir -p data

# 将PDF文件复制到data目录
cp your-report.pdf data/
```

## 步骤6：测试运行

### 测试步骤2（仅到JSONL）

```bash
python run_pipeline_step2.py "data/test.pdf" "AI" "Test Report" "2024"
```

检查输出：
- `output/local_store/` 目录下应该有JSONL文件
- `logs/pipeline.log` 应该有日志记录

### 测试完整流程

```bash
python run_pipeline_full.py "data/test.pdf" "AI" "Test Report" "2024"
```

检查输出：
- JSONL文件已生成
- Pinecone索引中应该有向量数据
- 日志文件记录完整流程

## 验证配置

运行以下Python脚本验证配置：

```python
import os
from dotenv import load_dotenv

load_dotenv()

print("=== 配置检查 ===")
print(f"S3_BUCKET_NAME: {os.getenv('S3_BUCKET_NAME', '未设置')}")
print(f"PINECONE_API_KEY: {'已设置' if os.getenv('PINECONE_API_KEY') else '未设置'}")
print(f"EMBEDDING_API_KEY: {'已设置' if os.getenv('EMBEDDING_API_KEY') else '未设置'}")
print(f"PINECONE_DIMENSION: {os.getenv('PINECONE_DIMENSION', '未设置')}")
```

## 常见问题排查

### 问题1：找不到.env文件

**解决方案：**
- 确保 `.env` 文件在项目根目录
- Windows用户注意：文件名应该是 `.env`，不是 `.env.txt`

### 问题2：环境变量未生效

**解决方案：**
- 确保 `.env` 文件格式正确（每行一个变量，没有多余空格）
- 重启终端/IDE
- 如果使用IDE运行，确保IDE支持.env文件

### 问题3：S3上传失败

**检查清单：**
- [ ] S3_BUCKET_NAME 是否正确
- [ ] AWS凭证是否正确配置
- [ ] S3存储桶是否存在
- [ ] IAM用户是否有S3读写权限

### 问题4：Pinecone连接失败

**检查清单：**
- [ ] PINECONE_API_KEY 是否正确
- [ ] PINECONE_ENVIRONMENT 是否正确（旧版本API）
- [ ] 网络连接是否正常
- [ ] Pinecone账户是否激活

### 问题5：Gemini API调用失败

**检查清单：**
- [ ] EMBEDDING_API_KEY 是否正确
- [ ] API配额是否用完
- [ ] 网络连接是否正常
- [ ] 模型名称是否正确

### 问题6：向量维度不匹配

**错误信息：** `dimension mismatch`

**解决方案：**
- 确保 `PINECONE_DIMENSION` 与embedding模型输出维度一致
- Gemini `embedding-001`: 768
- OpenAI `text-embedding-ada-002`: 1536

## 下一步

配置完成后，参考 [README.md](README.md) 了解如何使用管道。

