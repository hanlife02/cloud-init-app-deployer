<!--
 * @Author: Ethan yanghan0911@gmail.com
 * @Date: 2025-08-07 20:39:14
 * @LastEditors: Ethan yanghan0911@gmail.com
 * @LastEditTime: 2025-08-22 19:49:28
 * @FilePath: /Cloud-Init-App-Deployer/README.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
# Cloud-Init App Deployer

基于Flask的API服务，接收JSON配置生成Cloud-Init内容并直接启动OpenStack实例。

## 使用方法

### 1. 启动服务
```bash
pip install -r requirements.txt
python3 app.py
```

### 2. 部署实例（推荐方式）
```bash
curl -X POST http://localhost:5000/api/deploy-services \
  -H "Content-Type: application/json" \
  -d '{
    "openstack": {
      "instance_name": "test",
      "image": "Ubuntu 22.04",
      "flavor": "p2",
      "network": "pku",
      "key_name": "Ethan"
    },
    "enable_docker": true,
  }'
```

### 3. 查看实例
```bash
curl http://localhost:5000/api/instances
```

### 配置生成接口使用示例

#### 生成config.yaml配置
```bash
# 生成配置内容（仅返回内容，不生成文件）
curl -X POST http://localhost:5000/api/generate-config \
  -H "Content-Type: application/json" \
  -d '{
    "openstack": {
      "image": "Ubuntu 22.04"
    },
    "deployments": {
      "docker": {
        "packages": ["docker.io"],
        "commands": ["systemctl enable docker", "systemctl start docker"]
      }
    }
  }'

# 生成配置并保存到文件
curl -X POST "http://localhost:5000/api/generate-config?save=true" \
  -H "Content-Type: application/json" \
  -d '{
    "openstack": {
      "image": "Ubuntu 22.04"
    },
    "deployments": {
      "docker": {
        "packages": ["docker.io"],
        "commands": ["systemctl enable docker", "systemctl start docker"]
      }
    }
  }'

# 自定义文件名保存
curl -X POST "http://localhost:5000/api/generate-config?save=true&filename=my-config.yaml" \
  -H "Content-Type: application/json" \
  -d '{...}'
```
