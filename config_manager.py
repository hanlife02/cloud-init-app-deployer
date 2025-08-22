import json
from typing import Dict, Any


def load_deployment_configs() -> Dict[str, Any]:
    try:
        with open('deployment-configs.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'deployments': {}}
    except Exception as e:
        raise Exception(f"加载部署配置失败: {str(e)}")


def load_docker_install_configs() -> Dict[str, Any]:
    try:
        with open('deployment-configs.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return {
                'docker_install_configs': config.get('docker_install_configs', {}),
                'image_mapping': config.get('image_mapping', {})
            }
    except FileNotFoundError:
        raise Exception("部署配置文件不存在")
    except Exception as e:
        raise Exception(f"加载Docker安装配置失败: {str(e)}")


def get_docker_config_for_image(image_name: str) -> Dict[str, Any]:
    docker_configs = load_docker_install_configs()
    
    os_type = None
    for img_pattern, os_name in docker_configs['image_mapping'].items():
        if img_pattern.lower() in image_name.lower():
            os_type = os_name
            break
    
    if not os_type:
        os_type = 'ubuntu'
    
    if os_type not in docker_configs['docker_install_configs']:
        raise Exception(f"不支持的操作系统类型: {os_type}")
    
    return docker_configs['docker_install_configs'][os_type]