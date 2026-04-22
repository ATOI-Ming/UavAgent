"""
Flask + SocketIO Web 服务器
负责：
1. 提供 REST API
2. 处理 WebSocket 实时通信
3. 服务前端静态文件
"""
import logging
from pathlib import Path
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

from config.settings import WEB_HOST, WEB_PORT, WEB_DEBUG

logger = logging.getLogger(__name__)

# ── 创建 Flask 应用 ────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder=str(
        Path(__file__).parent.parent / "frontend" / "web" / "build"
    ),
    static_url_path="",
)
app.config["SECRET_KEY"] = "uav-agent-secret-2024"

# ── CORS 配置 ──────────────────────────────────────────────────
CORS(
    app,
    origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
)

# ── SocketIO 配置 ──────────────────────────────────────────────
socketio = SocketIO(
    app,
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
    async_mode="threading",   # 使用线程模式，兼容同步 LLM 调用
    logger=False,
    engineio_logger=False,
)


def create_app(orchestrator, grid_space):
    """
    注册路由和事件处理器
    在 main.py 中调用
    """
    from server.api import register_api_routes
    from server.events import register_socket_events

    register_api_routes(app, orchestrator, grid_space)
    register_socket_events(socketio, orchestrator, grid_space)

    logger.info("Web 服务配置完成")
    return app, socketio


def run_server(orchestrator, grid_space):
    """
    启动 Web 服务器
    在 main.py 中调用
    """
    create_app(orchestrator, grid_space)

    logger.info("=" * 50)
    logger.info(f"Web 服务器启动")
    logger.info(f"地址: http://localhost:{WEB_PORT}")
    logger.info(f"API:  http://localhost:{WEB_PORT}/api/status")
    logger.info("=" * 50)

    socketio.run(
        app,
        host=WEB_HOST,
        port=WEB_PORT,
        debug=True,
        use_reloader=False,
    )
