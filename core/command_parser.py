import re
from typing import List, Tuple, Dict, Optional
from config.settings import ACTIONS, ACTION_ALIASES, INITIAL_POSITION, GRID_SIZE


class CommandParser:
    """动作序列字符串 → 三维坐标航点列表"""

    def __init__(self):
        self.grid_size    = GRID_SIZE
        self.start_position = list(INITIAL_POSITION)

    def parse(self, command: str) -> Dict:
        """
        解析动作序列
        输入:  "上升3米,右移3米,前进3米,左移3米"
        输出:  {"success": True, "waypoints": [[x,y,z],...], "message": "..."}
        """
        try:
            parts = self._split(command)
            if not parts:
                return self._fail("命令为空，无法解析")

            waypoints = []
            current   = list(self.start_position)

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                result = self._parse_one(part, current)
                if result is None:
                    return self._fail(f"无法识别动作: '{part}'")

                new_pos = result
                # 边界裁剪
                new_pos[0] = max(0, min(new_pos[0], self.grid_size[0] - 1))
                new_pos[1] = max(0, min(new_pos[1], self.grid_size[1] - 1))
                new_pos[2] = max(0, min(new_pos[2], self.grid_size[2] - 1))

                waypoints.append(tuple(new_pos))
                current = new_pos

            return {
                "success":   True,
                "waypoints": waypoints,
                "message":   f"解析成功，共 {len(waypoints)} 个航点",
            }

        except Exception as e:
            return self._fail(f"解析异常: {str(e)}")

    # ── 内部方法 ──────────────────────────────────────────────
    def _split(self, command: str) -> List[str]:
        """按逗号/分号/顿号分割命令"""
        return re.split(r"[,;，；、]", command)

    def _parse_one(
        self, action_str: str, current: List[int]
    ) -> Optional[List[int]]:
        """解析单条动作，返回新位置"""
        # 提取距离数字（默认1）
        m = re.search(r"(\d+(?:\.\d+)?)", action_str)
        distance = int(float(m.group(1))) if m else 1

        # 匹配动作名
        action_name = self._match_action(action_str)
        if action_name is None:
            return None

        dx, dy, dz = ACTIONS[action_name]
        return [
            current[0] + dx * distance,
            current[1] + dy * distance,
            current[2] + dz * distance,
        ]

    def _match_action(self, text: str) -> Optional[str]:
        """优先匹配中文别名，再匹配英文名"""
        for alias, action in ACTION_ALIASES.items():
            if alias in text:
                return action
        for action in ACTIONS:
            if action in text.lower():
                return action
        return None

    def set_start_position(self, pos: Tuple):
        self.start_position = list(pos)

    def _fail(self, msg: str) -> Dict:
        return {"success": False, "waypoints": [], "message": msg}
