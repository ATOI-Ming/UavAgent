import logging
from typing import Dict, Optional, List, Tuple

logger = logging.getLogger(__name__)


class SafetyGuard:
    """
    安全守卫
    职责：对工具执行结果进行确定性碰撞检测
    
    工作原理：
    1. 只对路径相关工具进行检测
    2. 优先从工具返回结果中获取安全状态
    3. 如果工具没有返回安全信息，主动检测路径
    """

    # 需要进行安全检查的工具集合
    PATH_TOOLS = {
        "plan_flight",
        "ai_replan_with_obstacles",
        "parse_command",
    }

    def __init__(self, grid_space):
        self.grid = grid_space

    def check(self, tool_name: str, tool_result: Dict) -> Dict:
        """
        对工具执行结果进行安全检查
        
        参数:
            tool_name: 工具名称
            tool_result: 工具执行结果（来自 ToolRegistry.execute_flight_tool）
        
        返回:
            {
                "safe": bool,                    # 是否安全
                "needs_reflect": bool,           # 是否需要进入反思
                "collision_point": [x,y,z] or None,
                "nearby_obstacles": [[x,y,z],...],
                "tool_name": str,
                "skipped": bool,                 # 是否跳过检查
            }
        """
        # 非路径工具，跳过检查
        if tool_name not in self.PATH_TOOLS:
            return {
                "safe": True,
                "needs_reflect": False,
                "collision_point": None,
                "nearby_obstacles": [],
                "tool_name": tool_name,
                "skipped": True,
            }

        # 从工具结果中提取数据
        data = tool_result.get("data") or {}

        # ── 方式1：从工具结果直接获取安全状态 ──────────────────
        if "safe" in data:
            is_safe = data["safe"]
            collision_point = data.get("collision_point")
            logger.info(f"安全检查({tool_name}): 从工具结果获取 safe={is_safe}")

        # ── 方式2：主动检测路径 ───────────────────────────────
        else:
            path = data.get("path", [])
            if path:
                is_safe, collision_point = self._check_path(path)
                logger.info(f"安全检查({tool_name}): 主动检测路径 safe={is_safe}")
            else:
                # 检查航点
                waypoints = data.get("waypoints", [])
                if waypoints:
                    is_safe, collision_point = self._check_path(waypoints)
                    logger.info(f"安全检查({tool_name}): 检测航点 safe={is_safe}")
                else:
                    # 无路径数据，默认安全
                    is_safe = True
                    collision_point = None
                    logger.warning(f"安全检查({tool_name}): 无路径数据，默认安全")

        # ── 获取附近障碍物信息（供反思使用）──────────────────────
        nearby = []
        if not is_safe and collision_point:
            nearby = self.grid.get_nearby_obstacles(
                int(collision_point[0]),
                int(collision_point[1]),
                int(collision_point[2]),
                radius=5,
            )
            logger.warning(
                f"检测到碰撞: {collision_point}, "
                f"附近障碍物: {len(nearby)}个"
            )

        return {
            "safe": is_safe,
            "needs_reflect": not is_safe,
            "collision_point": list(collision_point) if collision_point else None,
            "nearby_obstacles": [list(o) for o in nearby[:10]],
            "tool_name": tool_name,
            "skipped": False,
        }

    # ── 内部方法 ──────────────────────────────────────────────
    def _check_path(
        self, path: List
    ) -> Tuple[bool, Optional[Tuple]]:
        """
        检查路径是否碰撞
        返回: (is_safe, collision_point)
        """
        path_tuples = [
            (int(p[0]), int(p[1]), int(p[2]))
            for p in path
        ]
        return self.grid.check_path_collision(path_tuples)
