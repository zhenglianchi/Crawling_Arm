"""
servoing module 
"""
import time
import numpy as np
from machinevisiontoolbox.base import *
from machinevisiontoolbox import *
from spatialmath.base import *
from spatialmath import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from scipy.spatial.transform import Rotation as R


def forward_planner(pose,direction):
    if direction == 1:
        v = [0,0,0.01,0,0,0]
    else:
        v = [0,0,-0.01,0,0,0]

    # 重新计算位姿增量 Td
    Td = SE3.Delta(v)

    # 获得机械臂末端位姿
    current_pos = pose

    #print(current_pos)

    current_object_pos = current_pos[:3]
    current_object_rot = current_pos[3:]

    T_translation = SE3(current_object_pos)
    T_rotation_to_world = SE3.Rx(current_object_rot[0]) * SE3.Ry(current_object_rot[1]) * SE3.Rz(current_object_rot[2])

    T_matrix_to_world = T_translation * T_rotation_to_world


    T_world_d = T_matrix_to_world @ Td @ T_matrix_to_world.inv()

    # 提取平移部分
    translation = T_world_d.t
    rot = v[3:]

    delta_speed = np.hstack((translation, rot)).reshape(1, 6).squeeze()

    return delta_speed



class Forward_planner(QThread):
    update_pose_signal = pyqtSignal(list)
    finished_signal = pyqtSignal(bool) 
    def __init__(self, ui, distance = 0.2, direction = 1):
        super().__init__()
        self.ui = ui
        self._run_flag = None
        self.video_thread = self.ui.thread
        self.distance = distance
        self.direction = direction

    def run(self):
        while self._run_flag:
            # 先用中心点深度，如果中心点深度为0则使用平均深度
            Z = self.video_thread.center_z if self.video_thread.center_z != 0 else self.video_thread.Z
            print(Z)

            x,y,z = float(self.ui.line_x.text()),float(self.ui.line_y.text()),float(self.ui.line_z.text())
            rx,ry,rz = float(self.ui.line_Rr.text()),float(self.ui.line_Rp.text()),float(self.ui.line_Ry.text())
            curr_pose = [x,y,z,rx,ry,rz]
            world_delta = forward_planner(curr_pose, self.direction)
            self.update_pose_signal.emit(world_delta.tolist())

            if self.direction == 1:
                if Z >=1e-6 and Z <= self.distance :
                    print("直线规划结束")
                    self.finished_signal.emit(True)
                    break
            else:
                if Z >= self.distance :
                    print("反向直线规划结束")
                    self.finished_signal.emit(True)
                    break

            time.sleep(0.1)  # 避免CPU占用过高

    def stop(self):
        self._run_flag = False
        self.wait()

    def start_forward(self):
        self._run_flag = True
        self.start()