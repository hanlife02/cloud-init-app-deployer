import logging
import os
from flask import Flask
from api_routes import register_routes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

register_routes(app)

if not os.getenv('API_TOKEN'):
    logging.warning('API_TOKEN环境变量未设置：受保护的API端点将拒绝所有请求')


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {'1', 'true', 'yes', 'on'}


if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    debug_mode = _as_bool(os.getenv('FLASK_DEBUG'), default=False)
    if debug_mode and host not in {'127.0.0.1', 'localhost'}:
        logging.warning('已禁用调试模式：请使用本地回环地址以启用Flask调试器')
        debug_mode = False
    app.run(host=host, port=port, debug=debug_mode)
