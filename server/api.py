"""
REST API 路由
提供前端查询静态数据的接口
"""
import logging
from pathlib import Path
from flask import jsonify, request, send_from_directory

from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)


def register_api_routes(app, orchestrator, grid_space):
    """注册所有 REST API 路由"""

    # ── 前端静态文件 ──────────────────────────────────────────
    @app.route("/")
    def index():
        """服务 React 前端构建产物"""
        build_dir = (
            Path(__file__).parent.parent / "frontend" / "web" / "build"
        )
        if (build_dir / "index.html").exists():
            return send_from_directory(str(build_dir), "index.html")
        # 前端未构建时返回 API 信息
        return jsonify({
            "message": "UAV Agent API 服务运行中",
            "status": "ok",
            "hint": "请先构建前端: cd frontend/web && npm run build",
            "api_docs": {
                "status": "/api/status",
                "grid":   "/api/grid-state",
                "agent":  "/api/agent/state",
            },
        })

    # ── 系统状态 ──────────────────────────────────────────────
    @app.route("/api/status")
    def get_status():
        """获取系统整体状态"""
        return jsonify({
            "status": "ok",
            "service": "uav-agent",
            "agent_state": orchestrator.get_state(),
            "grid": grid_space.get_state_summary(),
        })

    @app.route("/api/health")
    def health_check():
        """健康检查接口"""
        return jsonify({"status": "ok"})

    # ── Agent 状态 ────────────────────────────────────────────
    @app.route("/api/agent/state")
    def get_agent_state():
        """获取 Agent 当前运行状态"""
        return jsonify(orchestrator.get_state())

    # ── 栅格空间状态 ──────────────────────────────────────────
    @app.route("/api/grid-state")
    def get_grid_state():
        """获取栅格空间完整状态"""
        state = grid_space.get_state_summary()
        return jsonify({
            "success": True,
            "grid_size": list(state["size"]),
            "current_position": list(state["current_position"]),
            "obstacle_count": state["obstacle_count"],
            "free_ratio": state["free_ratio"],
            "obstacles": [
                list(o) for o in grid_space.get_obstacles_list()
            ],
            "obstacles_by_layer": state["obstacles_by_layer"],
        })

    # ── 障碍物管理 ────────────────────────────────────────────
    @app.route("/api/obstacles", methods=["GET"])
    def get_obstacles():
        """获取所有障碍物"""
        return jsonify({
            "success": True,
            "obstacles": [
                list(o) for o in grid_space.get_obstacles_list()
            ],
            "count": grid_space.get_obstacle_count(),
        })

    @app.route("/api/obstacles", methods=["POST"])
    def add_obstacles():
        """批量添加障碍物"""
        try:
            data = request.get_json()
            if not data or "obstacles" not in data:
                return jsonify({
                    "success": False,
                    "message": "请求体需要包含 obstacles 字段",
                }), 400

            obstacles = data["obstacles"]
            count = grid_space.add_obstacles_batch(
                [tuple(int(c) for c in o) for o in obstacles]
            )

            return jsonify({
                "success": True,
                "added": count,
                "total": grid_space.get_obstacle_count(),
                "message": f"成功添加 {count} 个障碍物",
            })

        except Exception as e:
            logger.exception("添加障碍物失败")
            return jsonify({
                "success": False,
                "message": str(e),
            }), 500

    @app.route("/api/obstacles", methods=["DELETE"])
    def clear_obstacles():
        """清除所有障碍物"""
        grid_space.clear_obstacles()
        return jsonify({
            "success": True,
            "message": "已清除所有障碍物",
        })

    # ── 文件资源 ──────────────────────────────────────────────
    @app.route("/api/layer-maps")
    def get_layer_maps():
        """获取分层切片图文件列表"""
        layer_dir = OUTPUT_DIR / "layer_maps"
        files = []
        if layer_dir.exists():
            for f in sorted(layer_dir.glob("*.png")):
                files.append({
                    "filename": f.name,
                    "url": f"/api/files/layer_maps/{f.name}",
                    "size": f.stat().st_size,
                })
        return jsonify({
            "success": True,
            "files": files,
            "count": len(files),
        })

    @app.route("/api/code-files")
    def get_code_files():
        """获取生成的飞行代码文件列表"""
        mission_dir = OUTPUT_DIR / "missions"
        files = []
        if mission_dir.exists():
            for f in sorted(
                mission_dir.glob("*.py"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,  # 最新的在前
            ):
                try:
                    content = f.read_text(encoding="utf-8")
                except Exception:
                    content = ""
                files.append({
                    "filename": f.name,
                    "url": f"/api/files/missions/{f.name}",
                    "content": content,
                    "size": f.stat().st_size,
                })
        return jsonify({
            "success": True,
            "files": files,
            "count": len(files),
        })

    @app.route("/api/visualizations")
    def get_visualizations():
        """获取可视化图片文件列表"""
        viz_dir = OUTPUT_DIR / "visualizations"
        files = []
        if viz_dir.exists():
            for f in sorted(
                viz_dir.glob("*.png"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            ):
                files.append({
                    "filename": f.name,
                    "url": f"/api/files/visualizations/{f.name}",
                    "size": f.stat().st_size,
                })
        return jsonify({
            "success": True,
            "files": files,
            "count": len(files),
        })

    @app.route("/api/files/<path:subpath>")
    def serve_output_file(subpath):
        """
        提供 data/output/ 目录下的文件
        例如: /api/files/layer_maps/layer_z00_xxx.png
        """
        return send_from_directory(str(OUTPUT_DIR), subpath)

    # ── 任务历史 ──────────────────────────────────────────────
    @app.route("/api/history")
    def get_history():
        """获取任务历史（如果记忆系统可用）"""
        try:
            if orchestrator.memory:
                history = orchestrator.memory.get_history()
                return jsonify({
                    "success": True,
                    "history": history,
                    "count": len(history),
                })
            return jsonify({
                "success": True,
                "history": [],
                "count": 0,
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": str(e),
            }), 500

    logger.info("REST API 路由注册完成")
