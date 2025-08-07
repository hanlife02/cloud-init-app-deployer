#!/bin/bash

CONFIG_FILE="deployment-configs.json"
OUTPUT_FILE="config.yaml"

# 获取启用的服务
enabled_services=($(jq -r '.deployments | to_entries[] | select(.value.enabled == true) | .key' "$CONFIG_FILE"))

# 生成配置文件
cat > "$OUTPUT_FILE" << 'EOF'
#cloud-config

package_update: true
package_upgrade: true

packages:
EOF

# 添加packages
for service in "${enabled_services[@]}"; do
    jq -r ".deployments.${service}.packages[]?" "$CONFIG_FILE" | while read -r package; do
        [ -n "$package" ] && echo "  - $package" >> "$OUTPUT_FILE"
    done
done

echo "" >> "$OUTPUT_FILE"
echo "runcmd:" >> "$OUTPUT_FILE"

# 添加commands
for service in "${enabled_services[@]}"; do
    echo "  # $service 配置" >> "$OUTPUT_FILE"
    jq -r ".deployments.${service}.commands[]?" "$CONFIG_FILE" | while read -r command; do
        [ -n "$command" ] && echo "  - $command" >> "$OUTPUT_FILE"
    done
    
    # 添加test_commands
    test_enabled=$(jq -r ".deployments.${service}.test_container?" "$CONFIG_FILE")
    if [ "$test_enabled" = "true" ]; then
        jq -r ".deployments.${service}.test_commands[]?" "$CONFIG_FILE" | while read -r test_cmd; do
            [ -n "$test_cmd" ] && echo "  - $test_cmd" >> "$OUTPUT_FILE"
        done
    fi
done

echo "" >> "$OUTPUT_FILE"
echo 'final_message: "应用部署完成"' >> "$OUTPUT_FILE"

echo "✅ 配置文件已生成: $OUTPUT_FILE"