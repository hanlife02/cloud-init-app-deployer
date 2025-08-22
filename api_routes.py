from flask import jsonify, request
import yaml
import os
from config_manager import load_deployment_configs
from cloud_config_generator import generate_cloud_config
from openstack_manager import deploy_to_openstack, get_instance_status, list_instances


def register_routes(app):
    
    @app.route('/api/generate-config', methods=['POST'])
    def generate_config():
        try:
            json_data = request.get_json()
            if not json_data:
                return jsonify({'error': '未提供JSON数据'}), 400
            
            yaml_content = generate_cloud_config(json_data)
            
            # 检查是否需要保存文件
            save_file = request.args.get('save', 'false').lower() == 'true'
            filename = request.args.get('filename', 'config.yaml')
            
            result = {
                'success': True,
                'message': '配置内容已生成',
                'content': yaml_content
            }
            
            if save_file:
                # 确保outputs目录存在
                output_dir = 'outputs'
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                file_path = os.path.join(output_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(yaml_content)
                
                result['message'] = f'cloud-init配置已生成并保存到 {file_path}'
                result['file_path'] = file_path
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500


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
                return jsonify({'error': '未提供JSON数据'}), 400
            
            if 'openstack' not in request_data:
                return jsonify({'error': '缺少OpenStack配置'}), 400
            
            deployment_configs = load_deployment_configs()
            
            enabled_services = {}
            for service_name, service_config in deployment_configs.get('deployments', {}).items():
                enable_key = f'enable_{service_name}'
                if request_data.get(enable_key, False):
                    enabled_services[service_name] = service_config.copy()
            
            final_config = {
                'openstack': request_data['openstack'],
                'deployments': enabled_services
            }
            
            result = deploy_to_openstack(final_config)
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/deploy', methods=['POST'])
    def deploy_instance():
        try:
            json_data = request.get_json()
            if not json_data:
                return jsonify({'error': '未提供JSON数据'}), 400
            
            result = deploy_to_openstack(json_data)
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/instance/status/<instance_name>', methods=['GET'])
    def instance_status(instance_name):
        try:
            result = get_instance_status(instance_name)
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 404
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/instances', methods=['GET'])
    def instances():
        try:
            result = list_instances()
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500