import sys
from PyQt5.QtWidgets import QMainWindow,QApplication,QTableWidgetItem
from Ui_System import Ui_MainWindow  #导入你写的界面类
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtCore import Qt
from control import Control
import faulthandler
from functools import partial
faulthandler.enable()

class MyMainWindow(QMainWindow,Ui_MainWindow): #这里也要记得改
    def __init__(self,parent =None):
        super(MyMainWindow,self).__init__(parent)
        self.setupUi(self)
        
        self.logText.setVisible(True)
        self.logText.setReadOnly(True)
        self.box_motor.addItem("请选择电机")
        self.box_motor.addItems(["手爪电机:b1", "关节电机:a1","关节电机:a2","关节电机:a3","关节电机:a4","关节电机:a5",
                                 "关节电机:a6","关节电机:a7","手爪电机:b2"])
        
        for i in range(1,10):
            if i == 1:
                index = f"b1"
            elif i == 9:
                index = f"b2"
            else:
                index=f"a{i-1}"
            item_data = QTableWidgetItem(index)
            self.table.setItem(i-1,0,item_data)

        # 不可编辑表格
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)   # 禁止编辑
        self.table.setSelectionMode(QAbstractItemView.NoSelection)     # 禁止选中  
        self.table.setFocusPolicy(Qt.NoFocus)                   # 禁止焦点（防止虚线框） 
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.verticalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setSectionsClickable(False)
        self.table.verticalHeader().setHighlightSections(False)
        self.table.verticalHeader().setSectionsClickable(False)
        # 不可编辑的文本框相关
        for line_edit in [self.line_x,self.line_y,self.line_z,
                          self.line_Rx,self.line_Ry,self.line_Rz,
                          self.line_Fx,self.line_Fy,self.line_Fz,
                          self.line_Tx,self.line_Ty,self.line_Tz]:
             line_edit.setReadOnly(True)
       
        # 按钮相关逻辑
        self.control = Control(self)
        # 按钮函数绑定
        self.button_connect.clicked.connect(self.control.open_connect)
        self.button_motor.clicked.connect(self.control.open_motor)
        self.button_switch.clicked.connect(self.control.switch_base)
        self.button_start.clicked.connect(self.control.open_start)
        self.button_forward.clicked.connect(self.control.open_forward)
        self.button_reverse.clicked.connect(self.control.open_reverse)
        self.button_stop.clicked.connect(self.control.open_stop)
        self.button_reset.clicked.connect(self.control.open_reset)
        self.button_zero.clicked.connect(self.control.open_zero)
        self.button_move.clicked.connect(self.control.open_move)


        self.button_servo_align1.clicked.connect(partial(self.control.servo_align,1))
        self.button_linear_plan1.clicked.connect(partial(self.control.linear_plan,1))
        self.button_close_clampA1.clicked.connect(partial(self.control.close_clampA,1))
        self.button_reverse_linear_1.clicked.connect(partial(self.control.reverse_linear,1))
        self.button_joint4_reverse_1.clicked.connect(partial(self.control.joint4_reverse,1))
        self.button_release_clampB1.clicked.connect(partial(self.control.release_clampB,1))

        self.button_servo_align2.clicked.connect(partial(self.control.servo_align,2))
        self.button_linear_plan2.clicked.connect(partial(self.control.linear_plan,2))
        self.button_close_clampA2.clicked.connect(partial(self.control.close_clampA,2))
        self.button_reverse_linear_2.clicked.connect(partial(self.control.reverse_linear,2))
        self.button_joint4_reverse_2.clicked.connect(partial(self.control.joint4_reverse,2))
        self.button_release_clampB2.clicked.connect(partial(self.control.release_clampB,2))

        self.button_servo_align3.clicked.connect(partial(self.control.servo_align,3))
        self.button_linear_plan3.clicked.connect(partial(self.control.linear_plan,3))
        self.button_close_clampA3.clicked.connect(partial(self.control.close_clampA,3))
        self.button_joint4_reverse_3.clicked.connect(partial(self.control.joint4_reverse,3))
        self.log_pos.clicked.connect(self.control.log_position)

        self.mounting4.clicked.connect(self.control.mounting)
        self.button_linear_plan4.clicked.connect(partial(self.control.linear_plan,4))

    # 日志显示
    def addLogs(self, *args, split=''):
       
        newLog = split.join(args)
        self.logText.appendPlainText(newLog)

        print(newLog)
       
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    myWin.show()
    sys.exit(app.exec_())    