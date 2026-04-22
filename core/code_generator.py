from typing import List, Dict
from datetime import datetime
from pathlib import Path


class CodeGenerator:
    """
    飞行代码生成器
    功能：根据航点列表生成可执行的无人机飞行代码
    输出两个版本：
    1. DroneKit 真实飞行版
    2. 仿真调试版
    """

    def __init__(self, mission_dir: Path):
        self.mission_dir = mission_dir
        self.mission_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        path: List = None,
        waypoints: List = None,
        task_description: str = "",
    ) -> Dict:
        """
        生成飞行代码
        返回: {
            "success": bool,
            "files": [{"type": str, "filename": str, "file_path": str}, ...],
            "message": str,
            "task_description": str,
            "waypoint_count": int,
        }
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        files = []

        # 优先使用 waypoints，如果没有则使用 path
        wp_list = waypoints if waypoints else path
        if not wp_list:
            wp_list = []

        # 1. 生成 DroneKit 版本
        dronekit_code = self._gen_dronekit(wp_list, task_description)
        dk_file = self.mission_dir / f"mission_dronekit_{ts}.py"
        dk_file.write_text(dronekit_code, encoding="utf-8")
        files.append({
            "type":      "dronekit",
            "filename":  dk_file.name,
            "file_path": str(dk_file),
        })

        # 2. 生成仿真版本
        sim_code = self._gen_simulation(wp_list, task_description)
        sim_file = self.mission_dir / f"mission_sim_{ts}.py"
        sim_file.write_text(sim_code, encoding="utf-8")
        files.append({
            "type":      "simulation",
            "filename":  sim_file.name,
            "file_path": str(sim_file),
        })

        return {
            "success":          True,
            "files":            files,
            "message":          f"成功生成 {len(files)} 个飞行代码文件",
            "task_description": task_description,
            "waypoint_count":   len(wp_list),
        }

    # ── DroneKit 版本 ─────────────────────────────────────────
    def _gen_dronekit(self, waypoints: List, task_desc: str) -> str:
        wp_code_lines = []
        for wp in waypoints:
            # 栅格坐标 → GPS偏移（简化映射，实际需要GPS转换）
            x, y, z = wp[0], wp[1], wp[2]
            wp_code_lines.append(
                f"    LocationGlobalRelative("
                f"lat + {x * 0.00001:.6f}, "
                f"lon + {y * 0.00001:.6f}, "
                f"{z}),"
            )
        wp_str = "\n".join(wp_code_lines) if wp_code_lines else "    # 无航点"

        return f'''#!/usr/bin/env python3
"""
UAV Mission - DroneKit Version
任务描述: {task_desc}
生成时间: {datetime.now().isoformat()}
航点数量: {len(waypoints)}
"""
from dronekit import connect, VehicleMode, LocationGlobalRelative
import time

CONNECTION_STRING = "127.0.0.1:14550"
TARGET_ALTITUDE = 10

def connect_vehicle():
    print("正在连接无人机...")
    vehicle = connect(CONNECTION_STRING, wait_ready=True)
    print(f"连接成功！电池电压: {{vehicle.battery.voltage}}V")
    return vehicle

def arm_and_takeoff(vehicle, altitude):
    print("检查是否可以解锁...")
    while not vehicle.is_armable:
        print("  等待无人机初始化...")
        time.sleep(1)
    
    print("切换到 GUIDED 模式...")
    vehicle.mode = VehicleMode("GUIDED")
    time.sleep(1)
    
    print("解锁电机...")
    vehicle.armed = True
    while not vehicle.armed:
        print("  等待解锁...")
        time.sleep(1)
    
    print(f"起飞到 {{altitude}} 米...")
    vehicle.simple_takeoff(altitude)
    
    while True:
        current_alt = vehicle.location.global_relative_frame.alt
        print(f"  当前高度: {{current_alt:.1f}}m")
        if current_alt >= altitude * 0.95:
            print("已到达目标高度！")
            break
        time.sleep(1)

def goto_waypoints(vehicle, waypoints):
    for i, wp in enumerate(waypoints, 1):
        print(f"飞往航点 {{i}}/{{len(waypoints)}}: {{wp}}")
        vehicle.simple_goto(wp)
        time.sleep(5)  # 每个航点间隔5秒
        print(f"  已到达航点 {{i}}")

def main():
    vehicle = connect_vehicle()
    
    # 获取当前GPS位置作为基准
    lat = vehicle.location.global_frame.lat
    lon = vehicle.location.global_frame.lon
    
    # 解锁并起飞
    arm_and_takeoff(vehicle, TARGET_ALTITUDE)
    
    # 航点列表（基于栅格坐标转换）
    waypoints = [
{wp_str}
    ]
    
    # 执行航点飞行
    if waypoints:
        goto_waypoints(vehicle, waypoints)
    else:
        print("无航点，悬停5秒...")
        time.sleep(5)
    
    print("任务完成，返航...")
    vehicle.mode = VehicleMode("RTL")
    
    time.sleep(10)
    vehicle.close()
    print("断开连接")

if __name__ == "__main__":
    main()
'''

    # ── 仿真版本 ─────────────────────────────────────────────
    def _gen_simulation(self, waypoints: List, task_desc: str) -> str:
        wp_lines = []
        for wp in waypoints:
            wp_lines.append(f"    {list(wp)},")
        wp_str = "\n".join(wp_lines) if wp_lines else "    # 无航点"

        return f'''#!/usr/bin/env python3
"""
UAV Mission - Simulation Version
任务描述: {task_desc}
生成时间: {datetime.now().isoformat()}
航点数量: {len(waypoints)}
"""
import time
import math


class SimDrone:
    """仿真无人机"""
    
    def __init__(self, start_pos=(50, 50, 0)):
        self.position = list(start_pos)
        self.speed = 5.0  # 米/秒
        self.battery = 100.0
    
    def goto(self, target):
        """飞往目标点"""
        print(f"\\n飞往目标: {{target}}")
        print(f"  当前位置: {{self.position}}")
        
        # 计算距离
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        dz = target[2] - self.position[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # 模拟飞行时间
        flight_time = max(0.5, distance / self.speed)
        print(f"  距离: {{distance:.2f}}米，预计耗时: {{flight_time:.1f}}秒")
        
        # 消耗电量
        self.battery -= distance * 0.1
        
        time.sleep(min(flight_time, 2.0))  # 最多sleep 2秒
        self.position = list(target)
        
        print(f"  已到达: {{self.position}}，电量: {{self.battery:.1f}}%")
    
    def takeoff(self, altitude):
        """起飞"""
        print(f"\\n起飞到 {{altitude}} 米...")
        target = [self.position[0], self.position[1], altitude]
        self.goto(target)
    
    def land(self):
        """降落"""
        print("\\n开始降落...")
        target = [self.position[0], self.position[1], 0]
        self.goto(target)
        print("已安全着陆！")


def main():
    print("=" * 50)
    print("UAV 仿真飞行任务")
    print("=" * 50)
    print(f"任务: {task_desc}")
    print(f"航点数量: {len(waypoints)}")
    print("=" * 50)
    
    drone = SimDrone()
    
    waypoints = [
{wp_str}
    ]
    
    if not waypoints:
        print("\\n无航点，执行默认悬停...")
        drone.takeoff(10)
        time.sleep(3)
        drone.land()
    else:
        # 起飞到第一个航点的高度
        first_alt = waypoints[0][2] if waypoints[0][2] > 0 else 10
        drone.takeoff(first_alt)
        
        # 依次飞往各航点
        for i, wp in enumerate(waypoints, 1):
            print(f"\\n--- 航点 {{i}}/{{len(waypoints)}} ---")
            drone.goto(wp)
        
        # 降落
        drone.land()
    
    print("\\n" + "=" * 50)
    print("任务完成！")
    print(f"剩余电量: {{drone.battery:.1f}}%")
    print("=" * 50)


if __name__ == "__main__":
    main()
'''
