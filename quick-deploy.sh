#!/bin/bash

# Cloud-Init App Deployer - 快速部署脚本
# 用于在云服务器上快速部署应用

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要使用root用户运行此脚本！"
        exit 1
    fi
}

# 检查系统类型
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        log_error "无法检测操作系统类型"
        exit 1
    fi
    
    log_info "检测到操作系统: $OS $VERSION"
}

# 安装依赖
install_dependencies() {
    log_info "正在安装系统依赖..."
    
    case $OS in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y git curl wget cloud-init cron
            ;;
        centos|rhel)
            sudo yum update -y
            sudo yum install -y git curl wget cloud-init cronie
            sudo systemctl enable crond && sudo systemctl start crond
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
    
    log_info "依赖安装完成"
}

# 创建目录结构
create_directories() {
    log_info "创建目录结构..."
    
    # 创建应用目录
    sudo mkdir -p /opt/app/{logs,data,config}
    sudo mkdir -p /var/log/cloud-app-deployer
    
    # 设置权限
    sudo chown -R $USER:$USER /opt/app
    sudo chown -R $USER:$USER /var/log/cloud-app-deployer
    
    log_info "目录结构创建完成"
}

# 配置Git (如果需要克隆仓库)
setup_git() {
    if ! command -v git &> /dev/null; then
        log_error "Git 未安装"
        exit 1
    fi
    
    # 如果还没有配置Git用户信息，设置默认值
    if ! git config --global user.name &> /dev/null; then
        git config --global user.name "Cloud App Deployer"
        git config --global user.email "deployer@example.com"
        log_info "已设置默认Git配置"
    fi
}

# 设置脚本权限
set_permissions() {
    log_info "设置脚本权限..."
    
    # 当前目录的脚本权限
    chmod +x scripts/app/*.sh 2>/dev/null || true
    chmod +x scripts/update/*.sh 2>/dev/null || true
    chmod +x scripts/monitor/*.sh 2>/dev/null || true
    chmod +x verify-setup.sh 2>/dev/null || true
    
    log_info "权限设置完成"
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."
    
    if [[ ! -f config.env ]]; then
        # 创建默认配置文件
        cat > config.env << 'EOF'
# 应用配置
APP_NAME="cloud-app"
APP_PORT=8080
APP_ENV="production"

# 监控配置
HEALTH_CHECK_INTERVAL=300
UPDATE_CHECK_INTERVAL=3600

# 日志配置
LOG_LEVEL="INFO"
LOG_DIR="/var/log/cloud-app-deployer"

# 通知配置 (可选)
NOTIFICATION_EMAIL=""
SLACK_WEBHOOK_URL=""
EOF
        log_info "已创建默认配置文件 config.env"
    else
        log_info "配置文件已存在，跳过创建"
    fi
}

# 安装应用
install_app() {
    log_info "开始安装应用..."
    
    if [[ -f scripts/app/install.sh ]]; then
        sudo ./scripts/app/install.sh
        log_info "应用安装完成"
    else
        log_warn "未找到安装脚本，跳过应用安装"
    fi
}

# 配置应用
configure_app() {
    log_info "配置应用..."
    
    if [[ -f scripts/app/configure.sh ]]; then
        sudo ./scripts/app/configure.sh
        log_info "应用配置完成"
    else
        log_warn "未找到配置脚本，跳过应用配置"
    fi
}

# 配置定时任务
setup_cron() {
    log_info "配置定时任务..."
    
    if [[ -f cron/crontab ]]; then
        sudo cp cron/crontab /etc/cron.d/cloud-app-monitor
        sudo chmod 644 /etc/cron.d/cloud-app-monitor
        sudo systemctl restart cron
        log_info "定时任务配置完成"
    else
        log_warn "未找到定时任务配置文件"
    fi
}

# 配置系统服务
setup_systemd() {
    log_info "配置系统服务..."
    
    if [[ -f cloud-app.service ]]; then
        sudo cp cloud-app.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable cloud-app
        log_info "系统服务配置完成"
    else
        log_warn "未找到系统服务配置文件"
    fi
}

# 启动应用
start_app() {
    log_info "启动应用..."
    
    # 首先尝试使用脚本启动
    if [[ -f scripts/app/start.sh ]]; then
        sudo ./scripts/app/start.sh
    fi
    
    # 然后尝试使用systemd启动
    if systemctl is-enabled cloud-app &> /dev/null; then
        sudo systemctl start cloud-app
        log_info "应用启动完成"
    else
        log_warn "未配置systemd服务，请手动启动应用"
    fi
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."
    
    if [[ -f verify-setup.sh ]]; then
        ./verify-setup.sh
    else
        log_warn "未找到验证脚本"
        
        # 手动验证
        log_info "手动验证系统状态..."
        
        # 检查系统服务
        if systemctl is-active cloud-app &> /dev/null; then
            log_info "✓ 应用服务正在运行"
        else
            log_warn "✗ 应用服务未运行"
        fi
        
        # 检查定时任务
        if [[ -f /etc/cron.d/cloud-app-monitor ]]; then
            log_info "✓ 定时任务已配置"
        else
            log_warn "✗ 定时任务未配置"
        fi
        
        # 检查日志目录
        if [[ -d /var/log/cloud-app-deployer ]]; then
            log_info "✓ 日志目录已创建"
        else
            log_warn "✗ 日志目录不存在"
        fi
    fi
}

# 显示部署信息
show_deployment_info() {
    log_info "部署完成！"
    echo
    echo "=== 部署信息 ==="
    echo "应用目录: /opt/app"
    echo "日志目录: /var/log/cloud-app-deployer"
    echo "配置文件: $(pwd)/config.env"
    echo
    echo "=== 常用命令 ==="
    echo "查看应用状态: sudo systemctl status cloud-app"
    echo "查看应用日志: sudo journalctl -u cloud-app -f"
    echo "重启应用: sudo systemctl restart cloud-app"
    echo "查看定时任务: sudo crontab -l"
    echo
    echo "=== 注意事项 ==="
    echo "1. 请确保防火墙已开放应用端口 (默认8080)"
    echo "2. 如需自定义配置，请编辑 config.env 文件"
    echo "3. 定时任务会自动运行健康检查和更新检查"
    echo "4. 查看详细文档: cat DEPLOYMENT.md"
}

# 主函数
main() {
    log_info "开始部署 Cloud-Init App Deployer..."
    
    # 检查环境
    check_root
    detect_os
    
    # 安装和配置
    install_dependencies
    create_directories
    setup_git
    set_permissions
    setup_environment
    
    # 部署应用
    install_app
    configure_app
    setup_cron
    setup_systemd
    start_app
    
    # 验证和显示信息
    verify_deployment
    show_deployment_info
    
    log_info "部署脚本执行完成！"
}

# 如果脚本被直接执行，运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
