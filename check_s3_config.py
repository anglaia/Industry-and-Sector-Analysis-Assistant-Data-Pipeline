"""
检查 S3 配置脚本
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    S3_BUCKET_NAME,
    S3_REGION,
    S3_PREFIX,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)

print("=" * 60)
print("S3 配置检查")
print("=" * 60)
print(f"S3_BUCKET_NAME: {S3_BUCKET_NAME or '(未配置)'}")
print(f"S3_REGION: {S3_REGION}")
print(f"S3_PREFIX: {S3_PREFIX}")
print(f"AWS_ACCESS_KEY_ID: {'已配置' if AWS_ACCESS_KEY_ID else '(未配置，将使用默认凭据)'}")
print(f"AWS_SECRET_ACCESS_KEY: {'已配置' if AWS_SECRET_ACCESS_KEY else '(未配置，将使用默认凭据)'}")
print("=" * 60)

if not S3_BUCKET_NAME:
    print("\n❌ 问题：S3_BUCKET_NAME 未配置")
    print("\n请在 .env 文件中添加以下配置：")
    print("S3_BUCKET_NAME=your-bucket-name")
    print("S3_REGION=us-east-1  # 根据你的bucket区域修改")
    print("S3_PREFIX=documents/  # 可选")
    print("\n如果需要使用特定的 AWS 凭据，还可以添加：")
    print("AWS_ACCESS_KEY_ID=your-access-key-id")
    print("AWS_SECRET_ACCESS_KEY=your-secret-access-key")
else:
    print("\n✅ S3_BUCKET_NAME 已配置")
    print("如果仍然无法上传，请检查：")
    print("1. AWS 凭据是否正确（如果配置了）")
    print("2. S3 bucket 是否存在")
    print("3. AWS 权限是否足够（需要 s3:PutObject 权限）")
