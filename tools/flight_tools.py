"""
飞行工具实现
13 个飞行工具 + task_complete 虚拟工具
这些工具通过 OpenAI Function Calling 由 LLM 选择调用
"""
import json
import logging
from typing import List, Dict, Any
from config.settings import (
    GRID_SIZE,
    INITIAL_POSITION,
    ACTIONS,
    ACTION_ALIASES,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
)

logger = logging.getLogger(__name__)


def register_flight_tools(
    registry,
    grid_space,
    flight_planner,
    command_parser,
    visualizer,
    code_generator,
):
    """
    注册所有飞行工具到 ToolRegistry
    
    参数:
        registry: ToolRegistry 实例
        grid_space: GridSpace 实例
        flight_planner: FlightPlanner 实例
        command_parser: CommandParser 实例
        visualizer: Visualizer 实例
        code_generator: CodeGenerator 实例
    """

    # ══════════════════════════════════════════════════════════
    # 1. ai_translate_flight — 自然语言翻译
    # ══════════════════════════════════════════════════════════
    def ai_translate_flight(instruction: str) -> Dict:
        """
        将自然语言飞行指令翻译为标准动作序列
        调用 LLM 进行翻译
        
        示例:
            输入: "飞一个边长3米的正方形"
            输出: "上升3米,右移3米,前进3米,左移3米,后退3米,下降3米"
        """
        from openai import OpenAI

        try:
            client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

            # 构建提示词
            actions_desc = "\n".join(
                f"  - {k}: 方向向量{v}" for k, v in ACTIONS.items()
            )
            aliases_desc = "\n".join(
                f"  - '{k}' = {v}" for k, v in ACTION_ALIASES.items()
            )

            prompt = f"""你是无人机飞行指令翻译器。

【任务】
将用户的自然语言飞行指令转换为标准动作序列字符串。

【可用动作】
{actions_desc}

【中文别名】
{aliases_desc}

【环境信息】
- 栅格空间: {GRID_SIZE[0]}x{GRID_SIZE[1]}x{GRID_SIZE[2]} 米
- 起始位置: {INITIAL_POSITION}

【输出格式】
- 格式: "动作名+距离，动作名+距离，..."
- 示例: "上升3米,前进5米,右移3米"
- 要求: 只输出动作序列字符串，不要任何解释

【用户指令】
{instruction}

【输出】
"""

            logger.info(f"调用 LLM 翻译指令: {instruction}")
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )

            action_sequence = response.choices[0].message.content.strip()
            logger.info(f"翻译结果: {action_sequence}")

            return {
                "success": True,
                "action_sequence": action_sequence,
                "message": f"翻译成功: {action_sequence}",
                "original_instruction": instruction,
            }

        except Exception as e:
            logger.exception("LLM 翻译失败")
            return {
                "success": False,
                "action_sequence": "",
                "message": f"翻译失败: {str(e)}",
                "original_instruction": instruction,
            }

    registry.register_flight_tool(
        name="ai_translate_flight",
        func=ai_translate_flight,
        description="⭐ 将自然语言飞行指令翻译为标准动作序列字符串。例如：'飞一个边长3米的正方形' → '上升3米,右移3米,前进3米,左移3米,后退3米,下降3米'",
        parameters={
            "type": "object",
            "properties": {
                "instruction": {
                    "type": "string",
                    "description": "自然语言飞行指令，如'飞一个边长3米的正方形'",
                }
            },
            "required": ["instruction"],
        },
        category="input",
    )

    # ══════════════════════════════════════════════════════════
    # 2. parse_command — 动作序列解析
    # ══════════════════════════════════════════════════════════
    def parse_command(command: str) -> Dict:
        """
        将动作序列字符串解析为三维坐标航点列表
        
        示例:
            输入: "上升3米,右移3米,前进3米"
            输出: [[50,50,3], [53,50,3], [53,53,3]]
        """
        logger.info(f"解析动作序列: {command}")
        result = command_parser.parse(command)
        logger.info(
            f"解析完成: {len(result.get('waypoints', []))}个航点"
        )
        return result

    registry.register_flight_tool(
        name="parse_command",
        func=parse_command,
        description="⭐ 将动作序列字符串解析为三维坐标航点列表。输入格式：'上升3米,右移3米,前进3米'",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "动作序列字符串，如'上升3米,前进5米,右移3米'",
                }
            },
            "required": ["command"],
        },
        category="parsing",
    )

    # ══════════════════════════════════════════════════════════
    # 3. plan_flight — 路径规划
    # ══════════════════════════════════════════════════════════
    def plan_flight(waypoints: List, algorithm: str = "astar") -> Dict:
        """
        对航点列表进行路径规划，生成安全飞行路径
        
        参数:
            waypoints: 航点列表 [[x,y,z], ...]
            algorithm: 规划算法 "astar" | "bfs" | "direct"
        """
        logger.info(
            f"路径规划: {len(waypoints)}个航点, 算法={algorithm}"
        )
        wp_tuples = [tuple(int(c) for c in w) for w in waypoints]
        result = flight_planner.plan(wp_tuples, algorithm)
        logger.info(
            f"规划完成: 路径点={len(result.get('path', []))}, "
            f"安全={result.get('safe')}"
        )
        return result

    registry.register_flight_tool(
        name="plan_flight",
        func=plan_flight,
        description="⭐ 对航点列表进行路径规划，生成安全飞行路径。支持A*、BFS、直线三种算法，自动进行碰撞检测",
        parameters={
            "type": "object",
            "properties": {
                "waypoints": {
                    "type": "array",
                    "items": {"type": "array"},
                    "description": "航点列表，每个航点为[x,y,z]坐标",
                },
                "algorithm": {
                    "type": "string",
                    "enum": ["astar", "bfs", "direct"],
                    "description": "路径规划算法：astar=A*算法(推荐), bfs=广度优先, direct=直线",
                    "default": "astar",
                },
            },
            "required": ["waypoints"],
        },
        category="planning",
    )

    # ══════════════════════════════════════════════════════════
    # 4. ai_replan_with_obstacles — 避障重规划
    # ══════════════════════════════════════════════════════════
    def ai_replan_with_obstacles(
        start: List,
        goal: List,
        strategy: str = "climb_over",
        obstacle_info: Dict = None,
    ) -> Dict:
        """
        碰撞后使用指定策略重新规划路径
        
        参数:
            start: 起始位置 [x,y,z]
            goal: 目标位置 [x,y,z]
            strategy: 避障策略
        """
        logger.info(f"避障重规划: {start} → {goal}, 策略={strategy}")

        start_t = tuple(int(c) for c in start)
        goal_t = tuple(int(c) for c in goal)
        sx, sy, sz = start_t
        gx, gy, gz = goal_t

        # 根据策略生成新航点
        if strategy == "climb_over":
            # 上升绕过
            max_z = grid_space.size_z - 1
            climb_height = min(sz + 5, max_z)
            new_waypoints = [
                (sx, sy, climb_height),
                (gx, gy, climb_height),
                goal_t,
            ]
            logger.info(f"策略: 上升到高度 {climb_height}")

        elif strategy == "descend_under":
            # 下降绕过
            descend_z = max(sz - 3, 0)
            new_waypoints = [
                (sx, sy, descend_z),
                (gx, gy, descend_z),
                goal_t,
            ]
            logger.info(f"策略: 下降到高度 {descend_z}")

        elif strategy == "planar_detour":
            # 水平绕行
            mid_x = (sx + gx) // 2
            mid_y = (sy + gy) // 2
            offset = 10
            detour = (mid_x + offset, mid_y + offset, sz)
            new_waypoints = [detour, goal_t]
            logger.info(f"策略: 水平绕行经过 {detour}")

        elif strategy == "ai_replan":
            # 使用 A* 重新规划
            logger.info("策略: A* 智能重规划")
            result = flight_planner.plan([goal_t], "astar")
            result["strategy_used"] = strategy
            return result

        else:  # combined
            # 组合策略：上升 + 水平偏移
            climb_height = min(sz + 5, grid_space.size_z - 1)
            mid_x = (sx + gx) // 2
            new_waypoints = [
                (mid_x, sy, climb_height),
                goal_t,
            ]
            logger.info(f"策略: 组合（上升+偏移）")

        # 执行规划
        result = flight_planner.plan(new_waypoints, "astar")
        result["strategy_used"] = strategy
        logger.info(f"重规划完成: 安全={result.get('safe')}")
        return result

    registry.register_flight_tool(
        name="ai_replan_with_obstacles",
        func=ai_replan_with_obstacles,
        description="⭐ 碰撞检测失败后，使用指定策略重新规划绕过障碍物的路径。支持5种策略：上升绕过、下降绕过、水平绕行、AI智能规划、组合策略",
        parameters={
            "type": "object",
            "properties": {
                "start": {
                    "type": "array",
                    "description": "起始位置 [x,y,z]",
                },
                "goal": {
                    "type": "array",
                    "description": "目标位置 [x,y,z]",
                },
                "strategy": {
                    "type": "string",
                    "enum": [
                        "climb_over",
                        "descend_under",
                        "planar_detour",
                        "ai_replan",
                        "combined",
                    ],
                    "description": "避障策略：climb_over=上升绕过, descend_under=下降绕过, planar_detour=水平绕行, ai_replan=AI智能规划, combined=组合策略",
                    "default": "climb_over",
                },
                "obstacle_info": {
                    "type": "object",
                    "description": "障碍物信息（可选）",
                },
            },
            "required": ["start", "goal"],
        },
        category="replanning",
    )

    # ══════════════════════════════════════════════════════════
    # 5. add_obstacles — 添加障碍物
    # ══════════════════════════════════════════════════════════
    def add_obstacles(obstacles: List) -> Dict:
        """添加障碍物到栅格空间"""
        logger.info(f"添加障碍物: {len(obstacles)}个")
        count = grid_space.add_obstacles_batch(
            [tuple(int(c) for c in o) for o in obstacles]
        )
        return {
            "success": True,
            "added_count": count,
            "total_obstacles": grid_space.get_obstacle_count(),
            "message": f"成功添加 {count} 个障碍物，总计 {grid_space.get_obstacle_count()} 个",
        }

    registry.register_flight_tool(
        name="add_obstacles",
        func=add_obstacles,
        description="向栅格空间添加障碍物",
        parameters={
            "type": "object",
            "properties": {
                "obstacles": {
                    "type": "array",
                    "items": {"type": "array"},
                    "description": "障碍物坐标列表，每个为[x,y,z]",
                }
            },
            "required": ["obstacles"],
        },
        category="space",
    )

    # ══════════════════════════════════════════════════════════
    # 6. clear_obstacles — 清除障碍物
    # ══════════════════════════════════════════════════════════
    def clear_obstacles() -> Dict:
        """清除所有障碍物"""
        logger.info("清除所有障碍物")
        grid_space.clear_obstacles()
        return {
            "success": True,
            "message": "已清除所有障碍物",
        }

    registry.register_flight_tool(
        name="clear_obstacles",
        func=clear_obstacles,
        description="清除栅格空间中的所有障碍物",
        parameters={"type": "object", "properties": {}},
        category="space",
    )

    # ══════════════════════════════════════════════════════════
    # 7. get_obstacles — 获取障碍物
    # ══════════════════════════════════════════════════════════
    def get_obstacles() -> Dict:
        """获取当前所有障碍物"""
        obstacles = grid_space.get_obstacles_list()
        logger.info(f"查询障碍物: {len(obstacles)}个")
        return {
            "success": True,
            "obstacles": [list(o) for o in obstacles],
            "count": len(obstacles),
            "message": f"当前共有 {len(obstacles)} 个障碍物",
        }

    registry.register_flight_tool(
        name="get_obstacles",
        func=get_obstacles,
        description="获取当前栅格空间中所有障碍物的坐标列表",
        parameters={"type": "object", "properties": {}},
        category="space",
    )

    # ══════════════════════════════════════════════════════════
    # 8. visualize_flight — 3D可视化
    # ══════════════════════════════════════════════════════════
    def visualize_flight(path: List = None, waypoints: List = None) -> Dict:
        """生成3D飞行路径可视化图片"""
        logger.info("生成3D可视化")
        result = visualizer.visualize_flight(path or [], waypoints)
        logger.info(f"可视化完成: {result.get('filename')}")
        return result

    registry.register_flight_tool(
        name="visualize_flight",
        func=visualize_flight,
        description="⭐ 生成3D飞行路径可视化图片（PNG格式），包含航点、路径、障碍物",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "array",
                    "description": "飞行路径点列表（可选）",
                },
                "waypoints": {
                    "type": "array",
                    "description": "关键航点列表（可选）",
                },
            },
        },
        category="visualization",
    )

    # ══════════════════════════════════════════════════════════
    # 9. generate_layer_maps — 2D切片图
    # ══════════════════════════════════════════════════════════
    def generate_layer_maps() -> Dict:
        """生成栅格空间的2D分层切片图"""
        logger.info("生成2D分层切片图")
        result = visualizer.generate_layer_maps()
        logger.info(f"切片图生成完成: {result.get('count')}张")
        return result

    registry.register_flight_tool(
        name="generate_layer_maps",
        func=generate_layer_maps,
        description="生成栅格空间的2D分层俯视切片图，按高度层分别展示障碍物分布",
        parameters={"type": "object", "properties": {}},
        category="visualization",
    )

    # ══════════════════════════════════════════════════════════
    # 10. get_flight_info — 获取飞行信息
    # ══════════════════════════════════════════════════════════
    def get_flight_info() -> Dict:
        """获取当前飞行状态和环境信息"""
        state = grid_space.get_state_summary()
        return {
            "success": True,
            "current_position": list(grid_space.current_position),
            "grid_size": list(state["size"]),
            "obstacle_count": state["obstacle_count"],
            "free_ratio": state["free_ratio"],
            "obstacles_by_layer": state["obstacles_by_layer"],
            "message": "飞行信息获取成功",
        }

    registry.register_flight_tool(
        name="get_flight_info",
        func=get_flight_info,
        description="获取当前无人机飞行状态和环境信息",
        parameters={"type": "object", "properties": {}},
        category="status",
    )

    # ══════════════════════════════════════════════════════════
    # 11. reset_position — 重置位置
    # ══════════════════════════════════════════════════════════
    def reset_position(position: List = None) -> Dict:
        """重置无人机当前位置"""
        pos = (
            tuple(int(c) for c in position)
            if position
            else INITIAL_POSITION
        )
        logger.info(f"重置位置: {pos}")
        grid_space.set_position(*pos)
        command_parser.set_start_position(pos)
        return {
            "success": True,
            "position": list(pos),
            "message": f"位置已重置为 {pos}",
        }

    registry.register_flight_tool(
        name="reset_position",
        func=reset_position,
        description="重置无人机当前位置到指定坐标或初始位置",
        parameters={
            "type": "object",
            "properties": {
                "position": {
                    "type": "array",
                    "description": "新位置 [x,y,z]，不填则重置到初始位置",
                }
            },
        },
        category="status",
    )

    # ══════════════════════════════════════════════════════════
    # 12. generate_uav_code — 生成飞行代码
    # ══════════════════════════════════════════════════════════
    def generate_uav_code(
        path: List = None,
        waypoints: List = None,
        task_description: str = "",
    ) -> Dict:
        """生成DroneKit和仿真版本的飞行代码"""
        logger.info("生成飞行代码")
        result = code_generator.generate(path or [], waypoints, task_description)
        logger.info(f"代码生成完成: {len(result.get('files', []))}个文件")
        return result

    registry.register_flight_tool(
        name="generate_uav_code",
        func=generate_uav_code,
        description="⭐ 根据飞行路径生成DroneKit和仿真版本的可执行飞行代码（Python）",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "array",
                    "description": "飞行路径点（可选）",
                },
                "waypoints": {
                    "type": "array",
                    "description": "关键航点（可选）",
                },
                "task_description": {
                    "type": "string",
                    "description": "任务描述（可选）",
                },
            },
        },
        category="output",
    )

    # ══════════════════════════════════════════════════════════
    # 13. task_complete — 任务完成标记（虚拟工具）
    # ══════════════════════════════════════════════════════════
    registry.register_flight_tool(
        name="task_complete",
        func=None,  # 虚拟工具，无实际函数
        description="⭐⭐⭐ 标记当前任务已完成。当所有飞行任务步骤都已执行完毕时，必须调用此工具结束任务",
        parameters={
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "任务完成摘要，简述已完成的工作",
                }
            },
            "required": ["summary"],
        },
        category="control",
    )

    logger.info(
        f"飞行工具注册完成: {len(registry.get_flight_tool_names())}个"
    )
