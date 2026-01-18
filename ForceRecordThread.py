# -------------------------- 力数据记录线程 (直接复制到你的代码中即可) --------------------------
import threading
import time
import datetime
import os
import pyads

class ForceRecordThread(threading.Thread):
    def __init__(self, tc3, parent=None):
        super(ForceRecordThread, self).__init__()
        self.tc3 = tc3  # 传入你的ADS通信实例，用于读取力数据
        self.is_running = False  # 线程运行标志位
        self.record_interval = 0.05  # 采样间隔，默认50ms，可自行修改(如0.01=10ms)
        self.file_path = ""
        self.parent = parent
        self.daemon = True
        
    def run(self):
        """线程核心运行方法，持续读取并记录力数据"""
        self.is_running = True
        # 1. 生成以当前时间命名的txt文件 (格式: 2026-01-18_20-58-30_力传感器数据.txt)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.file_path = f"{current_time}_力传感器数据.txt"
        
        # 2. 打开文件，持续写入数据
        with open(self.file_path, 'a', encoding='utf-8') as f:
            # 写入表头，方便识别列名
            f.write("fx,fy,fz,tx,ty,tz\n")
            while self.is_running:
                try:
                    # 读取六维力数据 fx/fy/fz 力分量  tx/ty/tz 力矩分量
                    fx = self.tc3.read_by_name("MAIN.FX1" if self.parent.switch_on is False else "MAIN.FX2", pyads.PLCTYPE_REAL)
                    fy = self.tc3.read_by_name("MAIN.FY1" if self.parent.switch_on is False else "MAIN.FY2", pyads.PLCTYPE_REAL)
                    fz = self.tc3.read_by_name("MAIN.FZ1" if self.parent.switch_on is False else "MAIN.FZ2", pyads.PLCTYPE_REAL)
                    tx = self.tc3.read_by_name("MAIN.TX1" if self.parent.switch_on is False else "MAIN.TX2", pyads.PLCTYPE_REAL)
                    ty = self.tc3.read_by_name("MAIN.TY1" if self.parent.switch_on is False else "MAIN.TY2", pyads.PLCTYPE_REAL)
                    tz = self.tc3.read_by_name("MAIN.TZ1" if self.parent.switch_on is False else "MAIN.TZ2", pyads.PLCTYPE_REAL)
                    
                    # 按格式拼接数据：保留4位小数，逗号分隔，一行一条
                    data_line = f"{round(fx,4)},{round(fy,4)},{round(fz,4)},{round(tx,4)},{round(ty,4)},{round(tz,4)}\n"
                    f.write(data_line)
                    f.flush()  # 立即写入磁盘，防止数据缓存丢失
                    
                    # 采样间隔，可根据需求调整
                    time.sleep(self.record_interval)
                except Exception as e:
                    # 捕获异常，防止线程崩溃，不影响主线程
                    print(f"力数据记录异常: {str(e)}")
                    time.sleep(self.record_interval)
                    continue
        # 线程结束提示
        print(f"力数据记录结束，文件保存至: {self.file_path}")

    def stop_record(self):
        """停止线程，外部调用此方法即可"""
        self.is_running = False
        #self.join()  # 等待线程完全结束