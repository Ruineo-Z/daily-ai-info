#!/usr/bin/env python3
"""测试静态网站生成器"""

import os
import sys
import json
from datetime import datetime, timedelta

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.static_site_generator import StaticSiteGenerator

def create_test_data():
    """创建测试数据"""
    test_reports = []

    # 生成过去7天的测试数据
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')

        # 模拟AI项目数据
        projects = []
        project_summaries = []

        for j in range(5):  # 每天5个项目
            project = {
                "name": f"awesome-ai-project-{i}-{j}",
                "title": f"AI项目{i}-{j}",
                "description": f"这是第{i}天的第{j}个AI项目，专注于机器学习和深度学习技术创新。",
                "url": f"https://github.com/user{j}/awesome-ai-project-{i}-{j}",
                "stars": str(1000 + j * 100),
                "stars_today": str(10 + j * 2),
                "language": ["Python", "JavaScript", "TypeScript", "Go", "Rust"][j],
                "author": f"developer{j}",
                "source": "GitHub Trending Web",
                "crawled_at": date.strftime("%Y-%m-%d %H:%M:%S"),
                "type": "repository",
                "platform": "GitHub",
                "readme": f"# AI项目{i}-{j}\n\n这是一个创新的AI项目，使用最新的机器学习技术。\n\n## 特性\n\n- 🤖 智能算法\n- 📊 数据分析\n- 🚀 高性能\n- 📱 用户友好\n\n## 快速开始\n\n```bash\npip install awesome-ai-project-{i}-{j}\n```\n\n这个项目旨在解决现实世界的AI问题，提供简单易用的API接口。"
            }
            projects.append(project)

            # AI摘要
            summary = f"这是一个专注于{project['language']}的AI项目，提供了创新的机器学习解决方案，特别适合{['初学者', '进阶用户', '企业级应用', '研究人员', '开发者'][j]}使用。"
            project_summaries.append(summary)

        # 技术趋势
        trends = [
            f"大模型技术在{date_str}继续快速发展",
            f"开源AI工具生态日趋完善",
            f"多模态AI应用场景不断扩展",
            f"AI安全和可解释性受到更多关注"
        ]

        report = {
            "date": date_str,
            "generation_time": date.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": f"今日共分析了{len(projects)}个热门AI项目，涵盖了机器学习、深度学习、自然语言处理等多个领域。这些项目展现了AI技术的最新发展趋势，为开发者提供了丰富的学习资源和实践机会。",
            "trends": trends,
            "project_summaries": project_summaries,
            "projects": projects
        }

        test_reports.append(report)

    return test_reports

def test_site_generation():
    """测试网站生成"""
    print("🔧 创建测试数据...")
    reports_data = create_test_data()
    latest_summary = reports_data[0] if reports_data else {}

    print("🌐 初始化静态网站生成器...")
    generator = StaticSiteGenerator("test_dist")

    print("🚀 生成静态网站...")
    try:
        success = generator.generate_site(reports_data, latest_summary)
        if success:
            site_size = generator.get_output_size()
            print(f"✅ 网站生成成功！")
            print(f"📊 生成统计:")
            print(f"   - 报告数量: {len(reports_data)}")
            print(f"   - 项目总数: {sum(len(r['projects']) for r in reports_data)}")
            print(f"   - 网站大小: {site_size}")
            print(f"   - 输出目录: test_dist/")
            print(f"")
            print(f"📂 生成的文件:")

            # 列出生成的文件
            for root, dirs, files in os.walk("test_dist"):
                level = root.replace("test_dist", "").count(os.sep)
                indent = " " * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = " " * 2 * (level + 1)
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    if file_size < 1024:
                        size_str = f"{file_size}B"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size/1024:.1f}KB"
                    else:
                        size_str = f"{file_size/(1024*1024):.1f}MB"
                    print(f"{subindent}{file} ({size_str})")

            return True
        else:
            print("❌ 网站生成失败")
            return False
    except Exception as e:
        print(f"❌ 网站生成出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 静态网站生成器测试")
    print("=" * 50)
    print()

    success = test_site_generation()

    print()
    if success:
        print("🎉 测试完成！要查看效果，请运行：")
        print("   cd test_dist && python -m http.server 8000")
        print("   然后访问: http://localhost:8000")
    else:
        print("💥 测试失败，请检查错误信息")
    print()