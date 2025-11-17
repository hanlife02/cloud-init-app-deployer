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
# 安装 python-dotenv 以自动加载 .env
pip install python-dotenv

# 修改 .env 中的 API_TOKEN 和 PORT 后，直接运行
python app.py
```

服务启动后，所有受保护接口都必须在请求头中携带 `X-API-Key: <API_TOKEN>`。

### 2. 部署实例（推荐方式：一次部署多个服务）

#### 一次性部署 Docker、LobeChat 和 1Panel（直接在 OpenStack 上创建实例）
```bash
curl -X POST http://localhost:5002/api/deploy-services \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-token" \
  -d '{
    "openstack": {
      "instance_name": "test",
      "image": "Ubuntu 22.04",
      "flavor": "p2",
      "network": "pku",
      "key_name": "Ethan"
    },
    "enable_docker": true,
    "enable_lobechat": true,
    "enable_1panel": true
  }'
```

> 注意：
> - 通过 `enable_docker`、`enable_lobechat`、`enable_1panel` 等参数，你可以用一次请求灵活组合要安装的服务；
> - 未设置或为 `false` 的服务不会被部署；
> - 支持的服务名称以 `enable_服务名` 的形式出现在请求体中（详见下方“可用服务”）。

### 3. 查看实例
```bash
curl http://localhost:5002/api/instances -H "X-API-Key: your-api-token"
```

### 配置生成接口使用示例

#### 生成 Cloud-Init YAML（仅返回内容，不保存到文件）
```bash
curl -X POST http://localhost:5002/api/generate-config \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-token" \
  -d '{
    "openstack": {
      "image": "Ubuntu 22.04"
    },
    "deployments": {
      "docker": {},
      "lobechat": {},
      "1panel": {}
    }
  }'

#### 生成 Cloud-Init 并保存到 outputs/config.yaml
curl -X POST "http://localhost:5002/api/generate-config?save=true" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: clabv2" \
  -d '{
    "openstack": {
      "image": "Ubuntu 22.04"
    },
    "deployments": {
      "docker": {},
      "lobechat": {},
      "1panel": {}
    }
  }'

#### 生成 Cloud-Init 并保存到自定义文件名
curl -X POST "http://localhost:5002/api/generate-config?save=true&filename=my-cloud-init.yaml" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-token" \
  -d '{
    "openstack": {
      "image": "Ubuntu 22.04"
    },
    "deployments": {
      "docker": {},
      "lobechat": {},
      "1panel": {}
    }
  }'
```

## 可用服务（enable_* 开关）

- `enable_docker`   - 安装 Docker 运行环境
- `enable_lobechat` - 部署 LobeChat（基于 Docker）
- `enable_1panel`   - 部署 1Panel 面板（基于官方安装脚本）

这些开关可以任意组合出现在同一个请求体中，由后端生成对应的 Cloud-Init，内部会自动按顺序执行 `services/` 目录下的安装脚本。
