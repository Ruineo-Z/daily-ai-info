"""超轻量级静态网站生成器 - 专为2核2G服务器优化"""

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from .config import PROJECT_ROOT


class StaticSiteGenerator:
    """静态网站生成器，生成轻量级HTML网站"""

    def __init__(self, output_dir: str = "dist"):
        self.project_root = Path(PROJECT_ROOT)
        self.templates_dir = self.project_root / "app" / "templates"
        self.output_dir = Path(output_dir)

        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)

        # 初始化Jinja2模板引擎
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

        logger.info(f"静态网站生成器初始化: 输出目录 {self.output_dir}")

    def generate_site(self, reports_data: List[Dict[str, Any]],
                     latest_summary: Dict[str, Any]) -> bool:
        """生成完整的静态网站"""
        try:
            logger.info("开始生成静态网站")

            # 1. 清理旧文件但保留结构
            self._clean_output_dir()

            # 2. 处理数据
            processed_data = self._process_reports_data(reports_data)

            # 3. 生成首页
            self._generate_index_page(processed_data, latest_summary)

            # 4. 生成历史归档页
            self._generate_archive_page(processed_data)

            # 5. 生成每日报告页面
            self._generate_report_pages(reports_data)

            # 6. 生成关于页面
            self._generate_about_page()

            # 7. 生成API数据文件
            self._generate_api_data(processed_data)

            # 8. 创建robots.txt和sitemap
            self._generate_seo_files(processed_data)

            logger.info("✅ 静态网站生成完成")
            return True

        except Exception as e:
            logger.error(f"静态网站生成失败: {e}")
            raise RuntimeError(f"静态网站生成失败: {e}") from e

    def _clean_output_dir(self):
        """清理输出目录，但保留必要的结构"""
        if self.output_dir.exists():
            # 只删除HTML文件和API文件，保留可能的静态资源
            for item in self.output_dir.iterdir():
                if item.is_file() and item.suffix in ['.html', '.json', '.xml', '.txt']:
                    item.unlink()
                elif item.is_dir() and item.name in ['reports', 'api']:
                    shutil.rmtree(item)

    def _process_reports_data(self, reports_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理报告数据，生成统计信息"""
        if not reports_data:
            return {
                "total_reports": 0,
                "total_projects": 0,
                "total_trends": 0,
                "active_days": 0,
                "years": [],
                "reports_by_year": {},
                "recent_reports": [],
                "language_stats": {},
                "total_stars_today": 0
            }

        # 按时间排序
        sorted_reports = sorted(reports_data, key=lambda x: x.get('date', ''), reverse=True)
        recent_reports = sorted_reports[:7]  # 最近7天

        # 统计信息
        total_projects = sum(len(report.get('projects', [])) for report in reports_data)
        total_trends = sum(len(report.get('trends', [])) for report in reports_data)

        # 按年月分组
        reports_by_year = {}
        years = set()

        for report in sorted_reports:
            date_str = report.get('date', '')
            if not date_str:
                continue

            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                year = str(date_obj.year)
                month = f"{date_obj.month:02d}"

                years.add(year)

                if year not in reports_by_year:
                    reports_by_year[year] = {}
                if month not in reports_by_year[year]:
                    reports_by_year[year][month] = []

                # 添加URL和其他元数据
                report_with_meta = report.copy()
                report_with_meta['url'] = f"/reports/{date_str}.html"
                report_with_meta['projects_count'] = len(report.get('projects', []))
                report_with_meta['trends_count'] = len(report.get('trends', []))

                reports_by_year[year][month].append(report_with_meta)

            except ValueError:
                logger.warning(f"无效的日期格式: {date_str}")
                continue

        # 语言统计
        language_stats = {}
        total_stars_today = 0

        for report in reports_data:
            for project in report.get('projects', []):
                lang = project.get('language', 'Unknown')
                language_stats[lang] = language_stats.get(lang, 0) + 1

                # 统计今日新增Stars
                stars_today_str = str(project.get('stars_today', '')).replace(',', '')
                try:
                    if stars_today_str.isdigit():
                        total_stars_today += int(stars_today_str)
                except (ValueError, TypeError):
                    pass

        # 排序语言统计
        sorted_language_stats = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_reports": len(reports_data),
            "total_projects": total_projects,
            "total_trends": total_trends,
            "active_days": len(reports_data),
            "years": sorted(years, reverse=True),
            "reports_by_year": reports_by_year,
            "recent_reports": [
                {
                    "date": r.get('date', ''),
                    "url": f"/reports/{r.get('date', '')}.html",
                    "projects_count": len(r.get('projects', []))
                } for r in recent_reports
            ],
            "language_stats": sorted_language_stats,
            "total_stars_today": total_stars_today
        }

    def _generate_index_page(self, processed_data: Dict[str, Any],
                           latest_summary: Dict[str, Any]):
        """生成首页"""
        template = self.env.get_template('index.html')

        # 准备最新的项目数据
        latest_projects = []
        if processed_data['recent_reports']:
            # 从最新报告中获取项目
            latest_date = processed_data['recent_reports'][0]['date']
            for report in self._load_reports_data():
                if report.get('date') == latest_date:
                    latest_projects = report.get('projects', [])[:10]  # 只显示前10个
                    break

        # 添加AI摘要到项目中
        for i, project in enumerate(latest_projects):
            if 'project_summaries' in latest_summary and i < len(latest_summary['project_summaries']):
                project['ai_summary'] = latest_summary['project_summaries'][i]

        content = template.render(
            current_page='index',
            last_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            summary=latest_summary.get('summary', ''),
            trends=latest_summary.get('trends', []),
            projects=latest_projects,
            recent_reports=processed_data['recent_reports'],
            language_stats=processed_data['language_stats'],
            total_stars_today=processed_data['total_stars_today']
        )

        output_file = self.output_dir / "index.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ 首页生成完成: {output_file}")

    def _generate_archive_page(self, processed_data: Dict[str, Any]):
        """生成历史归档页面"""
        template = self.env.get_template('archive.html')

        content = template.render(
            current_page='archive',
            **processed_data
        )

        output_file = self.output_dir / "archive.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ 归档页面生成完成: {output_file}")

    def _generate_report_pages(self, reports_data: List[Dict[str, Any]]):
        """生成每日报告页面"""
        template = self.env.get_template('report.html')
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(exist_ok=True)

        for report in reports_data:
            date_str = report.get('date', '')
            if not date_str:
                continue

            # 处理项目数据，添加AI摘要
            projects = report.get('projects', [])
            project_summaries = report.get('project_summaries', [])

            for i, project in enumerate(projects):
                if i < len(project_summaries):
                    project['ai_summary'] = project_summaries[i]

            # 计算语言统计
            language_stats = {}
            total_stars_today = 0

            for project in projects:
                lang = project.get('language', 'Unknown')
                language_stats[lang] = language_stats.get(lang, 0) + 1

                stars_today_str = str(project.get('stars_today', '')).replace(',', '')
                try:
                    if stars_today_str.isdigit():
                        total_stars_today += int(stars_today_str)
                except (ValueError, TypeError):
                    pass

            sorted_language_stats = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)

            content = template.render(
                current_page='report',
                report_title=f"GitHub Trending AI技术分析报告 - {date_str}",
                generation_time=report.get('generation_time', date_str),
                summary=report.get('summary', ''),
                trends=report.get('trends', []),
                projects=projects,
                language_stats=sorted_language_stats,
                total_stars_today=total_stars_today
            )

            output_file = reports_dir / f"{date_str}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

        logger.info(f"✅ {len(reports_data)} 个报告页面生成完成")

    def _generate_about_page(self):
        """生成关于页面"""
        about_content = """
        <div class="card">
            <div class="card-header">
                <h1 class="card-title">关于本项目</h1>
            </div>
            <div class="card-body">
                <h2>项目简介</h2>
                <p>每日AI技术趋势分析是一个自动化的AI技术资讯分析系统，通过爬取GitHub Trending数据，结合Google Gemini AI进行智能分析，为开发者提供最新的AI技术动态和趋势洞察。</p>

                <h2>技术架构</h2>
                <ul>
                    <li><strong>数据来源</strong>: GitHub Trending API</li>
                    <li><strong>AI分析</strong>: Google Gemini 2.5 Pro</li>
                    <li><strong>调度系统</strong>: APScheduler (每日8:30自动执行)</li>
                    <li><strong>网站生成</strong>: 静态HTML页面，优化加载速度</li>
                </ul>

                <h2>功能特点</h2>
                <ul>
                    <li>🔍 自动爬取GitHub热门AI项目</li>
                    <li>🤖 AI智能去重和内容分析</li>
                    <li>📈 技术趋势识别和总结</li>
                    <li>📱 响应式设计，支持移动设备</li>
                    <li>🚀 极速加载，优化用户体验</li>
                </ul>

                <h2>联系方式</h2>
                <p>如有问题或建议，欢迎联系我们。</p>
            </div>
        </div>
        """

        template = self.env.get_template('base.html')
        content = template.render(
            current_page='about',
            page_title='关于本项目'
        ).replace('{% block content %}{% endblock %}', about_content)

        output_file = self.output_dir / "about.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ 关于页面生成完成: {output_file}")

    def _generate_api_data(self, processed_data: Dict[str, Any]):
        """生成API数据文件"""
        api_dir = self.output_dir / "api"
        api_dir.mkdir(exist_ok=True)

        # 生成汇总API
        api_data = {
            "stats": {
                "total_reports": processed_data["total_reports"],
                "total_projects": processed_data["total_projects"],
                "total_trends": processed_data["total_trends"],
                "active_days": processed_data["active_days"]
            },
            "recent_reports": processed_data["recent_reports"],
            "language_stats": processed_data["language_stats"],
            "last_updated": datetime.now().isoformat()
        }

        with open(api_dir / "summary.json", 'w', encoding='utf-8') as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)

        logger.info("✅ API数据文件生成完成")

    def _generate_seo_files(self, processed_data: Dict[str, Any]):
        """生成SEO相关文件"""
        # robots.txt
        robots_content = """User-agent: *
Allow: /

Sitemap: /sitemap.xml
"""
        with open(self.output_dir / "robots.txt", 'w', encoding='utf-8') as f:
            f.write(robots_content)

        # sitemap.xml
        sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>/archive.html</loc>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>/about.html</loc>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
"""

        # 添加报告页面
        for report in processed_data["recent_reports"]:
            sitemap_content += f"""    <url>
        <loc>{report['url']}</loc>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>
"""

        sitemap_content += "</urlset>"

        with open(self.output_dir / "sitemap.xml", 'w', encoding='utf-8') as f:
            f.write(sitemap_content)

        logger.info("✅ SEO文件生成完成")

    def _load_reports_data(self) -> List[Dict[str, Any]]:
        """加载历史报告数据"""
        # 这里应该从实际的数据存储中加载
        # 临时返回空列表
        return []

    def get_output_size(self) -> str:
        """获取输出目录大小"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.output_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)

            # 转换为人类可读格式
            if total_size < 1024:
                return f"{total_size}B"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.1f}KB"
            else:
                return f"{total_size / (1024 * 1024):.1f}MB"
        except Exception as e:
            logger.error(f"计算输出大小失败: {e}")
            return "未知"