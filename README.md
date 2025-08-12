<!--
 * @Author: Ethan yanghan0911@gmail.com
 * @Date: 2025-08-07 20:39:14
 * @LastEditors: Ethan yanghan0911@gmail.com
 * @LastEditTime: 2025-08-12 21:53:13
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
    "enable_nginx": false,
    "enable_mysql": false,
    "enable_nodejs": false
  }'
```

### 3. 查看实例
```bash
curl http://localhost:5000/api/instances
```

## API接口

- `POST /api/deploy-services` - 接收OpenStack配置并根据enable_*参数选择性部署服务（推荐）
- `POST /api/deploy` - 接收完整JSON配置并启动实例（自定义方式）
- `POST /api/generate-config` - 仅生成配置文件
- `GET /api/instances` - 列出实例
- `GET /api/instance/status/<name>` - 实例状态

## 可用服务

- `docker` - Docker 容器引擎
- `nginx` - Web 服务器
- `mysql` - 数据库服务
- `nodejs` - Node.js 运行时