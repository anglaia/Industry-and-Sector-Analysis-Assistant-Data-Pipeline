"""
文件处理工具
"""
import hashlib
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta
from utils.logger import logger


class FileUtils:
    """文件处理工具类"""
    
    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = "md5") -> str:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
            algorithm: 哈希算法 (md5, sha1, sha256)
            
        Returns:
            文件哈希值（十六进制字符串）
        """
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    @staticmethod
    def is_duplicate(file_path: Path, existing_hashes: set) -> bool:
        """
        检查文件是否重复
        
        Args:
            file_path: 文件路径
            existing_hashes: 已存在的文件哈希集合
            
        Returns:
            是否重复
        """
        file_hash = FileUtils.calculate_file_hash(file_path)
        return file_hash in existing_hashes
    
    @staticmethod
    def get_file_size_mb(file_path: Path) -> float:
        """
        获取文件大小（MB）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（MB）
        """
        return file_path.stat().st_size / (1024 * 1024)
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """
        生成安全的文件名（移除特殊字符）
        
        Args:
            filename: 原始文件名
            
        Returns:
            安全的文件名
        """
        import re
        # 移除或替换不安全的字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(safe_name) > 200:
            name, ext = safe_name.rsplit('.', 1) if '.' in safe_name else (safe_name, '')
            safe_name = name[:200-len(ext)-1] + '.' + ext if ext else name[:200]
        return safe_name
    
    @staticmethod
    def cleanup_old_files(directory: Path, days: int) -> int:
        """
        清理指定天数之前的文件
        
        Args:
            directory: 目录路径
            days: 天数阈值
            
        Returns:
            删除的文件数量
        """
        if not directory.exists():
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} files older than {days} days from {directory}")
        return deleted_count
    
    @staticmethod
    def compress_files(directory: Path, pattern: str = "*.log") -> int:
        """
        压缩目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            
        Returns:
            压缩的文件数量
        """
        import gzip
        
        if not directory.exists():
            return 0
        
        compressed_count = 0
        
        for file_path in directory.glob(pattern):
            if file_path.suffix != '.gz':
                try:
                    gz_path = file_path.with_suffix(file_path.suffix + '.gz')
                    with open(file_path, 'rb') as f_in:
                        with gzip.open(gz_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    file_path.unlink()
                    compressed_count += 1
                    logger.debug(f"Compressed: {file_path} -> {gz_path}")
                except Exception as e:
                    logger.error(f"Failed to compress {file_path}: {e}")
        
        logger.info(f"Compressed {compressed_count} files in {directory}")
        return compressed_count
    
    @staticmethod
    def ensure_directory(directory: Path) -> Path:
        """
        确保目录存在，不存在则创建
        
        Args:
            directory: 目录路径
            
        Returns:
            目录路径
        """
        directory.mkdir(parents=True, exist_ok=True)
        return directory
    
    @staticmethod
    def get_files_by_extension(directory: Path, extension: str) -> List[Path]:
        """
        获取目录中指定扩展名的所有文件
        
        Args:
            directory: 目录路径
            extension: 文件扩展名（例如 '.pdf'）
            
        Returns:
            文件路径列表
        """
        if not extension.startswith('.'):
            extension = '.' + extension
        
        return list(directory.glob(f'**/*{extension}'))
    
    @staticmethod
    def move_file(src: Path, dst_dir: Path, new_name: Optional[str] = None) -> Path:
        """
        移动文件到目标目录
        
        Args:
            src: 源文件路径
            dst_dir: 目标目录
            new_name: 新文件名（可选）
            
        Returns:
            移动后的文件路径
        """
        FileUtils.ensure_directory(dst_dir)
        
        filename = new_name if new_name else src.name
        dst_path = dst_dir / filename
        
        # 如果目标文件已存在，添加数字后缀
        counter = 1
        while dst_path.exists():
            name_without_ext = dst_path.stem
            ext = dst_path.suffix
            dst_path = dst_dir / f"{name_without_ext}_{counter}{ext}"
            counter += 1
        
        shutil.move(str(src), str(dst_path))
        logger.debug(f"Moved file: {src} -> {dst_path}")
        
        return dst_path

