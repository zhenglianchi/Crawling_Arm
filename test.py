import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QFrame, QLabel
)
from PyQt5.QtCore import Qt

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("导航栏 + 功能按钮示例")
        self.resize(800, 600)

        # 主布局：水平布局（左导航 + 右内容）
        main_layout = QHBoxLayout(self)

        # 左侧导航栏
        nav_layout = QVBoxLayout()
        nav_layout.setAlignment(Qt.AlignTop)

        # 导航按钮配置
        self.nav_config = [
            {"name": "首页", "buttons": ["刷新", "搜索", "新建"]},
            {"name": "设置", "buttons": ["主题", "语言", "通知", "保存"]},
            {"name": "用户", "buttons": ["登录", "注册", "退出"]},
            {"name": "帮助", "buttons": ["文档", "反馈", "关于"]}
        ]

        self.nav_buttons = []
        for i, config in enumerate(self.nav_config):
            btn = QPushButton(config["name"])
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # 默认选中第一个
        self.nav_buttons[0].setChecked(True)

        # 右侧内容区域
        self.stacked_widget = QStackedWidget()

        # 为每个页面创建按钮组
        for config in self.nav_config:
            page = self.create_button_page(config["buttons"])
            self.stacked_widget.addWidget(page)

        # 添加到主布局
        nav_frame = QFrame()
        nav_frame.setLayout(nav_layout)
        nav_frame.setFixedWidth(150)

        main_layout.addWidget(nav_frame)
        main_layout.addWidget(self.stacked_widget)

    def create_button_page(self, button_names):
        """创建包含多个按钮的页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignTop)  # 按钮靠上对齐

        # 添加标题（可选）
        title = QLabel(f"功能区: {button_names[0] if button_names else ''}")
        title.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(title)

        # 创建功能按钮
        for name in button_names:
            btn = QPushButton(name)
            btn.setFixedHeight(40)
            # 这里可以连接具体功能
            btn.clicked.connect(lambda checked, n=name: self.handle_function_button(n))
            layout.addWidget(btn)

        layout.addStretch()  # 剩余空间推到下方
        return page

    def switch_page(self, index):
        """切换页面并更新按钮选中状态"""
        for btn in self.nav_buttons:
            btn.setChecked(False)
        self.nav_buttons[index].setChecked(True)
        self.stacked_widget.setCurrentIndex(index)

    def handle_function_button(self, name):
        """处理功能按钮点击事件"""
        print(f"点击了功能按钮: {name}")
        # 这里可以添加具体逻辑，比如弹窗、执行操作等


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())