# 部署指南

## 快速开始

### 1. 准备云平台镜像

支持的云平台：
- AWS EC2
- Google Cloud Platform
- Azure
- 阿里云
- 腾讯云
- 华为云

### 2. 使用 Cloud-Init 部署

#### 方法一：直接使用 user-data（推荐）

1. 将 `cloud-init/user-data` 文件内容复制到云平台的用户数据/自定义数据字段中
2. 创建实例时选择支持 cloud-init 的操作系统镜像（如 Ubuntu 18.04+, CentOS 7+, Amazon Linux 2）
3. 启动实例

#### 方法二：制作自定义镜像

1. 基于标准镜像创建实例
2. 手动安装并配置应用
3. 制作镜像快照
4. 使用自定义镜像创建新实例

### 3. AWS EC2 部署示例

```bash
# 使用 AWS CLI 创建实例
aws ec2 run-instances \
    --image-id ami-0abcdef1234567890 \
    --instance-type t3.micro \
    --key-name your-key-pair \
    --security-group-ids sg-0123456789abcdef0 \
    --user-data file://cloud-init/user-data \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=cloud-init-app}]'
```

### 4. 验证部署

部署完成后，可以通过以下方式验证：

```bash
# SSH 连接到实例
ssh -i your-key.pem ubuntu@your-instance-ip

# 检查服务状态
sudo systemctl status cloud-app.service

# 查看日志
sudo journalctl -u cloud-app.service -f
tail -f /opt/app/logs/deployment.log

# 检查定时任务
sudo crontab -l
```

## 配置说明

### 环境变量配置

在部署前，请根据实际需求修改 `config.env` 文件中的配置参数。

### 安全组配置

确保云平台的安全组开放以下端口：
- 22 (SSH)
- 8080 (应用端口，可根据需要修改)

### 存储配置

建议为日志目录挂载独立的存储卷：
- 最小存储容量：10GB
- 推荐存储容量：50GB
- 存储类型：通用SSD

## 故障排除

### 常见问题

1. **Cloud-init 未执行**
   - 检查镜像是否支持 cloud-init
   - 查看 `/var/log/cloud-init.log`

2. **脚本执行失败**
   - 检查脚本权限：`ls -la /opt/app/scripts/`
   - 查看错误日志：`tail -f /opt/app/logs/deployment.log`

3. **服务启动失败**
   - 检查服务状态：`systemctl status cloud-app.service`
   - 查看服务日志：`journalctl -u cloud-app.service`

4. **定时任务未运行**
   - 检查 cron 服务：`systemctl status cron`
   - 查看任务配置：`cat /etc/cron.d/app-monitor`

### 调试命令

```bash
# 检查 cloud-init 状态
cloud-init status

# 重新运行 cloud-init
sudo cloud-init clean
sudo cloud-init init
sudo cloud-init modules

# 手动执行脚本测试
sudo /opt/app/scripts/app/install.sh
sudo /opt/app/scripts/monitor/health-check.sh
```

## 更新和维护

### 应用更新

系统会自动检查更新（每天凌晨2点），也可以手动触发：

```bash
sudo /opt/app/scripts/update/check-update.sh
```

### 日志管理

- 日志文件会自动轮转和清理
- 手动清理：`sudo find /opt/app/logs -name "*.log.*" -mtime +7 -delete`

### 备份

建议定期备份以下内容：
- 应用配置：`/opt/app/config/`
- 应用数据：`/opt/app/data/`
- 重要日志：`/opt/app/logs/`
