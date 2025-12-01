from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from ads import TwinCat3_ADSserver
import pyads
import re
from video import VideoThread
from Servo import VisualServoThread
from Forward_planner import Forward_planner
import numpy as np
import time


class Control:
    def __init__(self, ui):
        # 将 ui 的所有控件动态绑定到 self
        for name, widget in ui.__dict__.items():
            setattr(self, name, widget)  # 例如：self.button_camera = ui.button_camera

        # 初始化状态标志
        self.connect_flag = False
        self.open_motor_flag = False

        self.open_start_flag = False
        self.open_forward_flag = True
        self.open_reverse_flag = True
        self.open_stop_flag = True
        self.open_reset_flag = True
        self.open_zero_flag = True
        self.open_move_flag = True

        self.open_servo_flag = False
        self.open_forwardplanner_flag = False
        self.open_reverseplanner_flag = False
        self.close_clampA_flag = False
        self.reverse_joint4_flag = False
        self.release_clampB_flag = False

        # 双相机
        self.cameraA_serial = "909512070942"
        self.cameraB_serial = "840412061540"

        self.open_cameraA_flag = False
        self.open_cameraB_flag = False

        self.thread = None
        # 初始化连接
        self.tc3 = TwinCat3_ADSserver()

    # ---------------------总体控制相关函数-------------------------
    def open_connect(self):
        if self.connect_flag:
            self.connect_flag = False
            self.button_connect.setText("启动")
            # 指示灯颜色
            self.connect_led.setStyleSheet("""
            background-color:red;
            border-radius: 20px; 
            border: 1px solid gray;
            margin-top: 0px;
            """)
            self.button_connect.setStyleSheet("""
            background-color: #f3f3f3;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
        """)
            self.addLogs("Twincat连接关闭")
            self.tc3.write_by_name(f"crawl1.RepythonX", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonY", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonZ", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRx", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRy", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRz", 0, pyads.PLCTYPE_LREAL)
            self.tc3.stop_monitoring()
            self.tc3.variables = {}
            self.tc3.close()
        else:
            try:
                self.connect_flag = True
                self.button_connect.setText("关闭")
                self.addLogs("Twincat连接开启")
                self.tc3.connect()
                self.add_adsvars()
                self.tc3.moving_signal.connect(self.value_changed)
                self.tc3.pos_signal.connect(self.value_changed)
                self.tc3.velo_signal.connect(self.value_changed)
                self.tc3.error_signal.connect(self.value_changed)
                self.tc3.eeposx_signal.connect(self.value_changed)
                self.tc3.eeposy_signal.connect(self.value_changed)
                self.tc3.eeposz_signal.connect(self.value_changed)
                self.tc3.eeposrx_signal.connect(self.value_changed)
                self.tc3.eeposry_signal.connect(self.value_changed)
                self.tc3.eeposrz_signal.connect(self.value_changed)
                '''self.tc3.close_A1.connect(self.value_changed)
                self.tc3.release_B1.connect(self.value_changed)
                self.tc3.reverse_joint41.connect(self.value_changed)
                self.tc3.close_A2.connect(self.value_changed)
                self.tc3.release_B2.connect(self.value_changed)
                self.tc3.reverse_joint42.connect(self.value_changed)
                self.tc3.close_A3.connect(self.value_changed)
                self.tc3.release_B3.connect(self.value_changed)
                self.tc3.reverse_joint43.connect(self.value_changed)'''

                self.tc3.start_monitoring()
                self.connect_led.setStyleSheet("""
                background-color: rgb(88, 214, 92);
                border-radius: 20px; 
                border: 1px solid gray;
                margin-top: 0px;
                """)
                self.button_connect.setStyleSheet("""
                background-color: gray;
                color: black;
                padding: 5px 10px;
                border-left: 0px;
                border-top: 0px;
                border-right: 2px solid #a3a3a3;
                border-bottom: 2px solid #a3a3a3;
                margin-top: 0px;
                """)
            except Exception as e:
                self.addLogs(str(e))

    # #   -------------------------------相机切换-----------------------------------
    def open_cameraA(self):
        if self.open_cameraA_flag:
            self.open_cameraA_flag = False
            self.button_cameraA.setText("开启A侧相机及六维力")
            self.button_cameraA.setStyleSheet("""
                background-color: #f3f3f3;
                color: black;
                padding: 5px 10px;
                border-left: 0px;
                border-top: 0px;
                border-right: 2px solid #a3a3a3;
                border-bottom: 2px solid #a3a3a3;
                margin-top: 0px;
            """)
            if self.thread:
                self.thread.stop_camera()
            self.VisionPictureRGB_2.setPixmap(QPixmap(""))
            self.addLogs("A侧相机和六维力关闭")
        else:
            self.addLogs("A侧相机和六维力开启中")
            try:
                # 如果 B 已开启，先关掉 B
                if self.open_cameraB_flag:
                    self.open_cameraB_flag = False
                    self.button_cameraB.setText("开启B侧相机及六维力")
                    self.button_cameraB.setStyleSheet("""
                    background-color: #f3f3f3;
                    color: black;
                    padding: 5px 10px;
                    border-left: 0px;
                    border-top: 0px;
                    border-right: 2px solid #a3a3a3;
                    border-bottom: 2px solid #a3a3a3;
                    margin-top: 0px;
                """)
                    if self.thread:
                        self.thread.stop_camera()

                self.thread = VideoThread(serial=self.cameraA_serial)
                self.thread.change_pixmap_signal.connect(self.update_image)
                self.thread.start_camera()
            except Exception as e:
                self.addLogs(str(e))

    def open_cameraB(self):
        if self.open_cameraB_flag:
            self.open_cameraB_flag = False
            self.button_cameraB.setText("开启B侧相机及六维力")
            self.button_cameraB.setStyleSheet("""
                background-color: #f3f3f3;
                color: black;
                padding: 5px 10px;
                border-left: 0px;
                border-top: 0px;
                border-right: 2px solid #a3a3a3;
                border-bottom: 2px solid #a3a3a3;
                margin-top: 0px;
            """)
            if self.thread:
                self.thread.stop_camera()
            self.VisionPictureRGB_2.setPixmap(QPixmap(""))
            self.addLogs("B侧相机和六维力关闭")
        else:
            self.addLogs("B侧相机和六维力开启中")
            try:
                # 如果 A 已开启，先关掉 A
                if self.open_cameraA_flag:
                    self.open_cameraA_flag = False
                    self.button_cameraA.setText("开启A侧相机及六维力")
                    self.button_cameraA.setStyleSheet("""
                    background-color: #f3f3f3;
                    color: black;
                    padding: 5px 10px;
                    border-left: 0px;
                    border-top: 0px;
                    border-right: 2px solid #a3a3a3;
                    border-bottom: 2px solid #a3a3a3;
                    margin-top: 0px;
                """)
                    if self.thread:
                        self.thread.stop_camera()

                self.thread = VideoThread(serial=self.cameraB_serial)
                self.thread.change_pixmap_signal.connect(self.update_image)
                self.thread.start_camera()
            except Exception as e:
                self.addLogs(str(e))

    def open_motor(self):
        if self.open_motor_flag:
            self.open_motor_flag = False
            self.button_motor.setText("开启电机")
            self.button_motor.setStyleSheet("""
            background-color: #f3f3f3;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
        """)
            self.addLogs("电机关闭")
            self.tc3.write_by_name(f"GVL.Enable_Open", False, pyads.PLCTYPE_BOOL)
            self.box_motor.setEnabled(False)
        else:
            try:
                self.open_motor_flag = True
                self.button_motor.setText("关闭电机")
                self.button_motor.setStyleSheet("""
                background-color: gray;
                color: black;
                padding: 5px 10px;
                border-left: 0px;
                border-top: 0px;
                border-right: 2px solid #a3a3a3;
                border-bottom: 2px solid #a3a3a3;
                margin-top: 0px;
            """)
                self.addLogs("电机开启")
                self.tc3.write_by_name(f"GVL.Enable_Open", True, pyads.PLCTYPE_BOOL)
                self.tc3.write_by_name(f"GVL.Signal", 1, pyads.PLCTYPE_INT)
                self.box_motor.setEnabled(True)
            except Exception as e:
                self.addLogs(str(e))

    # ------------------------------单机调试相关函数-------------------------------------

    def open_start(self):
        if self.open_start_flag:
            self.open_start_flag = False
            self.box_motor.setEnabled(True)
            self.button_start.setText("启动")
            self.start_led.setStyleSheet("""
            background-color:red;
            border-radius: 20px; 
            border: 1px solid gray;
            margin-top: 0px;
            """)
            self.button_start.setStyleSheet("""
            background-color: #f3f3f3;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
        """)
            self.addLogs("单机调试关闭")
            select_axis = int(self.box_motor.currentIndex())
            self.tc3.write_by_name(f"Single.nSelect", select_axis, pyads.PLCTYPE_INT)
            self.tc3.write_by_name(f"Single.Enable_Open[{select_axis}]", False, pyads.PLCTYPE_BOOL)
        else:
            try:
                # 检查是否选择了电机
                select_axis = self.box_motor.currentIndex()
                if select_axis == 0:
                    self.addLogs("请先选择电机")
                    return
                self.open_start_flag = True
                self.box_motor.setEnabled(False)
                self.button_start.setText("关闭")
                self.addLogs(f"{select_axis}单机调试启动")
                self.tc3.write_by_name(f"Single.nSelect", select_axis, pyads.PLCTYPE_INT)
                self.tc3.write_by_name(f"Single.Enable_Open[{select_axis}]", True, pyads.PLCTYPE_BOOL)
                self.start_led.setStyleSheet("""
                background-color: rgb(88, 214, 92);
                border-radius: 20px; 
                border: 1px solid gray;
                margin-top: 0px;
                """)
                self.button_start.setStyleSheet("""
                background-color: gray;
                color: black;
                padding: 5px 10px;
                border-left: 0px;
                border-top: 0px;
                border-right: 2px solid #a3a3a3;
                border-bottom: 2px solid #a3a3a3;
                margin-top: 0px;
            """)
            except Exception as e:
                self.addLogs(str(e))

    def open_forward(self):
        if self.open_forward_flag:
            if not self.open_start_flag:
                self.addLogs("请先开启电机")
                return
            self.open_forward_flag = True
            self.button_forward.setText("正转")
            self.button_forward.setStyleSheet("""
            background-color: gray;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
        """)
            self.addLogs("电机正转")
            select_axis = self.box_motor.currentIndex()
        self.tc3.write_by_name(f"Single.Positive_Open[{select_axis}]", True, pyads.PLCTYPE_BOOL)
        self.button_reverse.setEnabled(False)
        self.button_move.setEnabled(False)
        self.button_zero.setEnabled(False)
        self.button_reset.setEnabled(False)
        self.button_start.setEnabled(False)

    def open_reverse(self):
        if self.open_reverse_flag:
            if not self.open_start_flag:
                self.addLogs("请先开启电机")
                return
            self.open_reverse_flag = True
            self.button_reverse.setText("反转")
            self.button_reverse.setStyleSheet("""
            background-color: gray;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
        """)
            self.addLogs("电机反转")
            select_axis = self.box_motor.currentIndex()
        self.tc3.write_by_name(f"Single.Negative_Open[{select_axis}]", True, pyads.PLCTYPE_BOOL)
        self.button_forward.setEnabled(False)
        self.button_move.setEnabled(False)
        self.button_zero.setEnabled(False)
        self.button_reset.setEnabled(False)
        self.button_start.setEnabled(False)

    def open_stop(self):
        if self.open_stop_flag:
            self.button_stop.setText("停止")
            self.button_stop.setStyleSheet("""
            background-color: #f3f3f3;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
        """)
            self.button_forward.setText("正转")
            self.button_forward.setStyleSheet("""
            background-color: #f3f3f3;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
            """)
            # 反转按钮变色
            self.button_reverse.setText("反转")
            self.button_reverse.setStyleSheet("""
            background-color: #f3f3f3;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
            """)
            # 复位按钮
            self.button_reset.setText("复位")
            self.button_reset.setStyleSheet("""
            background-color: #f3f3f3;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
            """)

            # 回零按钮
            self.button_zero.setText("回零")
            self.button_zero.setStyleSheet("""
            background-color: #f3f3f3;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
            """)

            # 移动按钮
            self.button_move.setText("移动")
            self.button_move.setStyleSheet("""
            background-color: #f3f3f3;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
            """)
            self.addLogs("电机停止")
            select_axis = self.box_motor.currentIndex()
        self.tc3.write_by_name(f"Single.stop_flag[{select_axis}]", True, pyads.PLCTYPE_BOOL)
        self.button_forward.setEnabled(True)
        self.button_reverse.setEnabled(True)
        self.button_move.setEnabled(True)
        self.button_zero.setEnabled(True)
        self.button_reset.setEnabled(True)
        self.button_start.setEnabled(True)

    def open_reset(self):
        if self.open_reset_flag:
            if not self.open_start_flag:
                self.addLogs("请先开启电机")
                return
            self.open_reset_flag = True
            self.button_reset.setText("复位")
            self.button_reset.setStyleSheet("""
            background-color: gray;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
        """)
            self.addLogs("电机复位")
            select_axis = self.box_motor.currentIndex()
        self.tc3.write_by_name(f"Single.reset_flag[{select_axis}]", True, pyads.PLCTYPE_BOOL)
        self.set_button_style(self.button_reset, False)

    def open_zero(self):
        if self.open_zero_flag:
            if not self.open_start_flag:
                self.addLogs("请先开启电机")
                return
            self.open_zero_flag = True
            self.button_zero.setText("回零")
            self.button_zero.setStyleSheet("""
            background-color: gray;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
        """)
            self.addLogs("电机回零")
            select_axis = self.box_motor.currentIndex()
        self.tc3.write_by_name(f"Single.home_flag[{select_axis}]", True, pyads.PLCTYPE_BOOL)
        self.set_button_style(self.button_zero, False)

    def open_move(self):
        if self.open_move_flag:
            position_text = self.p_edit.text().strip()
            speed_text = self.v_edit.text().strip()
            # --------------------------------------限制位置速度大小-------------------------------------------
            if not self.open_start_flag:
                self.addLogs("请先开启电机")
                return
            # 判断输入合法性
            if not position_text and not speed_text:
                self.addLogs("请输入位置和速度")
                return
            elif not position_text:
                self.addLogs("请输入位置")
                return
            elif not speed_text:
                self.addLogs("请输入速度")
                return
            # 限制范围判断（这部分按实际修改）
            try:
                position = float(position_text)
                speed = float(speed_text)

                # 检查位置和速度范围
                if position < -180 or position > 180:
                    self.addLogs("位置范围错误,请输入-180到180之间的值")
                    return

                if speed < -30 or speed > 30:
                    self.addLogs("速度范围错误,请输入0到15之间的值")
                    return

            except ValueError:
                self.addLogs("输入错误，请输入有效的数字")
                return
            self.open_move_flag = True
            self.button_move.setText("移动")
            select_axis = self.box_motor.currentIndex()
            setpos = float(self.p_edit.text())
            setvelo = float(self.v_edit.text())
            self.tc3.write_by_name(f"Single.abs_Position[{select_axis}]", setpos, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"Single.abs_Velocity[{select_axis}]", setvelo, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"Single.abs_flag[{select_axis}]", True, pyads.PLCTYPE_BOOL)
            self.button_move.setStyleSheet("""
            background-color: gray;
            color: black;
            padding: 5px 10px;
            border-left: 0px;
            border-top: 0px;
            border-right: 2px solid #a3a3a3;
            border-bottom: 2px solid #a3a3a3;
            margin-top: 0px;
        """)
            self.addLogs(f"电机以{speed_text}m/s速度移动至({position_text})")
            self.set_button_style(self.button_move, False)

    # ------------------------分系统流程相关函数----------------------------
    def set_button_style(self, button, active):
        if active:
            button.setStyleSheet("""
                background-color: gray;
                font: 15pt \"Adobe 黑体 Std R\";
                color: black;
                margin-left: 60px;
            """)
        else:
            button.setStyleSheet("""
                background-color: #f4f4f4;
                color: black;
                font: 15pt \"Adobe 黑体 Std R\";
                margin-left: 60px;
            """)

    def set_led_style(self, led, active):
        if active:
            led.setStyleSheet("""
                background-color: rgb(88, 214, 92);
                border-radius: 15px; 
                border: 1px solid gray;
                margin-top: 0px;
            """)
        else:
            led.setStyleSheet("""
                background-color: red;
                border-radius: 15px; 
                border: 1px solid gray;
                margin-top: 0px;
            """)

    def servo_align(self, step):
        # 这里step代表第几步爬行触发的按钮
        if self.open_servo_flag:
            self.addLogs("捕获流程结束")
            self.servo.stop()
            self.open_servo_flag = False
            # self.set_led_style(self.led3, not self.open_servo_flag)
            if step == 1:
                self.set_button_style(self.button_servo_align1, self.open_servo_flag)
                self.set_led_style(self.led1, not self.open_servo_flag)
            elif step == 2:
                self.set_button_style(self.button_servo_align2, self.open_servo_flag)
                self.set_led_style(self.led11, not self.open_servo_flag)
            elif step == 3:
                self.set_button_style(self.button_servo_align3, self.open_servo_flag)
                self.set_led_style(self.led21, not self.open_servo_flag)
            self.tc3.write_by_name(f"crawl1.RepythonX", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonY", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonZ", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRx", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRy", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRz", 0, pyads.PLCTYPE_LREAL)
        else:
            self.open_servo_flag = True
            self.addLogs("捕获流程开始")
            if step == 1:
                self.set_button_style(self.button_servo_align1, self.open_servo_flag)
                self.tc3.write_by_name(f"GVL.VisSer_Open", True, pyads.PLCTYPE_BOOL)
                self.tc3.write_by_name(f"GVL.Signal", 1, pyads.PLCTYPE_INT)
            elif step == 2:
                self.set_button_style(self.button_servo_align2, self.open_servo_flag)
                self.tc3.write_by_name(f"GVL.VisSer_Open2", True, pyads.PLCTYPE_BOOL)
                self.tc3.write_by_name(f"GVL.Signal", 9, pyads.PLCTYPE_INT)
            elif step == 3:
                self.set_button_style(self.button_servo_align3, self.open_servo_flag)
                self.tc3.write_by_name(f"GVL.VisSer_Open4", True, pyads.PLCTYPE_BOOL)
                self.tc3.write_by_name(f"GVL.Signal", 17, pyads.PLCTYPE_INT)
            lambda_gain = np.array([0.6, 0.6, 0.6, 0.7, 0.7, 0.7])
            lambda_gain = np.diag(lambda_gain)
            self.servo = VisualServoThread(self, lambda_gain)
            self.servo.update_pose_signal.connect(self.write_delta)
            self.servo.finished_signal.connect(self.servo_judge)
            self.servo.start_servo()

    def linear_plan(self, step):
        if self.open_forwardplanner_flag:
            self.addLogs("直线规划结束")
            self.forward.stop()
            self.open_forwardplanner_flag = False
            if step == 1:
                self.set_button_style(self.button_linear_plan1, self.open_forwardplanner_flag)
                self.set_led_style(self.led2, not self.open_forwardplanner_flag)
            elif step == 2:
                self.set_button_style(self.button_linear_plan2, self.open_forwardplanner_flag)
                self.set_led_style(self.led12, not self.open_forwardplanner_flag)
            elif step == 3:
                self.set_button_style(self.button_linear_plan3, self.open_forwardplanner_flag)
                self.set_led_style(self.led22, not self.open_forwardplanner_flag)
            elif step == 4:
                self.set_button_style(self.button_linear_plan4, self.open_forwardplanner_flag)
                self.set_led_style(self.led32, not self.open_forwardplanner_flag)
            # self.set_led_style(self.led3, not self.open_forwardplanner_flag)
            self.tc3.write_by_name(f"crawl1.RepythonX", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonY", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonZ", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRx", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRy", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRz", 0, pyads.PLCTYPE_LREAL)
        else:
            self.open_forwardplanner_flag = True
            self.addLogs("直线规划开始")
            if step == 1:
                self.set_button_style(self.button_linear_plan1, self.open_forwardplanner_flag)
                self.tc3.write_by_name(f"GVL.Signal", 2, pyads.PLCTYPE_INT)
            elif step == 2:
                self.set_button_style(self.button_linear_plan2, self.open_forwardplanner_flag)
                self.tc3.write_by_name(f"GVL.Signal", 10, pyads.PLCTYPE_INT)
            elif step == 3:
                self.set_button_style(self.button_linear_plan3, self.open_forwardplanner_flag)
                self.tc3.write_by_name(f"GVL.Signal", 18, pyads.PLCTYPE_INT)
            elif step == 4:
                self.set_button_style(self.button_linear_plan4, self.open_forwardplanner_flag)
                self.tc3.write_by_name(f"GVL.Signal", 18, pyads.PLCTYPE_INT)

            distance = 0.2
            direction = 1
            self.forward = Forward_planner(self, distance=distance, direction=direction)
            self.forward.update_pose_signal.connect(self.write_delta)
            self.forward.finished_signal.connect(self.forward_judge)
            self.forward.start_forward()

    def close_clampA(self, step):
        if self.close_clampA_flag:
            self.addLogs("夹爪A闭合结束")
            self.close_clampA_flag = False
            if step == 1:
                self.set_button_style(self.button_close_clampA1, self.close_clampA_flag)
                self.set_led_style(self.led3, not self.close_clampA_flag)
            elif step == 2:
                self.set_button_style(self.button_close_clampA2, self.close_clampA_flag)
                self.set_led_style(self.led13, not self.close_clampA_flag)
            elif step == 3:
                self.set_button_style(self.button_close_clampA3, self.close_clampA_flag)
                self.set_led_style(self.led23, not self.close_clampA_flag)
        else:
            self.close_clampA_flag = True
            self.addLogs("夹爪A开始闭合")
            if step == 1:
                self.set_button_style(self.button_close_clampA1, self.close_clampA_flag)
                self.tc3.write_by_name(f"GVL.Signal", 3, pyads.PLCTYPE_INT)
                while True:
                    done_value = self.tc3.read_by_name('GVL.mcMoveAbsolute[10].Done', pyads.PLCTYPE_BOOL)
                    if done_value:
                        print("抓捕已完成！")
                        break  # 退出循环，继续执行后续程序
                    else:
                        print("等待8号点击抓捕")
                        time.sleep(0.5)  # 避免频繁查询，100ms 检查一次
                self.tc3.write_by_name(f"GVL.Signal", 4, pyads.PLCTYPE_INT)
            elif step == 2:
                self.set_button_style(self.button_close_clampA2, self.close_clampA_flag)
                self.tc3.write_by_name(f"GVL.Signal", 11, pyads.PLCTYPE_INT)
                while True:
                    done_value = self.tc3.read_by_name('GVL.mcMoveAbsolute[14].Done', pyads.PLCTYPE_BOOL)
                    if done_value:
                        print("抓捕已完成！")
                        break  # 退出循环，继续执行后续程序
                    else:
                        print("等待9号电机抓捕")
                        time.sleep(0.5)  # 避免频繁查询，100ms 检查一次
                        self.tc3.write_by_name(f"GVL.Signal", 12, pyads.PLCTYPE_INT)
            elif step == 3:
                self.set_button_style(self.button_close_clampA3, self.close_clampA_flag)
                self.tc3.write_by_name(f"GVL.Signal", 19, pyads.PLCTYPE_INT)
                while True:
                    done_value = self.tc3.read_by_name('GVL.mcMoveAbsolute[17].Done', pyads.PLCTYPE_BOOL)
                    if done_value:
                        print("抓捕已完成！")
                        break  # 退出循环，继续执行后续程序
                    else:
                        print("等待8号电机抓捕")
                        time.sleep(0.5)  # 避免频繁查询，100ms 检查一次
                        self.tc3.write_by_name(f"GVL.Signal", 20, pyads.PLCTYPE_INT)

    def release_clampB(self, step):
        if self.release_clampB_flag:
            self.addLogs("夹爪B松开结束")
            self.release_clampB_flag = False
            if step == 1:
                self.set_button_style(self.button_release_clampB1, self.release_clampB_flag)
                self.set_led_style(self.led4, not self.release_clampB_flag)
            elif step == 2:
                self.set_button_style(self.button_release_clampB2, self.release_clampB_flag)
                self.set_led_style(self.led14, not self.release_clampB_flag)
            elif step == 3:
                self.set_button_style(self.button_release_clampB3, self.release_clampB_flag)
                self.set_led_style(self.led24, not self.release_clampB_flag)
            # self.set_led_style(self.led3, not self.release_clampB_flag)
        else:
            self.release_clampB_flag = True
            self.addLogs("夹爪B开始松开")
            if step == 1:
                self.set_button_style(self.button_release_clampB1, self.release_clampB_flag)
                self.tc3.write_by_name(f"GVL.Signal", 5, pyads.PLCTYPE_INT)
            elif step == 2:
                self.set_button_style(self.button_release_clampB2, self.release_clampB_flag)
                self.tc3.write_by_name(f"GVL.Signal", 13, pyads.PLCTYPE_INT)
            elif step == 3:
                self.set_button_style(self.button_release_clampB3, self.release_clampB_flag)
                self.tc3.write_by_name(f"GVL.Signal", 21, pyads.PLCTYPE_INT)

    def reverse_linear(self, step):
        if self.open_reverseplanner_flag:
            self.addLogs("直线规划结束")
            self.forward.stop()
            self.open_reverseplanner_flag = False
            if step == 1:
                self.set_button_style(self.button_reverse_linear_1, self.open_reverseplanner_flag)
                self.set_led_style(self.led5, not self.open_reverseplanner_flag)
            elif step == 2:
                self.set_button_style(self.button_reverse_linear_2, self.open_reverseplanner_flag)
                self.set_led_style(self.led15, not self.open_reverseplanner_flag)
            elif step == 3:
                self.set_button_style(self.button_reverse_linear_3, self.open_reverseplanner_flag)
                self.set_led_style(self.led25, not self.open_reverseplanner_flag)
            # self.set_led_style(self.led3, not self.open_reverseplanner_flag)
            self.tc3.write_by_name(f"crawl1.RepythonX", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonY", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonZ", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRx", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRy", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"crawl1.RepythonRz", 0, pyads.PLCTYPE_LREAL)
        else:
            self.open_reverseplanner_flag = True
            self.addLogs("直线规划开始")
            if step == 1:
                self.set_button_style(self.button_reverse_linear_1, self.open_reverseplanner_flag)
                self.tc3.write_by_name(f"GVL.Signal", 6, pyads.PLCTYPE_INT)
                self.tc3.write_by_name(f"GVL.VisSer_Open1", True, pyads.PLCTYPE_BOOL)
                time.sleep(3)
                self.tc3.write_by_name(f"GVL.Signal", 7, pyads.PLCTYPE_INT)

            elif step == 2:
                self.set_button_style(self.button_reverse_linear_2, self.open_reverseplanner_flag)
                self.tc3.write_by_name(f"GVL.Signal", 14, pyads.PLCTYPE_INT)
                self.tc3.write_by_name(f"GVL.VisSer_Open3", True, pyads.PLCTYPE_BOOL)
                time.sleep(2)
                self.tc3.write_by_name(f"GVL.Signal", 15, pyads.PLCTYPE_INT)
            elif step == 3:
                self.set_button_style(self.button_reverse_linear_3, self.open_reverseplanner_flag)
                self.tc3.write_by_name(f"GVL.Signal", 22, pyads.PLCTYPE_INT)
                self.tc3.write_by_name(f"GVL.VisSer_Open5", True, pyads.PLCTYPE_BOOL)
                time.sleep(2)
                self.tc3.write_by_name(f"GVL.Signal", 23, pyads.PLCTYPE_INT)
            distance = 0.2
            direction = -1
            self.forward = Forward_planner(self, distance=distance, direction=direction)
            self.forward.update_pose_signal.connect(self.write_delta)
            self.forward.finished_signal.connect(self.revforward_judge)
            self.forward.start_forward()

    def joint4_reverse(self, step):
        if self.reverse_joint4_flag:
            self.addLogs("4号电机反转结束")
            self.reverse_joint4_flag = False
            if step == 1:
                self.set_button_style(self.button_joint4_reverse_1, self.reverse_joint4_flag)
                self.set_led_style(self.led6, not self.reverse_joint4_flag)
            elif step == 2:
                self.set_button_style(self.button_joint4_reverse_2, self.reverse_joint4_flag)
                self.set_led_style(self.led16, not self.reverse_joint4_flag)
            elif step == 3:
                self.set_button_style(self.button_joint4_reverse_3, self.reverse_joint4_flag)
                self.set_led_style(self.led26, not self.reverse_joint4_flag)
            # self.set_led_style(self.led3, not self.reverse_joint4_flag)
        else:
            self.reverse_joint4_flag = True
            self.addLogs("4号点击开始反转")
            if step == 1:
                self.set_button_style(self.button_joint4_reverse_1, self.reverse_joint4_flag)
                self.tc3.write_by_name(f"GVL.Signal", 8, pyads.PLCTYPE_INT)
            elif step == 2:
                self.set_button_style(self.button_joint4_reverse_2, self.reverse_joint4_flag)
                self.tc3.write_by_name(f"GVL.Signal", 16, pyads.PLCTYPE_INT)
            elif step == 3:
                self.set_button_style(self.button_joint4_reverse_3, self.reverse_joint4_flag)
                self.tc3.write_by_name(f"GVL.Signal", 24, pyads.PLCTYPE_INT)

            # self.tc3.write_by_name(f"GVL.Signal", 8, pyads.PLCTYPE_INT)

    def log_position(self):
        print("已经成功记录位置")
        self.set_button_style(self.log_pos, True)
        self.set_led_style(self.led27, True)

    def mounting(self):
        print("装配")
        self.set_button_style(self.mounting4, True)
        self.set_led_style(self.led31, True)

    # 日志显示相关
    def addLogs(self, *args, split=''):

        newLog = split.join(args)
        self.logText.appendPlainText(newLog)

        print(newLog)

    def add_adsvars(self):
        # 添加要监控的变量
        for i in range(9):
            self.tc3.add_variable(f"GVL.axis[{i + 1}].Status.Moving", pyads.PLCTYPE_BOOL, self.value_changed)
            self.tc3.add_variable(f"GVL.axis[{i + 1}].NcToPlc.ActVelo", pyads.PLCTYPE_LREAL, self.value_changed)
            self.tc3.add_variable(f"GVL.axis[{i + 1}].NcToPlc.ActPos", pyads.PLCTYPE_LREAL, self.value_changed)
            self.tc3.add_variable(f"GVL.axis[{i + 1}].NcToPlc.ErrorCode", pyads.PLCTYPE_UDINT, self.value_changed)

        self.tc3.add_variable(f"crawl1.ReaTwinX", pyads.PLCTYPE_LREAL, self.value_changed)
        self.tc3.add_variable(f"crawl1.ReaTwinY", pyads.PLCTYPE_LREAL, self.value_changed)
        self.tc3.add_variable(f"crawl1.ReaTwinZ", pyads.PLCTYPE_LREAL, self.value_changed)
        self.tc3.add_variable(f"crawl1.ReaTwinRX", pyads.PLCTYPE_LREAL, self.value_changed)
        self.tc3.add_variable(f"crawl1.ReaTwinRY", pyads.PLCTYPE_LREAL, self.value_changed)
        self.tc3.add_variable(f"crawl1.ReaTwinRZ", pyads.PLCTYPE_LREAL, self.value_changed)
        
        # 这里连接是否完成的变量
        #self.tc3.add_variable(f"GVL.CangMen_State_Close", pyads.PLCTYPE_BOOL, self.value_changed)

    # 定义回调函数
    def value_changed(self, name, value):
        pattern = r'\d+'
        types = name.split(".")[-1]
        try:
            row = int(re.findall(pattern, name)[0])
            if types == "Moving":
                if float(self.table.item(row - 1, 2).text()) == 0:
                    astr = "停止状态"
                else:
                    astr = "运行状态"
                item_data = QtWidgets.QTableWidgetItem(astr)
                self.table.setItem(row - 1, 1, item_data)
            elif types == "ActVelo":
                item_data = QtWidgets.QTableWidgetItem(str(round(value, 3)))
                self.table.setItem(row - 1, 2, item_data)
            elif types == "ActPos":
                item_data = QtWidgets.QTableWidgetItem(str(round(value, 3)))
                self.table.setItem(row - 1, 3, item_data)
            elif types == "ErrorCode":
                item_data = QtWidgets.QTableWidgetItem(str(value))
                self.table.setItem(row - 1, 4, item_data)
        except:
            if types == "ReaTwinX":
                self.line_x.setText(str(round(value, 3)))
            elif types == "ReaTwinY":
                self.line_y.setText(str(round(value, 3)))
            elif types == "ReaTwinZ":
                self.line_z.setText(str(round(value, 3)))
            elif types == "ReaTwinRX":
                self.line_Rx.setText(str(round(value, 3)))
            elif types == "ReaTwinRY":
                self.line_Ry.setText(str(round(value, 3)))
            elif types == "ReaTwinRZ":
                self.line_Rz.setText(str(round(value, 3)))

            '''elif types == "CangMen_State_Close":
                if value and self.close_clampA_flag:
                    self.close_clampA()'''


    def update_image(self, img_color):
        # Update the image_label with a new image
        # get image info
        h, w, ch = img_color.shape
        # create QImage from image
        bytes_per_line = ch * w
        convert_to_qt_format = QImage(img_color.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.VisionPictureRGB_2.setPixmap(QPixmap.fromImage(convert_to_qt_format))

    def write_delta(self, delta_world):
        self.tc3.write_by_name(f"crawl1.RepythonX", delta_world[0], pyads.PLCTYPE_LREAL)
        self.tc3.write_by_name(f"crawl1.RepythonY", delta_world[1], pyads.PLCTYPE_LREAL)
        self.tc3.write_by_name(f"crawl1.RepythonZ", delta_world[2], pyads.PLCTYPE_LREAL)
        self.tc3.write_by_name(f"crawl1.RepythonRx", delta_world[3], pyads.PLCTYPE_LREAL)
        self.tc3.write_by_name(f"crawl1.RepythonRy", delta_world[4], pyads.PLCTYPE_LREAL)
        self.tc3.write_by_name(f"crawl1.RepythonRz", delta_world[5], pyads.PLCTYPE_LREAL)

    def servo_judge(self, finished_flag=False):
        if finished_flag:
            self.servo_align()

    def forward_judge(self, finished_flag=False):
        if finished_flag:
            self.linear_plan()

    def revforward_judge(self, finished_flag=False):
        if finished_flag:
            self.reverse_linear()
