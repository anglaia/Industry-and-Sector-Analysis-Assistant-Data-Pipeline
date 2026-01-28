"""
自动创建 .env 文件（非交互式）
"""
from pathlib import Path

def read_env_vars(env_path):
    """读取 .env 文件的变量"""
    env_vars = {}
    if not Path(env_path).exists():
        return env_vars
    
    try:
        for encoding in ['utf-8', 'gbk', 'latin-1']:
            try:
                with open(env_path, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
                print(f"✅ 读取 {env_path} 成功 (编码: {encoding})")
                return env_vars
            except UnicodeDecodeError:
                continue
    except Exception as e:
        print(f"⚠️  读取 {env_path} 失败: {e}")
    
    return env_vars

def main():
    print("=" * 70)
    print("🔧 自动配置 data-pipeline/.env")
    print("=" * 70)
    print()
    
    # 判断当前目录
    current_dir = Path.cwd().name
    if current_dir == 'data-pipeline':
        backend_node_path = '../backend-node/.env'
        backend_ai_path = '../backend-ai/.env'
    else:
        backend_node_path = 'backend-node/.env'
        backend_ai_path = 'backend-ai/.env'
    
    # 读取配置
    backend_node = read_env_vars(backend_node_path)
    backend_ai = read_env_vars(backend_ai_path)
    
    if not backend_node and not backend_ai:
        print("❌ 未找到任何配置文件")
        return 1
    
    # 提取配置
    config = {
        'AWS_REGION': backend_node.get('AWS_REGION', 'ap-southeast-2'),
        'AWS_S3_BUCKET_NAME': backend_node.get('AWS_S3_BUCKET_NAME', ''),
        'AWS_ACCESS_KEY_ID': backend_node.get('AWS_ACCESS_KEY_ID', ''),
        'AWS_SECRET_ACCESS_KEY': backend_node.get('AWS_SECRET_ACCESS_KEY', ''),
        'GOOGLE_API_KEY': backend_ai.get('GOOGLE_API_KEY', ''),
        'PINECONE_API_KEY': backend_ai.get('PINECONE_API_KEY', ''),
        'PINECONE_ENVIRONMENT': backend_ai.get('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
        'PINECONE_INDEX_NAME': backend_ai.get('PINECONE_INDEX_NAME', 'industry-reports'),
    }
    
    print("📋 找到以下配置：")
    print(f"   - AWS Bucket: {config['AWS_S3_BUCKET_NAME'] or '(未设置)'}")
    print(f"   - AWS Region: {config['AWS_REGION']}")
    print(f"   - AWS Access Key: {'***' + config['AWS_ACCESS_KEY_ID'][-4:] if config['AWS_ACCESS_KEY_ID'] else '(未设置)'}")
    print(f"   - Google API Key: {'***' + config['GOOGLE_API_KEY'][-4:] if config['GOOGLE_API_KEY'] else '(未设置)'}")
    print(f"   - Pinecone API Key: {'***' + config['PINECONE_API_KEY'][-4:] if config['PINECONE_API_KEY'] else '(未设置)'}")
    print(f"   - Pinecone Index: {config['PINECONE_INDEX_NAME']}")
    print()
    
    # 生成 .env 内容
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
    
    # 写入文件
    try:
        env_file_path = 'data-pipeline/.env' if current_dir != 'data-pipeline' else '.env'
        with open(env_file_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ .env 文件创建成功！")
        print()
        print("=" * 70)
        print("📋 下一步：")
        print("=" * 70)
        print("   1. 运行: python import_s3_to_pinecone.py --preview-only")
        print("   2. 运行: python import_s3_to_pinecone.py")
        print()
        return 0
        
    except Exception as e:
        print(f"❌ 创建文件失败: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

