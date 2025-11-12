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
# 复制示例环境变量文件后进行修改
cp .env.example .env
# 将私密变量写入 .env 或通过其它安全方式注入到环境
set -a
source .env
set +a
python3 app.py
```

服务启动后，所有受保护接口都必须在请求头中携带 `X-API-Key: <API_TOKEN>`。

### 2. 部署实例（推荐方式）

#### 部署 Docker 和 LobeChat
```bash
curl -X POST http://localhost:5000/api/deploy-services \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-strong-token" \
  -d '{
    "openstack": {
      "instance_name": "test",
      "image": "Ubuntu 22.04",
      "flavor": "p2",
      "network": "pku",
      "key_name": "Ethan"
    },
    "enable_docker": true,
    "enable_lobechat": true
  }'
```

> 注意：`enable_docker` 和 `enable_lobechat` 参数可以设置为 `true` 或 `false`，可以灵活组合使用。

### 3. 查看实例
```bash
curl http://localhost:5000/api/instances -H "X-API-Key: your-strong-token"
```

### 配置生成接口使用示例

#### 生成config.yaml配置
```bash
# 生成配置内容（仅返回内容，不生成文件）
curl -X POST http://localhost:5000/api/generate-config \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-strong-token" \
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
  -H "X-API-Key: your-strong-token" \
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
  -H "X-API-Key: your-strong-token" \
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
- `1panel` - 1Panel Linux服务器运维管理面板（支持主流Linux发行版）

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

### 1Panel服务详情

#### 功能特性
- 自动检测系统架构和操作系统
- 支持stable、beta、dev三种安装模式
- 自动下载并验证安装包的SHA256哈希值
- 完整的Docker管理功能
- 应用商店一键安装常用应用
- 文件管理、数据库管理、网站管理等功能

#### 系统要求
- 操作系统：Ubuntu 20.04/22.04、CentOS 7/8、Debian 10/11（包括国产操作系统）
- 服务器架构：x86_64、aarch64、armv7l、ppc64le、s390x
- 内存要求：建议可用内存在 1GB 以上
- 浏览器要求：Chrome、FireFox、IE10+、Edge 等现代浏览器

#### 访问方式
部署完成后，1Panel会在控制台输出访问信息：
```
http://服务器IP:端口/安全入口
```

登录服务器后，可通过以下命令查看访问信息：
```bash
1pctl user-info
```

#### 使用示例
```bash
# 部署1Panel
curl -X POST http://localhost:5000/api/deploy-services \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-strong-token" \
  -d '{
    "openstack": {
      "instance_name": "panel-server",
      "image": "Ubuntu 22.04",
      "flavor": "p2",
      "network": "pku",
      "key_name": "Ethan"
    },
    "enable_1panel": true
  }'
```

#### 注意事项
1. 确保OpenStack安全组开放1Panel的访问端口（默认端口会在安装时随机生成）
2. 安装完成后，请及时记录并妥善保管安全入口地址
3. 首次登录后建议修改默认密码
4. 1Panel会在 `/tmp` 目录下载安装包，安装完成后会自动清理
5. 支持通过 `1pctl` 命令行工具进行维护和管理
6. 官方文档：https://1panel.cn/docs/
