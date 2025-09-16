"""配置管理模块"""

import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# API配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "2"))

# 爬取配置
CRAWL_SCHEDULE_HOUR = int(os.getenv("CRAWL_SCHEDULE_HOUR", "6"))
CRAWL_SCHEDULE_MINUTE = int(os.getenv("CRAWL_SCHEDULE_MINUTE", "0"))

# 数据保留配置
DATA_RETENTION_DAYS = int(os.getenv("DATA_RETENTION_DAYS", "30"))

# AI配置
AI_DEDUP_ENABLED = os.getenv("AI_DEDUP_ENABLED", "true").lower() == "true"
AI_SUMMARY_ENABLED = os.getenv("AI_SUMMARY_ENABLED", "true").lower() == "true"
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "4000"))

# 目标网站配置
TARGET_SITES = {
    "github_trending": {
        "name": "GitHub Trending (AI/ML)",
        "url": "https://api.github.com/search/repositories",
        "api_available": True,
        "priority": 1
    },
    "papers_with_code": {
        "name": "Papers with Code",
        "url": "https://paperswithcode.com/",
        "api_available": False,  # 需要确认
        "priority": 2
    },
    "huggingface": {
        "name": "Hugging Face Models",
        "url": "https://huggingface.co/api/models",
        "api_available": True,
        "priority": 3
    },
    "arxiv": {
        "name": "arXiv AI Papers",
        "url": "http://export.arxiv.org/api/query",
        "api_available": True,
        "priority": 4
    },
    "towards_datascience": {
        "name": "Towards Data Science",
        "url": "https://towardsdatascience.com/",
        "api_available": False,
        "priority": 5
    }
}

# HTTP请求配置
REQUEST_TIMEOUT = 30
REQUEST_RETRY_TIMES = 3
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 验证必需的配置
def validate_config():
    """验证关键配置是否存在"""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY 未设置，AI功能将无法使用")
        return False

    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN 未设置，GitHub API限制较低")

    logger.info(f"配置加载完成: 数据目录={DATA_DIR}, 日志目录={LOGS_DIR}")
    return True