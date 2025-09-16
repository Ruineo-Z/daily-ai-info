"""AI处理模块 - 使用Gemini进行去重和总结"""

import google.generativeai as genai
from typing import List, Dict, Any, Optional
from loguru import logger
from .config import GEMINI_API_KEY, GEMINI_MODEL, AI_MAX_TOKENS
import asyncio
import time


class AIProcessor:
    """AI处理器，负责去重和内容总结"""

    def __init__(self):
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY 未设置，AI功能无法使用")
            raise ValueError("Missing GEMINI_API_KEY")

        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        logger.info(f"Gemini AI 初始化完成，模型: {GEMINI_MODEL}")

    async def _call_ai_with_retry(self, prompt: str, max_retries: int = 3, base_delay: int = 2) -> str:
        """带重试机制的AI调用"""
        for attempt in range(max_retries):
            try:
                logger.info(f"AI调用尝试 {attempt + 1}/{max_retries}")

                # 设置较长的超时时间
                response = await asyncio.to_thread(
                    lambda: self.model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=AI_MAX_TOKENS,
                            temperature=0.3
                        )
                    )
                )

                if response and response.text:
                    logger.info("AI调用成功")
                    return response.text.strip()
                else:
                    raise ValueError("AI返回空响应")

            except Exception as e:
                logger.warning(f"AI调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    # 指数退避策略
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"等待 {delay} 秒后重试...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"AI调用完全失败，已重试 {max_retries} 次")
                    raise e

    async def deduplicate_by_titles(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于标题进行AI去重"""
        if len(items) <= 1:
            return items

        logger.info(f"开始AI去重，原始数据 {len(items)} 条")

        # 提取标题和URL
        titles_with_indices = []
        for i, item in enumerate(items):
            title = item.get('name', item.get('title', 'Unknown'))
            url = item.get('url', item.get('link', '#'))
            titles_with_indices.append(f"{i}: {title} ({url})")

        # 构建去重提示词
        prompt = self._build_dedup_prompt(titles_with_indices)

        try:
            result_text = await self._call_ai_with_retry(prompt)

            # 解析AI返回的索引
            kept_indices = self._parse_dedup_result(result_text)

            # 根据索引筛选数据
            deduplicated_items = [items[i] for i in kept_indices if i < len(items)]

            logger.info(f"AI去重完成，保留 {len(deduplicated_items)} 条")
            return deduplicated_items

        except Exception as e:
            logger.error(f"AI去重失败: {e}")
            # 失败时返回原始数据
            return items

    async def summarize_content(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """对去重后的内容进行总结和分析"""
        if not items:
            return {"summary": "今日暂无AI技术资讯", "trends": [], "categories": {}}

        logger.info(f"开始AI内容总结，处理 {len(items)} 条数据")

        # 构建总结提示词
        prompt = self._build_summary_prompt(items)

        try:
            result_text = await self._call_ai_with_retry(prompt)

            # 解析总结结果
            summary_result = self._parse_summary_result(result_text)

            logger.info("AI内容总结完成")
            return summary_result

        except Exception as e:
            logger.error(f"AI总结失败: {e}")
            return {
                "summary": "AI处理失败，请查看原始数据",
                "trends": [],
                "project_summaries": [],
                "categories": {"其他": items}
            }

    def _build_dedup_prompt(self, titles_with_indices: List[str]) -> str:
        """构建去重提示词"""
        titles_text = "\n".join(titles_with_indices)

        return f"""请分析以下AI技术资讯的标题，识别重复或高度相似的内容。
对于重复的内容，请保留最有价值的版本（优先考虑：官方源 > 详细描述 > 知名度高的来源）。

标题列表：
{titles_text}

请只返回需要保留的条目索引，用逗号分隔，例如：0,1,3,5,7

索引列表："""

    def _parse_dedup_result(self, result_text: str) -> List[int]:
        """解析去重结果"""
        try:
            # 提取数字索引
            indices_str = result_text.strip()
            indices = [int(x.strip()) for x in indices_str.split(',') if x.strip().isdigit()]
            return indices
        except Exception as e:
            logger.warning(f"解析去重结果失败: {e}，返回所有索引")
            return list(range(100))  # 返回足够大的范围

    def _build_summary_prompt(self, items: List[Dict[str, Any]]) -> str:
        """构建总结提示词"""
        content_text = ""
        for i, item in enumerate(items, 1):
            name = item.get('name', item.get('title', 'Unknown'))
            description = item.get('description', item.get('summary', ''))
            url = item.get('url', item.get('link', '#'))
            readme = item.get('readme', '')

            content_text += f"{i}. {name}\n"
            if description:
                content_text += f"   项目描述: {description}\n"
            if readme:
                # 取README前500字符作为参考
                readme_preview = readme[:500].replace('\n', ' ')
                content_text += f"   README内容: {readme_preview}...\n"
            content_text += f"   项目链接: {url}\n\n"

        return f"""请分析以下AI技术资讯，提供结构化的总结和分析。

项目信息：
{content_text}

请严格按照以下格式返回分析结果，必须使用中文：

## 今日摘要
[用2-3句话概括今日AI技术的主要动态和趋势]

## 技术趋势
[列出3-5个主要的技术趋势或热点话题，每个用一句话描述，用数字列表格式]

## 项目摘要
[为每个项目提供一句话的中文核心价值总结]

重要要求：
1. 必须全部使用中文
2. 严格按照格式输出
3. 项目摘要要突出技术价值，避免重复项目描述
4. 保持专业和简洁的表达"""

    def _parse_summary_result(self, result_text: str) -> Dict[str, Any]:
        """解析总结结果"""
        try:
            sections = result_text.split("##")
            summary = ""
            trends = []
            project_summaries = []

            for section in sections:
                section = section.strip()
                if section.startswith("今日摘要"):
                    summary = section.replace("今日摘要", "").strip()
                elif section.startswith("技术趋势"):
                    trends_text = section.replace("技术趋势", "").strip()
                    # 解析数字列表格式的趋势
                    trends = []
                    for line in trends_text.split("\n"):
                        line = line.strip()
                        if line and (line.startswith(("1.", "2.", "3.", "4.", "5.")) or line.startswith("- ")):
                            # 清理数字前缀和markdown符号
                            clean_line = line
                            for prefix in ["1.", "2.", "3.", "4.", "5.", "- ", "* "]:
                                if clean_line.startswith(prefix):
                                    clean_line = clean_line[len(prefix):].strip()
                                    break
                            if clean_line:
                                trends.append(clean_line)
                elif section.startswith("项目摘要"):
                    project_text = section.replace("项目摘要", "").strip()
                    # 解析项目摘要列表
                    for line in project_text.split("\n"):
                        line = line.strip()
                        if line and not line.startswith("#"):
                            project_summaries.append(line)

            return {
                "summary": summary or "今日AI技术资讯已收集",
                "trends": trends,
                "project_summaries": project_summaries,
                "categories": {"AI技术": project_summaries}
            }

        except Exception as e:
            logger.warning(f"解析总结结果失败: {e}")
            return {
                "summary": result_text[:200] + "..." if len(result_text) > 200 else result_text,
                "trends": [],
                "project_summaries": [],
                "categories": {"其他": []}
            }