# 日志目录说明
#
# 该目录用于存储应用的各种日志文件：
#
# app.log          - 应用程序运行日志
# update.log       - 应用更新日志
# monitor.log      - 健康检查和监控日志
# deployment.log   - 部署过程日志
# system.log       - 系统操作日志
# reports.log      - 定期报告日志
# maintenance.log  - 维护操作日志
#
# 日志轮转策略：
# - 每小时检查日志大小
# - 超过100MB的日志文件会被轮转
# - 保留最近7天的日志文件
# - 压缩旧的日志文件以节省空间

# 创建时间: $(date)
# 权限: 755 (appuser:appuser)
