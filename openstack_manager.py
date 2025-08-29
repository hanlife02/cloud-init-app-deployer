import subprocess
import tempfile
import os
import json
import logging
from contextlib import contextmanager
from typing import Dict, Any
from cloud_config_generator import generate_cloud_config

logger = logging.getLogger(__name__)


@contextmanager
def temp_yaml_file(content: str):
    """上下文管理器用于处理临时YAML文件"""
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        temp_file.write(content)
        temp_file.flush()
        yield temp_file.name
    finally:
        if temp_file:
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


def deploy_to_openstack(config_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if 'openstack' not in config_data:
            raise ValueError("缺少OpenStack配置")
        
        openstack_config = config_data['openstack']
        required_fields = ['instance_name', 'image', 'flavor', 'network', 'key_name']
        
        for field in required_fields:
            if field not in openstack_config:
                raise ValueError(f"缺少必需的OpenStack配置字段: {field}")
        
        logger.info(f"开始部署实例: {openstack_config['instance_name']}")
        
        yaml_content = generate_cloud_config(config_data)
        
        with temp_yaml_file(yaml_content) as temp_file_path:
            cmd = [
                'openstack', 'server', 'create',
                '--image', openstack_config['image'],
                '--flavor', openstack_config['flavor'],
                '--network', openstack_config['network'],
                '--user-data', temp_file_path,
                '--key-name', openstack_config['key_name']
            ]
            
            if 'security_groups' in openstack_config:
                for sg in openstack_config['security_groups']:
                    cmd.extend(['--security-group', sg])
            
            if 'availability_zone' in openstack_config:
                cmd.extend(['--availability-zone', openstack_config['availability_zone']])

            cmd.append(openstack_config['instance_name'])
            
            logger.info(f"OpenStack命令: {' '.join(cmd[:3])} ... {openstack_config['instance_name']}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"实例 {openstack_config['instance_name']} 创建成功")
            
            return {
                'success': True,
                'message': f'实例 {openstack_config["instance_name"]} 创建成功',
                'output': result.stdout,
                'user_data': yaml_content
            }
        
    except subprocess.CalledProcessError as e:
        error_msg = f'OpenStack命令执行失败: {e.stderr}'
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'returncode': e.returncode
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f'部署失败: {error_msg}')
        return {
            'success': False,
            'error': error_msg
        }


def get_instance_status(instance_name: str) -> Dict[str, Any]:
    try:
        logger.info(f"查询实例状态: {instance_name}")
        
        cmd = ['openstack', 'server', 'show', instance_name, '--format', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        instance_info = json.loads(result.stdout)
        
        return {
            'success': True,
            'instance': {
                'name': instance_info.get('name'),
                'status': instance_info.get('status'),
                'power_state': instance_info.get('power_state'),
                'created': instance_info.get('created'),
                'updated': instance_info.get('updated'),
                'addresses': instance_info.get('addresses', {})
            }
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f'无法获取实例状态: {e.stderr}'
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }
    except json.JSONDecodeError as e:
        error_msg = f'JSON解析错误: {str(e)}'
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f'获取实例状态失败: {error_msg}')
        return {
            'success': False,
            'error': error_msg
        }


def list_instances() -> Dict[str, Any]:
    try:
        logger.info("查询所有实例列表")
        
        cmd = ['openstack', 'server', 'list', '--format', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        instances = json.loads(result.stdout)
        
        return {
            'success': True,
            'instances': instances
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f'无法获取实例列表: {e.stderr}'
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }
    except json.JSONDecodeError as e:
        error_msg = f'JSON解析错误: {str(e)}'
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f'获取实例列表失败: {error_msg}')
        return {
            'success': False,
            'error': error_msg
        }