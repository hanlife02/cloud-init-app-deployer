#!/usr/bin/env python3
from flask import Flask
from api_routes import register_routes

app = Flask(__name__)

# 注册所有API路由
register_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)