"""
日志配置
使用 loguru 提供强大的日志功能
"""
import sys
from pathlib import Path
from loguru import logger
from config.settings import settings

# 移除默认的处理器
logger.remove()

# 添加控制台输出（带颜色）
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True
)

# 添加文件输出 - 常规日志
logger.add(
    settings.logs_path / "data_pipeline_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="00:00",  # 每天轮换
    retention=f"{settings.log_retention_days} days",  # 保留天数
    compression="zip",  # 压缩旧日志
    encoding="utf-8"
)

# 添加文件输出 - 错误日志（单独文件）
logger.add(
    settings.logs_path / "errors_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="00:00",
    retention="90 days",  # 错误日志保留更久
    compression="zip",
    encoding="utf-8"
)

# 如果配置了 Sentry，添加错误追踪
if hasattr(settings, 'sentry_dsn') and settings.sentry_dsn:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=1.0
        )
        logger.info("Sentry error tracking initialized")
    except ImportError:
        logger.warning("Sentry SDK not installed, skipping error tracking")

# 导出日志记录器
__all__ = ['logger']

