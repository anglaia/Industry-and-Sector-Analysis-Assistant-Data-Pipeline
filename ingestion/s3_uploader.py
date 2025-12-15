"""
S3 上传模块 - 先将原始 PDF 上传到 S3，再进行后续处理
"""
import logging
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from core.models import Document
from config.settings import (
    S3_BUCKET_NAME,
    S3_REGION,
    S3_PREFIX,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)

logger = logging.getLogger(__name__)


def _get_s3_client():
    """
    创建 S3 客户端
    """
    session_kwargs = {}
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        session_kwargs["aws_access_key_id"] = AWS_ACCESS_KEY_ID
        session_kwargs["aws_secret_access_key"] = AWS_SECRET_ACCESS_KEY

    session = boto3.session.Session(region_name=S3_REGION, **session_kwargs)
    return session.client("s3")


def upload_pdf_to_s3(document: Document, overwrite: bool = False) -> Optional[str]:
    """
    将 PDF 上传到 S3，并在成功后回填 document.s3_url

    Args:
        document: Document 对象，需包含 local_path 和 source_file
        overwrite: 是否允许覆盖已存在的对象

    Returns:
        s3_url: 上传后的 S3 URL，如果上传失败或未配置 S3 则返回 None
    """
    if not S3_BUCKET_NAME:
        logger.warning("未配置 S3_BUCKET_NAME，跳过上传到 S3 的步骤。")
        return None

    pdf_path = Path(document.local_path)
    if not pdf_path.exists():
        logger.error(f"本地 PDF 文件不存在，无法上传到 S3: {pdf_path}")
        return None

    s3_client = _get_s3_client()

    # 对象 key：前缀 + 文件名
    object_key = f"{S3_PREFIX.rstrip('/')}/{document.source_file}"

    # 如果不允许覆盖，可以先检查对象是否存在
    if not overwrite:
        try:
            s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=object_key)
            # 如果没有抛异常，说明对象已存在
            logger.info(f"S3 对象已存在，跳过上传: s3://{S3_BUCKET_NAME}/{object_key}")
            document.s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{object_key}"
            return document.s3_url
        except ClientError as e:
            # 404 时才继续上传，其他错误需要记录
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code not in ("403", "404", "NoSuchKey"):
                logger.warning(f"检查 S3 对象是否存在时出错，将继续尝试上传: {e}")

    try:
        logger.info(f"开始上传 PDF 到 S3: {pdf_path} -> s3://{S3_BUCKET_NAME}/{object_key}")
        with pdf_path.open("rb") as f:
            s3_client.upload_fileobj(f, S3_BUCKET_NAME, object_key)

        s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{object_key}"
        document.s3_url = s3_url
        logger.info(f"PDF 上传到 S3 成功: {s3_url}")
        return s3_url
    except (BotoCoreError, ClientError) as e:
        logger.error(f"上传 PDF 到 S3 失败: {e}", exc_info=True)
        return None


