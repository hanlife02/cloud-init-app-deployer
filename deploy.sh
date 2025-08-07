#!/bin/bash

echo "🚀 一键部署到 OpenStack"

CONFIG_FILE="deployment-configs.json"

# 从JSON读取配置
INSTANCE_NAME=$(jq -r '.openstack.instance_name' "$CONFIG_FILE")
IMAGE=$(jq -r '.openstack.image' "$CONFIG_FILE")
FLAVOR=$(jq -r '.openstack.flavor' "$CONFIG_FILE")
NETWORK=$(jq -r '.openstack.network' "$CONFIG_FILE")
KEY_NAME=$(jq -r '.openstack.key_name' "$CONFIG_FILE")
USER_DATA_FILE=$(jq -r '.openstack.user_data_file' "$CONFIG_FILE")

echo "📋 配置: $INSTANCE_NAME ($IMAGE)"

# 1. 生成Cloud-Init配置
echo "🔧 生成配置文件..."
./generate_config.sh

# 2. 部署到OpenStack
echo "🚀 部署实例..."
openstack server create \
  --image "$IMAGE" \
  --flavor "$FLAVOR" \
  --network "$NETWORK" \
  --user-data "$USER_DATA_FILE" \
  --key-name "$KEY_NAME" \
  "$INSTANCE_NAME"

echo "✅ 部署完成!"