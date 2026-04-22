import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use("Agg")  # 无GUI后端
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib 未安装，可视化功能将不可用")


class Visualizer:
    """
    可视化生成器
    功能：
    1. visualize_flight()     — 生成3D航线可视化PNG
    2. generate_layer_maps()  — 生成2D分层切片图
    """

    def __init__(self, grid_space, output_dir: Path):
        self.grid      = grid_space
        self.output_dir = output_dir
        self.viz_dir   = output_dir / "visualizations"
        self.layer_dir = output_dir / "layer_maps"

        self.viz_dir.mkdir(parents=True, exist_ok=True)
        self.layer_dir.mkdir(parents=True, exist_ok=True)

    # ── 3D 航线可视化 ─────────────────────────────────────────
    def visualize_flight(
        self,
        path: List = None,
        waypoints: List = None,
    ) -> Dict:
        """
        生成3D飞行路径可视化
        返回: {"success": bool, "file_path": str, "filename": str, "message": str}
        """
        if not HAS_MATPLOTLIB:
            return {
                "success":  False,
                "message":  "matplotlib未安装",
                "file_path": None,
                "filename": None,
            }

        try:
            fig = plt.figure(figsize=(12, 9))
            ax = fig.add_subplot(111, projection="3d")

            # 1. 绘制障碍物（红色半透明方块）
            obstacles = self.grid.get_obstacles_list()
            if obstacles:
                ox = [o[0] for o in obstacles]
                oy = [o[1] for o in obstacles]
                oz = [o[2] for o in obstacles]
                ax.scatter(
                    ox, oy, oz,
                    c="red",
                    marker="s",
                    s=20,
                    alpha=0.3,
                    label="障碍物",
                )

            # 2. 绘制飞行路径（蓝色曲线）
            if path and len(path) > 1:
                px = [p[0] for p in path]
                py = [p[1] for p in path]
                pz = [p[2] for p in path]
                ax.plot(px, py, pz, "b-", linewidth=2, label="飞行路径")

                # 起点（绿色三角）
                ax.scatter(
                    px[0], py[0], pz[0],
                    c="green",
                    s=100,
                    marker="^",
                    label="起点",
                    zorder=5,
                )

                # 终点（橙色倒三角）
                ax.scatter(
                    px[-1], py[-1], pz[-1],
                    c="orange",
                    s=100,
                    marker="v",
                    label="终点",
                    zorder=5,
                )

            # 3. 绘制航点（黄色星星）
            if waypoints:
                wx = [w[0] for w in waypoints]
                wy = [w[1] for w in waypoints]
                wz = [w[2] for w in waypoints]
                ax.scatter(
                    wx, wy, wz,
                    c="yellow",
                    s=80,
                    marker="*",
                    label="航点",
                    zorder=5,
                )

            # 4. 绘制当前位置（青色菱形）
            cp = self.grid.current_position
            ax.scatter(
                cp[0], cp[1], cp[2],
                c="cyan",
                s=150,
                marker="D",
                label="当前位置",
                zorder=6,
            )

            # 5. 设置坐标轴
            ax.set_xlabel("X (米)")
            ax.set_ylabel("Y (米)")
            ax.set_zlabel("Z 高度 (米)")
            ax.set_xlim(0, self.grid.size_x)
            ax.set_ylim(0, self.grid.size_y)
            ax.set_zlim(0, self.grid.size_z)
            ax.set_title("无人机飞行路径 3D 可视化")
            ax.legend(loc="upper left", fontsize=9)

            # 6. 保存图片
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flight_{ts}.png"
            filepath = self.viz_dir / filename

            plt.savefig(filepath, dpi=100, bbox_inches="tight")
            plt.close(fig)

            return {
                "success":  True,
                "file_path": str(filepath),
                "filename": filename,
                "message":  "3D航线可视化生成成功",
            }

        except Exception as e:
            logger.exception("3D可视化生成失败")
            return {
                "success":  False,
                "message":  f"可视化失败: {str(e)}",
                "file_path": None,
                "filename": None,
            }

    # ── 2D 分层切片图 ─────────────────────────────────────────
    def generate_layer_maps(self) -> Dict:
        """
        生成栅格空间的2D分层俯视图
        返回: {"success": bool, "files": [...], "count": int, "message": str}
        """
        if not HAS_MATPLOTLIB:
            return {
                "success": False,
                "files":   [],
                "count":   0,
                "message": "matplotlib未安装",
            }

        try:
            files = []

            # 找出所有有障碍物的高度层
            occupied_layers = set(o[2] for o in self.grid.obstacles)
            if not occupied_layers:
                occupied_layers = {0}  # 至少生成一张

            for z in sorted(occupied_layers):
                result = self._generate_single_layer(z)
                if result["success"]:
                    files.append(result)

            return {
                "success": True,
                "files":   files,
                "count":   len(files),
                "message": f"成功生成 {len(files)} 张分层切片图",
            }

        except Exception as e:
            logger.exception("分层切片图生成失败")
            return {
                "success": False,
                "files":   [],
                "count":   0,
                "message": f"生成失败: {str(e)}",
            }

    def _generate_single_layer(self, z: int) -> Dict:
        """生成单层切片图（内部方法）"""
        fig, ax = plt.subplots(figsize=(8, 8))

        layer_data = self.grid.get_layer_data(z)
        obstacles  = layer_data["obstacles"]

        # 设置坐标轴
        ax.set_xlim(0, self.grid.size_x)
        ax.set_ylim(0, self.grid.size_y)
        ax.set_aspect("equal")

        # 绘制障碍物（红色方块）
        for ox, oy in obstacles:
            rect = plt.Rectangle(
                (ox, oy), 1, 1,
                color="red",
                alpha=0.7,
            )
            ax.add_patch(rect)

        # 如果无人机在这一层，标记位置
        cp = self.grid.current_position
        if cp[2] == z:
            ax.plot(
                cp[0] + 0.5, cp[1] + 0.5,
                "g^",
                markersize=12,
                label="无人机位置",
            )

        ax.set_xlabel("X (米)")
        ax.set_ylabel("Y (米)")
        ax.set_title(f"高度层 Z={z} 米 — 障碍物: {len(obstacles)} 个")
        ax.grid(True, alpha=0.3)
        if cp[2] == z:
            ax.legend()

        # 保存
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"layer_z{z:02d}_{ts}.png"
        filepath = self.layer_dir / filename

        plt.savefig(filepath, dpi=80, bbox_inches="tight")
        plt.close(fig)

        return {
            "success":        True,
            "z":              z,
            "file_path":      str(filepath),
            "filename":       filename,
            "obstacle_count": len(obstacles),
        }
