# 使用Python 3.12官方镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 安装uv包管理器
RUN pip install uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY VERSION ./

# 安装Python依赖
RUN uv sync --frozen --no-dev

# 复制应用代码
COPY app/ ./app/
COPY main.py ./
COPY scheduler_runner.py ./
COPY CLAUDE.md ./

# 创建必要的目录
RUN mkdir -p data logs dist

# 设置文件权限
RUN chmod +x scheduler_runner.py main.py

# 暴露端口（如果使用内置HTTP服务器）
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 默认运行调度器
CMD ["python", "scheduler_runner.py"]