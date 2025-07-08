#!/bin/bash

# 项目结构验证脚本
# 用于验证 Cloud-Init App Deployer 项目结构是否完整

set -e

PROJECT_ROOT="/opt/app"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔍 验证 Cloud-Init App Deployer 项目结构..."
echo "项目根目录: $PROJECT_ROOT"
echo "当前目录: $CURRENT_DIR"
echo

# 检查目录结构
check_directory() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo "✅ $description: $dir"
        return 0
    else
        echo "❌ $description: $dir (缺失)"
        return 1
    fi
}

# 检查文件
check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo "✅ $description: $file"
        return 0
    else
        echo "❌ $description: $file (缺失)"
        return 1
    fi
}

# 检查脚本文件权限
check_script_permissions() {
    local script=$1
    
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "✅ 脚本可执行: $script"
        return 0
    elif [ -f "$script" ]; then
        echo "⚠️  脚本存在但不可执行: $script"
        return 1
    else
        echo "❌ 脚本不存在: $script"
        return 1
    fi
}

echo "=== 检查项目目录结构 ==="

# 检查主要目录
check_directory "$PROJECT_ROOT" "应用根目录"
check_directory "$PROJECT_ROOT/scripts" "脚本目录"
check_directory "$PROJECT_ROOT/scripts/app" "应用脚本目录"
check_directory "$PROJECT_ROOT/scripts/update" "更新脚本目录"
check_directory "$PROJECT_ROOT/scripts/monitor" "监控脚本目录"
check_directory "$PROJECT_ROOT/config" "配置目录"
check_directory "$PROJECT_ROOT/data" "数据目录"
check_directory "$PROJECT_ROOT/logs" "日志目录"

echo
echo "=== 检查配置文件 ==="

# 检查配置文件
check_file "$PROJECT_ROOT/config/app.conf" "应用配置文件"
check_file "/etc/systemd/system/cloud-app.service" "系统服务文件"
check_file "/etc/cron.d/app-monitor" "定时任务配置"

echo
echo "=== 检查脚本文件权限 ==="

# 检查脚本文件权限
check_script_permissions "$PROJECT_ROOT/scripts/app/install.sh"
check_script_permissions "$PROJECT_ROOT/scripts/app/configure.sh"
check_script_permissions "$PROJECT_ROOT/scripts/app/start.sh"
check_script_permissions "$PROJECT_ROOT/scripts/app/stop.sh"
check_script_permissions "$PROJECT_ROOT/scripts/update/check-update.sh"
check_script_permissions "$PROJECT_ROOT/scripts/update/apply-update.sh"
check_script_permissions "$PROJECT_ROOT/scripts/monitor/health-check.sh"
check_script_permissions "$PROJECT_ROOT/scripts/monitor/notify.sh"

echo
echo "=== 检查服务状态 ==="

# 检查系统服务
if systemctl is-enabled cloud-app.service >/dev/null 2>&1; then
    echo "✅ cloud-app.service 已启用"
else
    echo "⚠️  cloud-app.service 未启用"
fi

if systemctl is-active cloud-app.service >/dev/null 2>&1; then
    echo "✅ cloud-app.service 运行中"
else
    echo "⚠️  cloud-app.service 未运行"
fi

# 检查 cron 服务
if systemctl is-active cron >/dev/null 2>&1; then
    echo "✅ cron 服务运行中"
else
    echo "❌ cron 服务未运行"
fi

echo
echo "=== 检查日志文件 ==="

# 检查日志文件
for log_file in deployment.log app.log monitor.log update.log; do
    if [ -f "$PROJECT_ROOT/logs/$log_file" ]; then
        size=$(du -h "$PROJECT_ROOT/logs/$log_file" | cut -f1)
        echo "✅ $log_file ($size)"
    else
        echo "ℹ️  $log_file (未创建)"
    fi
done

echo
echo "=== 检查网络连接 ==="

# 检查应用端口
if command -v netstat >/dev/null 2>&1; then
    if netstat -tlnp | grep -q ":8080"; then
        echo "✅ 应用端口 8080 正在监听"
    else
        echo "ℹ️  应用端口 8080 未监听（应用可能未启动）"
    fi
else
    echo "ℹ️  netstat 命令不可用，跳过端口检查"
fi

echo
echo "=== 检查完成 ==="

# 显示系统信息
echo "系统信息:"
echo "- 操作系统: $(uname -s)"
echo "- 内核版本: $(uname -r)"
echo "- 主机名: $(hostname)"
echo "- 当前用户: $(whoami)"
echo "- 系统时间: $(date)"

if [ -f "$PROJECT_ROOT/logs/deployment.log" ]; then
    echo
    echo "=== 最近的部署日志 ==="
    tail -n 10 "$PROJECT_ROOT/logs/deployment.log" 2>/dev/null || echo "无法读取部署日志"
fi

echo
echo "验证完成！如果发现问题，请检查相应的配置和权限设置。"
