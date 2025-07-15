import pyrealsense2 as rs

# 获取所有连接的摄像头
ctx = rs.context()
devices = ctx.query_devices()

for dev in devices:
    print("Serial Number:", dev.get_info(rs.camera_info.serial_number))