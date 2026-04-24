# -------------------------- 末端位姿记录线程 --------------------------
import threading
import time
import datetime
import os
import pyads

class PoseRecordThread(threading.Thread):
    def __init__(self, tc3, parent=None):
        super(PoseRecordThread, self).__init__()
        self.tc3 = tc3  # 传入ADS通信实例，用于读取位姿数据
        self.is_running = False  # 线程运行标志位
        self.record_interval = 0.05  # 采样间隔，默认50ms
        self.file_path = ""
        self.parent = parent
        self.daemon = True
        
    def run(self):
        """线程核心运行方法，持续读取并记录末端位姿数据"""
        self.is_running = True
        # 生成以当前时间命名的txt文件
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.file_path = f"{current_time}_末端位姿数据.txt"
        
        # 打开文件，持续写入数据
        with open(self.file_path, 'a', encoding='utf-8') as f:
            # 写入表头
            f.write("x,y,z,rx,ry,rz")
            while self.is_running:
                try:
                    # 读取末端位姿数据
                    x = self.tc3.read_by_name("crawl1.ReaTwinX", pyads.PLCTYPE_LREAL)
                    y = self.tc3.read_by_name("crawl1.ReaTwinY", pyads.PLCTYPE_LREAL)
                    z = self.tc3.read_by_name("crawl1.ReaTwinZ", pyads.PLCTYPE_LREAL)
                    rx = self.tc3.read_by_name("crawl1.ReaTwinRX", pyads.PLCTYPE_LREAL)
                    ry = self.tc3.read_by_name("crawl1.ReaTwinRY", pyads.PLCTYPE_LREAL)
                    rz = self.tc3.read_by_name("crawl1.ReaTwinRZ", pyads.PLCTYPE_LREAL)
                    
                    # 按格式拼接数据：保留4位小数，逗号分隔，一行一条
                    data_line = f"{round(x,4)},{round(y,4)},{round(z,4)},{round(rx,4)},{round(ry,4)},{round(rz,4)}\n"
                    f.write(data_line)
                    f.flush()  # 立即写入磁盘，防止数据缓存丢失
                    
                    # 采样间隔
                    time.sleep(self.record_interval)
                except Exception as e:
                    # 捕获异常，防止线程崩溃
                    print(f"位姿数据记录异常: {str(e)}")
                    time.sleep(self.record_interval)
                    continue
        # 线程结束提示
        print(f"位姿数据记录结束，文件保存至: {self.file_path}")

    def stop_record(self):
        """停止线程，外部调用此方法即可"""
        self.is_running = False
