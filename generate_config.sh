#!/bin/bash

# 通用配置生成脚本 - 自动读取JSON中所有应用配置
CONFIG_FILE="deployment-configs.json"
OUTPUT_FILE="config.yaml"

echo "🔧 生成 Cloud-Init 配置..."

# 检查JSON文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件 $CONFIG_FILE 不存在"
    exit 1
fi

# 检查是否安装了jq (如果没有则使用备用方案)
if command -v jq &> /dev/null; then
    USE_JQ=true
else
    USE_JQ=false
fi

# 开始生成配置文件
cat > "$OUTPUT_FILE" << 'EOF'
#cloud-config

package_update: true
package_upgrade: true

packages:
EOF

echo "📦 检查启用的服务..."
services_enabled=false
enabled_services=()

# 获取所有启用的服务
if [ "$USE_JQ" = true ]; then
    # 使用jq解析JSON
    enabled_services=($(jq -r '.deployments | to_entries[] | select(.value.enabled == true) | .key' "$CONFIG_FILE"))
else
    # 备用方案：使用grep解析
    enabled_services=($(grep -B 1 '"enabled".*true' "$CONFIG_FILE" | grep -o '"[^"]*":' | tr -d '":' | grep -v enabled))
fi

# 添加所有启用服务的packages
for service in "${enabled_services[@]}"; do
    echo "  ✅ $service"
    services_enabled=true
    
    if [ "$USE_JQ" = true ]; then
        # 使用jq获取packages
        packages=($(jq -r ".deployments.${service}.packages[]?" "$CONFIG_FILE" 2>/dev/null))
    else
        # 备用方案：使用sed/awk获取packages
        packages=($(sed -n "/${service}/,/}/p" "$CONFIG_FILE" | grep -A 100 '"packages"' | sed -n '/\[/,/\]/p' | grep -o '"[^"]*"' | tr -d '"' | grep -v packages))
    fi
    
    # 添加packages到配置文件
    for package in "${packages[@]}"; do
        if [ -n "$package" ] && [ "$package" != "null" ]; then
            echo "  - $package" >> "$OUTPUT_FILE"
        fi
    done
done

# 添加runcmd部分
echo "" >> "$OUTPUT_FILE"
echo "runcmd:" >> "$OUTPUT_FILE"

# 添加所有启用服务的commands
for service in "${enabled_services[@]}"; do
    echo "  # $service 配置" >> "$OUTPUT_FILE"
    
    if [ "$USE_JQ" = true ]; then
        # 使用jq获取commands (逐行处理避免空格分割)
        jq -r ".deployments.${service}.commands[]?" "$CONFIG_FILE" 2>/dev/null | while IFS= read -r command; do
            if [ -n "$command" ] && [ "$command" != "null" ]; then
                echo "  - $command" >> "$OUTPUT_FILE"
            fi
        done
    else
        # 备用方案：使用sed/awk获取commands (逐行处理)
        sed -n "/${service}/,/}/p" "$CONFIG_FILE" | grep -A 100 '"commands"' | sed -n '/\[/,/\]/p' | grep -o '"[^"]*"' | tr -d '"' | grep -v commands | while IFS= read -r command; do
            if [ -n "$command" ] && [ "$command" != "null" ]; then
                echo "  - $command" >> "$OUTPUT_FILE"
            fi
        done
    fi
    
    # 检查是否有test_commands且test_container为true
    if [ "$USE_JQ" = true ]; then
        test_enabled=$(jq -r ".deployments.${service}.test_container?" "$CONFIG_FILE" 2>/dev/null)
        if [ "$test_enabled" = "true" ]; then
            jq -r ".deployments.${service}.test_commands[]?" "$CONFIG_FILE" 2>/dev/null | while IFS= read -r test_cmd; do
                if [ -n "$test_cmd" ] && [ "$test_cmd" != "null" ]; then
                    echo "  - $test_cmd" >> "$OUTPUT_FILE"
                fi
            done
        fi
    else
        # 备用方案检查test_container
        if sed -n "/${service}/,/}/p" "$CONFIG_FILE" | grep -q '"test_container".*true'; then
            sed -n "/${service}/,/}/p" "$CONFIG_FILE" | grep -A 100 '"test_commands"' | sed -n '/\[/,/\]/p' | grep -o '"[^"]*"' | tr -d '"' | grep -v test_commands | while IFS= read -r test_cmd; do
                if [ -n "$test_cmd" ] && [ "$test_cmd" != "null" ]; then
                    echo "  - $test_cmd" >> "$OUTPUT_FILE"
                fi
            done
        fi
    fi
done

# 添加完成消息
echo "" >> "$OUTPUT_FILE"
if [ "$services_enabled" = true ]; then
    echo 'final_message: "应用部署完成，系统已在 $UPTIME 秒后启动"' >> "$OUTPUT_FILE"
else
    echo 'final_message: "未启用任何服务，基础系统已完成初始化"' >> "$OUTPUT_FILE"
fi

echo "✅ 配置文件已生成: $OUTPUT_FILE"

# 显示启用的服务
if [ "$services_enabled" = true ]; then
    echo "🎉 启用的服务: ${enabled_services[*]}"
    echo "💡 这些服务将在新机器启动后自动安装"
else
    echo "⚠️  未启用任何服务，仅生成基础系统配置"
fi

if [ "$USE_JQ" = false ]; then
    echo "💡 提示: 安装 jq 可以获得更好的JSON解析性能: sudo apt-get install jq"
fi