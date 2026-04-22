import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Reflector:
    """
    反思引擎
    职责：碰撞后生成重规划策略指南
    
    工作流：
    1. 分析碰撞信息（碰撞点、障碍物密度）
    2. 根据重试次数和密度推荐策略
    3. 生成反思指南供 LLM 选择
    """

    # 可用策略列表
    STRATEGIES = [
        "climb_over",      # 上升绕过
        "descend_under",   # 下降绕过
        "planar_detour",   # 水平绕行
        "ai_replan",       # AI智能重规划
        "combined",        # 组合策略
    ]

    def __init__(self, grid_space):
        self.grid = grid_space

    def build_reflect_guide(
        self,
        safety_result: Dict,
        cycles_so_far: List[Dict],
        retry_count: int,
    ) -> Dict:
        """
        构建反思指南
        
        参数:
            safety_result: 安全检查结果
            cycles_so_far: 已完成的循环历史
            retry_count: 当前重试次数
        
        返回:
            {
                "phase": "REFLECT",
                "retry_count": int,
                "collision_info": {...},
                "recommended_strategy": str,
                "available_strategies": [...],
                "replan_tool": "ai_replan_with_obstacles",
                "suggested_call": {...},
                "message": str,
            }
        """
        collision_point = safety_result.get("collision_point")
        nearby_obstacles = safety_result.get("nearby_obstacles", [])

        # ── 分析障碍物密度 ────────────────────────────────────
        obstacle_count = len(nearby_obstacles)
        density = self._analyze_density(obstacle_count)

        # ── 推荐策略 ──────────────────────────────────────────
        strategy = self._pick_strategy(retry_count, density)

        # ── 提取起点和终点 ────────────────────────────────────
        start = list(self.grid.current_position)
        goal = self._extract_goal(cycles_so_far)

        logger.info(
            f"反思分析: 重试{retry_count}, 障碍密度={density}, "
            f"推荐策略={strategy}"
        )

        # ── 构建反思指南 ──────────────────────────────────────
        return {
            "phase": "REFLECT",
            "retry_count": retry_count,
            "collision_info": {
                "point": collision_point,
                "nearby_obstacle_count": obstacle_count,
                "density": density,
            },
            "recommended_strategy": strategy,
            "available_strategies": self._get_strategy_descriptions(),
            "replan_tool": "ai_replan_with_obstacles",
            "suggested_call": {
                "tool_name": "ai_replan_with_obstacles",
                "arguments": {
                    "start": start,
                    "goal": goal,
                    "strategy": strategy,
                },
            },
            "message": (
                f"检测到路径碰撞于 {collision_point}，"
                f"附近障碍物 {obstacle_count} 个（{density}密度）。"
                f"建议使用 '{strategy}' 策略重规划路径。"
                f"重试次数: {retry_count}/{3}"
            ),
        }

    # ── 内部方法 ──────────────────────────────────────────────
    def _analyze_density(self, count: int) -> str:
        """根据障碍物数量分析密度"""
        if count < 3:
            return "low"
        elif count < 8:
            return "medium"
        else:
            return "high"

    def _pick_strategy(self, retry: int, density: str) -> str:
        """
        根据重试次数和密度推荐策略
        重试次数越多，策略越保守
        """
        strategy_by_retry = {
            0: "climb_over",      # 第一次：上升绕过
            1: "planar_detour",   # 第二次：水平绕行
            2: "ai_replan",       # 第三次：AI智能规划
        }

        if retry in strategy_by_retry:
            return strategy_by_retry[retry]

        # 超过3次重试，根据密度选择
        if density == "high":
            return "ai_replan"
        elif density == "medium":
            return "combined"
        else:
            return "climb_over"

    def _extract_goal(self, cycles: List[Dict]) -> Optional[List]:
        """
        从历史循环中提取最终目标位置
        （倒序查找最后一次执行的航点列表）
        """
        for cycle in reversed(cycles):
            data = (cycle.get("action_result") or {}).get("data") or {}
            waypoints = data.get("waypoints")
            if waypoints and len(waypoints) > 0:
                return list(waypoints[-1])
        return None

    def _get_strategy_descriptions(self) -> List[Dict]:
        """获取所有策略的详细描述"""
        return [
            {
                "name": "climb_over",
                "description": "上升绕过障碍物",
                "适用场景": "障碍物高度较低，上方空间充足",
            },
            {
                "name": "descend_under",
                "description": "下降绕过障碍物",
                "适用场景": "障碍物悬空，下方空间安全",
            },
            {
                "name": "planar_detour",
                "description": "水平方向绕行",
                "适用场景": "障碍物密度中等，侧面可通行",
            },
            {
                "name": "ai_replan",
                "description": "使用 A* 算法智能重规划",
                "适用场景": "障碍物密集，需要全局最优路径",
            },
            {
                "name": "combined",
                "description": "组合多种策略",
                "适用场景": "复杂环境，需要混合策略",
            },
        ]
