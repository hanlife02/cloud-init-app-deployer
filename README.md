<!--
 * @Author: Ethan yanghan0911@gmail.com
 * @Date: 2025-08-07 20:39:14
 * @LastEditors: Ethan yanghan0911@gmail.com
 * @LastEditTime: 2025-09-11 20:30:00
 * @FilePath: /Cloud-Init-App-Deployer/README.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
# Cloud-Init App Deployer

基于Flask的API服务，接收JSON配置生成Cloud-Init内容并直接启动OpenStack实例。

## 文件结构

```
Cloud-Init-App-Deployer/
├── README.md                   # 项目文档
├── requirements.txt            # Python依赖包
├── app.py                     # Flask应用主入口
├── api_routes.py              # API路由定义
├── cloud_config_generator.py   # Cloud-Init配置生成器
├── config_manager.py          # 配置管理器
├── openstack_manager.py       # OpenStack实例管理
├── deployment-configs.json    # 部署配置文件（Docker安装配置）
└── outputs/                   # 生成的配置文件目录（自动创建）
    └── config.yaml           # 生成的Cloud-Init配置文件
```

## 使用方法

### 1. 启动服务
```bash
pip install -r requirements.txt
python3 app.py
```

### 2. 部署实例（推荐方式）

#### Docker服务部署
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
    "enable_docker": true
  }'
```

#### LobeChat部署
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
    "enable_lobechat": true
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
      "docker": {}
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
      "docker": {}
    }
  }'

# 自定义文件名保存
curl -X POST "http://localhost:5000/api/generate-config?save=true&filename=my-config.yaml" \
  -H "Content-Type: application/json" \
  -d '{
    "openstack": {
      "image": "Ubuntu 22.04"
    },
    "deployments": {
      "docker": {}
    }
  }'
```

## 可用服务

- `docker` - Docker 容器引擎（支持 Ubuntu、CentOS、Debian 系统的智能安装）
- `lobechat` - LobeChat AI聊天应用（基于Docker部署，包含自动更新功能）

### LobeChat服务详情

#### 功能特性
- 自动安装Docker和docker-compose
- 部署到`/opt/lobechat`目录
- 默认端口：3210
- 包含自动更新脚本（每日凌晨2点执行）
- 支持环境变量配置（OPENAI_API_KEY、OPENAI_PROXY_URL、ACCESS_CODE）

#### 访问方式
部署完成后，可通过以下方式访问：
```
http://实例IP:3210
```

#### 注意事项
1. 确保OpenStack安全组开放3210端口
2. 需要配置OPENAI_API_KEY等环境变量
3. 自动更新脚本会定期检查并更新到最新版本
4. 默认配置可通过修改`deployment-configs.json`文件调整

#### 生成的文件
- `/opt/lobechat/docker-compose.yml` - Docker Compose配置文件
- `/opt/lobechat/auto-update-lobe-chat.sh` - 自动更新脚本
- 自动添加到crontab的定时任务