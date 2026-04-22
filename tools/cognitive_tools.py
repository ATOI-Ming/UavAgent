"""
认知工具实现
5 个认知工具：agent_observe, agent_think, agent_act, agent_safety_check, agent_reflect
由 Orchestrator 在认知循环的各阶段自动调用
返回结构化"决策指南"，不直接做决策
"""
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def register_cognitive_tools(registry, grid_space, memory):
    """
    注册所有认知工具到 ToolRegistry
    
    参数:
        registry: ToolRegistry 实例
        grid_space: GridSpace 实例
        memory: Memory 实例（可选）
    """

    # ── 1. OBSERVE ────────────────────────────────────────────
    def agent_observe(
        user_input: str,
        iteration: int,
        cycles_so_far: List[Dict],
    ) -> Dict:
        """
        OBSERVE 阶段认知工具
        收集环境观察信息，生成观察指南
        """
        state = grid_space.get_state_summary()
        cp = state["current_position"]

        # 提取上一轮的动作和结果
        last_action = None
        last_result = None
        if cycles_so_far:
            last = cycles_so_far[-1]
            last_action = last.get("action")
            last_result = last.get("action_result")

        observation = {
            "phase": "OBSERVE",
            "iteration": iteration,
            "user_input": user_input,
            "environment": {
                "grid_size": list(state["size"]),
                "current_position": list(cp),
                "obstacle_count": state["obstacle_count"],
                "free_ratio": state["free_ratio"],
                "obstacles_by_layer": state["obstacles_by_layer"],
            },
            "last_action": last_action,
            "last_result": last_result,
            "cycles_completed": len(cycles_so_far),
            "actions_taken": [
                c.get("action", {}).get("tool_name")
                for c in cycles_so_far
                if c.get("action")
            ],
        }

        # 注入记忆提示
        if memory:
            observation["memory_hints"] = memory.get_hints()

        logger.debug(f"OBSERVE: 迭代{iteration}, 已完成{len(cycles_so_far)}轮")
        return observation

    registry.register_cognitive_tool("agent_observe", agent_observe)

    # ── 2. THINK ──────────────────────────────────────────────
    def agent_think(
        observation: Dict,
        user_input: str,
        cycles_so_far: List[Dict],
    ) -> Dict:
        """
        THINK 阶段认知工具
        分析用户意图，推荐下一步工具，生成决策指南
        """
        actions_taken = observation.get("actions_taken", [])

        # ── 1. 分析用户意图 ───────────────────────────────────
        intent = _analyze_intent(user_input, actions_taken)

        # ── 2. 推荐下一步工具 ─────────────────────────────────
        recommended = _recommend_next_tool(intent, actions_taken)

        # ── 3. 获取标准工作流 ─────────────────────────────────
        workflow = _get_workflow(intent)

        guide = {
            "phase": "THINK",
            "user_intent": intent,
            "actions_taken_so_far": actions_taken,
            "recommended_next_tool": recommended,
            "standard_workflow": workflow,
            "decision_guidelines": {
                "rule1": "每次只选择一个工具",
                "rule2": "按照工作流顺序执行",
                "rule3": "所有步骤完成后必须调用 task_complete",
                "rule4": "如果路径规划失败，使用 ai_replan_with_obstacles",
            },
            "available_tools": registry.get_flight_tool_names(),
            "output_format": {
                "description": "通过 function calling 选择工具",
                "required_fields": ["tool_name", "arguments"],
            },
        }

        logger.debug(f"THINK: 意图={intent}, 推荐={recommended}")
        return guide

    registry.register_cognitive_tool("agent_think", agent_think)

    # ── 3. SAFETY_CHECK ───────────────────────────────────────
    def agent_safety_check(
        tool_name: str,
        tool_result: Dict,
        path: List = None,
    ) -> Dict:
        """
        SAFETY_CHECK 阶段认知工具
        生成安全检查指南
        
        注意：实际碰撞检测由 SafetyGuard 完成，此工具仅用于记录
        """
        path_tools = {"plan_flight", "ai_replan_with_obstacles", "parse_command"}

        if tool_name not in path_tools:
            return {
                "phase": "SAFETY_CHECK",
                "tool_checked": tool_name,
                "check_required": False,
                "safe": True,
                "message": "此工具无需安全检查",
            }

        # 从工具结果提取安全信息
        data = tool_result.get("data") or {}
        is_safe = data.get("safe", True)
        collision_point = data.get("collision_point")

        # 如果工具没有返回安全信息，主动检查
        if not is_safe and collision_point is None and path:
            is_safe, collision_point = grid_space.check_path_collision(
                [tuple(p) for p in path]
            )

        result = {
            "phase": "SAFETY_CHECK",
            "tool_checked": tool_name,
            "check_required": True,
            "safe": is_safe,
            "collision_point": collision_point,
            "message": "路径安全" if is_safe else f"路径碰撞于 {collision_point}",
        }

        if not is_safe and collision_point:
            nearby = grid_space.get_nearby_obstacles(
                *[int(c) for c in collision_point[:3]], radius=5
            )
            result["nearby_obstacles"] = [list(o) for o in nearby[:10]]

        return result

    registry.register_cognitive_tool("agent_safety_check", agent_safety_check)

    # ── 4. REFLECT ────────────────────────────────────────────
    def agent_reflect(
        safety_result: Dict,
        cycles_so_far: List[Dict],
        retry_count: int,
    ) -> Dict:
        """
        REFLECT 阶段认知工具
        生成反思指南，引导 LLM 选择避障策略
        
        注意：实际策略分析由 Reflector 完成，此工具仅用于记录
        """
        collision_point = safety_result.get("collision_point")
        nearby_obstacles = safety_result.get("nearby_obstacles", [])
        obstacle_count = len(nearby_obstacles)

        # 分析障碍物密度
        if obstacle_count < 3:
            density = "low"
            recommended = "climb_over"
        elif obstacle_count < 8:
            density = "medium"
            recommended = "planar_detour"
        else:
            density = "high"
            recommended = "ai_replan"

        # 根据重试次数调整策略
        strategies_by_retry = {
            0: "climb_over",
            1: "planar_detour",
            2: "ai_replan",
        }
        if retry_count in strategies_by_retry:
            recommended = strategies_by_retry[retry_count]

        # 提取当前路径的起点和终点
        start_pos = list(grid_space.current_position)
        goal_pos = None
        for cycle in reversed(cycles_so_far):
            data = (cycle.get("action_result") or {}).get("data") or {}
            wp = data.get("waypoints")
            if wp and len(wp) > 0:
                goal_pos = wp[-1]
                break

        return {
            "phase": "REFLECT",
            "retry_count": retry_count,
            "failure_analysis": {
                "collision_point": collision_point,
                "obstacles_nearby": obstacle_count,
                "obstacle_density": density,
            },
            "available_strategies": [
                {
                    "name": "climb_over",
                    "description": "上升绕过障碍物",
                },
                {
                    "name": "descend_under",
                    "description": "下降绕过障碍物",
                },
                {
                    "name": "planar_detour",
                    "description": "水平方向绕行",
                },
                {
                    "name": "ai_replan",
                    "description": "使用A*算法智能重规划",
                },
                {
                    "name": "combined",
                    "description": "组合多种策略",
                },
            ],
            "recommended_strategy": recommended,
            "replan_parameters": {
                "start": start_pos,
                "goal": goal_pos,
                "tool": "ai_replan_with_obstacles",
            },
        }

    registry.register_cognitive_tool("agent_reflect", agent_reflect)

    logger.info(f"认知工具注册完成: {len(registry.list_cognitive_tools())}个")


# ── 辅助函数 ──────────────────────────────────────────────────
def _analyze_intent(user_input: str, actions_taken: List[str]) -> str:
    """
    分析用户意图
    返回: "flight_task" | "obstacle_handling" | "visualization" | "code_generation"
    """
    inp = user_input.lower()

    # 优先根据关键词判断
    if any(k in inp for k in ["飞", "移动", "上升", "前进", "路径", "square",
                               "circle", "正方形", "圆", "轨迹", "航点"]):
        return "flight_task"

    if any(k in inp for k in ["障碍", "obstacle", "绕过", "避开"]):
        return "obstacle_handling"

    if any(k in inp for k in ["显示", "可视化", "图", "visualize", "看"]):
        return "visualization"

    if any(k in inp for k in ["代码", "code", "生成", "generate"]):
        return "code_generation"

    # 默认为飞行任务
    return "flight_task"


def _recommend_next_tool(intent: str, actions_taken: List[str]) -> str:
    """
    根据意图和已执行动作推荐下一个工具
    """
    workflow_map = {
        "flight_task": [
            "ai_translate_flight",
            "parse_command",
            "plan_flight",
            "visualize_flight",
            "generate_uav_code",
            "task_complete",
        ],
        "obstacle_handling": [
            "add_obstacles",
            "ai_translate_flight",
            "parse_command",
            "plan_flight",
            "visualize_flight",
            "task_complete",
        ],
        "visualization": [
            "generate_layer_maps",
            "visualize_flight",
            "task_complete",
        ],
        "code_generation": [
            "generate_uav_code",
            "task_complete",
        ],
    }

    workflow = workflow_map.get(intent, workflow_map["flight_task"])

    # 找出第一个未执行的工具
    for tool in workflow:
        if tool not in actions_taken:
            return tool

    # 所有工具都执行过，推荐 task_complete
    return "task_complete"


def _get_workflow(intent: str) -> str:
    """
    获取推荐工作流描述
    """
    workflows = {
        "flight_task": (
            "ai_translate_flight → parse_command → plan_flight "
            "→ visualize_flight → generate_uav_code → task_complete"
        ),
        "obstacle_handling": (
            "add_obstacles → ai_translate_flight → parse_command "
            "→ plan_flight → visualize_flight → task_complete"
        ),
        "visualization": (
            "generate_layer_maps → visualize_flight → task_complete"
        ),
        "code_generation": (
            "generate_uav_code → task_complete"
        ),
    }
    return workflows.get(intent, workflows["flight_task"])
