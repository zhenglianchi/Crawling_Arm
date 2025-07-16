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


def visjac_p(uv, depth,K):
    uv = base.getmatrix(uv, (2, None))
    Z = depth

    Z = base.getvector(Z)
    if len(Z) == 1:
        Z = np.repeat(Z, uv.shape[1])
    elif len(Z) != uv.shape[1]:
        raise ValueError("Z must be a scalar or have same number of columns as uv")

    L = np.empty((0, 6))  # empty matrix

    Kinv = np.linalg.inv(K)

    for z, p in zip(Z, uv.T):  # iterate over each column (point)

        # convert to normalized image-plane coordinates
        xy = Kinv @ base.e2h(p)
        x = xy[0, 0]
        y = xy[1, 0]

        # 2x6 Jacobian for this point
        # fmt: off
        Lp = K[:2,:2] @ np.array(
            [ [-1/z,  0,     x/z, x * y,      -(1 + x**2), y],
                [ 0,   -1/z,   y/z, (1 + y**2), -x*y,       -x] ])
        # fmt: on
        # stack them vertically
        L = np.vstack([L, Lp])

    return L


def get_K(fu=0.008,fv=0.008,rhou=1e-05,rhov=1e-05,u0=250.0,v0=250.0):
    # fmt: off
    K = np.array([[fu / rhou, 0,                   u0],
                    [ 0,                  fv / rhov, v0],
                    [ 0,                  0,                    1]
                    ], dtype=np.float64)
    # fmt: on
    return K



def servo(pose,uv,Z,p_star,lambda_gain,K):
    if Z <= 1e-6:
        Z = 0.5

    J = visjac_p(uv, Z, K)  # compute visual Jacobian

    # 计算误差（目标特征点与当前特征点的差值）
    e = uv - p_star  # feature error
    e = e.flatten(order="F")  # convert columnwise to a 1D vector

    error_rms = np.sqrt(np.mean(e**2))
    #print("误差:",error_rms)

    v = -lambda_gain @ np.linalg.pinv(J) @ e

    # 重新计算位姿增量 Td
    Td = SE3.Delta(v)

    # 获得机械臂末端位姿
    current_pos = pose

    current_object_pos = current_pos[:3]
    current_object_rot = current_pos[3:]

    T_rotation = R.from_euler("xyz",np.array(current_object_rot)).as_matrix()
    T_matrix_to_world = SE3.Rt(R=T_rotation,t=current_object_pos)

    T_world_d = T_matrix_to_world @ Td @ T_matrix_to_world.inv()

    # 提取平移部分
    translation = T_world_d.t
    rot = R.from_matrix(T_world_d.R).as_euler("xyz")

    delta_speed = np.hstack((translation, rot)).reshape(1, 6).squeeze()

    return v,delta_speed,error_rms



class VisualServoThread(QThread):
    update_pose_signal = pyqtSignal(list)

    def __init__(self, ui , lambda_gain):
        super().__init__()
        self.ui = ui
        self.video_thread = self.ui.thread
        self.lambda_gain = lambda_gain
        self._run_flag = None

    def run(self):
        while self._run_flag:
            if self.video_thread.uv is not None and self.video_thread.p_star is not None and self.video_thread.Z is not None:
                uv = self.video_thread.uv
                p_star = self.video_thread.p_star
                Z = self.video_thread.Z
                x,y,z = float(self.ui.line_x.text()),float(self.ui.line_y.text()),float(self.ui.line_z.text())
                rx,ry,rz = float(self.ui.line_Rx.text()),float(self.ui.line_Ry.text()),float(self.ui.line_Rz.text())
                curr_pose = [x,y,z,rx,ry,rz]
                cam_delta, world_delta, error_rms = servo(curr_pose, uv, Z, p_star, self.lambda_gain, self.video_thread.camera.K)
                self.update_pose_signal.emit(world_delta.tolist())
            else:
                world_delta = np.array([0,0,0,0,0,0])
                self.update_pose_signal.emit(world_delta.tolist())
            time.sleep(0.1)  # 避免CPU占用过高

    def stop(self):
        self._run_flag = False
        self.wait()

    def start_servo(self):
        self._run_flag = True
        self.start()