"""定时任务运行器 - 启动每日AI技术分析调度器"""

import asyncio
import signal
import sys
from app.logger_config import setup_logger
from app.config import validate_config
from app.scheduler import DailyAIScheduler
from loguru import logger


class SchedulerRunner:
    """调度器运行器"""

    def __init__(self):
        self.scheduler = None
        self.running = True

    async def run(self):
        """运行调度器"""
        # 初始化
        setup_logger()
        logger.info("=== Daily AI Info 定时调度器启动 ===")

        # 验证配置
        if not validate_config():
            logger.error("配置验证失败，程序退出")
            return

        # 创建并配置调度器
        self.scheduler = DailyAIScheduler()
        self.scheduler.add_daily_job()

        # 设置信号处理
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，开始优雅关闭...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # 终止信号

        try:
            # 启动调度器
            self.scheduler.start()

            logger.info("📋 调度器运行状态:")
            logger.info("   - 任务名称: 每日AI技术分析")
            logger.info("   - 执行时间: 每天8:30")
            logger.info("   - 时区: Asia/Shanghai")
            logger.info("   - 数据源: GitHub Trending")
            logger.info("   - AI引擎: Gemini 2.5 Pro")
            logger.info("")
            logger.info("🎯 调度器已就绪，等待定时执行...")
            logger.info("💡 按 Ctrl+C 优雅退出")

            # 保持运行状态
            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("用户中断，开始关闭...")
        except Exception as e:
            logger.error(f"调度器运行异常: {e}")
        finally:
            if self.scheduler:
                self.scheduler.stop()
            logger.info("✅ 定时调度器已安全关闭")

    async def test_mode(self):
        """测试模式：立即执行一次分析"""
        setup_logger()
        logger.info("=== Daily AI Info 测试模式 ===")

        if not validate_config():
            logger.error("配置验证失败，程序退出")
            return

        scheduler = DailyAIScheduler()
        success = await scheduler.test_run()

        if success:
            logger.info("🎉 测试模式执行完成")
        else:
            logger.error("❌ 测试模式执行失败")


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # 测试模式
        runner = SchedulerRunner()
        asyncio.run(runner.test_mode())
    else:
        # 正常运行模式
        runner = SchedulerRunner()
        try:
            asyncio.run(runner.run())
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()