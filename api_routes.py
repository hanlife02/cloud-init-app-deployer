from flask import jsonify, request
import yaml
import os
import logging
from config_manager import load_deployment_configs
from cloud_config_generator import generate_cloud_config
from openstack_manager import deploy_to_openstack, get_instance_status, list_instances

logger = logging.getLogger(__name__)


def validate_openstack_config(config):
    """验证OpenStack配置"""
    required_fields = ['instance_name', 'image', 'flavor', 'network', 'key_name']
    for field in required_fields:
        if field not in config:
            raise ValueError(f'缺少必需的OpenStack配置字段: {field}')
    return True


def handle_api_error(error, status_code=500):
    """统一的API错误处理"""
    logger.error(f'API错误: {str(error)}')
    return jsonify({'error': str(error)}), status_code


def register_routes(app):
    
    @app.route('/api/generate-config', methods=['POST'])
    def generate_config():
        try:
            json_data = request.get_json()
            if not json_data:
                return handle_api_error('未提供JSON数据', 400)
            
            logger.info(f'生成配置请求: {json_data.keys()}')
            
            yaml_content = generate_cloud_config(json_data)
            
            save_file = request.args.get('save', 'false').lower() == 'true'
            filename = request.args.get('filename', 'config.yaml')
            
            result = {
                'success': True,
                'message': '配置内容已生成',
                'content': yaml_content
            }
            
            if save_file:
                output_dir = 'outputs'
                os.makedirs(output_dir, exist_ok=True)
                
                file_path = os.path.join(output_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(yaml_content)
                
                result['message'] = f'cloud-init配置已生成并保存到 {file_path}'
                result['file_path'] = file_path
                logger.info(f'配置文件已保存: {file_path}')
            
            return jsonify(result)
            
        except Exception as e:
            return handle_api_error(e)


    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Cloud-Init Config Generator API is running'})

    @app.route('/', methods=['GET'])
    def index():
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

    @app.route('/api/deploy-services', methods=['POST'])
    def deploy_with_services():
        try:
            request_data = request.get_json()
            if not request_data:
                return handle_api_error('未提供JSON数据', 400)
            
            if 'openstack' not in request_data:
                return handle_api_error('缺少OpenStack配置', 400)
            
            validate_openstack_config(request_data['openstack'])
            
            logger.info(f'部署服务请求: {request_data["openstack"]["instance_name"]}')
            
            deployment_configs = load_deployment_configs()
            
            enabled_services = {}
            for service_name, service_config in deployment_configs.get('deployments', {}).items():
                enable_key = f'enable_{service_name}'
                if request_data.get(enable_key, False):
                    enabled_services[service_name] = service_config.copy()
                    logger.info(f'启用服务: {service_name}')
            
            final_config = {
                'openstack': request_data['openstack'],
                'deployments': enabled_services
            }
            
            result = deploy_to_openstack(final_config)
            
            if result['success']:
                logger.info(f'部署成功: {request_data["openstack"]["instance_name"]}')
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except ValueError as e:
            return handle_api_error(e, 400)
        except Exception as e:
            return handle_api_error(e)

    @app.route('/api/deploy', methods=['POST'])
    def deploy_instance():
        try:
            json_data = request.get_json()
            if not json_data:
                return handle_api_error('未提供JSON数据', 400)
            
            if 'openstack' not in json_data:
                return handle_api_error('缺少OpenStack配置', 400)
            
            validate_openstack_config(json_data['openstack'])
            
            logger.info(f'部署实例请求: {json_data["openstack"]["instance_name"]}')
            
            result = deploy_to_openstack(json_data)
            
            if result['success']:
                logger.info(f'实例部署成功: {json_data["openstack"]["instance_name"]}')
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except ValueError as e:
            return handle_api_error(e, 400)
        except Exception as e:
            return handle_api_error(e)

    @app.route('/api/instance/status/<instance_name>', methods=['GET'])
    def instance_status(instance_name):
        try:
            logger.info(f'查询实例状态: {instance_name}')
            result = get_instance_status(instance_name)
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 404
                
        except Exception as e:
            return handle_api_error(e)

    @app.route('/api/instances', methods=['GET'])
    def instances():
        try:
            logger.info('查询所有实例')
            result = list_instances()
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return handle_api_error(e)