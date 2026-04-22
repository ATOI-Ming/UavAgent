#!/usr/bin/env python3
"""
UavAgent 主入口
启动命令: python main.py
"""
import logging
import sys
from pathlib import Path

# ── 日志配置 ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("uav_agent.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查必要依赖"""
    missing = []
    required = [
        ("flask",         "Flask"),
        ("flask_socketio","Flask-SocketIO"),
        ("flask_cors",    "Flask-CORS"),
        ("openai",        "OpenAI"),
        ("dotenv",        "python-dotenv"),
    ]
    for module, name in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(name)

    if missing:
        logger.error(f"缺少依赖: {', '.join(missing)}")
        logger.error("请执行: pip install -r requirements.txt")
        sys.exit(1)

    try:
        import matplotlib
        logger.info("matplotlib 已安装，可视化功能可用")
    except ImportError:
        logger.warning("matplotlib 未安装，可视化功能不可用")


def check_config():
    """检查关键配置"""
    from config.settings import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL
    if not LLM_API_KEY:
        logger.error("LLM_API_KEY 未配置，请检查 .env 文件")
        sys.exit(1)
    logger.info(f"LLM 配置: {LLM_MODEL} @ {LLM_BASE_URL}")


def main():
    logger.info("=" * 60)
    logger.info("  UavAgent 启动中...")
    logger.info("=" * 60)

    # ── Step 1: 检查依赖和配置 ────────────────────────────────
    logger.info("[Step 1] 检查依赖和配置...")
    check_dependencies()
    check_config()

    # ── Step 2: 初始化核心组件 ────────────────────────────────
    logger.info("[Step 2] 初始化核心组件...")

    from config.settings import (
        GRID_SIZE,
        INITIAL_POSITION,
        OUTPUT_DIR,
        MISSION_DIR,
    )
    from core.grid_space import GridSpace
    from core.command_parser import CommandParser
    from core.flight_planner import FlightPlanner
    from core.visualizer import Visualizer
    from core.code_generator import CodeGenerator

    # 栅格空间
    grid_space = GridSpace(size=GRID_SIZE)
    grid_space.set_position(*INITIAL_POSITION)
    logger.info(f"栅格空间: {GRID_SIZE}, 起始位置: {INITIAL_POSITION}")

    # 核心功能组件
    command_parser = CommandParser()
    flight_planner = FlightPlanner(grid_space)

    visualizer     = Visualizer(grid_space, OUTPUT_DIR)
    code_generator = CodeGenerator(MISSION_DIR)

    logger.info("核心组件初始化完成")

    # ── Step 3: 初始化记忆系统 ────────────────────────────────
    logger.info("[Step 3] 初始化记忆系统...")

    from memory.memory import Memory
    memory = Memory()
    logger.info("记忆系统初始化完成")

    # ── Step 4: 初始化工具系统 ────────────────────────────────
    logger.info("[Step 4] 初始化工具系统...")

    from tools.registry import ToolRegistry
    from tools.flight_tools import register_flight_tools
    from tools.cognitive_tools import register_cognitive_tools

    tool_registry = ToolRegistry()

    register_flight_tools(
        registry=tool_registry,
        grid_space=grid_space,
        flight_planner=flight_planner,
        command_parser=command_parser,
        visualizer=visualizer,
        code_generator=code_generator,
    )

    register_cognitive_tools(
        registry=tool_registry,
        grid_space=grid_space,
        memory=memory,
    )

    stats = tool_registry.get_stats()
    logger.info(
        f"工具系统初始化完成: "
        f"飞行工具={stats['flight_tools_count']}个, "
        f"认知工具={stats['cognitive_tools_count']}个"
    )

    # ── Step 5: 初始化 Agent ──────────────────────────────────
    logger.info("[Step 5] 初始化 Agent...")

    from agent.safety_guard import SafetyGuard
    from agent.reflector import Reflector
    from agent.orchestrator import Orchestrator

    safety_guard = SafetyGuard(grid_space)
    reflector    = Reflector(grid_space)

    orchestrator = Orchestrator(
        grid_space=grid_space,
        tool_registry=tool_registry,
        safety_guard=safety_guard,
        reflector=reflector,
        memory=memory,
    )

    logger.info("Agent 初始化完成")

    # ── Step 6: 启动 Web 服务器 ───────────────────────────────
    logger.info("[Step 6] 启动 Web 服务器...")
    logger.info(f"访问地址: http://localhost:5000")

    from server.app import run_server
    run_server(orchestrator, grid_space)


if __name__ == "__main__":
    main()
