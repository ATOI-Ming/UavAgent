from typing import Set, Tuple, List, Dict, Optional, Callable


class GridSpace:
    """三维栅格空间管理"""

    def __init__(self, size: Tuple[int, int, int] = (100, 100, 20)):
        self.size_x, self.size_y, self.size_z = size
        self.obstacles: Set[Tuple[int, int, int]] = set()
        self.current_position: Tuple[int, int, int] = (50, 50, 0)
        self._listeners: List[Callable] = []

    # ── 障碍物管理 ────────────────────────────────────────────
    def add_obstacle(self, x: int, y: int, z: int) -> bool:
        if not self.in_bounds(x, y, z):
            return False
        self.obstacles.add((x, y, z))
        self._notify("add", (x, y, z))
        return True

    def add_obstacles_batch(self, points: List[Tuple]) -> int:
        count = 0
        for p in points:
            if self.add_obstacle(int(p[0]), int(p[1]), int(p[2])):
                count += 1
        return count

    def remove_obstacle(self, x: int, y: int, z: int) -> bool:
        if (x, y, z) in self.obstacles:
            self.obstacles.discard((x, y, z))
            self._notify("remove", (x, y, z))
            return True
        return False

    def clear_obstacles(self):
        self.obstacles.clear()
        self._notify("clear", None)

    # ── 查询方法 ──────────────────────────────────────────────
    def in_bounds(self, x: int, y: int, z: int) -> bool:
        return (
            0 <= x < self.size_x and
            0 <= y < self.size_y and
            0 <= z < self.size_z
        )

    def is_obstacle(self, x: int, y: int, z: int) -> bool:
        return (x, y, z) in self.obstacles

    def is_free(self, x: int, y: int, z: int) -> bool:
        return self.in_bounds(x, y, z) and not self.is_obstacle(x, y, z)

    def get_obstacle_count(self) -> int:
        return len(self.obstacles)

    def get_obstacles_list(self) -> List[Tuple]:
        return list(self.obstacles)

    def get_layer_data(self, z: int) -> Dict:
        """获取指定高度层的数据"""
        layer_obs = [(x, y) for (x, y, oz) in self.obstacles if oz == z]
        return {
            "z": z,
            "obstacles": layer_obs,
            "obstacle_count": len(layer_obs),
        }

    def check_path_collision(
        self,
        path: List[Tuple],
        margin: int = 0,
    ) -> Tuple[bool, Optional[Tuple]]:
        """
        检查路径是否与障碍物碰撞
        返回: (is_safe, collision_point)
        """
        for point in path:
            x, y, z = int(point[0]), int(point[1]), int(point[2])

            # 边界检查
            if not self.in_bounds(x, y, z):
                return False, (x, y, z)

            # 障碍物检查
            if self.is_obstacle(x, y, z):
                return False, (x, y, z)

            # 安全边距检查
            if margin > 0:
                for dx in range(-margin, margin + 1):
                    for dy in range(-margin, margin + 1):
                        for dz in range(-margin, margin + 1):
                            if self.is_obstacle(x + dx, y + dy, z + dz):
                                return False, (x, y, z)

        return True, None

    def get_nearby_obstacles(
        self, x: int, y: int, z: int, radius: int = 5
    ) -> List[Tuple]:
        """获取指定位置附近的障碍物"""
        result = []
        for ox, oy, oz in self.obstacles:
            dist = abs(ox - x) + abs(oy - y) + abs(oz - z)
            if dist <= radius:
                result.append((ox, oy, oz))
        return result

    def get_state_summary(self) -> Dict:
        """获取空间状态摘要（供前端和认知工具使用）"""
        total_cells = self.size_x * self.size_y * self.size_z
        obs_count   = len(self.obstacles)

        obs_by_layer = {}
        for (x, y, z) in self.obstacles:
            obs_by_layer[z] = obs_by_layer.get(z, 0) + 1

        return {
            "size":             (self.size_x, self.size_y, self.size_z),
            "current_position": self.current_position,
            "obstacle_count":   obs_count,
            "free_ratio":       round(1 - obs_count / total_cells, 4),
            "obstacles_by_layer": obs_by_layer,
        }

    # ── 位置管理 ──────────────────────────────────────────────
    def set_position(self, x: int, y: int, z: int):
        if self.in_bounds(x, y, z):
            self.current_position = (x, y, z)

    def reset_position(self):
        from config.settings import INITIAL_POSITION
        self.current_position = INITIAL_POSITION

    # ── 事件系统 ──────────────────────────────────────────────
    def add_listener(self, callback: Callable):
        self._listeners.append(callback)

    def _notify(self, event_type: str, data):
        for cb in self._listeners:
            try:
                cb(event_type, data)
            except Exception:
                pass
