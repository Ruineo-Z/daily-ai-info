#!/usr/bin/env python3
"""立即执行一次完整流程并生成静态网站"""

import asyncio
from app.scheduler import DailyAIScheduler
from loguru import logger

async def main():
    """立即执行一次分析流程"""
    logger.info("🚀 立即执行AI分析和网站生成流程")

    scheduler = DailyAIScheduler()

    # 直接调用日常分析方法
    await scheduler.run_daily_analysis()

    logger.info("✅ 立即执行完成")

if __name__ == "__main__":
    asyncio.run(main())