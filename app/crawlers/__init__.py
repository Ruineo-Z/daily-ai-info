"""爬虫模块"""

from .base_crawler import BaseCrawler
from .github_trending_web import GitHubTrendingWebCrawler

__all__ = ["BaseCrawler", "GitHubTrendingWebCrawler"]