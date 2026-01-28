"""
简化版 S3 导入脚本
直接运行，无需复杂依赖
"""
import os
import sys
import boto3
import tempfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加 backend-ai 到 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend-ai"))

try:
    from app.services.rag_service import RAGService
    print("✅ 成功导入 RAGService")
except Exception as e:
    print(f"❌ 导入 RAGService 失败: {e}")
    sys.exit(1)

def main():
    print("=" * 70)
    print("📦 S3 到 Pinecone 导入工具（简化版）")
    print("=" * 70)
    print()
    
    # 读取配置
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    region = os.getenv('AWS_REGION', 'ap-southeast-2')
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    if not all([bucket_name, access_key, secret_key]):
        print("❌ 缺少 AWS 配置")
        print("   请确保 .env 文件包含:")
        print("   - AWS_S3_BUCKET_NAME")
        print("   - AWS_ACCESS_KEY_ID")
        print("   - AWS_SECRET_ACCESS_KEY")
        return 1
    
    print(f"📝 配置:")
    print(f"   - Bucket: {bucket_name}")
    print(f"   - Region: {region}")
    print()
    
    # 初始化 S3 客户端
    try:
        s3_client = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        print("✅ S3 客户端初始化成功")
    except Exception as e:
        print(f"❌ S3 客户端初始化失败: {e}")
        return 1
    
    # 列出 PDF 文件
    print()
    print("=" * 70)
    print("🔍 扫描 S3 Bucket...")
    print("=" * 70)
    print()
    
    try:
        pdf_files = []
        paginator = s3_client.get_paginator('list_objects_v2')
        
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                key = obj['Key']
                if key.lower().endswith('.pdf'):
                    pdf_files.append({
                        'key': key,
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'filename': Path(key).name
                    })
        
        print(f"✅ 找到 {len(pdf_files)} 个 PDF 文件")
        print()
        
        if pdf_files:
            print("📋 文件列表:")
            print("-" * 70)
            for i, file_info in enumerate(pdf_files, 1):
                size_mb = file_info['size'] / (1024 * 1024)
                print(f"{i}. {file_info['filename']}")
                print(f"   路径: {file_info['key']}")
                print(f"   大小: {size_mb:.2f} MB")
                print(f"   修改时间: {file_info['last_modified']}")
                print()
        
        return 0
        
    except Exception as e:
        print(f"❌ 扫描失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

