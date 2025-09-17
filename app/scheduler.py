"""定时任务调度器 - 每天早上8:30执行GitHub Trending分析"""

import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor
from pytz import timezone
from loguru import logger
from .crawlers.github_trending_web import GitHubTrendingWebCrawler
from .ai_processor import AIProcessor
from .github_uploader import GitHubUploader
from .static_site_generator import StaticSiteGenerator
import os
import json


class DailyAIScheduler:
    """每日AI资讯定时调度器"""

    def __init__(self):
        # 设置上海时区
        self.shanghai_tz = timezone('Asia/Shanghai')

        # 配置调度器
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,  # 不合并作业
            'max_instances': 1  # 同时最多一个实例
        }

        self.scheduler = AsyncIOScheduler(
            executors=executors,
            job_defaults=job_defaults,
            timezone=self.shanghai_tz
        )

        # 初始化静态网站生成器
        self.site_generator = StaticSiteGenerator()

        logger.info("定时调度器初始化完成，时区：上海")

    def generate_report_path(self):
        """生成按日期组织的报告路径"""
        now = datetime.now(self.shanghai_tz)
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        time_str = now.strftime("%H%M")

        # 按日期组织目录结构
        date_dir = os.path.join("data", year, month, day)
        os.makedirs(date_dir, exist_ok=True)

        filename = f"GitHub-Trending-AI分析_{time_str}.md"
        filepath = os.path.join(date_dir, filename)

        return filename, filepath, date_dir

    def generate_markdown_report(self, summary_result: dict, projects: list) -> str:
        """生成Markdown报告"""
        now = datetime.now(self.shanghai_tz)
        today_str = now.strftime("%Y年%m月%d日")

        markdown = f"""# GitHub Trending AI技术分析报告 - {today_str}

> 基于GitHub Daily Trending的AI技术动态深度分析
>
> 🕐 **生成时间**: {now.strftime('%Y-%m-%d %H:%M:%S')} (上海时区)

## 📋 今日摘要

{summary_result.get('summary', '今日AI技术资讯已整理完成')}

"""

        # 技术趋势
        trends = summary_result.get('trends', [])
        if trends:
            markdown += "## 📈 核心技术趋势\n\n"
            for i, trend in enumerate(trends, 1):
                markdown += f"{i}. {trend}\n"
            markdown += "\n"

        # 项目详情
        markdown += f"## 🚀 GitHub热门项目深度解析 ({len(projects)}个)\n\n"
        project_summaries = summary_result.get('project_summaries', [])

        for i, project in enumerate(projects, 1):
            name = project.get('name', 'Unknown')
            description = project.get('description', '暂无描述')
            url = project.get('url', '#')
            stars = project.get('stars', '0')
            language = project.get('language', 'Unknown')
            stars_today = project.get('stars_today', '')
            author = project.get('author', 'Unknown')

            markdown += f"### {i}. [{name}]({url})\n\n"

            # AI生成的技术洞察
            if i <= len(project_summaries) and project_summaries[i-1]:
                ai_summary = project_summaries[i-1].strip()
                # 清理前缀
                prefixes = [f"{i}.", f"{i}、", "- ", "* ", f"**{name}**: ", f"**{name.split('/')[-1]}**: "]
                for prefix in prefixes:
                    if ai_summary.startswith(prefix):
                        ai_summary = ai_summary[len(prefix):].strip()
                        break
                markdown += f"**AI技术洞察**: {ai_summary}\n\n"
            else:
                markdown += f"**项目简介**: {description}\n\n"

            markdown += f"**GitHub数据**:\n"
            markdown += f"- ⭐ **Stars**: {stars}"
            if stars_today:
                markdown += f" (今日+{stars_today})"
            markdown += f"\n- 💻 **主语言**: {language}\n"
            markdown += f"- 👨‍💻 **作者**: {author}\n\n"
            markdown += "---\n\n"

        # 数据统计
        markdown += "## 📊 GitHub Trending数据分析\n\n"
        markdown += f"- **分析项目总数**: {len(projects)}\n"

        # 编程语言统计
        languages = {}
        for project in projects:
            lang = project.get('language', 'Unknown')
            languages[lang] = languages.get(lang, 0) + 1

        top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:7]
        markdown += f"- **编程语言分布**: {', '.join([f'{lang}({count})' for lang, count in top_languages])}\n"

        # Stars活跃度
        total_stars_today = 0
        for project in projects:
            stars_today_str = project.get('stars_today', '').replace(' stars today', '').replace(',', '')
            if stars_today_str.isdigit():
                total_stars_today += int(stars_today_str)

        if total_stars_today > 0:
            markdown += f"- **今日新增Stars总数**: {total_stars_today:,}\n"

        # 报告信息
        markdown += f"\n## 📋 分析报告信息\n\n"
        markdown += f"- **数据来源**: GitHub Trending (Daily)\n"
        markdown += f"- **执行时间**: {now.strftime('%Y-%m-%d %H:%M:%S')} (Asia/Shanghai)\n"
        markdown += f"- **AI分析引擎**: Google Gemini 2.5 Pro\n"
        markdown += f"- **分析深度**: 项目描述 + README内容\n"
        markdown += f"- **调度方式**: 定时任务 (每日8:30)\n"
        markdown += f"- **报告格式**: Markdown v1.0\n"

        return markdown

    async def run_daily_analysis(self):
        """执行每日AI技术分析任务"""
        now = datetime.now(self.shanghai_tz)
        logger.info(f"🕐 开始执行每日AI技术分析 - {now.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # 步骤1: 爬取GitHub Trending数据
            logger.info("🔍 爬取GitHub Trending数据")
            async with GitHubTrendingWebCrawler() as crawler:
                trending_data = await crawler.crawl(fetch_readme=True)

            if not trending_data:
                logger.error("❌ 未获取到trending数据，任务失败")
                return False

            logger.info(f"✅ 爬取成功，获得 {len(trending_data)} 个热门项目")

            # 步骤2: AI处理与分析
            logger.info("🤖 启动AI分析引擎")
            ai_processor = AIProcessor()

            logger.info("🧹 执行智能去重")
            deduplicated_data = await ai_processor.deduplicate_by_titles(trending_data)

            logger.info("📝 生成技术洞察与趋势分析")
            summary_result = await ai_processor.summarize_content(deduplicated_data)

            # 步骤3: 生成并保存报告
            logger.info("📋 生成每日分析报告")
            markdown_content = self.generate_markdown_report(summary_result, deduplicated_data)

            filename, filepath, date_dir = self.generate_report_path()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            # 步骤4: 保存数据到JSON文件（用于静态网站）
            logger.info("💾 保存数据到本地存储")
            report_data = {
                "date": now.strftime("%Y-%m-%d"),
                "generation_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "summary": summary_result.get('summary', ''),
                "trends": summary_result.get('trends', []),
                "project_summaries": summary_result.get('project_summaries', []),
                "projects": deduplicated_data
            }

            # 保存当前报告数据
            json_filepath = filepath.replace('.md', '.json')
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            # 步骤5: 生成静态网站
            logger.info("🌐 生成静态网站")
            try:
                # 加载历史数据
                historical_data = self._load_historical_reports()
                historical_data.append(report_data)

                # 生成静态网站
                site_success = self.site_generator.generate_site(historical_data, summary_result)
                if site_success:
                    site_size = self.site_generator.get_output_size()
                    logger.info(f"✅ 静态网站生成成功，大小: {site_size}")
                else:
                    raise RuntimeError("静态网站生成失败")
            except Exception as e:
                logger.error(f"静态网站生成失败: {e}")
                raise RuntimeError(f"静态网站生成失败，用户无法访问最新内容: {e}") from e

            # 步骤6: 上传到GitHub（保留作为备份）
            github_url = None
            try:
                logger.info("📤 上传报告到GitHub")
                github_uploader = GitHubUploader()
                github_url = await github_uploader.upload_daily_report(markdown_content, filepath)
                logger.info(f"🌐 GitHub备份成功: {github_url}")
            except Exception as e:
                logger.warning(f"GitHub备份失败（非致命错误）: {e}")

            # 输出执行结果
            trends_count = len(summary_result.get('trends', []))
            logger.info("🎉 每日AI技术分析完成！")
            logger.info(f"📊 执行结果:")
            logger.info(f"   - 分析项目: {len(deduplicated_data)} 个")
            logger.info(f"   - 技术趋势: {trends_count} 个")
            logger.info(f"   - 报告目录: {date_dir}")
            logger.info(f"   - 报告文件: {filename}")
            logger.info(f"   - 文件大小: {len(markdown_content):,} 字符")
            logger.info(f"   - 静态网站大小: {self.site_generator.get_output_size()}")
            if github_url:
                logger.info(f"   - GitHub备份: {github_url}")

            return True

        except Exception as e:
            logger.error(f"❌ 每日分析任务执行失败: {e}")
            return False

    def _load_historical_reports(self) -> list:
        """加载历史报告数据"""
        historical_data = []
        data_dir = os.path.join("data")

        if not os.path.exists(data_dir):
            return historical_data

        try:
            # 遍历年/月/日目录结构
            for year_dir in os.listdir(data_dir):
                year_path = os.path.join(data_dir, year_dir)
                if not os.path.isdir(year_path):
                    continue

                for month_dir in os.listdir(year_path):
                    month_path = os.path.join(year_path, month_dir)
                    if not os.path.isdir(month_path):
                        continue

                    for day_dir in os.listdir(month_path):
                        day_path = os.path.join(month_path, day_dir)
                        if not os.path.isdir(day_path):
                            continue

                        # 查找JSON文件
                        for file in os.listdir(day_path):
                            if file.endswith('.json'):
                                json_path = os.path.join(day_path, file)
                                try:
                                    with open(json_path, 'r', encoding='utf-8') as f:
                                        report_data = json.load(f)
                                        historical_data.append(report_data)
                                except Exception as e:
                                    logger.warning(f"加载历史报告失败 {json_path}: {e}")

            # 按日期排序
            historical_data.sort(key=lambda x: x.get('date', ''), reverse=True)
            logger.info(f"加载了 {len(historical_data)} 份历史报告")

        except Exception as e:
            logger.error(f"加载历史报告失败: {e}")

        return historical_data

    def add_daily_job(self):
        """添加每日8:30的定时任务"""
        self.scheduler.add_job(
            func=self.run_daily_analysis,
            trigger=CronTrigger(
                hour=8,           # 8点
                minute=30,        # 30分
                timezone=self.shanghai_tz
            ),
            id='daily_ai_analysis',
            name='每日AI技术分析',
            replace_existing=True
        )
        logger.info("✅ 定时任务已配置: 每天8:30 (上海时区) 执行AI技术分析")

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("🚀 定时调度器已启动")

        # 显示下次执行时间
        next_run = self.scheduler.get_job('daily_ai_analysis').next_run_time
        if next_run:
            next_run_shanghai = next_run.astimezone(self.shanghai_tz)
            logger.info(f"📅 下次执行时间: {next_run_shanghai.strftime('%Y-%m-%d %H:%M:%S')} (上海时区)")

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("🛑 定时调度器已停止")

    async def test_run(self):
        """测试运行一次分析任务"""
        logger.info("🧪 测试模式：立即执行一次分析任务")
        result = await self.run_daily_analysis()
        if result:
            logger.info("✅ 测试运行成功")
        else:
            logger.error("❌ 测试运行失败")
        return result