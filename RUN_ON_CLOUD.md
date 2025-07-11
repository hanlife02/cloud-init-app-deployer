# 🚀 如何在云服务器上运行 Cloud-Init App Deployer

## 📋 准备工作

### 1. 云服务器要求
- **操作系统**: Ubuntu 18.04+, CentOS 7+, Amazon Linux 2
- **内存**: 至少 1GB RAM
- **存储**: 至少 10GB 可用空间
- **权限**: 需要 sudo 权限
- **网络**: 需要访问互联网

### 2. 安全组配置
确保在云平台控制台中开放以下端口：
- **22** (SSH)
- **8080** (应用端口，可自定义)

## 🎯 快速部署（推荐）

### 方法一：使用快速部署脚本

```bash
# 1. 登录到云服务器
ssh -i your-key.pem ubuntu@your-server-ip

# 2. 克隆项目
git clone https://github.com/your-username/Cloud-Init-App-Deployer.git
cd Cloud-Init-App-Deployer

# 3. 运行快速部署脚本
./quick-deploy.sh
```

### 方法二：手动部署

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装依赖
sudo apt install -y git curl wget cloud-init cron

# 3. 克隆项目
git clone https://github.com/your-username/Cloud-Init-App-Deployer.git
cd Cloud-Init-App-Deployer

# 4. 配置环境
cp config.env.example config.env
nano config.env  # 根据需要修改配置

# 5. 设置权限
chmod +x scripts/app/*.sh
chmod +x scripts/update/*.sh
chmod +x scripts/monitor/*.sh

# 6. 创建目录
sudo mkdir -p /opt/app/{logs,data,config}
sudo mkdir -p /var/log/cloud-app-deployer
sudo chown -R $USER:$USER /opt/app
sudo chown -R $USER:$USER /var/log/cloud-app-deployer

# 7. 安装应用
sudo ./scripts/app/install.sh
sudo ./scripts/app/configure.sh

# 8. 配置定时任务
sudo cp cron/crontab /etc/cron.d/cloud-app-monitor
sudo systemctl restart cron

# 9. 配置系统服务
sudo cp cloud-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cloud-app
sudo systemctl start cloud-app

# 10. 验证部署
./verify-setup.sh
```

## 🔧 配置说明

### 编辑配置文件
```bash
nano config.env
```

**重要配置项：**
- `APP_NAME`: 应用名称
- `APP_PORT`: 应用端口（确保安全组已开放）
- `NOTIFICATION_EMAIL`: 告警邮箱
- `AUTO_UPDATE_ENABLED`: 是否启用自动更新

### 配置通知（可选）
```bash
# 配置邮件通知
NOTIFICATION_EMAIL="admin@example.com"
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"

# 配置Slack通知
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

## 🔍 验证部署

### 检查服务状态
```bash
# 检查应用服务
sudo systemctl status cloud-app

# 检查定时任务
sudo crontab -l
sudo systemctl status cron
```

### 查看日志
```bash
# 应用日志
sudo journalctl -u cloud-app -f

# 部署日志
tail -f /var/log/cloud-app-deployer/deployment.log

# 监控日志
tail -f /var/log/cloud-app-deployer/monitor.log
```

### 测试应用
```bash
# 测试应用响应
curl http://localhost:8080/health

# 如果配置了域名
curl http://your-domain.com:8080/health
```

## 🛠️ 常见问题解决

### 1. 脚本权限问题
```bash
sudo chmod +x scripts/app/*.sh
sudo chmod +x scripts/update/*.sh
sudo chmod +x scripts/monitor/*.sh
```

### 2. 端口被占用
```bash
# 查看端口占用
sudo netstat -tlnp | grep :8080
sudo lsof -i :8080

# 杀死占用端口的进程
sudo kill -9 <PID>
```

### 3. 服务启动失败
```bash
# 查看详细错误日志
sudo journalctl -u cloud-app -n 50

# 手动启动调试
sudo ./scripts/app/start.sh
```

### 4. 定时任务不执行
```bash
# 检查cron服务
sudo systemctl status cron
sudo systemctl restart cron

# 检查定时任务配置
cat /etc/cron.d/cloud-app-monitor
```

### 5. 网络连接问题
```bash
# 检查DNS
nslookup google.com

# 检查防火墙
sudo ufw status
sudo iptables -L
```

## 📊 监控和维护

### 实时监控
```bash
# 查看系统资源
htop
df -h
free -h

# 查看应用状态
sudo systemctl status cloud-app
curl http://localhost:8080/health
```

### 日志管理
```bash
# 清理旧日志
sudo find /var/log/cloud-app-deployer -name "*.log.*" -mtime +7 -delete

# 查看日志大小
du -sh /var/log/cloud-app-deployer/
```

### 手动更新
```bash
# 检查更新
sudo /opt/cloud-app-deployer/scripts/update/check-update.sh

# 应用更新
sudo /opt/cloud-app-deployer/scripts/update/apply-update.sh
```

## 🔒 安全建议

### 1. 配置防火墙
```bash
sudo ufw allow ssh
sudo ufw allow 8080/tcp
sudo ufw enable
```

### 2. 定期更新系统
```bash
# 设置自动安全更新
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. 备份重要数据
```bash
# 手动备份
tar -czf backup-$(date +%Y%m%d).tar.gz /opt/app/data /opt/app/config

# 自动备份脚本
0 2 * * * /opt/cloud-app-deployer/scripts/backup.sh
```

## 🚨 故障排除

### 快速诊断
```bash
# 运行系统诊断
./verify-setup.sh

# 查看系统状态
sudo systemctl status cloud-app
sudo systemctl status cron
```

### 重启服务
```bash
# 重启应用
sudo systemctl restart cloud-app

# 重启定时任务
sudo systemctl restart cron
```

### 完全重新部署
```bash
# 停止所有服务
sudo systemctl stop cloud-app
sudo systemctl disable cloud-app

# 清理环境
sudo rm -rf /opt/app
sudo rm -rf /var/log/cloud-app-deployer
sudo rm /etc/systemd/system/cloud-app.service
sudo rm /etc/cron.d/cloud-app-monitor

# 重新部署
./quick-deploy.sh
```

## 📞 获取帮助

如果遇到问题：
1. 查看日志文件找到错误信息
2. 检查 [DEPLOYMENT.md](./DEPLOYMENT.md) 详细文档
3. 运行 `./verify-setup.sh` 进行系统检查
4. 在 GitHub 上提交 Issue

## 📚 相关文档

- [详细部署指南](./DEPLOYMENT.md)
- [项目说明](./README.md)
- [配置文件模板](./config.env.example)
