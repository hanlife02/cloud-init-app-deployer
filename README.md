<!--
 * @Author: Ethan yanghan0911@gmail.com
 * @Date: 2025-08-07 20:39:14
 * @LastEditors: Ethan yanghan0911@gmail.com
 * @LastEditTime: 2025-08-07 21:30:41
 * @FilePath: /Cloud-Init-App-Deployer/README.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
### 1. 配置应用
`deployment-configs.json` 文件，设置需要部署的应用：

### 2. 一键部署
```bash
./deploy.sh
```

## 文件说明

- `deployment-configs.json` - 应用部署配置（包含OpenStack参数）
- `deploy.sh` - 一键部署脚本
- `generate_config.sh` - 配置生成脚本  
- `config.yaml` - 生成的 Cloud-Init 配置文件

## 支持的应用

| 应用 | 说明 |
|------|------|
| docker | Docker CE 容器运行时 |

## 添加新应用

在 `deployment-configs.json` 中添加新应用配置：

```json
{
  "deployments": {
    "your-app": {
      "enabled": true,
      "version": "latest",
      "packages": ["package1", "package2"],
      "commands": [
        "command1",
        "command2"
      ],
      "test_container": false,
      "test_commands": ["test-command"]
    }
  }
}
```

## 要求

- Bash 4.0+
- 可选：`jq` (用于更好的 JSON 解析性能)

```bash
# 安装 jq (可选)
sudo apt-get install jq
```