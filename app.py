#!/usr/bin/env python3
from flask import Flask, request, jsonify
import json
import yaml
import subprocess
from typing import Dict, Any

app = Flask(__name__)

def load_deployment_configs() -> Dict[str, Any]:
    """从本地文件加载部署配置（仅包含 Docker 等服务配置）"""
    try:
        with open('deployment-configs.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'deployments': {}}
    except Exception as e:
        raise Exception(f"加载部署配置失败: {str(e)}")

def generate_cloud_config(config_data: Dict[str, Any]) -> str:
    """根据JSON配置生成cloud-config YAML"""
    
    # 获取部署配置中的所有服务（所有传入的服务都认为是启用的）
    enabled_services = list(config_data.get('deployments', {}).keys())
    
    # 构建cloud-config结构
    cloud_config = {
        '#cloud-config': None,
        'package_update': True,
        'package_upgrade': True,
        'packages': [],
        'runcmd': [],
        'final_message': '应用部署完成'
    }
    
    # 收集所有包
    packages = set()
    commands = []
    
    for service in enabled_services:
        service_config = config_data['deployments'][service]
        
        # 添加包
        if 'packages' in service_config:
            packages.update(service_config['packages'])
        
        # 添加命令
        commands.append(f'# {service} 配置')
        if 'commands' in service_config:
            commands.extend(service_config['commands'])
        
        # 添加测试命令（如果启用）
        if service_config.get('test_container', False) and 'test_commands' in service_config:
            commands.extend(service_config['test_commands'])
    
    cloud_config['packages'] = sorted(list(packages))
    cloud_config['runcmd'] = commands
    
    # 转换为YAML格式
    yaml_content = "#cloud-config\n\n"
    yaml_content += yaml.dump({
        'package_update': cloud_config['package_update'],
        'package_upgrade': cloud_config['package_upgrade'],
        'packages': cloud_config['packages'],
        'runcmd': cloud_config['runcmd'],
        'final_message': cloud_config['final_message']
    }, default_flow_style=False, allow_unicode=True, indent=2)
    
    return yaml_content

@app.route('/api/generate-config', methods=['POST'])
def generate_config():
    """接收JSON配置并生成config.yaml内容"""
    try:
        # 获取JSON数据
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': '未提供JSON数据'}), 400
        
        # 生成cloud-config
        yaml_content = generate_cloud_config(json_data)
        
        return jsonify({
            'success': True,
            'message': '配置内容已生成',
            'content': yaml_content
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'healthy', 'message': 'Cloud-Init Config Generator API is running'})

@app.route('/', methods=['GET'])
def index():
    """API文档"""
    return jsonify({
        'name': 'Cloud-Init Config Generator API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/generate-config': '接收JSON配置并生成config.yaml内容',
            'POST /api/deploy': '接收完整JSON配置并启动OpenStack实例',
            'POST /api/deploy-services': '接收OpenStack配置并根据enable_*参数选择性部署服务（推荐）',
            'GET /api/instances': '列出所有OpenStack实例',
            'GET /api/instance/status/<name>': '获取指定实例的状态',
            'GET /api/health': '健康检查'
        },
        'example_request_deploy_services': {
            'openstack': {
                'instance_name': 'test',
                'image': 'Ubuntu 22.04',
                'flavor': 'p2',
                'network': 'pku',
                'key_name': 'Ethan'
            },
            'enable_docker': True,
            'enable_nginx': True,
            'enable_mysql': False,
            'enable_nodejs': False
        },
        'available_services': ['docker', 'nginx', 'mysql', 'nodejs'],
        'example_request_deploy': {
            'openstack': {
                'instance_name': 'test',
                'image': 'Ubuntu 22.04',
                'flavor': 'p2',
                'network': 'pku',
                'key_name': 'Ethan'
            },
            'deployments': {
                'docker': {
                    'enabled': True,
                    'packages': ['docker.io'],
                    'commands': ['systemctl enable docker', 'systemctl start docker']
                }
            }
        }
    })

def deploy_to_openstack(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """部署实例到OpenStack"""
    try:
        # 检查OpenStack配置
        if 'openstack' not in config_data:
            raise ValueError("缺少OpenStack配置")
        
        openstack_config = config_data['openstack']
        required_fields = ['instance_name', 'image', 'flavor', 'network', 'key_name']
        
        for field in required_fields:
            if field not in openstack_config:
                raise ValueError(f"缺少必需的OpenStack配置字段: {field}")
        
        # 生成cloud-config内容
        yaml_content = generate_cloud_config(config_data)
        
        # 构建OpenStack命令
        cmd = [
            'openstack', 'server', 'create',
            '--image', openstack_config['image'],
            '--flavor', openstack_config['flavor'],
            '--network', openstack_config['network'],
            '--user-data', '-',  # 从stdin读取user-data
            '--key-name', openstack_config['key_name']
        ]
        
        # 可选参数
        if 'security_groups' in openstack_config:
            for sg in openstack_config['security_groups']:
                cmd.extend(['--security-group', sg])
        
        if 'availability_zone' in openstack_config:
            cmd.extend(['--availability-zone', openstack_config['availability_zone']])
        
        # 实例名称
        cmd.append(openstack_config['instance_name'])
        
        # 执行OpenStack命令，通过stdin传递user-data
        result = subprocess.run(cmd, input=yaml_content, text=True, capture_output=True, check=True)
        
        return {
            'success': True,
            'message': f'实例 {openstack_config["instance_name"]} 创建成功',
            'output': result.stdout,
            'user_data': yaml_content
        }
        
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

@app.route('/api/deploy-services', methods=['POST'])
def deploy_with_services():
    """接收OpenStack配置并根据enable_*参数选择性部署服务"""
    try:
        # 获取请求中的配置
        request_data = request.get_json()
        if not request_data:
            return jsonify({'error': '未提供JSON数据'}), 400
        
        # 检查OpenStack配置
        if 'openstack' not in request_data:
            return jsonify({'error': '缺少OpenStack配置'}), 400
        
        # 从本地文件加载服务配置
        deployment_configs = load_deployment_configs()
        
        # 根据请求中的 enable_* 参数启用相应服务
        enabled_services = {}
        for service_name, service_config in deployment_configs.get('deployments', {}).items():
            enable_key = f'enable_{service_name}'
            if request_data.get(enable_key, False):
                # 直接复制服务配置，不需要设置 enabled 字段
                enabled_services[service_name] = service_config.copy()
        
        # 合并 OpenStack 配置和启用的服务配置
        final_config = {
            'openstack': request_data['openstack'],
            'deployments': enabled_services
        }
        
        # 部署到OpenStack
        result = deploy_to_openstack(final_config)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deploy', methods=['POST'])
def deploy_instance():
    """接收JSON配置并启动OpenStack实例"""
    try:
        # 获取JSON数据
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': '未提供JSON数据'}), 400
        
        # 部署到OpenStack
        result = deploy_to_openstack(json_data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instance/status/<instance_name>', methods=['GET'])
def get_instance_status(instance_name):
    """获取OpenStack实例状态"""
    try:
        cmd = ['openstack', 'server', 'show', instance_name, '--format', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        instance_info = json.loads(result.stdout)
        
        return jsonify({
            'success': True,
            'instance': {
                'name': instance_info.get('name'),
                'status': instance_info.get('status'),
                'power_state': instance_info.get('power_state'),
                'created': instance_info.get('created'),
                'updated': instance_info.get('updated'),
                'addresses': instance_info.get('addresses', {})
            }
        })
        
    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'error': f'无法获取实例状态: {e.stderr}'
        }), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instances', methods=['GET'])
def list_instances():
    """列出所有OpenStack实例"""
    try:
        cmd = ['openstack', 'server', 'list', '--format', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        instances = json.loads(result.stdout)
        
        return jsonify({
            'success': True,
            'instances': instances
        })
        
    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'error': f'无法获取实例列表: {e.stderr}'
        }), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)