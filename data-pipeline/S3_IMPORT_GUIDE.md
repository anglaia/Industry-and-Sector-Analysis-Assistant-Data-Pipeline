# 📦 从 S3 导入文档到 Pinecone - 完整指南

## 🎯 目标

将存储在 AWS S3 的 PDF 文档导入到 Pinecone 向量数据库，以支持前端的 Citations（溯源）功能。

---

## 🔧 前置准备

### 1. 安装依赖

```bash
cd data-pipeline
pip install -r requirements.txt
```

### 2. 配置环境变量

你需要在 **两个地方** 配置环境变量：

#### A. `backend-node/.env` （已有配置）
```env
# AWS S3 配置
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

#### B. `data-pipeline/.env` （新建文件）
复制 `backend-node/.env` 的 AWS 配置，同时添加 AI 相关配置：

```bash
# 创建 .env 文件
cd data-pipeline
cp env.template .env
```

编辑 `.env` 文件，添加以下内容：

```env
# ========== AWS S3 配置 ==========
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# ========== Google Gemini API ==========
GOOGLE_API_KEY=your_google_api_key_here

# ========== Pinecone 配置 ==========
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=industry-reports
```

---

## 🚀 使用方法

### 方式 1: 预览文件列表（推荐先执行）

先查看 S3 里有哪些 PDF 文件：

```bash
cd data-pipeline
python import_s3_to_pinecone.py --preview-only
```

**示例输出：**
```
📋 预览模式 - 文件列表
======================================================================
1. Lab_Equipment_Report_2024.pdf
   路径: reports/Lab_Equipment_Report_2024.pdf
   大小: 1,234,567 bytes
   修改时间: 2024-01-15 10:30:00

2. ROI_Analysis_2024.pdf
   路径: reports/ROI_Analysis_2024.pdf
   大小: 987,654 bytes
   修改时间: 2024-01-20 14:20:00

📊 统计: 2 个文件, 总大小: 2,222,221 bytes
```

---

### 方式 2: 导入所有 PDF

```bash
cd data-pipeline
python import_s3_to_pinecone.py
```

**执行流程：**
1. 扫描 S3 bucket，找到所有 `.pdf` 文件
2. 逐个下载并提取文本内容
3. 分块、生成向量嵌入
4. 上传到 Pinecone 向量数据库

---

### 方式 3: 导入指定文件夹的 PDF

如果你的 S3 有文件夹结构，可以只导入某个文件夹：

```bash
# 导入 reports/2024/ 文件夹下的所有 PDF
python import_s3_to_pinecone.py --prefix reports/2024/

# 导入 industry-reports/ 文件夹
python import_s3_to_pinecone.py --prefix industry-reports/
```

---

### 方式 4: 测试模式（限制文件数）

先导入少量文件测试：

```bash
# 只导入前 5 个 PDF 文件
python import_s3_to_pinecone.py --max-files 5
```

---

## 📊 导入结果示例

成功执行后，你会看到：

```
🚀 步骤 2/2: 向量化并上传到 Pinecone
======================================================================
✅ 导入完成！
======================================================================
📊 导入统计:
   - 总文件数: 5
   - 成功: 5
   - 失败: 0
   - 总 chunks: 87

🎉 现在你可以在前端看到带 Citations 的内容了!
```

---

## ✅ 验证导入结果

### 1. 检查 Pinecone 数据库

访问 [Pinecone Console](https://app.pinecone.io/) 查看索引统计。

### 2. 测试 backend-ai 的 RAG 查询

```bash
cd backend-ai
python test_canvas_api.py
```

### 3. 前端测试

1. 启动前端和后端服务
2. 在 Live Demo 页面点击任意 Canvas 卡片
3. 等待内容生成完成
4. **滚动到底部**，查看 "References & Sources" 部分
5. 你应该能看到引用列表，包含：
   - 引用 ID（如 [1], [2]）
   - 源文件名
   - 页码
   - 文本预览
   - "View Source Document" 链接

---

## 🔍 故障排查

### 问题 1: 提示 "AWS credentials not found"

**解决方法：**
- 确认 `data-pipeline/.env` 文件存在
- 检查 `AWS_ACCESS_KEY_ID` 和 `AWS_SECRET_ACCESS_KEY` 是否正确

### 问题 2: 提示 "NoSuchBucket" 错误

**解决方法：**
- 检查 `AWS_S3_BUCKET_NAME` 是否正确
- 确认你的 AWS 账号有权限访问该 bucket

### 问题 3: 找不到任何 PDF 文件

**解决方法：**
- 使用 `--preview-only` 查看文件列表
- 检查 `--prefix` 参数是否正确
- 确认 S3 里确实有 `.pdf` 文件

### 问题 4: 导入成功，但前端没有 Citations

**可能原因：**

1. **测试模式未关闭**：
   - 检查 `frontend/src/components/LiveDemo.tsx`
   - 确保 `const isTestMode = false;` （第 457 行）

2. **use_rag 未启用**：
   - 检查 `frontend/src/components/LiveDemo.tsx`
   - 确保 `use_rag: true` （第 499 行）

3. **backend-ai 未重启**：
   - 重启 AI 后端以重新连接 Pinecone

4. **前端缓存问题**：
   - 清除浏览器缓存或硬刷新（Ctrl+Shift+R）

---

## 📋 完整工作流程

```bash
# 1. 预览文件
cd data-pipeline
python import_s3_to_pinecone.py --preview-only

# 2. 测试导入（先导入 5 个文件）
python import_s3_to_pinecone.py --max-files 5

# 3. 确认成功后，导入所有文件
python import_s3_to_pinecone.py

# 4. 关闭测试模式（如果之前开启了）
# 编辑 frontend/src/components/LiveDemo.tsx
# 设置: const isTestMode = false;

# 5. 重启服务
cd ../backend-ai
python main.py  # 或 run.bat

cd ../frontend
npm run dev

# 6. 测试前端 Citations
# 打开浏览器，进入 Live Demo，点击任意卡片，查看底部的 References
```

---

## 🎉 成功标志

当你看到以下内容时，说明导入成功：

1. ✅ `import_s3_to_pinecone.py` 显示 "导入完成"
2. ✅ Pinecone Console 显示向量数增加
3. ✅ backend-ai 启动时日志显示连接到 Pinecone
4. ✅ frontend 卡片底部显示 "References & Sources"
5. ✅ Citations 包含真实的文件名和 S3 URL

---

## 💡 高级选项

### 定制行业分类

编辑 `import_s3_to_pinecone.py` 的 `_infer_industry` 方法，添加你的行业关键词：

```python
industry_keywords = {
    'YourIndustry': ['keyword1', 'keyword2', 'keyword3'],
    # ...
}
```

### 批量定期更新

创建定时任务，每天自动导入新文档：

```bash
# Linux/Mac (crontab)
0 2 * * * cd /path/to/data-pipeline && python import_s3_to_pinecone.py >> logs/import.log 2>&1
```

---

## 📞 需要帮助？

如果遇到问题：

1. 查看日志文件：`data-pipeline/storage/logs/`
2. 检查环境变量配置
3. 使用 `--preview-only` 调试
4. 先用 `--max-files 1` 测试单个文件

---

**祝你导入顺利！🚀**

