import yaml
import logging
from typing import Dict, Any
from config_manager import get_docker_config_for_image, load_deployment_configs

logger = logging.getLogger(__name__)


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