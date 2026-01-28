# 环境变量配置指南

## 快速设置

在 `rag-pipeline` 目录下创建一个 `.env` 文件，包含以下内容：

```env
# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Pinecone API Key and Environment
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=rag-news-index
```

## 详细说明

### 1. 获取 Gemini API Key

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 登录你的 Google 账户
3. 点击 "Create API Key" 创建新的 API 密钥
4. 复制生成的 API 密钥
5. 将密钥粘贴到 `.env` 文件的 `GEMINI_API_KEY` 字段

```env
GEMINI_API_KEY=AIzaSyC_your_actual_api_key_here
```

### 2. 获取 Pinecone API Key

1. 访问 [Pinecone Console](https://app.pinecone.io/)
2. 注册或登录你的账户
3. 进入 "API Keys" 页面
4. 复制你的 API Key
5. 将密钥粘贴到 `.env` 文件的 `PINECONE_API_KEY` 字段

```env
PINECONE_API_KEY=your-pinecone-api-key-here
```

### 3. 设置 Pinecone Environment

Pinecone 环境通常是你创建项目时选择的云服务区域，例如：
- `us-east-1`
- `us-west-1`
- `eu-west-1`
- `asia-southeast-1`

你可以在 Pinecone Console 的项目设置中找到你的环境。

```env
PINECONE_ENVIRONMENT=us-east-1
```

### 4. 设置 Pinecone Index Name

这是你想要创建或使用的 Pinecone 索引名称。如果索引不存在，程序会自动创建。

```env
PINECONE_INDEX_NAME=rag-news-index
```

## 完整示例

```env
# Gemini API Key
GEMINI_API_KEY=AIzaSyC_your_actual_gemini_api_key_here

# Pinecone Configuration
PINECONE_API_KEY=abcd1234-5678-90ef-ghij-klmnopqrstuv
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=rag-news-index
```

## 验证配置

运行以下命令验证配置是否正确：

```python
from dotenv import load_dotenv
import os

load_dotenv()

print("Gemini API Key:", "✓ 已设置" if os.getenv("GEMINI_API_KEY") else "✗ 未设置")
print("Pinecone API Key:", "✓ 已设置" if os.getenv("PINECONE_API_KEY") else "✗ 未设置")
print("Pinecone Environment:", "✓ 已设置" if os.getenv("PINECONE_ENVIRONMENT") else "✗ 未设置")
print("Pinecone Index Name:", os.getenv("PINECONE_INDEX_NAME", "rag-news-index"))
```

## 安全提示

⚠️ **重要**: 
- **永远不要**将 `.env` 文件提交到 Git 仓库
- `.env` 文件已在 `.gitignore` 中被忽略
- 不要在代码或文档中硬编码 API 密钥
- 定期轮换你的 API 密钥

## 故障排查

### 问题：无法加载环境变量

**解决方案**：
1. 确保 `.env` 文件在 `rag-pipeline` 目录的根目录下
2. 检查文件名是否正确（`.env`，不是 `env.txt` 或其他）
3. 确保安装了 `python-dotenv` 包：`pip install python-dotenv`

### 问题：API 密钥无效

**解决方案**：
1. 重新检查复制的 API 密钥是否完整
2. 确保密钥没有多余的空格或换行符
3. 尝试重新生成 API 密钥

### 问题：Pinecone 连接失败

**解决方案**：
1. 验证 Pinecone 环境设置是否正确
2. 检查网络连接
3. 确认 Pinecone 账户状态是否正常

