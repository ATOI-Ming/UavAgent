#!/usr/bin/env python3
"""
UAV Mission - DroneKit Version
任务描述: 飞一个边长3米的正方形
生成时间: 2026-04-06T01:11:37.928663
航点数量: 4
"""
from dronekit import connect, VehicleMode, LocationGlobalRelative
import time

CONNECTION_STRING = "127.0.0.1:14550"
TARGET_ALTITUDE = 10

def connect_vehicle():
    print("正在连接无人机...")
    vehicle = connect(CONNECTION_STRING, wait_ready=True)
    print(f"连接成功！电池电压: {vehicle.battery.voltage}V")
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
    
    print(f"起飞到 {altitude} 米...")
    vehicle.simple_takeoff(altitude)
    
    while True:
        current_alt = vehicle.location.global_relative_frame.alt
        print(f"  当前高度: {current_alt:.1f}m")
        if current_alt >= altitude * 0.95:
            print("已到达目标高度！")
            break
        time.sleep(1)

def goto_waypoints(vehicle, waypoints):
    for i, wp in enumerate(waypoints, 1):
        print(f"飞往航点 {i}/{len(waypoints)}: {wp}")
        vehicle.simple_goto(wp)
        time.sleep(5)  # 每个航点间隔5秒
        print(f"  已到达航点 {i}")

def main():
    vehicle = connect_vehicle()
    
    # 获取当前GPS位置作为基准
    lat = vehicle.location.global_frame.lat
    lon = vehicle.location.global_frame.lon
    
    # 解锁并起飞
    arm_and_takeoff(vehicle, TARGET_ALTITUDE)
    
    # 航点列表（基于栅格坐标转换）
    waypoints = [
    LocationGlobalRelative(lat + 0.000500, lon + 0.000530, 0),
    LocationGlobalRelative(lat + 0.000530, lon + 0.000530, 0),
    LocationGlobalRelative(lat + 0.000530, lon + 0.000500, 0),
    LocationGlobalRelative(lat + 0.000500, lon + 0.000500, 0),
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
