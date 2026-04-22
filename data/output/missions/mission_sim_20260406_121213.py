#!/usr/bin/env python3
"""
UAV Mission - Simulation Version
任务描述: 无人机先上升5米，再飞行一个边长10米的正方形，再上升5米，最后下降返回原地
生成时间: 2026-04-06T12:12:13.374563
航点数量: 7
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
        print(f"\n飞往目标: {target}")
        print(f"  当前位置: {self.position}")
        
        # 计算距离
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        dz = target[2] - self.position[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # 模拟飞行时间
        flight_time = max(0.5, distance / self.speed)
        print(f"  距离: {distance:.2f}米，预计耗时: {flight_time:.1f}秒")
        
        # 消耗电量
        self.battery -= distance * 0.1
        
        time.sleep(min(flight_time, 2.0))  # 最多sleep 2秒
        self.position = list(target)
        
        print(f"  已到达: {self.position}，电量: {self.battery:.1f}%")
    
    def takeoff(self, altitude):
        """起飞"""
        print(f"\n起飞到 {altitude} 米...")
        target = [self.position[0], self.position[1], altitude]
        self.goto(target)
    
    def land(self):
        """降落"""
        print("\n开始降落...")
        target = [self.position[0], self.position[1], 0]
        self.goto(target)
        print("已安全着陆！")


def main():
    print("=" * 50)
    print("UAV 仿真飞行任务")
    print("=" * 50)
    print(f"任务: 无人机先上升5米，再飞行一个边长10米的正方形，再上升5米，最后下降返回原地")
    print(f"航点数量: 7")
    print("=" * 50)
    
    drone = SimDrone()
    
    waypoints = [
    [50, 50, 5],
    [50, 60, 5],
    [60, 60, 5],
    [60, 50, 5],
    [50, 50, 5],
    [50, 50, 10],
    [50, 50, 5],
    ]
    
    if not waypoints:
        print("\n无航点，执行默认悬停...")
        drone.takeoff(10)
        time.sleep(3)
        drone.land()
    else:
        # 起飞到第一个航点的高度
        first_alt = waypoints[0][2] if waypoints[0][2] > 0 else 10
        drone.takeoff(first_alt)
        
        # 依次飞往各航点
        for i, wp in enumerate(waypoints, 1):
            print(f"\n--- 航点 {i}/{len(waypoints)} ---")
            drone.goto(wp)
        
        # 降落
        drone.land()
    
    print("\n" + "=" * 50)
    print("任务完成！")
    print(f"剩余电量: {drone.battery:.1f}%")
    print("=" * 50)


if __name__ == "__main__":
    main()
