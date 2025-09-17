"""GitHub Trending 网页爬虫 - 直接爬取官方trending页面"""

import re
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger
from .base_crawler import BaseCrawler
from ..config import GITHUB_TOKEN


class GitHubTrendingWebCrawler(BaseCrawler):
    """GitHub Trending网页爬虫，直接爬取官方trending页面"""

    def __init__(self):
        super().__init__("GitHub Trending Web", api_available=False)
        self.trending_url = "https://github.com/trending"
        self.api_url = "https://api.github.com"
        self.headers = {}

        # 如果有GitHub token，添加到请求头（用于README API请求）
        if GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {GITHUB_TOKEN}"
            logger.info("使用GitHub Token，README API限制提升到5000/小时")
        else:
            logger.warning("未配置GitHub Token，README API限制为60/小时")

    async def crawl(self, fetch_readme: bool = True) -> List[Dict[str, Any]]:
        """爬取GitHub Trending页面"""
        logger.info("开始爬取GitHub Trending官方页面")

        try:
            # 爬取今日trending页面
            response = await self.fetch_with_retry(
                f"{self.trending_url}?since=daily"
            )

            if not response:
                logger.error("无法访问GitHub Trending页面")
                # 按照fail-fast原则，无法访问页面时应该抛出异常
                raise ConnectionError("GitHub Trending页面不可访问，网络连接失败")

            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            trending_repos = self._parse_trending_page(soup)

            if not trending_repos:
                logger.error("未解析到任何trending项目")
                # 按照fail-fast原则，解析失败时应该抛出异常
                raise ValueError("GitHub Trending页面解析失败，未找到任何项目数据")

            # 是否需要获取README内容
            if fetch_readme:
                trending_repos = await self._fetch_readmes(trending_repos)

            logger.info(f"GitHub Trending爬取完成，共 {len(trending_repos)} 个项目")
            return trending_repos

        except Exception as e:
            logger.error(f"GitHub Trending爬取失败: {e}")
            # 按照fail-fast原则，立即抛出异常
            raise RuntimeError(f"GitHub Trending数据爬取失败，系统无法继续处理: {e}") from e

    def _parse_trending_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析trending页面的HTML"""
        repos = []

        try:
            # 查找trending项目列表
            # GitHub的trending页面结构：每个项目在一个article标签中
            repo_articles = soup.find_all('article', class_='Box-row')

            for article in repo_articles:
                repo_data = self._parse_repo_article(article)
                if repo_data:
                    repos.append(repo_data)

            logger.debug(f"解析到 {len(repos)} 个trending项目")
            return repos

        except Exception as e:
            logger.error(f"解析Trending页面失败: {e}")
            # 按照fail-fast原则，立即抛出异常
            raise RuntimeError(f"GitHub Trending页面解析失败，数据格式可能已变化: {e}") from e

    def _parse_repo_article(self, article) -> Optional[Dict[str, Any]]:
        """解析单个项目的article元素"""
        try:
            # 获取项目名称和链接
            title_link = article.find('h2', class_='h3 lh-condensed')
            if not title_link:
                return None

            link_element = title_link.find('a')
            if not link_element:
                return None

            # 项目完整名称 (owner/repo)
            full_name = link_element.get('href', '').strip('/')
            project_url = f"https://github.com/{full_name}"

            # 项目名称
            name_parts = full_name.split('/')
            repo_name = name_parts[-1] if name_parts else "Unknown"

            # 项目描述
            desc_element = article.find('p', class_='col-9')
            description = ""
            if desc_element:
                description = desc_element.get_text(strip=True)

            # 编程语言
            language = ""
            lang_element = article.find('span', {'itemprop': 'programmingLanguage'})
            if lang_element:
                language = lang_element.get_text(strip=True)

            # 获取星数信息
            stars_today = ""
            stars_total = ""

            # 查找今日新增星数
            stars_span = article.find('span', class_='d-inline-block float-sm-right')
            if stars_span:
                stars_today = stars_span.get_text(strip=True)

            # 查找总星数 - 通过链接中包含"stargazers"的元素
            star_links = article.find_all('a', href=re.compile(r'/stargazers$'))
            for star_link in star_links:
                star_text = star_link.get_text(strip=True)
                if star_text and star_text.replace(',', '').isdigit():
                    stars_total = star_text
                    break

            # 获取作者信息
            author = name_parts[0] if len(name_parts) >= 2 else "Unknown"

            return {
                "name": full_name,
                "title": repo_name,
                "description": description or f"{language} 项目，由 {author} 开发",
                "url": project_url,
                "stars": stars_total or "0",
                "stars_today": stars_today,
                "language": language or "Unknown",
                "author": author,
                "source": self.name,
                "crawled_at": self._get_current_time(),
                "type": "repository",
                "platform": "GitHub",
                "trending_rank": len([r for r in [1]]) + 1  # 这里需要传入当前索引
            }

        except Exception as e:
            logger.error(f"解析单个repo失败: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())

        # 移除特殊字符
        text = re.sub(r'[\r\n\t]', ' ', text)

        return text.strip()

    def _parse_number(self, text: str) -> str:
        """解析数字文本（处理k, m等单位）"""
        if not text:
            return "0"

        text = text.strip().lower()

        # 移除非数字字符，但保留k, m
        clean_text = re.sub(r'[^\d.km]', '', text)

        if 'k' in clean_text:
            try:
                num = float(clean_text.replace('k', ''))
                return str(int(num * 1000))
            except Exception as e:
                # 数字解析失败应该抛出具体错误，而不是静默忽略
                raise ValueError(f"k单位数字解析失败，输入格式不符合预期: {clean_text}") from e
        elif 'm' in clean_text:
            try:
                num = float(clean_text.replace('m', ''))
                return str(int(num * 1000000))
            except Exception as e:
                # 数字解析失败应该抛出具体错误，而不是静默忽略
                raise ValueError(f"m单位数字解析失败，输入格式不符合预期: {clean_text}") from e

        # 尝试直接转换
        try:
            return str(int(float(clean_text)))
        except Exception as e:
            # 按照fail-fast原则，数字解析失败应该抛出异常而不是返回默认值
            raise ValueError(f"最终数字解析失败，输入不是有效数字格式: {clean_text}") from e

    async def _fetch_readmes(self, repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """并发获取所有项目的README内容，并发数限制为5"""
        logger.info(f"开始并发获取 {len(repos)} 个项目的README内容")

        # 创建信号量限制并发数为5
        semaphore = asyncio.Semaphore(5)

        # 创建任务列表
        tasks = []
        for repo in repos:
            task = self._fetch_single_readme(semaphore, repo)
            tasks.append(task)

        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        updated_repos = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"获取README失败 {repos[i].get('name', 'unknown')}: {result}")
                # 即使失败也要保留原始项目数据
                updated_repos.append(repos[i])
            else:
                updated_repos.append(result)

        logger.info(f"README获取完成，成功获取 {len([r for r in updated_repos if r.get('readme')])} 个项目的README")
        return updated_repos

    async def _fetch_single_readme(self, semaphore: asyncio.Semaphore, repo: Dict[str, Any]) -> Dict[str, Any]:
        """获取单个项目的README内容"""
        async with semaphore:
            try:
                # 从项目名称中提取owner和repo名
                full_name = repo.get('name', '')
                if '/' not in full_name:
                    logger.warning(f"无效的项目名称: {full_name}")
                    return repo

                owner, repo_name = full_name.split('/', 1)

                # GitHub API获取README
                readme_content = await self._get_repository_readme(owner, repo_name)

                # 将README内容添加到项目数据中
                repo_copy = repo.copy()
                repo_copy['readme'] = readme_content
                repo_copy['readme_length'] = len(readme_content) if readme_content else 0

                if readme_content:
                    logger.debug(f"✓ 获取README成功: {full_name} ({len(readme_content)} 字符)")
                else:
                    logger.debug(f"✗ README为空或获取失败: {full_name}")

                return repo_copy

            except Exception as e:
                logger.error(f"处理项目README失败 {repo.get('name', 'unknown')}: {e}")
                return repo

    async def _get_repository_readme(self, owner: str, repo: str) -> str:
        """获取仓库README内容"""
        try:
            url = f"{self.api_url}/repos/{owner}/{repo}/readme"
            response = await self.fetch_with_retry(url, headers=self.headers)

            if response and response.status_code == 200:
                data = response.json()
                # GitHub API返回的是base64编码的内容
                import base64
                content = base64.b64decode(data.get("content", "")).decode("utf-8")

                # 限制README长度（防止过长）
                max_length = 2000
                if len(content) > max_length:
                    content = content[:max_length] + "\n\n[README内容已截断...]"

                return content

        except Exception as e:
            logger.error(f"获取README失败 {owner}/{repo}: {e}")
            # 按照fail-fast原则，README获取失败应该抛出异常
            raise RuntimeError(f"GitHub API README获取失败: {owner}/{repo}, 原因: {e}") from e