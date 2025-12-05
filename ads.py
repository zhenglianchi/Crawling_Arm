import pyads
import threading
import time
from PyQt5.QtCore import QThread, pyqtSignal

class TwinCat3_ADSserver(QThread):
    # Signal to send data back to the main thread
    moving_signal = pyqtSignal(str, bool)
    velo_signal = pyqtSignal(str, float)
    pos_signal = pyqtSignal(str, float)
    error_signal = pyqtSignal(str, int)

    eeposx_signal = pyqtSignal(str, float)
    eeposy_signal = pyqtSignal(str, float)
    eeposz_signal = pyqtSignal(str, float)
    eeposrx_signal = pyqtSignal(str, float)
    eeposry_signal = pyqtSignal(str, float)
    eeposrz_signal = pyqtSignal(str, float)

    fx_signal = pyqtSignal(str, float)
    fy_signal = pyqtSignal(str, float)
    fz_signal = pyqtSignal(str, float)
    tx_signal = pyqtSignal(str, float)
    ty_signal = pyqtSignal(str, float)
    tz_signal = pyqtSignal(str, float)

    def __init__(self, ip="192.168.217.176.1.1", amsNetIdTarget=pyads.PORT_TC3PLC1):
        '''
        type ip: str
        type amsNetIdTarget: pyads.PORT_xxx
        5.108.90.221.1.1
        127.0.0.1.1.1
        '''
        super().__init__()
        self.ip = ip
        self.amsNetIdTarget = amsNetIdTarget
        # 线程相关属性
        self.running = False
        self.lock = threading.Lock()
        self.variables = {}  # 存储要监控的变量 {name: (type, callback)}

    def read_by_name(self, name, var_type):
        '''
        type name: str
        type var_type: pyads.PLCTYPE_xxx; example:pyads.PLCTYPE_INT
        '''
        return self.plc.read_by_name(name, var_type)
    
    def write_by_name(self, name, value, var_type):
        '''
        type name: str
        type value: int, float, str, bool
        type var_type: pyads.PLCTYPE_xxx; example:pyads.PLCTYPE_INT
        '''
        self.plc.write_by_name(name, value, var_type)

    def add_variable(self, name, var_type, callback=None):
        """添加要监控的变量"""
        with self.lock:
            self.variables[name] = (var_type, callback)

    def remove_variable(self, name):
        """移除监控变量"""
        with self.lock:
            if name in self.variables:
                del self.variables[name]

    def run(self):
        """线程主循环"""
        self.running = True
        while self.running:
            try:
                # 复制当前变量列表避免遍历时修改
                with self.lock:
                    current_vars = self.variables.copy()

                # 遍历并读取所有变量
                for name, (var_type, callback) in current_vars.items():
                    types = name.split(".")[-1]
                    value = self.read_by_name(name, var_type)
                    if types == "Moving":
                        self.moving_signal.emit(name, value)
                    elif types == "ActVelo":
                        self.velo_signal.emit(name, value)
                    elif types == "ActPos":
                        self.pos_signal.emit(name, value)
                    elif types == "ErrorCode":
                        self.error_signal.emit(name, value)
                    elif types == "ReaTwinX":
                        self.eeposx_signal.emit(name, value)
                    elif types == "ReaTwinY":
                        self.eeposy_signal.emit(name, value)
                    elif types == "ReaTwinZ":
                        self.eeposz_signal.emit(name, value)
                    elif types == "ReaTwinRX":
                        self.eeposrx_signal.emit(name, value)
                    elif types == "ReaTwinRY":
                        self.eeposry_signal.emit(name, value)
                    elif types == "ReaTwinRZ":
                        self.eeposrz_signal.emit(name, value)
                    elif types == "fx":
                        self.fx_signal.emit(name, value)
                    elif types == "fy":
                        self.fy_signal.emit(name, value)
                    elif types == "fz":
                        self.fz_signal.emit(name, value)
                    elif types == "tx":
                        self.tx_signal.emit(name, value)
                    elif types == "ty":
                        self.ty_signal.emit(name, value)
                    elif types == "tz":
                        self.tz_signal.emit(name, value)
                    else:
                        print("读取到不存在的变量")
                
                # 更新间隔（可根据需要调整）
                time.sleep(0.01)
                
            except pyads.ADSError as e:
                print(f"ADS通信错误: {e}")
                time.sleep(1)  # 出错后等待重试
            except Exception as e:
                print(f"未知错误: {e}")
                break

    def connect(self):
        """连接到TwinCAT3 PLC"""
        self.plc = pyads.Connection(self.ip, self.amsNetIdTarget)
        self.plc.open()
        print("已连接到TwinCAT3 PLC")

    def close(self):
        """断开TwinCAT3 PLC"""
        self.plc.close()
        print("已断开与TwinCAT3 PLC")

    def start_monitoring(self):
        """Start the ADS communication thread"""
        if not self.isRunning():
            self.start()
            print("ADS 变量监控线程已启动")

    def stop_monitoring(self):
        """Stop the ADS communication thread"""
        self.running = False
        self.quit()
        self.wait()
        print("ADS 变量监控线程已停止")
