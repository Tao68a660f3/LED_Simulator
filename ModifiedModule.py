import sys
from PyQt5.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSpinBox, QTextEdit
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QPoint, QRect, QPropertyAnimation

class DraggableProportionalTable(QTableWidget):
    # 自定义信号，发送拖拽的起始行和目标行
    rowMoved = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 列宽比例，默认为None（平均分配）
        self.column_ratios = None
        self.min_total_width = 200  # 最小总宽度阈值
        self.initUI()
        
    def initUI(self):
        self.setMouseTracking(False)
        self.viewport().setMouseTracking(False)
        # 设置拖拽属性
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setDragDropMode(QTableWidget.InternalMove)
        
        # 初始化拖拽相关变量
        self.dragged_row = None
        self.dragged_items = None
        
    def resizeEvent(self, event):
        """重写resize事件，按比例调整列宽"""
        super().resizeEvent(event)
        self.adjust_column_widths()
    
    def adjust_column_widths(self):
        """根据比例调整列宽"""
        if self.columnCount() == 0 or not self.column_ratios:
            return
            
        # 计算可用宽度（已经是减去垂直滚动条宽度和行号列宽度）
        available_width = self.viewport().width()
        
        # 确保有足够的宽度
        if available_width < self.min_total_width:
            available_width = self.min_total_width
        
        # 按比例分配列宽
        total_ratio = sum(self.column_ratios)
        for col, ratio in enumerate(self.column_ratios):
            width = int(available_width * ratio / total_ratio)
            self.setColumnWidth(col, width)
    
    def set_column_ratios(self, ratios):
        """设置列宽比例"""
        if len(ratios) != self.columnCount():
            print(f"警告: 比例数量({len(ratios)})与列数({self.columnCount()})不匹配")
            return False
        
        self.column_ratios = ratios
        self.adjust_column_widths()
        return True
    
    def set_min_total_width(self, width):
        """设置最小总宽度阈值"""
        self.min_total_width = width
        self.adjust_column_widths()
    
    # 原有的拖拽方法保持不变
    def dragEnterEvent(self, event):
        self.dragged_row = self.currentRow()
        if self.dragged_row >= 0:
            self.dragged_items = self.getRowContent(self.dragged_row)
        event.accept()
        
    def dropEvent(self, event):
        if self.dragged_row is None:
            return
            
        drop_row = self.rowAt(event.pos().y())
        if drop_row == -1:
            drop_row = self.rowCount() - 1
            
        self.rowMoved.emit(self.dragged_row, drop_row)
        self.dragged_row = None
        self.dragged_items = None
        
    def getRowContent(self, row):
        """获取指定行的所有单元格内容"""
        items = []
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                items.append(item.text())
            else:
                items.append("")
        return items
    
    def add_row(self, data):
        """添加一行数据"""
        row = self.rowCount()
        self.insertRow(row)
        for col, value in enumerate(data):
            self.setItem(row, col, QTableWidgetItem(str(value)))

class SmartWindowBase(QWidget):
    """
    智能吸附窗口基类
    功能：边缘吸附、自动隐藏、鼠标唤醒
    使用方式：继承这个类并添加自定义内容
    """
    
    def __init__(self, width=400, height=300, title="智能窗口"):
        super().__init__()
        
        # 配置参数
        self.adsorb_distance = 25  # 吸附距离
        self.peek_width = 5        # 隐藏露出宽度
        self.hide_delay = 2000     # 隐藏延迟(毫秒)
        self.allow_auto_hide = False  # 是否允许自动隐藏
        
        # 状态变量
        self.is_adsorbed = False
        self.is_hidden = False
        self.adsorb_direction = None
        
        # 计时器
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.auto_hide)
        
        # 防止递归调用和反复横跳
        self.is_adjusting = False
        self.last_adsorb_check_pos = None
        
        # 记录吸附时的位置
        self.adsorbed_position = None
        
        # 鼠标是否在窗口内
        self.mouse_in_window = False
        
        # 拖动相关
        self.dragging = False
        self.drag_start_position = QPoint()

        # 添加拖动状态管理
        self.drag_release_timer = None  # 拖动释放后的防抖定时器
        self.drag_release_delay = 300   # 防抖延迟(毫秒)
        
        # 动画相关
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(300)
        self.animation.finished.connect(self.on_animation_finished)
        
        # 初始化无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setGeometry(100, 100, width, height)
        self.setWindowTitle(title)
        
        self.init_ui()
        self.setup_timers()
        
    def init_ui(self):
        """初始化UI - 子类可以重写此方法添加自定义内容"""
        # 创建布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题栏
        title_layout = QHBoxLayout()
        self.drag_label = QLabel("拖拽区域")
        self.drag_label.setAlignment(Qt.AlignCenter)
        self.drag_label.setStyleSheet("background-color: #e0e0e0; padding: 8px; border: 1px solid #a0a0a0; border-radius: 3px;")
        title_layout.addWidget(self.drag_label)
        main_layout.addLayout(title_layout)
        
        # 控制面板
        control_layout = QVBoxLayout()
        
        # 自动隐藏控制
        hide_layout = QHBoxLayout()
        self.auto_hide_check = QCheckBox("允许自动隐藏")
        self.auto_hide_check.setChecked(self.allow_auto_hide)
        self.auto_hide_check.stateChanged.connect(self.toggle_auto_hide)
        hide_layout.addWidget(self.auto_hide_check)
        control_layout.addLayout(hide_layout)
        
        # 延迟设置
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("隐藏延迟(秒):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 10)
        self.delay_spin.setValue(self.hide_delay // 1000)
        self.delay_spin.valueChanged.connect(self.update_hide_delay)
        delay_layout.addWidget(self.delay_spin)
        control_layout.addLayout(delay_layout)
        
        # 状态显示
        self.status_label = QLabel("状态: 正常显示")
        control_layout.addWidget(self.status_label)
        
        main_layout.addLayout(control_layout)
        self.setLayout(main_layout)
        
    def setup_timers(self):
        """设置定时器"""
        # 鼠标检测定时器
        self.mouse_check_timer = QTimer()
        self.mouse_check_timer.timeout.connect(self.check_mouse_proximity)
        self.mouse_check_timer.start(100)  # 每100ms检查一次
        
    def toggle_auto_hide(self, state):
        """切换自动隐藏功能"""
        self.allow_auto_hide = (state == Qt.Checked)
        # self.update_status(f"自动隐藏: {'开启' if self.allow_auto_hide else '关闭'}")
        if not self.allow_auto_hide and self.hide_timer.isActive():
            self.hide_timer.stop()
            
    def update_hide_delay(self, value):
        """更新隐藏延迟时间"""
        self.hide_delay = value * 1000
        # self.update_status(f"隐藏延迟设置为 {value} 秒")
        
    def mousePressEvent(self, event):
        """鼠标按下事件 - 整个窗口可拖动"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_position = event.globalPos()
            # 停止所有动画和计时器
            self.stop_all_operations()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 整个窗口可拖动"""
        if event.buttons() == Qt.LeftButton and self.dragging:
            delta = event.globalPos() - self.drag_start_position
            self.move(self.pos() + delta)
            self.drag_start_position = event.globalPos()
            event.accept()
            
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            # 拖动结束后检查吸附
            QTimer.singleShot(50, self.check_adsorption)
            event.accept()
            
    def enterEvent(self, event):
        """鼠标进入窗口事件"""
        self.mouse_in_window = True
        if self.is_hidden:
            self.show_window()
        elif self.hide_timer.isActive():
            self.hide_timer.stop()
            
    def leaveEvent(self, event):
        """鼠标离开窗口事件"""
        self.mouse_in_window = False
        # 如果已吸附且允许自动隐藏，启动隐藏计时器
        if self.is_adsorbed and self.allow_auto_hide and not self.is_hidden and not self.dragging:
            self.hide_timer.start(self.hide_delay)
            
    def moveEvent(self, event):
        """窗口移动事件 - 检测吸附"""
        if self.is_adjusting or self.is_hidden or self.dragging:
            return
            
        current_pos = self.pos()
        
        # 防抖机制：避免频繁检测
        if (self.last_adsorb_check_pos and 
            (current_pos - self.last_adsorb_check_pos).manhattanLength() < 5):
            return
            
        self.last_adsorb_check_pos = current_pos
        self.check_adsorption()
        
    def check_adsorption(self):
        """检测是否需要吸附到边缘"""
        if self.is_adjusting or self.is_hidden or self.dragging:
            return
            
        screen_geom = QApplication.primaryScreen().availableGeometry()
        window_geom = self.geometry()  # 无边框模式下geometry和frameGeometry相同
        
        # 计算窗口到屏幕各边的距离
        left_dist = abs(window_geom.left() - screen_geom.left())
        right_dist = abs(window_geom.right() - screen_geom.right())
        top_dist = abs(window_geom.top() - screen_geom.top())
        bottom_dist = abs(window_geom.bottom() - screen_geom.bottom())
        
        # 判断大窗口
        is_large_window = (window_geom.width() >= screen_geom.width() - 2 * self.adsorb_distance or
                          window_geom.height() >= screen_geom.height() - 2 * self.adsorb_distance)
        
        adsorb_directions = []
        
        # 检测各方向吸附条件
        if left_dist <= self.adsorb_distance:
            adsorb_directions.append('left')
        if right_dist <= self.adsorb_distance:
            adsorb_directions.append('right')
        if top_dist <= self.adsorb_distance:
            adsorb_directions.append('top')
        if bottom_dist <= self.adsorb_distance:
            adsorb_directions.append('bottom')
            
        # 大窗口特殊处理
        if is_large_window:
            if len(adsorb_directions) == 1:
                self.perform_adsorption(adsorb_directions[0], screen_geom, window_geom)
            else:
                self.is_adsorbed = False
                self.adsorb_direction = None
            return
            
        # 普通窗口处理 - 选择距离最小的方向
        if adsorb_directions:
            distances = {
                'left': left_dist,
                'right': right_dist,
                'top': top_dist,
                'bottom': bottom_dist
            }
            closest_dir = min(adsorb_directions, key=lambda x: distances[x])
            self.perform_adsorption(closest_dir, screen_geom, window_geom)
        else:
            self.is_adsorbed = False
            self.adsorb_direction = None
            if self.hide_timer.isActive():
                self.hide_timer.stop()
            # self.update_status("正常显示")
                
    def perform_adsorption(self, direction, screen_geom, window_geom):
        """执行吸附操作"""
        if self.is_adjusting:
            return
            
        self.is_adjusting = True
        
        # 计算吸附位置
        if direction == 'left':
            new_x = screen_geom.left()
            new_y = window_geom.y()
        elif direction == 'right':
            new_x = screen_geom.right() - window_geom.width() + 1
            new_y = window_geom.y()
        elif direction == 'top':
            new_x = window_geom.x()
            new_y = screen_geom.top()
        elif direction == 'bottom':
            new_x = window_geom.x()
            new_y = screen_geom.bottom() - window_geom.height() + 1
            
        new_pos = QPoint(new_x, new_y)
        
        # 记录吸附信息
        self.adsorb_direction = direction
        self.adsorbed_position = new_pos
        
        # 使用动画使吸附更平滑
        self.start_animation(new_pos, "adsorb")
        
    def auto_hide(self):
        """自动隐藏窗口"""
        if (not self.allow_auto_hide or not self.is_adsorbed or 
            self.is_hidden or self.mouse_in_window or self.dragging):
            return
            
        screen_geom = QApplication.primaryScreen().availableGeometry()
        self.hide_to_edge(self.adsorb_direction, screen_geom)

    def hide_to_edge(self, direction, screen_geom):
        """隐藏到边缘"""
        if self.is_adjusting:
            return
            
        self.is_adjusting = True
        
        # 记录隐藏前的置顶状态
        self.was_on_top_before_hide = self.windowFlags() & Qt.WindowStaysOnTopHint
        
        # 计算隐藏位置
        window_geom = self.geometry()
        
        if direction == 'left':
            new_x = screen_geom.left() - window_geom.width() + self.peek_width
            new_y = window_geom.y()
        elif direction == 'right':
            new_x = screen_geom.right() - self.peek_width
            new_y = window_geom.y()
        elif direction == 'top':
            new_x = window_geom.x()
            new_y = screen_geom.top() - window_geom.height() + self.peek_width
        elif direction == 'bottom':
            new_x = window_geom.x()
            new_y = screen_geom.bottom() - self.peek_width
            
        new_pos = QPoint(new_x, new_y)

        # 隐藏时强制置顶
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()
        
        # 使用动画隐藏
        self.start_animation(new_pos, "hide")
        
    def start_animation(self, target_pos, animation_type):
        """启动动画"""
        # 停止当前动画
        if self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()
            
        # 设置动画参数
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(target_pos)
        self.animation.setProperty(b"animation_type", animation_type)
        
        # 启动动画
        self.animation.start()
        
    def on_animation_finished(self):
        """动画完成回调"""
        animation_type = self.animation.property(b"animation_type")
        
        if animation_type == "adsorb":
            self.is_adsorbed = True
            # self.update_status(f"已吸附到{self.adsorb_direction}边")
            
            # 启动隐藏计时器
            if self.allow_auto_hide and not self.mouse_in_window and not self.is_hidden:
                self.hide_timer.start(self.hide_delay)
                
        elif animation_type == "hide":
            self.is_hidden = True
            self.on_window_hiden()
            # self.update_status(f"已隐藏到{self.adsorb_direction}边")
            
            # 性能优化：隐藏时停止绘制
            self.setAttribute(Qt.WA_UpdatesDisabled, True)
            
        elif animation_type == "show":
            self.is_hidden = False
            self.on_window_shown()
            # self.update_status(f"从{self.adsorb_direction}边显示")
            
            # 恢复绘制
            self.setAttribute(Qt.WA_UpdatesDisabled, False)
            
            # 激活窗口
            self.raise_()
            self.activateWindow()
            
            # 如果鼠标不在窗口内且允许自动隐藏，重新启动隐藏计时器
            if not self.mouse_in_window and self.allow_auto_hide and self.is_adsorbed:
                self.hide_timer.start(self.hide_delay)
        
        self.is_adjusting = False

    def on_window_shown(self):
        # 当窗口显示时调用的函数，在子类中重写。
        pass

    def on_window_hiden(self):
        # 当窗口隐藏时调用的函数，在子类中重写。
        pass
        
    def check_mouse_proximity(self):
        """检查鼠标是否靠近隐藏的窗口"""
        if not self.is_hidden:
            return
            
        mouse_pos = QApplication.desktop().cursor().pos()
        screen_geom = QApplication.primaryScreen().availableGeometry()
        
        # 检查鼠标是否在隐藏窗口的唤醒区域
        wake_zone = self.get_wake_zone(screen_geom)
        if wake_zone.contains(mouse_pos):
            self.show_window()
            
    def get_wake_zone(self, screen_geom):
        """获取鼠标唤醒区域"""
        wake_width = self.peek_width + 10  # 稍微扩大唤醒区域
        
        if self.adsorb_direction == 'left':
            return QRect(screen_geom.left(), screen_geom.top(), 
                        wake_width, screen_geom.height())
        elif self.adsorb_direction == 'right':
            return QRect(screen_geom.right() - wake_width, screen_geom.top(),
                        wake_width, screen_geom.height())
        elif self.adsorb_direction == 'top':
            return QRect(screen_geom.left(), screen_geom.top(),
                        screen_geom.width(), wake_width)
        elif self.adsorb_direction == 'bottom':
            return QRect(screen_geom.left(), screen_geom.bottom() - wake_width,
                        screen_geom.width(), wake_width)
        else:
            return QRect()
            
    def show_window(self):
        """显示窗口"""
        if not self.is_hidden or not self.adsorbed_position or self.is_adjusting:
            return
            
        self.is_adjusting = True
        
        # 使用动画显示
        self.start_animation(self.adsorbed_position, "show")
        
    def stop_all_operations(self):
        """停止所有操作"""
        if self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()
            
        if self.hide_timer.isActive():
            self.hide_timer.stop()
            
        self.is_adjusting = False
        
    # def update_status(self, message):
    #     """更新状态显示"""
    #     self.status_label.setText(f"状态: {message}")
        
    def closeEvent(self, event):
        """关闭事件 - 清理资源"""
        self.stop_all_operations()
        self.mouse_check_timer.stop()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 使用基类窗口
    base_window = SmartWindowBase()
    base_window.show()
    
    sys.exit(app.exec_())
            