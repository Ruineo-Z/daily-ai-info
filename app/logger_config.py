"""日志配置模块"""

import sys
from loguru import logger
from .config import LOG_LEVEL, LOG_RETENTION_DAYS, LOGS_DIR

def setup_logger():
    """配置loguru日志"""
    # 移除默认的控制台输出
    logger.remove()

    # 添加控制台输出（带颜色）
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    # 添加文件输出（自动轮转）
    logger.add(
        LOGS_DIR / "daily-ai-info.log",
        level=LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="00:00",  # 每天0点轮转
        retention=f"{LOG_RETENTION_DAYS} days",  # 保留天数
        compression="zip",  # 压缩旧日志
        encoding="utf-8"
    )

    # 错误日志单独文件
    logger.add(
        LOGS_DIR / "errors.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 week",
        retention=f"{LOG_RETENTION_DAYS} days",
        compression="zip",
        encoding="utf-8"
    )

    logger.info(f"日志系统初始化完成，保留{LOG_RETENTION_DAYS}天日志")