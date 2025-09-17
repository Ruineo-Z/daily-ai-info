"""GitHub自动上传模块 - 将分析报告上传到GitHub仓库"""

import base64
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger
import httpx
from .config import GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME


class GitHubUploader:
    """GitHub文件上传器，自动上传分析报告到指定仓库"""

    def __init__(self):
        if not GITHUB_TOKEN:
            logger.error("GITHUB_TOKEN 未设置，无法使用GitHub上传功能")
            raise ValueError("Missing GITHUB_TOKEN for GitHub upload")

        if not GITHUB_REPO_OWNER or not GITHUB_REPO_NAME:
            logger.error("GitHub仓库信息未配置")
            raise ValueError("Missing GitHub repository configuration")

        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        self.owner = GITHUB_REPO_OWNER
        self.repo = GITHUB_REPO_NAME

        logger.info(f"GitHub上传器初始化完成: {self.owner}/{self.repo}")

    async def upload_report(self, content: str, filepath: str, commit_message: str) -> bool:
        """上传分析报告到GitHub仓库

        Args:
            content: 文件内容
            filepath: GitHub仓库中的文件路径
            commit_message: 提交信息

        Returns:
            bool: 上传是否成功
        """
        try:
            logger.info(f"开始上传报告到GitHub: {filepath}")

            # 检查文件是否已存在
            existing_sha = await self._get_file_sha(filepath)

            # 准备上传数据
            upload_data = {
                "message": commit_message,
                "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                "branch": "main"
            }

            # 如果文件已存在，需要提供SHA
            if existing_sha:
                upload_data["sha"] = existing_sha
                logger.info(f"文件已存在，将更新: {filepath}")
            else:
                logger.info(f"创建新文件: {filepath}")

            # 执行上传
            url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{filepath}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(url, headers=self.headers, json=upload_data)

                if response.status_code in [200, 201]:
                    result = response.json()
                    file_url = result.get("content", {}).get("html_url", "")
                    logger.info(f"✅ 报告上传成功: {file_url}")
                    return True
                else:
                    error_msg = f"GitHub API响应错误: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise RuntimeError(f"GitHub文件上传失败: {error_msg}")

        except Exception as e:
            logger.error(f"上传报告到GitHub失败: {e}")
            raise RuntimeError(f"GitHub上传操作失败，系统无法继续处理: {e}") from e

    async def _get_file_sha(self, filepath: str) -> Optional[str]:
        """获取文件的SHA值（如果文件存在）"""
        try:
            url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{filepath}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code == 200:
                    data = response.json()
                    return data.get("sha")
                elif response.status_code == 404:
                    return None  # 文件不存在
                else:
                    error_msg = f"获取文件信息失败: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise RuntimeError(f"GitHub文件查询失败: {error_msg}")

        except httpx.RequestError as e:
            logger.error(f"GitHub API请求失败: {e}")
            raise RuntimeError(f"GitHub API连接失败，网络错误: {e}") from e
        except Exception as e:
            logger.error(f"检查文件SHA失败: {e}")
            raise RuntimeError(f"GitHub文件状态检查失败: {e}") from e

    async def create_index_page(self, reports: list) -> bool:
        """创建或更新历史报告索引页面"""
        try:
            logger.info("生成历史报告索引页面")

            # 生成索引页面内容
            index_content = self._generate_index_content(reports)

            # 上传索引页面
            commit_message = f"更新报告索引页面 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            success = await self.upload_report(index_content, "README.md", commit_message)

            if success:
                logger.info("✅ 索引页面更新成功")
                return True
            else:
                raise RuntimeError("索引页面上传失败")

        except Exception as e:
            logger.error(f"创建索引页面失败: {e}")
            raise RuntimeError(f"GitHub索引页面生成失败: {e}") from e

    def _generate_index_content(self, reports: list) -> str:
        """生成索引页面的Markdown内容"""
        now = datetime.now()

        content = f"""# 每日AI技术趋势分析报告 📊

> 基于GitHub Trending的AI技术动态深度分析，每日8:30自动更新

## 📈 最新报告

"""

        # 按日期倒序排列报告
        sorted_reports = sorted(reports, key=lambda x: x['date'], reverse=True)

        # 显示最近10份报告
        recent_reports = sorted_reports[:10]
        for report in recent_reports:
            date_str = report['date']
            filename = report['filename']
            filepath = report['filepath']

            content += f"- **{date_str}** - [{filename}]({filepath})\n"

        content += f"""

## 🗂️ 历史归档

### 2024年报告
"""

        # 按月份分组显示历史报告
        monthly_reports = {}
        for report in sorted_reports:
            month_key = report['date'][:7]  # YYYY-MM
            if month_key not in monthly_reports:
                monthly_reports[month_key] = []
            monthly_reports[month_key].append(report)

        for month, month_reports in sorted(monthly_reports.items(), reverse=True):
            content += f"\n#### {month}\n"
            for report in month_reports:
                date_str = report['date']
                filename = report['filename']
                filepath = report['filepath']
                content += f"- [{date_str}]({filepath})\n"

        content += f"""

## 📋 项目信息

- **数据源**: GitHub Trending (Daily)
- **分析引擎**: Google Gemini 2.5 Pro
- **更新频率**: 每日8:30 (北京时间)
- **技术栈**: Python + BeautifulSoup + Gemini AI
- **最后更新**: {now.strftime('%Y-%m-%d %H:%M:%S')}

## 🔧 系统状态

- ✅ GitHub Trending 数据爬取
- ✅ AI智能去重与分析
- ✅ 技术趋势识别
- ✅ 自动报告生成
- ✅ GitHub自动上传

---

*本项目基于开源技术构建，致力于为开发者提供AI技术动态的深度洞察*
"""

        return content

    def generate_github_path(self, local_filepath: str) -> str:
        """将本地文件路径转换为GitHub仓库路径"""
        # 移除本地路径前缀，保留data/目录结构
        if "data/" in local_filepath:
            github_path = local_filepath.split("data/", 1)[1]
        else:
            # 如果没有data前缀，使用文件名
            import os
            github_path = f"reports/{os.path.basename(local_filepath)}"

        return github_path

    async def upload_daily_report(self, content: str, local_filepath: str) -> str:
        """上传每日分析报告并返回GitHub文件URL

        Args:
            content: 报告内容
            local_filepath: 本地文件路径

        Returns:
            str: GitHub文件的URL
        """
        try:
            # 转换为GitHub路径
            github_path = self.generate_github_path(local_filepath)

            # 生成提交信息
            now = datetime.now()
            commit_message = f"📊 每日AI技术分析报告 - {now.strftime('%Y-%m-%d %H:%M')}"

            # 上传报告
            success = await self.upload_report(content, github_path, commit_message)

            if success:
                # 生成文件URL
                file_url = f"https://github.com/{self.owner}/{self.repo}/blob/main/{github_path}"
                logger.info(f"📊 报告已发布: {file_url}")
                return file_url
            else:
                raise RuntimeError("报告上传失败")

        except Exception as e:
            logger.error(f"上传每日报告失败: {e}")
            raise RuntimeError(f"每日报告发布失败: {e}") from e