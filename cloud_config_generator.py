#!/usr/bin/env python3
"""Cloud-config生成器模块"""

import yaml
from typing import Dict, Any
from config_manager import get_docker_config_for_image


def generate_cloud_config(config_data: Dict[str, Any]) -> str:
    """根据JSON配置生成cloud-config YAML"""
    
    enabled_services = list(config_data.get('deployments', {}).keys())
    
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
        service_config = config_data['deployments'][service].copy()
        
        if service == 'docker':
            try:
                docker_config = get_docker_config_for_image(image_name)
                service_config['packages'] = docker_config['packages']
                service_config['commands'] = docker_config['commands']
            except Exception as e:
                print(f"获取Docker配置失败，使用默认配置: {str(e)}")
        
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
    
    return yaml_content