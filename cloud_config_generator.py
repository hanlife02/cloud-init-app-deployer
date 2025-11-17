import copy
import logging
import os
from typing import Dict, Any
import yaml
from config_manager import get_docker_config_for_image, load_deployment_configs

logger = logging.getLogger(__name__)


def _render_heredoc(target_path: str, content: str) -> str:
    """将多行内容写入目标文件的shell命令"""
    body = content.rstrip('\n')
    return "\n".join([
        f"cat <<'EOF' > {target_path}",
        body,
        "EOF"
    ])


def generate_lobechat_install(service_config: Dict[str, Any]) -> list:
    """为LobeChat生成安装脚本调用"""
    if not isinstance(service_config, dict):
        raise ValueError("LobeChat服务配置必须是对象")

    files_commands = []

    script_path = os.path.join(os.path.dirname(__file__), 'services', 'install-lobechat.sh')
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            install_script = f.read()

        install_dir = service_config.get('install_dir', '/opt/lobechat')
        env_config = service_config.get('environment', {}) or {}

        files_commands.append(f"mkdir -p {install_dir}")
        files_commands.append(_render_heredoc(f"{install_dir}/install-lobechat.sh", install_script))
        files_commands.append(f"chmod +x {install_dir}/install-lobechat.sh")

        env_parts = [f"LOBECHAT_INSTALL_DIR={install_dir}"]
        if 'OPENAI_API_KEY' in env_config:
            env_parts.append(f"OPENAI_API_KEY='{env_config['OPENAI_API_KEY']}'")
        if 'OPENAI_PROXY_URL' in env_config:
            env_parts.append(f"OPENAI_PROXY_URL='{env_config['OPENAI_PROXY_URL']}'")
        if 'ACCESS_CODE' in env_config:
            env_parts.append(f"ACCESS_CODE='{env_config['ACCESS_CODE']}'")

        env_prefix = " ".join(env_parts)
        files_commands.append(f"cd {install_dir}")
        files_commands.append(f"{env_prefix} bash {install_dir}/install-lobechat.sh")

        logger.info("已添加LobeChat安装配置")
    except Exception as e:
        logger.error(f"读取Lobechat安装脚本失败: {str(e)}")
        raise ValueError(f"无法读取Lobechat安装脚本: {str(e)}")

    return files_commands


def generate_1panel_install(service_config: Dict[str, Any]) -> list:
    """为1Panel生成安装脚本"""
    if not isinstance(service_config, dict):
        raise ValueError("1Panel服务配置必须是对象")

    files_commands = []

    # 读取1Panel安装脚本
    script_path = os.path.join(os.path.dirname(__file__), 'services', 'install-1panel.sh')
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            install_script = f.read()

        # 设置安装模式（stable, beta, dev）
        install_mode = service_config.get('install_mode', 'stable')
        install_dir = service_config.get('install_dir', '/tmp')

        # 将安装脚本写入到目标系统
        files_commands.append(f"mkdir -p {install_dir}")
        files_commands.append(_render_heredoc(f"{install_dir}/install-1panel.sh", install_script))
        files_commands.append(f"chmod +x {install_dir}/install-1panel.sh")

        # 执行安装脚本
        files_commands.append(f"cd {install_dir}")
        files_commands.append(f"INSTALL_MODE={install_mode} bash {install_dir}/install-1panel.sh")

        logger.info("已添加1Panel安装配置")
    except Exception as e:
        logger.error(f"读取1Panel安装脚本失败: {str(e)}")
        raise ValueError(f"无法读取1Panel安装脚本: {str(e)}")

    return files_commands


def generate_cloud_config(config_data: Dict[str, Any]) -> str:
    """生成Cloud-Init配置内容"""
    try:
        deployment_configs = load_deployment_configs()
        
        deployments_section = config_data.get('deployments', {})
        if deployments_section is None:
            deployments_section = {}
        if not isinstance(deployments_section, dict):
            raise ValueError("deployments字段必须为对象")

        enabled_services = list(deployments_section.keys())
        logger.info(f"启用的服务: {enabled_services}")
        
        packages = set()
        commands = []
        
        image_name = config_data.get('openstack', {}).get('image', 'Ubuntu 22.04')
        
        for service in enabled_services:
            logger.info(f"处理服务: {service}")
            raw_service_config = deployments_section.get(service)
            if not isinstance(raw_service_config, dict):
                raise ValueError(f"{service} 配置必须为对象")
            service_config = copy.deepcopy(raw_service_config)
            
            # Docker 通过脚本安装
            if service == 'docker':
                install_dir = service_config.get('install_dir', '/tmp')
                script_path = os.path.join(os.path.dirname(__file__), 'services', 'install-docker.sh')
                try:
                    with open(script_path, 'r', encoding='utf-8') as f:
                        docker_script = f.read()
                    commands.append(f'# {service} 配置')
                    commands.append(f"mkdir -p {install_dir}")
                    commands.append(_render_heredoc(f"{install_dir}/install-docker.sh", docker_script))
                    commands.append(f"chmod +x {install_dir}/install-docker.sh")
                    commands.append(f"cd {install_dir}")
                    commands.append(f"bash {install_dir}/install-docker.sh")
                    logger.info("已添加Docker安装配置")
                except Exception as e:
                    logger.error(f"读取Docker安装脚本失败: {str(e)}")
                    raise ValueError(f"无法读取Docker安装脚本: {str(e)}")

            # LobeChat 部署通过脚本安装
            if service == 'lobechat':
                # 确保 Docker 安装
                if 'docker' not in enabled_services:
                    logger.info("LobeChat需要Docker，自动添加Docker安装脚本执行")
                    docker_service_cfg = deployment_configs.get('deployments', {}).get('docker', {'install_dir': '/tmp'})
                    docker_install_dir = docker_service_cfg.get('install_dir', '/tmp')
                    script_path = os.path.join(os.path.dirname(__file__), 'services', 'install-docker.sh')
                    try:
                        with open(script_path, 'r', encoding='utf-8') as f:
                            docker_script = f.read()
                        commands.append('# Docker 自动配置')
                        commands.append(f"mkdir -p {docker_install_dir}")
                        commands.append(_render_heredoc(f"{docker_install_dir}/install-docker.sh", docker_script))
                        commands.append(f"chmod +x {docker_install_dir}/install-docker.sh")
                        commands.append(f"cd {docker_install_dir}")
                        commands.append(f"bash {docker_install_dir}/install-docker.sh")
                    except Exception as e:
                        logger.error(f"读取Docker安装脚本失败: {str(e)}")
                        raise ValueError(f"无法读取Docker安装脚本: {str(e)}")

                lobechat_install = generate_lobechat_install(service_config)
                commands.extend(lobechat_install)

            # 1Panel 部署通过脚本安装
            if service == '1panel':
                onepanel_install = generate_1panel_install(service_config)
                commands.extend(onepanel_install)

            if service_config.get('test_container', False) and 'test_commands' in service_config:
                commands.extend(service_config['test_commands'])
        
        yaml_content = "#cloud-config\n\n"
        yaml_content += yaml.dump({
            'package_update': True,
            'package_upgrade': True,
            'packages': sorted(list(packages)),
            'runcmd': commands,
            'final_message': '应用部署完成'
        }, default_flow_style=False, allow_unicode=True, indent=2)
        
        logger.info(f"Cloud-Init配置已生成，包含{len(packages)}个包和{len(commands)}条命令")
        return yaml_content
        
    except Exception as e:
        logger.error(f"Cloud-Init配置生成失败: {str(e)}")
        raise
