#!/bin/bash

# 每日AI技术趋势分析 - 服务器部署脚本
# 专为2核2G服务器优化

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="daily-ai-info"
DOMAIN_NAME="your-domain.com"  # 请替换为实际域名
WEB_ROOT="/var/www/ai-reports"
PROJECT_DIR="/opt/${PROJECT_NAME}"
SERVICE_USER="aianalysis"
PYTHON_VERSION="3.9"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root权限运行此脚本"
        exit 1
    fi
}

# 检查系统资源
check_system() {
    log_step "检查系统资源"

    # 检查CPU核心数
    CPU_CORES=$(nproc)
    if [ "$CPU_CORES" -lt 2 ]; then
        log_warn "CPU核心数少于2核，性能可能受限"
    else
        log_info "CPU核心数: ${CPU_CORES}"
    fi

    # 检查内存
    TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
    if (( $(echo "$TOTAL_MEM < 1.5" | bc -l) )); then
        log_error "内存少于1.5GB，无法正常运行"
        exit 1
    else
        log_info "总内存: ${TOTAL_MEM}GB"
    fi

    # 检查磁盘空间
    DISK_SPACE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$DISK_SPACE" -lt 10 ]; then
        log_error "可用磁盘空间少于10GB，无法正常运行"
        exit 1
    else
        log_info "可用磁盘空间: ${DISK_SPACE}GB"
    fi
}

# 更新系统
update_system() {
    log_step "更新系统包"
    apt update && apt upgrade -y
    apt install -y curl wget git nginx python3 python3-pip python3-venv \
                   supervisor logrotate htop rsync bc
}

# 创建系统用户
create_user() {
    log_step "创建系统用户"
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$PROJECT_DIR" "$SERVICE_USER"
        log_info "用户 $SERVICE_USER 创建成功"
    else
        log_info "用户 $SERVICE_USER 已存在"
    fi
}

# 创建目录结构
create_directories() {
    log_step "创建目录结构"

    # 项目目录
    mkdir -p "$PROJECT_DIR"
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/data"

    # Web目录
    mkdir -p "$WEB_ROOT"
    mkdir -p "$WEB_ROOT/reports"
    mkdir -p "$WEB_ROOT/api"

    # 日志目录
    mkdir -p /var/log/ai-analysis

    # 设置权限
    chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
    chown -R "$SERVICE_USER:www-data" "$WEB_ROOT"
    chmod -R 755 "$WEB_ROOT"

    log_info "目录结构创建完成"
}

# 部署应用代码
deploy_application() {
    log_step "部署应用代码"

    # 如果是从本地部署，复制文件
    if [ -d "../app" ]; then
        log_info "从本地部署应用代码"
        cp -r ../app "$PROJECT_DIR/"
        cp -r ../pyproject.toml "$PROJECT_DIR/"
        cp -r ../.env.example "$PROJECT_DIR/"

        # 创建虚拟环境
        cd "$PROJECT_DIR"
        python3 -m venv venv
        source venv/bin/activate

        # 安装依赖（使用国内镜像加速）
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pip --upgrade
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e .

        log_info "应用代码部署完成"
    else
        log_error "未找到应用代码目录，请确保在项目根目录运行此脚本"
        exit 1
    fi
}

# 配置环境变量
configure_environment() {
    log_step "配置环境变量"

    if [ ! -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"

        log_warn "请编辑 $PROJECT_DIR/.env 文件，配置必要的API密钥："
        log_warn "- GEMINI_API_KEY: Google Gemini API密钥"
        log_warn "- GITHUB_TOKEN: GitHub访问令牌"
        log_warn "- 其他可选配置项"
    else
        log_info "环境变量文件已存在"
    fi
}

# 配置Nginx
configure_nginx() {
    log_step "配置Nginx"

    # 备份原配置
    if [ -f /etc/nginx/sites-available/default ]; then
        cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup
    fi

    # 复制配置文件
    cp nginx.conf /etc/nginx/sites-available/ai-reports

    # 更新域名
    sed -i "s/your-domain.com/$DOMAIN_NAME/g" /etc/nginx/sites-available/ai-reports

    # 启用站点
    ln -sf /etc/nginx/sites-available/ai-reports /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # 测试配置
    nginx -t
    if [ $? -eq 0 ]; then
        systemctl restart nginx
        systemctl enable nginx
        log_info "Nginx配置完成"
    else
        log_error "Nginx配置测试失败"
        exit 1
    fi
}

# 创建Supervisor配置
configure_supervisor() {
    log_step "配置Supervisor"

    cat > /etc/supervisor/conf.d/ai-analysis.conf << EOF
[program:ai-analysis]
command=$PROJECT_DIR/venv/bin/python scheduler_runner.py
directory=$PROJECT_DIR
user=$SERVICE_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ai-analysis/scheduler.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PATH="$PROJECT_DIR/venv/bin"

[program:ai-analysis-web-sync]
command=/bin/bash -c "while true; do rsync -av --delete $PROJECT_DIR/dist/ $WEB_ROOT/; sleep 300; done"
user=$SERVICE_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ai-analysis/sync.log
stdout_logfile_maxbytes=1MB
stdout_logfile_backups=2
EOF

    supervisorctl reread
    supervisorctl update

    log_info "Supervisor配置完成"
}

# 配置日志轮转
configure_logrotate() {
    log_step "配置日志轮转"

    cat > /etc/logrotate.d/ai-analysis << EOF
/var/log/ai-analysis/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 $SERVICE_USER $SERVICE_USER
    postrotate
        supervisorctl restart ai-analysis
        supervisorctl restart ai-analysis-web-sync
    endscript
}

/var/log/nginx/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 www-data adm
    prerotate
        if [ -d /etc/logrotate.d/httpd-prerotate ]; then \
            run-parts /etc/logrotate.d/httpd-prerotate; \
        fi \
    endscript
    postrotate
        invoke-rc.d nginx rotate >/dev/null 2>&1
    endscript
}
EOF

    log_info "日志轮转配置完成"
}

# 创建定时清理脚本
create_cleanup_script() {
    log_step "创建定时清理脚本"

    cat > /usr/local/bin/ai-analysis-cleanup.sh << 'EOF'
#!/bin/bash
# 清理30天前的数据文件，防止磁盘空间不足

PROJECT_DIR="/opt/daily-ai-info"
DATA_DIR="$PROJECT_DIR/data"
WEB_ROOT="/var/www/ai-reports"

# 清理30天前的数据文件
find "$DATA_DIR" -type f -mtime +30 -name "*.md" -delete
find "$DATA_DIR" -type f -mtime +30 -name "*.json" -delete

# 清理空目录
find "$DATA_DIR" -type d -empty -delete

# 清理Web目录中的旧报告（保留最近100个）
cd "$WEB_ROOT/reports"
ls -t *.html | tail -n +101 | xargs -r rm

# 重新生成网站（如果需要）
cd "$PROJECT_DIR"
source venv/bin/activate
python -c "
from app.scheduler import DailyAIScheduler
from app.static_site_generator import StaticSiteGenerator
import asyncio

async def regenerate_site():
    scheduler = DailyAIScheduler()
    historical_data = scheduler._load_historical_reports()
    if historical_data:
        site_generator = StaticSiteGenerator()
        site_generator.generate_site(historical_data, historical_data[0] if historical_data else {})

asyncio.run(regenerate_site())
"

echo "$(date): 清理完成" >> /var/log/ai-analysis/cleanup.log
EOF

    chmod +x /usr/local/bin/ai-analysis-cleanup.sh

    # 添加到crontab（每周执行一次）
    (crontab -l 2>/dev/null; echo "0 2 * * 0 /usr/local/bin/ai-analysis-cleanup.sh") | crontab -

    log_info "定时清理脚本创建完成"
}

# 设置防火墙
configure_firewall() {
    log_step "配置防火墙"

    if command -v ufw &> /dev/null; then
        ufw --force enable
        ufw allow 22/tcp  # SSH
        ufw allow 80/tcp  # HTTP
        ufw allow 443/tcp # HTTPS (如果需要)

        log_info "防火墙配置完成"
    else
        log_warn "未安装ufw，跳过防火墙配置"
    fi
}

# 创建初始静态页面
create_initial_page() {
    log_step "创建初始静态页面"

    cat > "$WEB_ROOT/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日AI技术趋势分析 - 正在启动</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               margin: 0; padding: 2rem; background: #f8f9fa; }
        .container { max-width: 800px; margin: 0 auto; text-align: center; }
        .card { background: white; padding: 3rem; border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db;
                  border-radius: 50%; width: 40px; height: 40px;
                  animation: spin 2s linear infinite; margin: 0 auto 2rem; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        h1 { color: #2c3e50; margin-bottom: 1rem; }
        p { color: #7f8c8d; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="spinner"></div>
            <h1>🤖 每日AI技术趋势分析</h1>
            <p>系统正在启动中，首次运行将在每日8:30自动开始分析...</p>
            <p>请稍后刷新页面查看最新的AI技术趋势分析报告。</p>
            <p style="margin-top: 2rem; font-size: 0.9rem; color: #95a5a6;">
                基于GitHub Trending数据 • 由Gemini AI驱动 • 每日自动更新
            </p>
        </div>
    </div>
</body>
</html>
EOF

    chown www-data:www-data "$WEB_ROOT/index.html"
    log_info "初始页面创建完成"
}

# 显示部署总结
show_summary() {
    log_step "部署完成总结"

    echo ""
    echo "========================================"
    echo -e "${GREEN}✅ 部署成功完成！${NC}"
    echo "========================================"
    echo ""
    echo "服务信息："
    echo "- 项目目录: $PROJECT_DIR"
    echo "- Web目录: $WEB_ROOT"
    echo "- 网站地址: http://$DOMAIN_NAME"
    echo "- 系统用户: $SERVICE_USER"
    echo ""
    echo "重要文件："
    echo "- 配置文件: $PROJECT_DIR/.env"
    echo "- 日志目录: /var/log/ai-analysis/"
    echo "- Nginx配置: /etc/nginx/sites-available/ai-reports"
    echo ""
    echo "常用命令："
    echo "- 查看服务状态: supervisorctl status"
    echo "- 重启服务: supervisorctl restart ai-analysis"
    echo "- 查看日志: tail -f /var/log/ai-analysis/scheduler.log"
    echo "- 手动运行分析: cd $PROJECT_DIR && source venv/bin/activate && python main.py"
    echo ""
    echo -e "${YELLOW}⚠️  下一步操作：${NC}"
    echo "1. 编辑 $PROJECT_DIR/.env 文件，配置API密钥"
    echo "2. 重启服务: supervisorctl restart ai-analysis"
    echo "3. 如需HTTPS，配置SSL证书"
    echo ""
    echo -e "${BLUE}系统将在每日8:30自动执行分析任务${NC}"
}

# 主函数
main() {
    echo "========================================"
    echo "每日AI技术趋势分析 - 服务器部署脚本"
    echo "专为2核2G服务器优化"
    echo "========================================"
    echo ""

    check_root
    check_system

    # 执行部署步骤
    update_system
    create_user
    create_directories
    deploy_application
    configure_environment
    configure_nginx
    configure_supervisor
    configure_logrotate
    create_cleanup_script
    configure_firewall
    create_initial_page

    show_summary
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"