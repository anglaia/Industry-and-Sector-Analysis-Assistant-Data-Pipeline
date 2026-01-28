"""
从 S3 导入 PDF 文档到 Pinecone 向量数据库
用于支持 RAG 系统的 Citations 功能

使用示例:
    python import_s3_to_pinecone.py --bucket your-bucket-name --prefix reports/
    python import_s3_to_pinecone.py --preview-only  # 只预览文件列表
    python import_s3_to_pinecone.py --max-files 10  # 限制导入文件数
"""
import os
import argparse
import boto3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import tempfile
from dotenv import load_dotenv

from ingest.batch_processor import BatchProcessor
from processors.pdf_processor import PDFProcessor
from utils.logger import logger
from config.settings import settings

# 加载环境变量
load_dotenv()


class S3PDFImporter:
    """从 S3 导入 PDF 文档到 Pinecone"""
    
    def __init__(
        self, 
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ):
        """
        初始化 S3 客户端
        
        Args:
            bucket_name: S3 bucket 名称（如不提供则从环境变量读取）
            region: AWS region（如不提供则从环境变量读取）
            access_key: AWS Access Key（如不提供则从环境变量读取）
            secret_key: AWS Secret Key（如不提供则从环境变量读取）
        """
        # 从参数或环境变量获取配置
        # 兼容两套命名：
        # - data-pipeline: AWS_S3_BUCKET_NAME / AWS_REGION
        # - 根目录管线: S3_BUCKET_NAME / S3_REGION
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET_NAME") or os.getenv("S3_BUCKET_NAME")
        region = region or os.getenv("AWS_REGION") or os.getenv("S3_REGION") or "us-east-1"
        access_key = access_key or os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = secret_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if not self.bucket_name:
            raise ValueError("必须提供 bucket_name 或设置环境变量 AWS_S3_BUCKET_NAME")
        
        if not access_key or not secret_key:
            raise ValueError("必须提供 AWS credentials 或设置环境变量 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY")
        
        # 初始化 S3 客户端
        self.s3_client = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # 初始化 PDF 处理器
        self.pdf_processor = PDFProcessor()
        
        logger.info(f"✅ S3 客户端初始化成功: {self.bucket_name} ({region})")
    
    def list_pdf_files(self, prefix: str = '', max_files: Optional[int] = None) -> List[Dict]:
        """
        列出 S3 bucket 中的 PDF 文件
        
        Args:
            prefix: S3 key 前缀（类似文件夹路径）
            max_files: 最大文件数限制
            
        Returns:
            文件信息列表
        """
        logger.info(f"🔍 正在扫描 S3 bucket: {self.bucket_name}/{prefix}")
        
        pdf_files = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        
        try:
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # 只处理 PDF 文件
                    if key.lower().endswith('.pdf'):
                        pdf_files.append({
                            'key': key,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                            'filename': Path(key).name
                        })
                        
                        # 检查是否达到最大文件数
                        if max_files and len(pdf_files) >= max_files:
                            logger.info(f"⚠️  已达到最大文件数限制: {max_files}")
                            break
                
                if max_files and len(pdf_files) >= max_files:
                    break
            
            logger.info(f"✅ 找到 {len(pdf_files)} 个 PDF 文件")
            return pdf_files
            
        except Exception as e:
            logger.error(f"❌ 列出文件失败: {e}", exc_info=True)
            return []
    
    def download_and_process_pdf(self, s3_key: str) -> Optional[Dict]:
        """
        从 S3 下载 PDF 并提取文本
        
        Args:
            s3_key: S3 对象的 key
            
        Returns:
            处理后的文档数据，包含文本内容和元数据
        """
        temp_file = None
        
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                temp_file = tmp.name
                
                # 从 S3 下载文件
                logger.debug(f"📥 下载中: {s3_key}")
                self.s3_client.download_file(self.bucket_name, s3_key, temp_file)
                
                # 提取 PDF 文本
                text = self.pdf_processor.extract_text(temp_file)
                
                if not text or len(text.strip()) < 100:
                    logger.warning(f"⚠️  文件内容过短或为空: {s3_key}")
                    return None
                
                # 构建 S3 URL
                s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
                
                # 获取文件名和元数据
                filename = Path(s3_key).name
                
                # 尝试从文件名推断行业类别
                industry = self._infer_industry(filename, text)
                
                doc_data = {
                    'text': text,
                    'file_id': s3_key.replace('/', '_').replace('.pdf', ''),
                    'industry': industry,
                    'metadata': {
                        'source_file': filename,
                        's3_url': s3_url,
                        's3_key': s3_key,
                        'bucket': self.bucket_name,
                        'file_size': os.path.getsize(temp_file),
                        'ingestion_date': datetime.now().isoformat(),
                        'source_type': 's3_import'
                    }
                }
                
                logger.debug(f"✅ 处理完成: {filename} ({len(text)} 字符)")
                return doc_data
                
        except Exception as e:
            logger.error(f"❌ 处理文件失败 {s3_key}: {e}", exc_info=True)
            return None
            
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def _infer_industry(self, filename: str, text: str) -> str:
        """
        从文件名或内容推断行业类别
        
        Args:
            filename: 文件名
            text: 文本内容（取前1000字符）
            
        Returns:
            行业类别
        """
        # 行业关键词映射
        industry_keywords = {
            'Technology': ['tech', 'software', 'ai', 'artificial intelligence', 'cloud', 'saas', 'digital'],
            'Healthcare': ['health', 'medical', 'pharma', 'biotech', 'clinical', 'patient'],
            'Finance': ['finance', 'banking', 'fintech', 'investment', 'insurance', 'trading'],
            'Energy': ['energy', 'oil', 'gas', 'renewable', 'solar', 'wind', 'power'],
            'Manufacturing': ['manufacturing', 'factory', 'production', 'supply chain', 'automotive'],
            'Retail': ['retail', 'ecommerce', 'consumer', 'shopping', 'merchandise'],
            'Education': ['education', 'learning', 'university', 'school', 'academic'],
        }
        
        # 合并文件名和文本前1000字符用于分析
        combined_text = f"{filename.lower()} {text[:1000].lower()}"
        
        # 查找匹配的行业
        for industry, keywords in industry_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return industry
        
        return 'General'  # 默认类别
    
    def import_to_pinecone(
        self, 
        prefix: str = '', 
        max_files: Optional[int] = None,
        preview_only: bool = False
    ) -> Dict:
        """
        执行导入流程
        
        Args:
            prefix: S3 key 前缀
            max_files: 最大文件数
            preview_only: 仅预览不导入
            
        Returns:
            导入结果统计
        """
        # 步骤1: 列出文件
        pdf_files = self.list_pdf_files(prefix, max_files)
        
        if not pdf_files:
            logger.error("❌ 未找到任何 PDF 文件")
            return {'total': 0, 'successful': 0, 'failed': 0}
        
        # 预览模式
        if preview_only:
            logger.info("\n" + "=" * 70)
            logger.info("📋 预览模式 - 文件列表")
            logger.info("=" * 70)
            
            for i, file_info in enumerate(pdf_files, 1):
                logger.info(f"{i}. {file_info['filename']}")
                logger.info(f"   路径: {file_info['key']}")
                logger.info(f"   大小: {file_info['size']:,} bytes")
                logger.info(f"   修改时间: {file_info['last_modified']}")
                logger.info("")
            
            total_size = sum(f['size'] for f in pdf_files)
            logger.info(f"📊 统计: {len(pdf_files)} 个文件, 总大小: {total_size:,} bytes")
            return {'total': len(pdf_files), 'successful': 0, 'failed': 0}
        
        # 步骤2: 下载并处理所有 PDF
        logger.info("\n" + "=" * 70)
        logger.info(f"📥 步骤 1/2: 下载并处理 PDF 文件")
        logger.info("=" * 70)
        
        documents = []
        failed_count = 0
        
        for i, file_info in enumerate(pdf_files, 1):
            logger.info(f"[{i}/{len(pdf_files)}] 处理中: {file_info['filename']}")
            
            doc_data = self.download_and_process_pdf(file_info['key'])
            
            if doc_data:
                documents.append(doc_data)
            else:
                failed_count += 1
        
        if not documents:
            logger.error("❌ 没有成功处理任何文件")
            return {'total': len(pdf_files), 'successful': 0, 'failed': failed_count}
        
        logger.info(f"✅ 成功处理 {len(documents)} 个文件, 失败 {failed_count} 个")
        
        # 步骤3: 批量导入到 Pinecone
        logger.info("\n" + "=" * 70)
        logger.info("🚀 步骤 2/2: 向量化并上传到 Pinecone")
        logger.info("=" * 70)
        
        try:
            processor = BatchProcessor()
            result = processor.ingester.ingest_batch(documents)
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ 导入完成！")
            logger.info("=" * 70)
            logger.info(f"📊 导入统计:")
            logger.info(f"   - 总文件数: {result['total']}")
            logger.info(f"   - 成功: {result['successful']}")
            logger.info(f"   - 失败: {result['failed']}")
            logger.info(f"   - 总 chunks: {result['total_chunks']}")
            logger.info(f"\n🎉 现在你可以在前端看到带 Citations 的内容了!")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 导入到 Pinecone 失败: {e}", exc_info=True)
            return {'total': len(documents), 'successful': 0, 'failed': len(documents)}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="从 S3 导入 PDF 文档到 Pinecone 向量数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 导入所有 PDF
  python import_s3_to_pinecone.py
  
  # 导入指定前缀（文件夹）的 PDF
  python import_s3_to_pinecone.py --prefix reports/2024/
  
  # 只预览文件列表
  python import_s3_to_pinecone.py --preview-only
  
  # 限制导入文件数（用于测试）
  python import_s3_to_pinecone.py --max-files 5
  
  # 指定 bucket（不使用环境变量）
  python import_s3_to_pinecone.py --bucket my-bucket-name
        """
    )
    
    parser.add_argument(
        '--bucket',
        type=str,
        help='S3 bucket 名称（默认从环境变量 AWS_S3_BUCKET_NAME 读取）'
    )
    
    parser.add_argument(
        '--prefix',
        type=str,
        default='',
        help='S3 key 前缀（类似文件夹路径，例如: reports/2024/）'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        help='最大导入文件数（用于测试）'
    )
    
    parser.add_argument(
        '--preview-only',
        action='store_true',
        help='只预览文件列表，不实际导入'
    )
    
    args = parser.parse_args()
    
    # 验证配置
    if not settings.validate_required_keys():
        logger.error("❌ 请先配置 PINECONE_API_KEY 和 GOOGLE_API_KEY")
        logger.error("   可以在 backend-ai/.env 或 data-pipeline/.env 中配置")
        return 1
    
    # 显示配置信息
    bucket_name = args.bucket or os.getenv('AWS_S3_BUCKET_NAME', '<未设置>')
    
    logger.info("=" * 70)
    logger.info("📦 S3 到 Pinecone 导入工具")
    logger.info("=" * 70)
    logger.info(f"📝 配置:")
    logger.info(f"   - S3 Bucket: {bucket_name}")
    logger.info(f"   - 前缀: {args.prefix or '(所有文件)'}")
    logger.info(f"   - 最大文件数: {args.max_files or '(无限制)'}")
    logger.info(f"   - 预览模式: {'是' if args.preview_only else '否'}")
    logger.info(f"   - Pinecone 索引: {settings.pinecone_index_name}")
    logger.info("")
    
    try:
        # 初始化导入器
        importer = S3PDFImporter(bucket_name=args.bucket)
        
        # 执行导入
        result = importer.import_to_pinecone(
            prefix=args.prefix,
            max_files=args.max_files,
            preview_only=args.preview_only
        )
        
        if result['total'] > 0 and (result['successful'] > 0 or args.preview_only):
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  用户中断操作")
        return 1
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

