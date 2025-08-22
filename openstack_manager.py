#!/usr/bin/env python3
"""OpenStack操作模块"""

import subprocess
import tempfile
import os
import json
from typing import Dict, Any
from cloud_config_generator import generate_cloud_config


def deploy_to_openstack(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """部署实例到OpenStack"""
    try:
        if 'openstack' not in config_data:
            raise ValueError("缺少OpenStack配置")
        
        openstack_config = config_data['openstack']
        required_fields = ['instance_name', 'image', 'flavor', 'network', 'key_name']
        
        for field in required_fields:
            if field not in openstack_config:
                raise ValueError(f"缺少必需的OpenStack配置字段: {field}")
        
        yaml_content = generate_cloud_config(config_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            temp_file.write(yaml_content)
            temp_file_path = temp_file.name
        
        try:
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
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                'success': True,
                'message': f'实例 {openstack_config["instance_name"]} 创建成功',
                'output': result.stdout,
                'user_data': yaml_content
            }
        
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': f'OpenStack命令执行失败: {e.stderr}',
            'returncode': e.returncode
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_instance_status(instance_name: str) -> Dict[str, Any]:
    """获取OpenStack实例状态"""
    try:
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
        return {
            'success': False,
            'error': f'无法获取实例状态: {e.stderr}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def list_instances() -> Dict[str, Any]:
    """列出所有OpenStack实例"""
    try:
        cmd = ['openstack', 'server', 'list', '--format', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        instances = json.loads(result.stdout)
        
        return {
            'success': True,
            'instances': instances
        }
        
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': f'无法获取实例列表: {e.stderr}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }