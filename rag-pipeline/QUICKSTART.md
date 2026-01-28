# 快速启动指南

本指南将帮助您在 5 分钟内启动 RAG 数据处理管道。

## 步骤 1: 安装依赖 (1 分钟)

```bash
cd rag-pipeline
pip install -r requirements.txt
```

## 步骤 2: 配置环境变量 (2 分钟)

创建 `.env` 文件：

```bash
# Windows
type nul > .env

# Linux/Mac
touch .env
```

编辑 `.env` 文件，添加你的 API 密钥：

```env
GEMINI_API_KEY=your_gemini_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=rag-news-index
```

> 📖 详细的环境变量配置说明，请参考 [ENV_SETUP.md](ENV_SETUP.md)

## 步骤 3: 运行管道 (2 分钟)

### 方式 A: 运行完整流程（推荐）

```bash
python main.py --all
```

这将：
1. 从 Kaggle 下载 MIT AI News 数据集
2. 清洗和分块文本
3. 保存为 JSONL 格式（`data/processed_data.jsonl`）
4. 生成嵌入向量
5. 上传到 Pinecone

### 方式 B: 分步运行

```bash
# 仅运行预处理
python main.py --phase1

# 仅运行向量摄取
python main.py --phase2
```

## 输出结果

### Phase 1 输出
- 文件位置: `data/processed_data.jsonl`
- 格式: 每行一个 JSON 对象

```json
{
  "id": "doc_000001_chunk_00",
  "text": "...",
  "metadata": {
    "industry": "AI/Technology",
    "year": 2023,
    "doc_id": "doc_000001",
    "title": "...",
    "source_url": "..."
  }
}
```

### Phase 2 输出
- 向量数据库: Pinecone Index
- 索引名称: 在 `.env` 中配置的 `PINECONE_INDEX_NAME`
- 向量维度: 768 (Gemini embedding-001)

## 验证结果

### 检查本地文件

```python
import json

with open('data/processed_data.jsonl', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 5:
            break
        doc = json.loads(line)
        print(f"文档 {i+1}: {doc['metadata']['title']}")
```

### 检查 Pinecone 索引

```python
from pinecone import Pinecone
import os
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

# 查看索引统计
stats = index.describe_index_stats()
print(f"向量总数: {stats['total_vector_count']}")
print(f"索引维度: {stats['dimension']}")
```

## 探索示例代码

运行交互式示例：

```bash
python example_usage.py
```

这将展示：
1. 如何运行完整管道
2. 如何自定义预处理
3. 如何自定义文本分块
4. 如何生成嵌入向量
5. 如何读取已处理数据

## 常见问题

### Q: Kaggle 认证失败？

**A**: 首次使用 `kagglehub` 时，它会提示你进行认证。按照提示操作即可。

### Q: Gemini API 速率限制？

**A**: 代码中已添加延迟。如果仍然遇到速率限制，可以在 `config.py` 中调整 `BATCH_SIZE`。

### Q: Pinecone 索引创建失败？

**A**: 检查：
1. Pinecone API Key 是否正确
2. Environment 设置是否正确
3. 账户是否有创建索引的权限

### Q: 内存不足？

**A**: 在 `config.py` 中减小 `BATCH_SIZE`（默认 100）。

## 下一步

- 📖 查看 [README.md](README.md) 了解详细架构
- 🔧 修改 [src/config.py](src/config.py) 调整参数
- 💡 运行 [example_usage.py](example_usage.py) 学习更多用法
- 🔍 使用 Pinecone 进行相似度搜索

## 性能预期

基于 MIT AI News 数据集（约 1000 篇新闻）：

- **Phase 1**: 2-5 分钟
- **Phase 2**: 10-20 分钟（取决于 API 速率）
- **总数据量**: 约 3000-5000 个文档块
- **JSONL 文件大小**: 约 5-10 MB

## 获取帮助

遇到问题？

1. 检查 [ENV_SETUP.md](ENV_SETUP.md) 确认配置正确
2. 查看终端输出的错误信息
3. 运行 `python example_usage.py` 测试单个组件

---

🎉 **恭喜！您已成功设置 RAG 数据处理管道！**

