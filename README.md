# Daily AI Info

每日AI技术资讯自动爬取和总结工具

## 功能特点

- 🤖 **智能爬取**: 自动从5个优质AI技术网站获取最新资讯
- 🧠 **AI去重**: 使用Gemini AI智能识别和去除重复内容
- 📝 **智能总结**: AI自动总结和分类技术趋势
- 📅 **定时运行**: 每日自动执行，无需人工干预
- 📁 **Markdown输出**: 生成易读的Markdown格式报告
- 🚀 **轻量设计**: 适合2核2G服务器运行

## 数据源

1. **GitHub Trending (AI/ML)** - 热门AI开源项目
2. **Papers with Code** - 论文+代码实现
3. **Hugging Face Models** - 预训练模型库
4. **arXiv AI Papers** - AI领域最新论文
5. **Towards Data Science** - AI技术文章和教程

## 技术架构

- **语言**: Python 3.9+
- **包管理**: uv
- **HTTP请求**: httpx + BeautifulSoup4
- **AI服务**: Google Gemini API
- **定时任务**: APScheduler
- **日志**: loguru (自动轮转，保留2天)
- **存储**: Markdown文件

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd daily-ai-info

# 使用uv安装依赖
uv sync
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
# 必需配置
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro

# 可选配置（但强烈推荐）
GITHUB_TOKEN=your_github_token_here
CRAWL_SCHEDULE_HOUR=6
CRAWL_SCHEDULE_MINUTE=0
```

### GitHub Token 获取和权限设置

1. 访问 [GitHub Personal Access Tokens](https://github.com/settings/tokens)
2. 点击 "Generate new token" -> "Generate new token (classic)"
3. 设置权限：
   - **public_repo** - 访问公开仓库（推荐）
   - 或者不选择任何权限（使用默认权限，限制更多）
4. 复制生成的token到 `.env` 文件

**注意**: GitHub Token可以显著提高API调用限制（从60次/小时提升到5000次/小时）

### 3. 运行程序

```bash
# 开发环境运行
uv run python main.py

# 生产环境运行
nohup uv run python main.py &
```

## 项目结构

```
daily-ai-info/
├── app/
│   ├── config.py              # 配置管理
│   ├── logger_config.py       # 日志配置
│   ├── utils.py               # 工具函数
│   ├── ai_processor.py        # AI处理模块
│   └── crawlers/              # 爬虫模块
│       ├── base_crawler.py    # 爬虫基类
│       ├── github_crawler.py  # GitHub爬虫
│       └── arxiv_crawler.py   # arXiv爬虫
├── data/                      # 生成的报告
├── logs/                      # 日志文件
├── main.py                    # 主程序
├── pyproject.toml            # 项目配置
└── .env.example              # 环境变量示例
```

## 许可证

MIT License