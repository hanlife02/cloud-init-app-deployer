import yaml
import logging
import json
from typing import Dict, Any
from config_manager import get_docker_config_for_image, load_deployment_configs

logger = logging.getLogger(__name__)


def generate_lobechat_files(service_config: Dict[str, Any]) -> list:
    """为LobeChat生成docker-compose文件和自动更新脚本"""
    files_commands = []
    
    # 生成docker-compose.yml文件
    docker_compose_content = {
        'version': service_config['docker_compose']['version'],
        'services': service_config['docker_compose']['services'].copy()
    }
    
    # 替换环境变量
    for service_name, service in docker_compose_content['services'].items():
        if 'environment' in service:
            for env_key, env_value in service['environment'].items():
                if env_value.startswith('${') and env_value.endswith('}'):
                    var_name = env_value[2:-1]  # 移除 ${ 和 }
                    if var_name in service_config['environment']:
                        service['environment'][env_key] = service_config['environment'][var_name]
    
    docker_compose_yaml = yaml.dump(docker_compose_content, default_flow_style=False, allow_unicode=True, indent=2)
    
    # 写入docker-compose.yml文件
    files_commands.append(f"cat > /opt/lobechat/docker-compose.yml << 'EOF'")
    files_commands.append(docker_compose_yaml.strip())
    files_commands.append("EOF")
    
    # 生成自动更新脚本
    update_script = service_config.get('auto_update_script', '')
    if update_script:
        files_commands.append(f"cat > /opt/lobechat/auto-update-lobe-chat.sh << 'EOF'")
        files_commands.append(update_script)
        files_commands.append("EOF")
        files_commands.append("chmod +x /opt/lobechat/auto-update-lobe-chat.sh")
        
        # 添加到crontab
        files_commands.append("(crontab -l 2>/dev/null; echo '0 2 * * * /opt/lobechat/auto-update-lobe-chat.sh >> /var/log/lobe-chat-update.log 2>&1') | crontab -")
    
    return files_commands


def generate_cloud_config(config_data: Dict[str, Any]) -> str:
    """生成Cloud-Init配置内容"""
    try:
        deployment_configs = load_deployment_configs()
        
        enabled_services = list(config_data.get('deployments', {}).keys())
        logger.info(f"启用的服务: {enabled_services}")
        
        cloud_config = {
            '#cloud-config': None,
            'package_update': True,
            'package_upgrade': True,
            'packages': [],
            'runcmd': [],
            'final_message': '应用部署完成'
        }
        
        packages = set()
        commands = []
        
        image_name = config_data.get('openstack', {}).get('image', 'Ubuntu 22.04')
        
        for service in enabled_services:
            logger.info(f"处理服务: {service}")
            service_config = config_data['deployments'][service].copy()
            
            if service == 'docker':
                try:
                    docker_config = get_docker_config_for_image(image_name)
                    service_config['packages'] = docker_config['packages']
                    service_config['commands'] = docker_config['commands']
                    logger.info(f"Docker配置已适配镜像: {image_name}")
                except Exception as e:
                    logger.warning(f"获取Docker配置失败，使用默认配置: {str(e)}")
                    if 'deployments' in deployment_configs and 'docker' in deployment_configs['deployments']:
                        default_docker = deployment_configs['deployments']['docker']
                        if 'packages' not in service_config and 'packages' in default_docker:
                            service_config['packages'] = default_docker['packages']
                        if 'commands' not in service_config and 'commands' in default_docker:
                            service_config['commands'] = default_docker['commands']
            else:
                if 'deployments' in deployment_configs and service in deployment_configs['deployments']:
                    default_service = deployment_configs['deployments'][service]
                    if 'packages' not in service_config and 'packages' in default_service:
                        service_config['packages'] = default_service['packages']
                    if 'commands' not in service_config and 'commands' in default_service:
                        service_config['commands'] = default_service['commands']
            
            if 'packages' in service_config:
                packages.update(service_config['packages'])
            
            commands.append(f'# {service} 配置')
            if 'commands' in service_config:
                commands.extend(service_config['commands'])
            
            # 特殊处理LobeChat部署
            if service == 'lobechat':
                # 首先检查并安装Docker
                if 'docker' not in enabled_services:
                    logger.info("LobeChat需要Docker，自动添加Docker安装步骤")
                    try:
                        docker_config = get_docker_config_for_image(image_name)
                        packages.update(docker_config['packages'])
                        commands.append('# Docker 自动配置')
                        commands.extend(docker_config['commands'])
                    except Exception as e:
                        logger.warning(f"获取Docker配置失败: {str(e)}")
                        commands.extend([
                            'apt-get install -y docker.io',
                            'systemctl enable docker',
                            'systemctl start docker',
                            'usermod -aG docker ubuntu'
                        ])
                
                # 生成LobeChat特定的文件和配置
                lobechat_files = generate_lobechat_files(service_config)
                commands.extend(lobechat_files)
                
                # 启动LobeChat服务
                commands.append('cd /opt/lobechat && docker-compose up -d')
                logger.info("已添加LobeChat部署和自动更新配置")
            
            if service_config.get('test_container', False) and 'test_commands' in service_config:
                commands.extend(service_config['test_commands'])
        
        cloud_config['packages'] = sorted(list(packages))
        cloud_config['runcmd'] = commands
        
        yaml_content = "#cloud-config\n\n"
        yaml_content += yaml.dump({
            'package_update': cloud_config['package_update'],
            'package_upgrade': cloud_config['package_upgrade'],
            'packages': cloud_config['packages'],
            'runcmd': cloud_config['runcmd'],
            'final_message': cloud_config['final_message']
        }, default_flow_style=False, allow_unicode=True, indent=2)
        
        logger.info(f"Cloud-Init配置已生成，包含{len(packages)}个包和{len(commands)}条命令")
        return yaml_content
        
    except Exception as e:
        logger.error(f"Cloud-Init配置生成失败: {str(e)}")
        raise