from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from ads import TwinCat3_ADSserver
import pyads
import re
from video import VideoThread
from Servo import VisualServoThread
import numpy as np

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

        self.open_machineopen_flag = False
        self.open_dooropen_flag = False
        self.open_doorclose_flag = False
        self.open_dock_flag = False
        self.open_doormoveopen_flag = False
        self.open_machineclose_flag = False
        self.open_target_flag = False
        self.open_servo_flag = False
         # 双相机
        self.cameraA_serial="909512070942"
        self.cameraB_serial="840412061540"

        self.open_cameraA_flag=False
        self.open_cameraB_flag=False

        self.thread=None
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
            self.tc3.stop_monitoring()
            self.tc3.variables={}
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
        self.set_button_style(self.button_reset,False)

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
        self.set_button_style(self.button_zero,False)

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
    # ------------------------分系统流程相关函数----------------------------
    def set_button_style(self, button, active):
        if active:
            button.setStyleSheet("""
                background-color: gray;
                color: black;
                padding: 5px 10px;
                border-left: 0px;
                border-top: 0px;
                border-right: 2px solid #a3a3a3;
                border-bottom: 2px solid #a3a3a3;
                margin-top: 0px;
            """)
        else:
            button.setStyleSheet("""
                background-color: #f3f3f3;
                color: black;
                padding: 5px 10px;
                border-left: 0px;
                border-top: 0px;
                border-right: 2px solid #a3a3a3;
                border-bottom: 2px solid #a3a3a3;
                margin-top: 0px;
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

    def open_capture(self):
        if self.open_servo_flag:
            self.addLogs("捕获流程结束")
            self.servo.stop()
            self.open_servo_flag = False
            self.set_led_style(self.led3, not self.open_servo_flag)
            self.tc3.write_by_name(f"SiJueShiFu.RepythonX", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"SiJueShiFu.RepythonY", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"SiJueShiFu.RepythonZ", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"SiJueShiFu.RepythonRx", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"SiJueShiFu.RepythonRy", 0, pyads.PLCTYPE_LREAL)
            self.tc3.write_by_name(f"SiJueShiFu.RepythonRz", 0, pyads.PLCTYPE_LREAL)
        else:
            self.open_servo_flag = True
            self.addLogs("捕获流程开始")
            self.set_button_style(self.button3, self.open_servo_flag)
            lambda_gain = np.array([0.6, 0.6, 0.6, 0.0007, 0.0007, 0.0007])
            lambda_gain = np.diag(lambda_gain)
            self.servo = VisualServoThread(self, lambda_gain)
            self.servo.update_pose_signal.connect(self.write_delta)
            self.servo.start_servo()
                    
    
    # 日志显示相关
    def addLogs(self, *args, split=''):
       
        newLog = split.join(args)
        self.logText.appendPlainText(newLog)
       
        print(newLog)


    def add_adsvars(self):
        # 添加要监控的变量
        for i in range(9):
            self.tc3.add_variable(f"GVL.axis[{i+1}].Status.Moving", pyads.PLCTYPE_BOOL, self.value_changed)
            self.tc3.add_variable(f"GVL.axis[{i+1}].NcToPlc.ActVelo", pyads.PLCTYPE_LREAL, self.value_changed)
            self.tc3.add_variable(f"GVL.axis[{i+1}].NcToPlc.ActPos", pyads.PLCTYPE_LREAL, self.value_changed)
            self.tc3.add_variable(f"GVL.axis[{i+1}].NcToPlc.ErrorCode", pyads.PLCTYPE_UDINT, self.value_changed)

        self.tc3.add_variable(f"SiJueShiFu.ReaTwinX", pyads.PLCTYPE_LREAL, self.value_changed)
        self.tc3.add_variable(f"SiJueShiFu.ReaTwinY", pyads.PLCTYPE_LREAL, self.value_changed)
        self.tc3.add_variable(f"SiJueShiFu.ReaTwinZ", pyads.PLCTYPE_LREAL, self.value_changed)
        self.tc3.add_variable(f"SiJueShiFu.ReaTwinRX", pyads.PLCTYPE_LREAL, self.value_changed)
        self.tc3.add_variable(f"SiJueShiFu.ReaTwinRY", pyads.PLCTYPE_LREAL, self.value_changed)
        self.tc3.add_variable(f"SiJueShiFu.ReaTwinRZ", pyads.PLCTYPE_LREAL, self.value_changed)

    # 定义回调函数
    def value_changed(self, name ,value):
        pattern = r'\d+'
        types = name.split(".")[-1]
        try:
            row = int(re.findall(pattern, name)[0])
            if types == "Moving":
                if float(self.table.item(row-1,2).text()) == 0:
                    astr = "停止状态"
                else:
                    astr = "运行状态"
                item_data = QtWidgets.QTableWidgetItem(astr)
                self.table.setItem(row-1,1,item_data)
            elif types == "ActVelo":
                item_data = QtWidgets.QTableWidgetItem(str(round(value,3)))
                self.table.setItem(row-1,2,item_data)
            elif types == "ActPos":
                item_data = QtWidgets.QTableWidgetItem(str(round(value,3)))
                self.table.setItem(row-1,3,item_data)
            elif types == "ErrorCode":
                item_data = QtWidgets.QTableWidgetItem(str(value))
                self.table.setItem(row-1,4,item_data)
        except:
            if types == "ReaTwinX":
                self.line_x.setText(str(round(value,3)))
            elif types == "ReaTwinY":
                self.line_y.setText(str(round(value,3)))
            elif types == "ReaTwinZ":
                self.line_z.setText(str(round(value,3)))
            elif types == "ReaTwinRX":
                self.line_Rx.setText(str(round(value,3)))
            elif types == "ReaTwinRY":
                self.line_Ry.setText(str(round(value,3)))
            elif types == "ReaTwinRZ":
                self.line_Rz.setText(str(round(value,3)))
        

    def update_image(self, img_color):
        # Update the image_label with a new image
        # get image info
        h, w, ch = img_color.shape
        # create QImage from image
        bytes_per_line = ch * w
        convert_to_qt_format = QImage(img_color.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.VisionPictureRGB_2.setPixmap(QPixmap.fromImage(convert_to_qt_format))

    def write_delta(self, delta_world):
        self.tc3.write_by_name(f"SiJueShiFu.RepythonX", delta_world[0], pyads.PLCTYPE_LREAL)
        self.tc3.write_by_name(f"SiJueShiFu.RepythonY", delta_world[1], pyads.PLCTYPE_LREAL)
        self.tc3.write_by_name(f"SiJueShiFu.RepythonZ", delta_world[2], pyads.PLCTYPE_LREAL)
        self.tc3.write_by_name(f"SiJueShiFu.RepythonRx", delta_world[3], pyads.PLCTYPE_LREAL)
        self.tc3.write_by_name(f"SiJueShiFu.RepythonRy", delta_world[4], pyads.PLCTYPE_LREAL)
        self.tc3.write_by_name(f"SiJueShiFu.RepythonRz", delta_world[5], pyads.PLCTYPE_LREAL)
        
