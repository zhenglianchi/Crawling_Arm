from PyQt5.QtCore import Qt, QThread, pyqtSignal
from camera import Camera
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
import time
import cv2
# pip install opencv-contrib-python==4.5.4.60
import cv2.aruco as aruco

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self,serial=None):
        super().__init__()
        self.serial=serial
        self.camera = Camera(serial=self.serial)
        self._run_flag = True
        self.uv = None
        self.p_star = None
        self.Z = None
        print("[DEBUG] VideoThread init called with serial:", serial)

    def run(self):
        while self._run_flag:
            if self.camera.is_opened():
                color_intrin, depth_intrin, img_color, img_depth, aligned_depth_frame, intr_coeffs, intr_matrix = self.camera.get_aligned_images()
                resolution = [color_intrin.width,color_intrin.height]
                f = [color_intrin.fx,color_intrin.fy]

                img_color = np.array(cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB))
                
                aruco_dict = aruco.Dictionary_get(aruco.DICT_ARUCO_ORIGINAL)
                # 创建detector parameters
                parameters = aruco.DetectorParameters_create()
                # 输入rgb图, aruco的dictionary, 相机内参, 相机的畸变参数
                corners, ids, rejected_img_points = aruco.detectMarkers(img_color, aruco_dict, parameters=parameters,cameraMatrix=intr_matrix, distCoeff=intr_coeffs)
                
                if corners:
                    aruco.drawDetectedMarkers(img_color, corners)
                    detected_points = corners[0][0]

                    average_x = (detected_points[0][0] + detected_points[1][0] + detected_points[2][0] + detected_points[3][0]) / 4
                    average_y = (detected_points[0][1] + detected_points[1][1] + detected_points[2][1] + detected_points[3][1]) / 4
                    # 得到中心点坐标
                    center_point = (average_x, average_y)

                    target_points = self.resize_and_center_box(detected_points,resolution)

                    for point in target_points:
                        cv2.circle(img_color, point, 3, (255, 255, 255), -1)

                    uv = np.array(detected_points).T
                    p_star = np.array(target_points).T

                    self.uv = uv
                    self.p_star = p_star
                    self.Z = img_depth[int(center_point[1]), int(center_point[0])]/1000.0
                else:
                    self.uv = None
                    self.p_star = None
                    self.Z = None

                img_color = cv2.resize(img_color, (467, 336))  # 注意参数是 (width, height)
                # emit signal
                self.change_pixmap_signal.emit(img_color)
            else:
                time.sleep(1)

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()

    def start_camera(self):
        """Start the camera if it's not already running."""
        self._run_flag = True
        self.start()

    def stop_camera(self):
        """Stop the camera without stopping the thread."""
        self.camera.stop()
        self._run_flag = False
        self.quit()  # 调用 quit 来终止线程
        self.wait()  # 等待线程彻底结束

    def resize_and_center_box(self, target_points, image_size, padding=0):
        if len(target_points) != 4:
            raise ValueError("目标框必须包含四个点。")

        points = np.array(target_points, dtype=np.float32)

        center = np.mean(points, axis=0)
        image_center = np.array([image_size[0] / 2, image_size[1] / 2])

        moved_points = points + (image_center - center)

        v1 = moved_points[1] - moved_points[0]
        v2 = moved_points[3] - moved_points[0]

        width = np.linalg.norm(v1)
        height = np.linalg.norm(v2)

        half_w = width / 2
        half_h = height / 2

        rect_points = np.array([
            [-half_w, -half_h],
            [ half_w, -half_h],
            [ half_w,  half_h],
            [-half_w,  half_h]
        ])

        rect_points += image_center

        center_rect = np.mean(rect_points, axis=0)
        rect_points = np.array([
            [
                rect_points[i][0] + (rect_points[i][0] - center_rect[0]) * padding / max(width, height),
                rect_points[i][1] + (rect_points[i][1] - center_rect[1]) * padding / max(width, height)
            ]
            for i in range(4)
        ])

        x_coords = [p[0] for p in rect_points]
        y_coords = [p[1] for p in rect_points]
        x_min, x_max = int(min(x_coords)), int(max(x_coords))
        y_min, y_max = int(min(y_coords)), int(max(y_coords))

        rect_points = [
            [x_min, y_min],  # 左上
            [x_max, y_min],  # 右上
            [x_max, y_max],  # 右下
            [x_min, y_max]   # 左下
        ]

        return rect_points