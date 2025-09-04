from PyQt5.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem
from PyQt5.QtCore import pyqtSignal

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