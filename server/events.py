"""
WebSocket 事件处理
负责实时双向通信：
- 接收前端用户指令
- 推送 Agent 认知循环事件
- 推送状态更新
"""
import logging
import threading
from flask_socketio import emit

logger = logging.getLogger(__name__)


def register_socket_events(socketio, orchestrator, grid_space):
    """注册所有 WebSocket 事件处理器"""

    # ── 连接管理 ──────────────────────────────────────────────
    @socketio.on("connect")
    def on_connect():
        """客户端连接时发送初始状态"""
        logger.info("客户端已连接")
        emit("connected", {
            "message": "已连接到 UAV Agent 服务器",
            "agent_state": orchestrator.get_state(),
            "grid": grid_space.get_state_summary(),
            "obstacles": [
                list(o) for o in grid_space.get_obstacles_list()
            ],
        })

    @socketio.on("disconnect")
    def on_disconnect():
        """客户端断开连接"""
        logger.info("客户端已断开连接")

    # ── 用户指令 ──────────────────────────────────────────────
    @socketio.on("user_message")
    def on_user_message(data):
        """
        接收用户飞行指令
        在后台线程中运行 Agent，避免阻塞 WebSocket
        """
        user_input = data.get("message", "").strip()
        if not user_input:
            emit("error", {"message": "指令不能为空"})
            return

        logger.info(f"收到用户指令: {user_input}")

        # 立即确认收到消息
        emit("message_received", {
            "message": user_input,
            "status": "processing",
        })

        # 在后台线程中运行 Agent
        def run_agent():
            try:
                # ── 设置事件回调 ──────────────────────────────
                # Agent 通过此回调将事件推送到前端
                def event_callback(event_name: str, event_data: dict):
                    socketio.emit(event_name, event_data)

                orchestrator.emit = event_callback

                # ── 执行任务 ──────────────────────────────────
                result = orchestrator.run(user_input)

                # ── 推送最终结果 ───────────────────────────────
                socketio.emit("task_result", {
                    "result": result,
                    "agent_state": orchestrator.get_state(),
                    "grid_state": grid_space.get_state_summary(),
                    "obstacles": [
                        list(o) for o in grid_space.get_obstacles_list()
                    ],
                })

                logger.info(f"任务完成: {result.get('status')}")

            except Exception as e:
                logger.exception("Agent 执行错误")
                socketio.emit("agent_error", {
                    "error": str(e),
                    "type": type(e).__name__,
                })

        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()

    # ── 障碍物管理 ────────────────────────────────────────────
    @socketio.on("add_obstacles")
    def on_add_obstacles(data):
        """通过 WebSocket 添加障碍物"""
        try:
            obstacles = data.get("obstacles", [])
            count = grid_space.add_obstacles_batch(
                [tuple(int(c) for c in o) for o in obstacles]
            )

            result = {
                "success": True,
                "added": count,
                "total": grid_space.get_obstacle_count(),
                "obstacles": [
                    list(o) for o in grid_space.get_obstacles_list()
                ],
                "message": f"已添加 {count} 个障碍物",
            }

            emit("obstacles_updated", result)

            # 广播栅格更新
            socketio.emit("grid_update", {
                "grid": grid_space.get_state_summary(),
                "obstacles": [
                    list(o) for o in grid_space.get_obstacles_list()
                ],
            })

        except Exception as e:
            logger.exception("添加障碍物失败")
            emit("error", {"message": str(e)})

    @socketio.on("clear_obstacles")
    def on_clear_obstacles():
        """通过 WebSocket 清除所有障碍物"""
        grid_space.clear_obstacles()
        emit("obstacles_updated", {
            "success": True,
            "total": 0,
            "obstacles": [],
            "message": "已清除所有障碍物",
        })
        socketio.emit("grid_update", {
            "grid": grid_space.get_state_summary(),
            "obstacles": [],
        })
        logger.info("清除所有障碍物")

    # ── 状态同步 ──────────────────────────────────────────────
    @socketio.on("request_state")
    def on_request_state():
        """前端请求当前完整状态"""
        emit("agent_state_update", {
            "agent": orchestrator.get_state(),
            "grid": grid_space.get_state_summary(),
            "obstacles": [
                list(o) for o in grid_space.get_obstacles_list()
            ],
        })

    @socketio.on("reset_position")
    def on_reset_position(data=None):
        """重置无人机位置"""
        from config.settings import INITIAL_POSITION
        grid_space.set_position(*INITIAL_POSITION)
        emit("position_reset", {
            "position": list(INITIAL_POSITION),
            "message": f"位置已重置为 {INITIAL_POSITION}",
        })
        logger.info(f"位置重置: {INITIAL_POSITION}")

    # ── 心跳检测 ──────────────────────────────────────────────
    @socketio.on("ping")
    def on_ping():
        """心跳检测"""
        emit("pong", {"status": "ok"})

    logger.info("WebSocket 事件注册完成")
