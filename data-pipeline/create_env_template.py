"""
创建 data-pipeline 的 .env 配置文件
避免编码问题
"""
import os
from pathlib import Path

def create_env_file():
    """创建 .env 文件模板"""
    
    # 检查是否已存在
    env_file = Path('.env')
    if env_file.exists():
        response = input("⚠️  .env 文件已存在，是否覆盖？(y/n): ")
        if response.lower() != 'y':
            print("❌ 已取消操作")
            return
    
    # 获取配置信息
    print("=" * 70)
    print("📝 配置 data-pipeline 环境变量")
    print("=" * 70)
    print()
    print("请输入以下配置信息（或按 Enter 跳过）：")
    print()
    
    # AWS 配置
    print("========== AWS S3 配置 ==========")
    aws_region = input("AWS_REGION [us-east-1]: ").strip() or "us-east-1"
    aws_bucket = input("AWS_S3_BUCKET_NAME: ").strip()
    aws_access_key = input("AWS_ACCESS_KEY_ID: ").strip()
    aws_secret_key = input("AWS_SECRET_ACCESS_KEY: ").strip()
    print()
    
    # Google API 配置
    print("========== Google Gemini API ==========")
    google_api_key = input("GOOGLE_API_KEY: ").strip()
    print()
    
    # Pinecone 配置
    print("========== Pinecone 配置 ==========")
    pinecone_api_key = input("PINECONE_API_KEY: ").strip()
    pinecone_env = input("PINECONE_ENVIRONMENT [us-west1-gcp]: ").strip() or "us-west1-gcp"
    pinecone_index = input("PINECONE_INDEX_NAME [industry-reports]: ").strip() or "industry-reports"
    print()
    
    # 生成 .env 文件内容（纯 ASCII，避免编码问题）
    env_content = f"""# ========== AWS S3 Configuration ==========
AWS_REGION={aws_region}
AWS_S3_BUCKET_NAME={aws_bucket}
AWS_ACCESS_KEY_ID={aws_access_key}
AWS_SECRET_ACCESS_KEY={aws_secret_key}

# ========== Google Gemini API ==========
GOOGLE_API_KEY={google_api_key}
# 支持写 "gemini-embedding-001" 或 "models/gemini-embedding-001"
EMBEDDING_MODEL=gemini-embedding-001

# ========== Pinecone Configuration ==========
PINECONE_API_KEY={pinecone_api_key}
PINECONE_ENVIRONMENT={pinecone_env}
PINECONE_INDEX_NAME={pinecone_index}
PINECONE_DIMENSION=3072

# ========== Chunk Configuration ==========
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5

# ========== Other Settings ==========
MAX_FILE_SIZE_MB=50
LOG_LEVEL=INFO
"""
    
    # 写入文件（使用 UTF-8 编码）
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("=" * 70)
        print("✅ .env 文件创建成功！")
        print("=" * 70)
        print()
        print("📋 下一步：")
        print("   1. 查看 .env 文件确认配置正确")
        print("   2. 运行: python import_s3_to_pinecone.py --preview-only")
        print("   3. 运行: python import_s3_to_pinecone.py")
        print()
        
    except Exception as e:
        print(f"❌ 创建文件失败: {e}")
        return


def read_existing_env(env_path: str):
    """读取现有的 .env 文件"""
    if not Path(env_path).exists():
        print(f"⚠️  未找到 {env_path}")
        return {}
    
    env_vars = {}
    try:
        # 尝试多种编码
        for encoding in ['utf-8', 'gbk', 'latin-1']:
            try:
                with open(env_path, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
                print(f"✅ 成功读取 {env_path} (编码: {encoding})")
                return env_vars
            except UnicodeDecodeError:
                continue
        
        print(f"⚠️  无法读取 {env_path}，编码不支持")
        return {}
        
    except Exception as e:
        print(f"⚠️  读取 {env_path} 失败: {e}")
        return {}


def auto_import_from_other_envs():
    """自动从其他 .env 文件导入配置"""
    print("=" * 70)
    print("🔍 尝试从其他 .env 文件自动导入配置...")
    print("=" * 70)
    print()
    
    # 读取 backend-node/.env
    backend_node_env = read_existing_env('../backend-node/.env')
    
    # 读取 backend-ai/.env
    backend_ai_env = read_existing_env('../backend-ai/.env')
    
    print()
    
    if not backend_node_env and not backend_ai_env:
        print("⚠️  未找到任何现有配置，需要手动输入")
        print()
        return None
    
    # 合并配置
    merged_config = {
        'AWS_REGION': backend_node_env.get('AWS_REGION', 'us-east-1'),
        'AWS_S3_BUCKET_NAME': backend_node_env.get('AWS_S3_BUCKET_NAME', ''),
        'AWS_ACCESS_KEY_ID': backend_node_env.get('AWS_ACCESS_KEY_ID', ''),
        'AWS_SECRET_ACCESS_KEY': backend_node_env.get('AWS_SECRET_ACCESS_KEY', ''),
        'GOOGLE_API_KEY': backend_ai_env.get('GOOGLE_API_KEY', ''),
        'PINECONE_API_KEY': backend_ai_env.get('PINECONE_API_KEY', ''),
        'PINECONE_ENVIRONMENT': backend_ai_env.get('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
        'PINECONE_INDEX_NAME': backend_ai_env.get('PINECONE_INDEX_NAME', 'industry-reports'),
    }
    
    print("📋 找到以下配置：")
    print(f"   - AWS Bucket: {merged_config['AWS_S3_BUCKET_NAME'] or '(未设置)'}")
    print(f"   - AWS Region: {merged_config['AWS_REGION']}")
    print(f"   - Google API Key: {'***' + merged_config['GOOGLE_API_KEY'][-4:] if merged_config['GOOGLE_API_KEY'] else '(未设置)'}")
    print(f"   - Pinecone API Key: {'***' + merged_config['PINECONE_API_KEY'][-4:] if merged_config['PINECONE_API_KEY'] else '(未设置)'}")
    print(f"   - Pinecone Index: {merged_config['PINECONE_INDEX_NAME']}")
    print()
    
    return merged_config


def create_env_from_config(config: dict):
    """根据配置创建 .env 文件"""
    env_content = f"""# ========== AWS S3 Configuration ==========
AWS_REGION={config['AWS_REGION']}
AWS_S3_BUCKET_NAME={config['AWS_S3_BUCKET_NAME']}
AWS_ACCESS_KEY_ID={config['AWS_ACCESS_KEY_ID']}
AWS_SECRET_ACCESS_KEY={config['AWS_SECRET_ACCESS_KEY']}

# ========== Google Gemini API ==========
GOOGLE_API_KEY={config['GOOGLE_API_KEY']}
# 支持写 "gemini-embedding-001" 或 "models/gemini-embedding-001"
EMBEDDING_MODEL=gemini-embedding-001

# ========== Pinecone Configuration ==========
PINECONE_API_KEY={config['PINECONE_API_KEY']}
PINECONE_ENVIRONMENT={config['PINECONE_ENVIRONMENT']}
PINECONE_INDEX_NAME={config['PINECONE_INDEX_NAME']}
PINECONE_DIMENSION=3072

# ========== Chunk Configuration ==========
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5

# ========== Other Settings ==========
MAX_FILE_SIZE_MB=50
LOG_LEVEL=INFO
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ .env 文件创建成功！")
        return True
    except Exception as e:
        print(f"❌ 创建文件失败: {e}")
        return False


def main():
    """主函数"""
    print()
    print("=" * 70)
    print("🛠️  data-pipeline 环境配置工具")
    print("=" * 70)
    print()
    
    # 尝试自动导入
    config = auto_import_from_other_envs()
    
    if config:
        response = input("是否使用以上配置创建 .env 文件？(y/n): ")
        if response.lower() == 'y':
            if create_env_from_config(config):
                print()
                print("=" * 70)
                print("📋 下一步：")
                print("=" * 70)
                print("   1. 查看 .env 文件确认配置正确")
                print("   2. 运行: python import_s3_to_pinecone.py --preview-only")
                print("   3. 运行: python import_s3_to_pinecone.py")
                print()
            return
    
    # 手动输入
    print()
    print("请选择配置方式：")
    print("  1. 手动输入配置信息")
    print("  2. 退出")
    print()
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == '1':
        create_env_file()
    else:
        print("❌ 已取消操作")


if __name__ == "__main__":
    main()

