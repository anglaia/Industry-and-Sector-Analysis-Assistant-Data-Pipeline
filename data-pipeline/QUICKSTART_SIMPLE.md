# 🚀 AI RAG Pipeline - 快速开始（5分钟搞定）

> **最快速的方式构建AI行业RAG知识库**

## ⚡ 极速开始（3步骤）

### 步骤 1: 安装（2分钟）

```bash
cd data-pipeline

# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器
python -m playwright install chromium
```

### 步骤 2: 配置（1分钟）

创建 `.env` 文件，填入两个必需的API密钥：

```bash
PINECONE_API_KEY=pk-xxxxxxxx
GOOGLE_API_KEY=AIzaSyxxxxxxxx
PINECONE_INDEX_NAME=industry-reports
```

**获取API密钥：**
- Pinecone: https://www.pinecone.io/ （免费版）
- Google AI: https://makersuite.google.com/app/apikey （免费）

### 步骤 3: 运行（30秒）

```bash
python run_ai_rag.py --articles 10
```

**完成！** 🎉 你的RAG库已经有了10篇AI行业文章。

---

## 📖 使用示例

### 基础使用
```bash
# 采集10篇AI文章（推荐）
python run_ai_rag.py --articles 10

# 采集5篇文章（快速测试）
python run_ai_rag.py --articles 5

# 采集20篇文章（完整演示）
python run_ai_rag.py --articles 20
```

### 调试模式
```bash
# 显示浏览器窗口（看看爬虫在做什么）
python run_ai_rag.py --articles 5 --no-headless

# 只预览不上传（测试爬虫）
python run_ai_rag.py --articles 5 --preview-only
```

### 获取帮助
```bash
python run_ai_rag.py --help
```

---

## ✅ 验证是否成功

运行后应该看到类似输出：

```
======================================================================
✅ 完成！RAG库已更新
======================================================================
📊 摄取统计:
   - 总文章数: 10
   - 成功: 10
   - 失败: 0
   - 总chunks: 156

🎉 你现在可以在backend-ai中查询这些AI行业内容了!
```

---

## 🔗 下一步

1. **在 backend-ai 中测试查询**
   ```bash
   cd ../backend-ai
   # 启动API服务并测试查询
   ```

2. **了解更多功能**
   - 阅读 [README_SIMPLE.md](README_SIMPLE.md) 了解完整功能
   - 查看 [config/sources.yaml](config/sources.yaml) 了解配置选项

---

## ⚠️ 常见问题

### 问题1: `playwright` 安装失败
```bash
# 手动安装浏览器
python -m playwright install --with-deps chromium
```

### 问题2: API密钥错误
确保 `.env` 文件在 `data-pipeline/` 目录下，格式正确：
```
PINECONE_API_KEY=pk-...    # 注意没有引号
GOOGLE_API_KEY=AIza...
```

### 问题3: 网络连接问题
```bash
# 使用代理（如果需要）
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port

python run_ai_rag.py --articles 5
```

### 问题4: Pinecone索引不存在
首次运行时会自动创建索引，等待约30秒。

---

## 📊 预期性能

| 文章数 | 预计时间 | Pinecone Chunks |
|--------|---------|----------------|
| 5篇    | ~20秒   | ~70 chunks     |
| 10篇   | ~35秒   | ~150 chunks    |
| 20篇   | ~60秒   | ~300 chunks    |

---

## 🎓 演示技巧

如果你要演示这个项目：

```bash
# 1. 准备阶段（提前运行一次）
python run_ai_rag.py --articles 3 --preview-only

# 2. 正式演示（现场运行）
python run_ai_rag.py --articles 5

# 3. 展示效果
# - 强调30秒完成
# - 展示AI关键词过滤
# - 展示Pinecone中的数据
```

---

**需要帮助？** 查看 [README_SIMPLE.md](README_SIMPLE.md) 获取详细文档。

**祝你成功！** 🚀

