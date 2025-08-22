<!--
 * @Author: Ethan yanghan0911@gmail.com
 * @Date: 2025-08-22 19:48:48
 * @LastEditors: Ethan yanghan0911@gmail.com
 * @LastEditTime: 2025-08-22 19:48:50
 * @FilePath: /Cloud-Init-App-Deployer/API.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
## API接口

### 部署相关
- `POST /api/deploy-services` - 接收OpenStack配置并根据enable_*参数选择性部署服务（推荐）
- `POST /api/deploy` - 接收完整JSON配置并启动实例（自定义方式）
- `POST /api/generate-config` - 生成cloud-init YAML配置文件
- `GET /api/instances` - 列出所有实例
- `GET /api/instance/status/<name>` - 获取指定实例状态