from PyQt5.QtGui import QImage, QPixmap
import pyads
import re
from video import VideoThread
import time
from control import Control

class Switch(Control):
    def __init__(self):
        self.switch_on = True

    def switch_base(self):
        if self.switch_on:
            self.tc3.write_by_name(f"GVL.output3", True, pyads.PLCTYPE_BOOL)
            self.tc3.write_by_name(f"GVL.output7", True, pyads.PLCTYPE_BOOL)
            time.sleep(3)
            self.tc3.write_by_name(f"GVL.output7", False, pyads.PLCTYPE_BOOL)
            self.open_cameraA()
        else:
            self.tc3.write_by_name(f"GVL.output4", True, pyads.PLCTYPE_BOOL)
            self.tc3.write_by_name(f"GVL.output8", True, pyads.PLCTYPE_BOOL)
            time.sleep(3)
            self.tc3.write_by_name(f"GVL.output8", False, pyads.PLCTYPE_BOOL)
            self.open_cameraB()


    def open_cameraA(self):
        if self.open_cameraA_flag:
            self.open_cameraA_flag = False
            if self.thread:
                self.thread.stop_camera()
                self.thread = None
            self.del_force1()
            self.VisionPictureRGB_2.setPixmap(QPixmap(""))
            self.addLogs("A侧相机和六维力关闭")
        else:
            self.open_cameraA_flag = True
            self.addLogs("A侧相机和六维力开启中")
            try:
                # 如果 B 已开启，先关掉 B
                if self.open_cameraB_flag:
                    self.open_cameraB()

                self.thread = VideoThread(serial=self.cameraA_serial)
                self.thread.change_pixmap_signal.connect(self.update_image)
                self.thread.start_camera()
                self.add_force1()
            except Exception as e:
                self.addLogs(str(e))


    def open_cameraB(self):
        if self.open_cameraB_flag:
            self.open_cameraB_flag = False
            if self.thread:
                self.thread.stop_camera()
                self.thread = None
            self.del_force2()
            self.VisionPictureRGB_2.setPixmap(QPixmap(""))
            self.addLogs("B侧相机和六维力关闭")
        else:
            self.open_cameraB_flag = True
            self.addLogs("B侧相机和六维力开启中")
            try:
                # 如果 A 已开启，先关掉 A
                if self.open_cameraA_flag:
                    self.open_cameraA()

                self.thread = VideoThread(serial=self.cameraB_serial)
                self.thread.change_pixmap_signal.connect(self.update_image)
                self.thread.start_camera()
                self.add_force2()
            except Exception as e:
                self.addLogs(str(e))

                