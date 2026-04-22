import math
import heapq
from collections import deque
from typing import List, Tuple, Dict, Optional


class FlightPlanner:
    """路径规划器 — 支持 A* / BFS / Direct 三种算法"""

    def __init__(self, grid_space):
        self.grid = grid_space

    def plan(
        self,
        waypoints: List[Tuple],
        algorithm: str = "astar",
    ) -> Dict:
        """
        对航点列表进行路径规划
        返回统一格式:
        {
            "success": bool,
            "path": [[x,y,z],...],
            "distance": float,
            "safe": bool,
            "collision_point": [x,y,z] or None,
            "waypoints": [...],
            "algorithm": str,
            "message": str,
        }
        """
        if not waypoints:
            return self._fail("航点列表为空")

        full_path = []
        start     = self.grid.current_position

        for wp in waypoints:
            wp = (int(wp[0]), int(wp[1]), int(wp[2]))
            segment = self._plan_segment(start, wp, algorithm)
            if not segment:
                return self._fail(f"无法规划路径段: {start} → {wp}")
            full_path.extend(segment)
            start = wp

        # 碰撞检测
        is_safe, col_pt = self.grid.check_path_collision(full_path)
        distance        = self._calc_distance(full_path)

        return {
            "success":         True,
            "path":            [list(p) for p in full_path],
            "distance":        round(distance, 2),
            "safe":            is_safe,
            "collision_point": list(col_pt) if col_pt else None,
            "waypoints":       [list(wp) for wp in waypoints],
            "algorithm":       algorithm,
            "message":         "路径规划成功" if is_safe
                               else f"路径碰撞于 {col_pt}",
        }

    # ── 算法选择 ──────────────────────────────────────────────
    def _plan_segment(
        self, start: Tuple, end: Tuple, algorithm: str
    ) -> List[Tuple]:
        if algorithm == "astar":
            return self._astar(start, end)
        elif algorithm == "bfs":
            return self._bfs(start, end)
        else:
            return self._direct(start, end)

    # ── A* ────────────────────────────────────────────────────
    def _astar(self, start: Tuple, end: Tuple) -> List[Tuple]:
        def h(a, b):
            return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

        open_set  = [(0, start)]
        came_from = {}
        g_score   = {start: 0}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == end:
                return self._reconstruct(came_from, current)

            for nb in self._neighbors(current):
                tg = g_score[current] + 1
                if tg < g_score.get(nb, float("inf")):
                    came_from[nb] = current
                    g_score[nb]   = tg
                    heapq.heappush(open_set, (tg + h(nb, end), nb))

        # A*未找到路径，降级为直线
        return self._direct(start, end)

    # ── BFS ───────────────────────────────────────────────────
    def _bfs(self, start: Tuple, end: Tuple) -> List[Tuple]:
        queue   = deque([[start]])
        visited = {start}

        while queue:
            path    = queue.popleft()
            current = path[-1]
            if current == end:
                return path

            for nb in self._neighbors(current):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(path + [nb])

        return self._direct(start, end)

    # ── Direct（布雷森汉姆插值直线）─────────────────────────────
    def _direct(self, start: Tuple, end: Tuple) -> List[Tuple]:
        path = [start]
        x0, y0, z0 = start
        x1, y1, z1 = end
        steps = max(abs(x1-x0), abs(y1-y0), abs(z1-z0), 1)

        for i in range(1, steps + 1):
            t = i / steps
            pt = (
                round(x0 + (x1 - x0) * t),
                round(y0 + (y1 - y0) * t),
                round(z0 + (z1 - z0) * t),
            )
            if pt not in path:
                path.append(pt)
        return path

    # ── 辅助 ──────────────────────────────────────────────────
    def _neighbors(self, pos: Tuple) -> List[Tuple]:
        x, y, z = pos
        dirs = [
            (1,0,0),(-1,0,0),
            (0,1,0),(0,-1,0),
            (0,0,1),(0,0,-1),
        ]
        return [
            (x+dx, y+dy, z+dz)
            for dx, dy, dz in dirs
            if self.grid.is_free(x+dx, y+dy, z+dz)
        ]

    def _reconstruct(self, came_from: Dict, current: Tuple) -> List[Tuple]:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return list(reversed(path))

    def _calc_distance(self, path: List[Tuple]) -> float:
        dist = 0.0
        for i in range(len(path) - 1):
            dist += math.sqrt(
                sum((a - b) ** 2 for a, b in zip(path[i], path[i+1]))
            )
        return dist

    def _fail(self, msg: str) -> Dict:
        return {
            "success":         False,
            "path":            [],
            "distance":        0.0,
            "safe":            False,
            "collision_point": None,
            "waypoints":       [],
            "algorithm":       "none",
            "message":         msg,
        }
