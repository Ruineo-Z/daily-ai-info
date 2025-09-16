"""Daily AI Info - 主程序入口"""

import asyncio
from datetime import datetime
from app.logger_config import setup_logger
from app.config import validate_config
from app.crawlers.github_trending_web import GitHubTrendingWebCrawler
from app.ai_processor import AIProcessor
from loguru import logger


def generate_report_path():
    """生成按日期组织的GitHub Trending分析报告路径"""
    import os

    today = datetime.now()
    year = today.strftime("%Y")           # 2025
    month = today.strftime("%m")          # 09
    day = today.strftime("%d")            # 16
    time_str = today.strftime("%H%M")     # 2323

    # 按日期组织目录结构: data/2025/09/16/
    date_dir = os.path.join("data", year, month, day)

    # 确保目录存在
    os.makedirs(date_dir, exist_ok=True)

    # 文件名: GitHub-Trending-AI分析_HHMM.md
    filename = f"GitHub-Trending-AI分析_{time_str}.md"
    filepath = os.path.join(date_dir, filename)

    return filename, filepath, date_dir


def generate_markdown_report(summary_result: dict, projects: list) -> str:
    """生成GitHub Trending AI技术分析报告"""
    today = datetime.now().strftime("%Y年%m月%d日")

    markdown = f"""# GitHub Trending AI技术分析报告 - {today}

> 基于GitHub Daily Trending的AI技术动态深度分析

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

    # 统计分析
    markdown += "## 📊 GitHub Trending数据分析\n\n"
    markdown += f"- **分析项目总数**: {len(projects)}\n"

    # 编程语言分析
    languages = {}
    for project in projects:
        lang = project.get('language', 'Unknown')
        languages[lang] = languages.get(lang, 0) + 1

    top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:7]
    markdown += f"- **编程语言分布**: {', '.join([f'{lang}({count})' for lang, count in top_languages])}\n"

    # Stars活跃度分析
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
    markdown += f"- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    markdown += f"- **AI分析引擎**: Google Gemini 2.5 Pro\n"
    markdown += f"- **分析深度**: 项目描述 + README内容\n"
    markdown += f"- **报告格式**: Markdown v1.0\n"

    return markdown


async def main():
    """主程序 - GitHub Trending AI技术分析"""
    # 初始化日志
    setup_logger()
    logger.info("=== GitHub Trending AI技术分析程序启动 ===")

    # 验证配置
    if not validate_config():
        logger.error("配置验证失败，程序退出")
        return

    try:
        # 步骤1: 爬取GitHub Trending数据
        logger.info("🔍 开始爬取GitHub Trending数据")
        async with GitHubTrendingWebCrawler() as crawler:
            trending_data = await crawler.crawl(fetch_readme=True)

        if not trending_data:
            logger.error("未获取到trending数据，程序退出")
            return

        logger.info(f"✅ 爬取完成，获得 {len(trending_data)} 个热门项目")

        # 步骤2: AI处理与分析
        logger.info("🤖 启动AI分析引擎")
        ai_processor = AIProcessor()

        logger.info("🧹 执行智能去重")
        deduplicated_data = await ai_processor.deduplicate_by_titles(trending_data)

        logger.info("📝 生成技术洞察与趋势分析")
        summary_result = await ai_processor.summarize_content(deduplicated_data)

        # 步骤3: 生成专业报告
        logger.info("📋 生成GitHub Trending AI技术分析报告")
        markdown_content = generate_markdown_report(summary_result, deduplicated_data)

        # 保存报告 - 按日期组织目录
        filename, filepath, date_dir = generate_report_path()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        # 输出结果统计
        trends_count = len(summary_result.get('trends', []))
        logger.info(f"🎉 分析完成！")
        logger.info(f"📊 处理统计:")
        logger.info(f"   - 分析项目: {len(deduplicated_data)} 个")
        logger.info(f"   - 技术趋势: {trends_count} 个")
        logger.info(f"   - 报告目录: {date_dir}")
        logger.info(f"   - 报告文件: {filename}")
        logger.info(f"   - 完整路径: {filepath}")
        logger.info(f"   - 文件大小: {len(markdown_content):,} 字符")

        logger.info("✅ GitHub Trending AI技术分析程序执行完成")

    except Exception as e:
        logger.error(f"❌ 程序执行失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())