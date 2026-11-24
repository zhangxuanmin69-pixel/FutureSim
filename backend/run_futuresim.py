"""
FutureSim API Gateway 轻量启动入口（成员 C）
仅加载 FutureSim 模块，不依赖 LLM/Zep/OASIS，无需密钥。
完整 MiroFish 后端（run.py）也会注册同一蓝图，两者接口一致。

启动: python run_futuresim.py  （默认端口 5001，可用 FLASK_PORT 覆盖）
"""
import os
import sys

if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_cors import CORS

from futuresim_gateway import futuresim_bp, register_error_handlers


def create_gateway_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False
    CORS(app, resources={r'/api/*': {'origins': '*'}})
    app.register_blueprint(futuresim_bp, url_prefix='/api/v1')
    register_error_handlers(app)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'FutureSim Gateway (standalone)'}

    return app


if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', '5001'))
    create_gateway_app().run(host='0.0.0.0', port=port, debug=False, threaded=True)