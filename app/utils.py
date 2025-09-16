"""工具函数模块"""

import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger


def get_today_str() -> str:
    """获取今天的日期字符串 YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")


def get_output_filename(date_str: str = None) -> str:
    """获取输出文件名"""
    if not date_str:
        date_str = get_today_str()
    return f"{date_str}-ai-news.md"


def generate_content_hash(title: str, url: str) -> str:
    """生成内容哈希，用于去重"""
    content = f"{title}|{url}"
    return hashlib.md5(content.encode()).hexdigest()[:8]


def clean_old_files(directory: Path, retention_days: int):
    """清理过期文件"""
    if not directory.exists():
        return

    cutoff_date = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0

    for file_path in directory.iterdir():
        if file_path.is_file():
            # 检查文件修改时间
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_mtime < cutoff_date:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"删除过期文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除文件失败 {file_path}: {e}")

    if deleted_count > 0:
        logger.info(f"清理 {directory} 目录，删除 {deleted_count} 个过期文件")


def format_markdown_section(title: str, items: List[Dict[str, Any]]) -> str:
    """格式化Markdown段落"""
    if not items:
        return ""

    lines = [f"## {title}\n"]

    for i, item in enumerate(items, 1):
        name = item.get('name', item.get('title', 'Unknown'))
        url = item.get('url', item.get('link', '#'))
        description = item.get('description', item.get('summary', ''))

        # 基本信息行
        lines.append(f"### {i}. [{name}]({url})")

        if description:
            lines.append(f"{description}")

        # 额外信息（如果有）
        extra_info = []
        if item.get('stars'):
            extra_info.append(f"⭐ {item['stars']}")
        if item.get('language'):
            extra_info.append(f"🔤 {item['language']}")
        if item.get('authors'):
            extra_info.append(f"👨‍💻 {item['authors']}")

        if extra_info:
            lines.append(f"*{' | '.join(extra_info)}*")

        lines.append("")  # 空行分隔

    return "\n".join(lines)


def create_daily_report_header(date_str: str) -> str:
    """创建每日报告头部"""
    return f"""# AI技术资讯日报 - {date_str}

> 由AI自动收集和总结，每日更新

**数据来源**：
- GitHub Trending (AI/ML)
- Papers with Code
- Hugging Face Models
- arXiv AI Papers
- Towards Data Science

---

"""


def save_markdown_report(file_path: Path, content: str):
    """保存Markdown报告"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"报告保存成功: {file_path}")
    except Exception as e:
        logger.error(f"保存报告失败 {file_path}: {e}")
        raise