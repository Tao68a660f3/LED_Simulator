from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtCore import pyqtSignal

class DraggableTableWidget(QTableWidget):
    # 自定义信号，发送拖拽的起始行和目标行
    rowMoved = pyqtSignal(int, int)
    
    def __init__(self,parent):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setMouseTracking(False)  # 禁用鼠标追踪
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
        
    def dragEnterEvent(self, event):
        print("dragEnterEvent")
        # 记录被拖拽的行号和内容
        self.dragged_row = self.currentRow()
        self.dragged_items = self.getRowContent(self.dragged_row)
        event.accept()
        
    def dropEvent(self, event):
        if self.dragged_row is None:
            return
            
        # 获取目标行
        drop_row = self.rowAt(event.pos().y())
        if drop_row == -1:
            drop_row = self.rowCount() - 1
            
        # 发送信号
        self.rowMoved.emit(self.dragged_row, drop_row)
        
        # 调用父类方法完成拖拽
        super().dropEvent(event)
        
        # 重置拖拽变量
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