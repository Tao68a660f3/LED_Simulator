import sys, os, ast, copy, datetime, base64, io
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QMainWindow, QAbstractItemView, QTableWidgetItem, QHeaderView, QFileDialog, QPushButton, QLabel, QColorDialog, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon, QTextCharFormat, QFont
from PyQt5.QtCore import pyqtSignal, Qt, QCoreApplication

from BmpCreater import FontManager, BmpCreater
from ControlPanel import Ui_ControlPanel
from NewALine import Ui_NewALine
from SelfDefineScreenDialog import Ui_SelfDefineScreen
from ScreenInfo import *
from LineInfo import *
from LedScreenModule import *
from About import *
from ColorMultiLine import *
from ProgSettings import *

#适配高分辨率
# QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

version = "体验版"
release_date = "20250216"

# 屏幕尺寸相关信息
pointKindDict = {"(6,6)":"midSize","(8,8)":"bigSize","(8,12)":"bigSizeScaled","(6,8)":"midSizeScaled68","(8,10)":"midSizeScaled810","(3,3)":"miniSize","(4,4)":"smallSize","(4,6)":"smallSizeScaled"}
ledTypes = [i for i in pointKindDict.keys()]
scales = [ast.literal_eval(i) for i in ledTypes]

screenLink = {"前路牌":"frontScreen","后路牌":"backScreen","前侧路牌":"frontSideScreen","后侧路牌":"backSideScreen"}


class AboutWindow(QWidget,Ui_Form):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.winsize = [500,300]
        self.setMinimumSize(self.winsize[0], self.winsize[1])
        self.offset = 3
        self.scnpsize = [144,16]
        self.pnum = [self.scnpsize[0]+2*self.offset,self.scnpsize[1]+2*self.offset]
        self.img = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("关于")
        self.set_version()
        self.create_img()
        self.resize(self.winsize[0],self.winsize[1])

    def set_version(self):
        self.label_Version.setFont(QFont('宋体', 18))
        self.label_Version.setText(f"关于LED模拟器{version}")
        self.label_Date.setText(f"发布日期：{release_date}")

    def create_img(self):
        im_base64 = "Qk1+AQAAAAAAAD4AAAAoAAAAiAAAABAAAAABAAEAAAAAAEABAADEDgAAxA4AAAIAAAACAAAAAAAAAP/////z+///1/t/7////+n733/BBwAAAP3xuAPZ8b7X////7vGvvd13AAAA/vfXud7Pvvf////vT+3d3XcAAAB+7++/3z/e9////++/7OvddwAAALtf77/ef973AQEH4AHtdwEBAAAA21/rt92/3veZmZNvv+23z+cAAADXv+mr27vAB52dmawHLffznwAAAO+/6rvYA973n5+ZqffN9/1/AAAA17/rO9u73vefl5nEB+X3AAEAAADXvwu7W7ve95+Hmc336ff+6wAAALm3+7ubu8AHn5eZ7APt1/7fAAAAuvv7u9gD3vefnZkC5wGXwQcAAAD7A+u737/e95+Zk+7v7bfddwAAAAN/2YHgAd73DwEH4AHvd913AAAA/3++e++7wAP////u6+/33XcAAAD/f///77//9////+7v7//BBwAAAA=="
        # 将base64字符串转换为字节
        img_data = base64.b64decode(im_base64)
        # 创建字节流
        buffer = io.BytesIO(img_data)
        # 打开图片
        self.img = Image.open(buffer)
        self.img = self.img.point(lambda x: not x)

    def resizeEvent(self, event):
        newSize = event.size()
        self.winsize = [newSize.width(),newSize.height()]
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setPen(Qt.NoPen)
        self.drawScreen(qp)
        qp.end()

    def drawScreen(self,qp):
        # print(self.winsize)
        psize = 3
        baseColor = QColor(60, 60, 60)
        frontColor = QColor(255, 255, 60)
        area = [int(0.8*self.winsize[0]),int(0.75*self.winsize[1])]

        if area[0]/area[1] >= self.pnum[0]/self.pnum[1]:
            psize = int(area[1]/self.pnum[1])
        else:
            psize = int(area[0]/self.pnum[0])
        if psize < 3:
            psize = 3

        d = int(psize * 0.8)

        w = psize*self.pnum[0]
        h = psize*self.pnum[1]

        xp = int((self.winsize[0] - w) * 0.5)
        yp = int((self.winsize[1] - h) * 0.4)

        offset = psize*self.offset

        xpos = int(0.5 * (self.scnpsize[0] - self.img.width))
        ypos = int(0.5 * (self.scnpsize[1] - self.img.height))

        qp.setBrush(QColor(15,15,15))
        qp.drawRect(xp,yp,w,h)
        qp.setBrush(QColor(30,30,30))
        qp.drawRect(xp+offset,yp+offset,w-2*offset,h-2*offset)

        for y in range(self.scnpsize[1]):
            for x in range(self.scnpsize[0]):
                if y - ypos in range(self.img.height) and x - xpos in range(self.img.width):
                    color = self.img.getpixel((x-xpos,y-ypos))
                else:
                    color = 0
                if color != 0:
                    qp.setBrush(frontColor)
                else:
                    qp.setBrush(baseColor)
                qp.drawEllipse(xp+x*psize+offset, yp+y*psize+offset, d, d+1)




        

class NewALine(QDialog,Ui_NewALine):
    dataEntered = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.initUI()
        self.setWindowTitle("LED模拟器 新建线路")
        self.setModal(True)

    def initUI(self):
        self.buttonBox.accepted.connect(self.onOk)
        colors = ["彩色屏幕","单色屏幕"]
        self.combo_Preset.addItems(["自定义","北京公交","普通"])
        self.combo_FlushRate.addItems(["60","54","50","48","30","24","18","15"])
        self.chk_FrontScreen.setChecked(True)
        self.chk_FrontScreen.setEnabled(False)
        colorCombo = [self.combo_FrontColor,self.combo_BackColor,self.combo_FrontSideColor,self.combo_BackSideColor]
        widthSpin = [self.spin_FrontWidth,self.spin_BackWidth,self.spin_FrontSideWidth,self.spin_BackSideWidth]
        heightSpin = [self.spin_FrontHeight,self.spin_BackHeight,self.spin_FrontSideHeight,self.spin_BackSideHeight]
        ledTypeCombo = [self.combo_FLedTyoe,self.combo_BLedTyoe,self.combo_FSLedTyoe,self.combo_BSLedTyoe]
        for combo in colorCombo:
            combo.addItems(colors)
        for combo in ledTypeCombo:
            combo.addItems(ledTypes)
        for spin in widthSpin:
            spin.setMaximum(512)
            spin.setMinimum(16)
            spin.setValue(224)
        for spin in heightSpin:
            spin.setMaximum(256)
            spin.setMinimum(16)
            spin.setValue(32)

        self.combo_Preset.currentTextChanged.connect(self.set_preset_argv)

    def set_preset_argv(self):
        colorCombo = [self.combo_FrontColor,self.combo_BackColor,self.combo_FrontSideColor,self.combo_BackSideColor]
        widthSpin = [self.spin_FrontWidth,self.spin_BackWidth,self.spin_FrontSideWidth,self.spin_BackSideWidth]
        heightSpin = [self.spin_FrontHeight,self.spin_BackHeight,self.spin_FrontSideHeight,self.spin_BackSideHeight]
        ledTypeCombo = [self.combo_FLedTyoe,self.combo_BLedTyoe,self.combo_FSLedTyoe,self.combo_BSLedTyoe]
        if self.combo_Preset.currentText() == "北京公交":
            for combo in colorCombo:
                combo.setCurrentText("单色屏幕")
                combo.setEnabled(False)
            for combo in ledTypeCombo[:2]:
                combo.setEnabled(False)
                combo.setCurrentText("(6,6)")
            for combo in ledTypeCombo[2:]:
                combo.setEnabled(False)
                combo.setCurrentText("(8,8)")
            for spin in widthSpin[:2]:
                spin.setValue(224)
            for spin in widthSpin[2:]:
                spin.setValue(128)
            for spin in heightSpin[:2]:
                spin.setValue(32)
            for spin in heightSpin[2:]:
                spin.setValue(16)
        elif self.combo_Preset.currentText() == "普通":
            for combo in colorCombo:
                combo.setCurrentText("单色屏幕")
                combo.setEnabled(False)
            for combo in ledTypeCombo[:2]:
                combo.setCurrentText("(6,6)")
                combo.setEnabled(False)
            for combo in ledTypeCombo[2:]:
                combo.setCurrentText("(8,8)")
                combo.setEnabled(False)
            for spin in widthSpin[:2]:
                spin.setValue(160)
            for spin in widthSpin[2:]:
                spin.setValue(128)
            for spin in heightSpin[:2]:
                spin.setValue(24)
            for spin in heightSpin[2:]:
                spin.setValue(16)
        else:
            for combo in colorCombo:
                combo.setCurrentText("彩色屏幕")
                combo.setEnabled(True)
            for combo in ledTypeCombo[:2]:
                combo.setCurrentText("(6,6)")
                combo.setEnabled(True)
            for combo in ledTypeCombo[2:]:
                combo.setCurrentText("(6,6)")
                combo.setEnabled(True)
            for spin in widthSpin[:2]:
                spin.setValue(224)
            for spin in widthSpin[2:]:
                spin.setValue(224)
            for spin in heightSpin[:2]:
                spin.setValue(32)
            for spin in heightSpin[2:]:
                spin.setValue(32)

    def onOk(self):
        lineName = self.lineEdit.text()
        preset = self.combo_Preset.currentText()
        flush = int(self.combo_FlushRate.currentText())
        ledTypeCombo = [self.combo_FLedTyoe,self.combo_BLedTyoe,self.combo_FSLedTyoe,self.combo_BSLedTyoe]
        scale = [item.currentIndex() for item in ledTypeCombo]
        f_enabled = self.chk_FrontScreen.isChecked()
        f_color = "RGB" if self.combo_FrontColor.currentText() == "彩色屏幕" else "1"
        f_w = self.spin_FrontWidth.value()
        f_h = self.spin_FrontHeight.value()
        f_s = scales[scale[0]]
        b_enabled = self.chk_BackScreen.isChecked()
        b_color = "RGB" if self.combo_BackColor.currentText() == "彩色屏幕" else "1"
        b_w = self.spin_BackWidth.value()
        b_h = self.spin_BackHeight.value()
        b_s = scales[scale[1]]
        fs_enabled = self.chk_FrontSideScreen.isChecked()
        fs_color = "RGB" if self.combo_FrontSideColor.currentText() == "彩色屏幕" else "1"
        fs_w = self.spin_FrontSideWidth.value()
        fs_h = self.spin_FrontSideHeight.value()
        fs_s = scales[scale[2]]
        bs_enabled = self.chk_BackSideScreen.isChecked()
        bs_color = "RGB" if self.combo_BackSideColor.currentText() == "彩色屏幕" else "1"
        bs_w = self.spin_BackSideWidth.value()
        bs_h = self.spin_BackSideHeight.value()
        bs_s = scales[scale[3]]
        ret = [lineName,preset,flush,[f_enabled,f_color,f_w,f_h,f_s],[b_enabled,b_color,b_w,b_h,b_s],[fs_enabled,fs_color,fs_w,fs_h,fs_s],[bs_enabled,bs_color,bs_w,bs_h,bs_s]]
        self.dataEntered.emit(ret)
        self.accept()

class SelfDefineLayout(QDialog,Ui_SelfDefineScreen):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.initUI()

    def initUI(self):
        self.setModal(True)
        self.setWindowTitle("选择要添加的屏幕")
        self.combo_Layout.addItems(["更改屏幕","水平布局","垂直布局"])
        self.combo_PointKind.addItems(ledTypes)

        self.combo_PointKind.currentTextChanged.connect(self.can_w_h)
        self.combo_Layout.currentTextChanged.connect(self.can_w_h)

    def set_value(self, pn=[0,0], ps=[0,0]):
        self.pn = pn
        self.ps = ps
        self.combo_PointKind.setCurrentText(f"({ps[0]},{ps[1]})")

    def can_w_h(self):
        pointKind = self.combo_PointKind.currentText()[1:-1].split(",")
        pointScale = [int(pointKind[0]),int(pointKind[1])]
        can_w = int(self.pn[0]*self.ps[0]/pointScale[0])
        can_h = int(self.pn[1]*self.ps[1]/pointScale[1])
        self.lab_AvailWidth.setText(str(can_w))
        self.lab_AvailHeight.setText(str(can_h))
        self.spin_SetWidth.setMinimum(4)
        self.spin_SetHeight.setMinimum(4)
        self.spin_SetWidth.setMaximum(can_w)
        self.spin_SetHeight.setMaximum(can_h)
        self.spin_SetWidth.setValue(can_w)
        self.spin_SetHeight.setValue(can_h)
        if self.combo_Layout.currentText() == "更改屏幕":
            self.spin_SetWidth.setEnabled(False)
            self.spin_SetHeight.setEnabled(False)
        else:
            if self.combo_Layout.currentText() == "水平布局":
                self.spin_SetWidth.setEnabled(True)
                self.spin_SetHeight.setEnabled(False)
            if self.combo_Layout.currentText() == "垂直布局":
                self.spin_SetWidth.setEnabled(False)
                self.spin_SetHeight.setEnabled(True)

class ColorMultiLine(QDialog,Ui_ColorMultiLine):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.initUI()
        self.text = ""
        self.multiLine = False
        self.lineSpace = 0
        self.colorMode = "1"
        self.richText = [False,False]  # 第一项：富文本 第二项：文本是否有背景

    def initUI(self):
        self.setWindowTitle("设置字符串颜色及多行")
        self.setModal(True)
        self.textEdit.setStyleSheet("background-color: black; color: white")

        default_format = QTextCharFormat()
        default_format.setForeground(QColor("#ffffffff"))
        default_format.setBackground(QColor("#ff000000"))
        self.textEdit.setCurrentCharFormat(default_format)

        self.point_spinBox.setMaximum(5)
        self.point_spinBox.setMinimum(-5)
        self.point_spinBox.setValue(1)

    def connect_signal(self):
        self.foreground_btn.clicked.connect(self.setTextColor)
        self.background_btn.clicked.connect(self.setBackgroundColor)
        self.checkBox_multiLine.stateChanged.connect(self.ui_value_changed)
        self.checkBox_bgcolor.stateChanged.connect(self.ui_value_changed)
        self.point_spinBox.valueChanged.connect(self.ui_value_changed)
        # print("reconnected")

    def disconnect_signal(self):
        try:
            self.foreground_btn.clicked.disconnect(self.setTextColor)
            self.background_btn.clicked.disconnect(self.setBackgroundColor)
            self.checkBox_multiLine.stateChanged.disconnect(self.ui_value_changed)
            self.checkBox_bgcolor.stateChanged.disconnect(self.ui_value_changed)
            self.point_spinBox.valueChanged.disconnect(self.ui_value_changed)
        except Exception as e:
            print("disconnect_signal: ", e)

    def set_value(self,text = "", multiLine = False, lineSpace = 1,colorMode = "1", richText = [False,False]):
        self.text = text
        self.multiLine = multiLine
        self.lineSpace = lineSpace
        self.colorMode = colorMode
        self.richText = richText

        self.set_ui_value()
        self.set_textEditor()

    def set_ui_value(self):
        self.disconnect_signal()
        # print("set_ui_value: ", self.multiLine,self.richText,self.lineSpace)

        self.checkBox_multiLine.setChecked(self.multiLine)
        self.checkBox_bgcolor.setChecked(self.richText[1])
        self.point_spinBox.setEnabled(self.multiLine)
        self.background_btn.setEnabled(self.richText[1])
        self.point_spinBox.setValue(self.lineSpace)

        if self.colorMode == "1":
            self.checkBox_bgcolor.setEnabled(False)
            self.foreground_btn.setEnabled(False)
            self.background_btn.setEnabled(False)

        QTimer.singleShot(0, self.connect_signal)
        
    def ui_value_changed(self):
        self.multiLine = self.checkBox_multiLine.isChecked()
        self.richText[1] = self.checkBox_bgcolor.isChecked()
        self.lineSpace = self.point_spinBox.value()

        # print("ui_value_changed: ", self.multiLine,self.richText,self.lineSpace)

        self.set_ui_value()
        # self.set_textEditor()

    def set_textEditor(self):
        cursor = self.textEdit.textCursor()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#ffffffff"))
        fmt.setBackground(QColor("#00000000"))

        if self.colorMode == "1":   
            self.textEdit.clear()         
            cursor.insertText(self.text, fmt)
            # self.textEdit.setEnabled(False)  # 单色也应该可使用文本框添加换行、编辑等，因此注释掉这行代码

        if self.colorMode == "RGB":
            if self.richText[0]:
                try:
                    data = ast.literal_eval(self.text)
                    self.textEdit.clear()
                    for char_data in data:
                        char = char_data['char']                    
                        cursor.movePosition(cursor.End)
                        foreground = QColor(char_data['foreground'])
                        fmt.setForeground(foreground)
                        if char_data['background'] == "0" or not self.richText[1]:
                            background = QColor("#00000000")
                        else:
                            background = QColor(char_data['background'])
                        fmt.setBackground(background)
                        cursor.insertText(char, fmt)
                except Exception as e:
                    print("set_textEditor,", e)
            else:
                self.textEdit.clear()
                cursor.insertText(self.text, fmt)

    def setTextColor(self):
        self.richText[0] = True
        color = QColorDialog.getColor(
            initial=Qt.white,
            options=QColorDialog.ShowAlphaChannel
        )
        if color.isValid():
            cursor = self.textEdit.textCursor()
            fmt = QTextCharFormat()
            # 使用QBrush来保持透明度信息
            brush = color.toRgb()  # 确保颜色是RGB格式
            fmt.setForeground(brush)
            cursor.mergeCharFormat(fmt)

    def setBackgroundColor(self):
        color = QColorDialog.getColor(
            initial=Qt.white,
            options=QColorDialog.ShowAlphaChannel
        )
        if color.isValid():
            cursor = self.textEdit.textCursor()
            fmt = QTextCharFormat()
            brush = color.toRgb()
            fmt.setBackground(brush)
            cursor.mergeCharFormat(fmt)

    def translate_to_str(self):
        txt = self.textEdit.toPlainText()
        if self.richText[0]:
            data = []
            cursor = self.textEdit.textCursor()
            cursor.select(cursor.Document)
            text = cursor.selectedText()
            for i in range(len(text)):
                cursor.setPosition(i)
                cursor.movePosition(cursor.Right, cursor.KeepAnchor, 1)
                char_format = cursor.charFormat()
                if self.richText[1]:
                    char_data = {
                        'char': text[i],
                        'foreground': char_format.foreground().color().name(QColor.HexArgb),
                        'background': char_format.background().color().name(QColor.HexArgb)
                    }
                else:
                    char_data = {
                        'char': text[i],
                        'foreground': char_format.foreground().color().name(QColor.HexArgb),
                        'background': '0'
                    }
                data.append(char_data)
            # 催化重整，把颜色，背景色一样的字符合成一个字符串
            s_d = []
            for d in data:
                if len(s_d) >= 1:
                    if d['foreground'] == s_d[-1]['foreground'] and d['background'] == s_d[-1]['background']:
                        s_d[-1]['char'] += d['char']
                    else:
                        s_d.append(d)
                else:
                    s_d.append(d)

            colorstr = str(s_d)
            return colorstr
        else:
            return txt

    def get_edit_result(self):
        self.text = self.translate_to_str()
        # print("get_edit_result: ", self.text)

        return [self.text, self.multiLine, self.lineSpace, self.richText]

class ProgramSettings(QDialog,Ui_ProgSet):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.initUI()
        self.Parent = parent
        self.unitCount = 0

        self.backgroundDescribeText = ""      # noBackground, None, colorBackground((r,g,b)), colorMask((r,g,b))
                                              # imgBackground("img_filename(not dir)","fillMode"), videoBackground("video_filename(not dir)","fillMode", vol)
                                              # imgMask("img_filename(not dir)","fillMode"), videoMask("video_filename(not dir)","fillMode", vol)
        self.triggerList = []
        self.ProgScreenSetting = {
            "background" : "noBackground",
            "trigger" : [],      # 原先的触发器键名拼写和内容都设置错误，已重新修改    # 二次改设计, 单个触发器改为 {"u" : -1 , "c" : -1 , "to" : 1}
            "inherit" : 0,
        }

    def initUI(self):
        self.setModal(True)
        self.setWindowTitle("路牌节目设置（实验）")

        # tab 0
        self.comboBox_mode.addItems(["纯色背景","图片背景",])#"视频背景"])
        self.comboBox_fill.addItems(["平铺","居中","填充","拉伸","适应"])  # 0123
        self.spinBox.setMaximum(100)
        self.spinBox.setMinimum(0)
        self.label_bgDescribe.setText("")

        # tab 1
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)    #设置表格的选取方式是行选取
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)    #设置选取方式为单个选取
        self.tableWidget.setHorizontalHeaderLabels(["屏幕分区","重复次数","跳转至"])   #设置行表头
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)  #始终禁止编辑
        self.tableWidget.verticalHeader().setDefaultSectionSize(18)
        self.spin_Unit.setMinimum(1)
        self.spin_Unit.setMaximum(1)
        self.spin_Count.setMinimum(1)
        self.spin_Count.setMaximum(65535)
        self.spin_Goto.setMinimum(1)
        self.spin_Goto.setMaximum(65535)
        self.tableWidget.rowMoved.connect(self.onRowMoved)

    def connect_signal(self):
        self.checkBox_enableBg.stateChanged.connect(self.onBgEnabledChanged)
        self.checkBox_mask.stateChanged.connect(self.onMaskChanged)
        self.pushButton.clicked.connect(self.set_background)
        self.comboBox_mode.currentIndexChanged.connect(self.onModeChanged)
        self.comboBox_fill.currentIndexChanged.connect(self.onFillChanged)
        
        self.pushButton_Add.clicked.connect(self.addTrigger)
        self.pushButton_Delete.clicked.connect(self.deleteTrigger)
        self.chk_abs.stateChanged.connect(self.onAbstChanged)

        self.tableWidget.itemSelectionChanged.connect(self.onSelectionChanged)

    def disconnect_signal(self):
        try:
            self.checkBox_enableBg.stateChanged.disconnect(self.onBgEnabledChanged)
            self.checkBox_mask.stateChanged.disconnect(self.onMaskChanged)
            self.pushButton.clicked.disconnect(self.set_background)
            self.comboBox_mode.currentIndexChanged.disconnect(self.onModeChanged)
            self.comboBox_fill.currentIndexChanged.disconnect(self.onFillChanged)

            self.pushButton_Add.clicked.disconnect(self.addTrigger)
            self.pushButton_Delete.clicked.disconnect(self.deleteTrigger)
            self.chk_abs.stateChanged.disconnect(self.onAbstChanged)

            self.tableWidget.itemSelectionChanged.disconnect(self.onSelectionChanged)
        except Exception as e:
            print("disconnect_signal: ", e)

    def set_ui_enabled(self,enabled):
        self.comboBox_mode.setEnabled(enabled)
        self.comboBox_fill.setEnabled(enabled)
        self.pushButton.setEnabled(enabled)
        self.checkBox_mask.setEnabled(enabled)
        self.spinBox.setEnabled(enabled)
    
    def show_tgTable(self):
        colname = ["u","c","to"]
        self.tableWidget.setRowCount(0)
        for row in range(len(self.triggerList)):
            self.tableWidget.insertRow(row)
            for col in range(len(colname)):
                context = str(self.triggerList[row][colname[col]])
                if col == 2:
                    if "abst" in self.triggerList[row].keys():
                        if self.triggerList[row]["abst"]:
                            context = f"相对: {context}"
                        else:
                            context = f"绝对: {context}"
                    else:
                        context = f"相对: {context}"
                item = QTableWidgetItem(context)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignCenter)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)    #设置为只可选择可用拖动
                self.tableWidget.setItem(row,col,item)

    def onRowMoved(self,drag,drop):
        if drag != drop:
            moving_data = self.triggerList[drag]
            self.triggerList.pop(drag)
            self.triggerList.insert(drop,moving_data)
        self.show_tgTable()

    def onSelectionChanged(self):
        row = self.Parent.selected_row(self.tableWidget)
        if isinstance(row, int):
            tg = self.triggerList[row]
            if "abst" in tg.keys():
                self.chk_abs.setChecked(tg["abst"])
            else:
                self.chk_abs.setChecked(True)
            self.spin_Unit.setValue(tg["u"])
            self.spin_Count.setValue(tg["c"])
            self.spin_Goto.setValue(tg["to"])


    def onModeChanged(self):
        return

    def onFillChanged(self):
        mode = self.comboBox_mode.currentIndex()
        fill = self.comboBox_fill.currentIndex()
        if mode == 1:
            self.set_background_img(fill)
        elif mode == 2:
            pass

    def onBgEnabledChanged(self):
        enabled = self.checkBox_enableBg.isChecked()
        if not enabled:
            self.backgroundDescribeText = "noBackground"
        else:
            self.backgroundDescribeText = "None"
        self.set_ui_value()

    def onMaskChanged(self):
        print("onMaskChanged",self.checkBox_mask.isChecked())
        if self.backgroundDescribeText != "noBackground":
            if "Background" in self.backgroundDescribeText and self.checkBox_mask.isChecked():
                self.backgroundDescribeText = self.backgroundDescribeText.replace("Background","Mask")
            if "Mask" in self.backgroundDescribeText and not self.checkBox_mask.isChecked():
                self.backgroundDescribeText = self.backgroundDescribeText.replace("Mask","Background")

        self.set_ui_value()

    def onAbstChanged(self):
        abst = self.chk_abs.isChecked()
        if abst:
            self.spin_Goto.setMinimum(-65536)
        else:
            self.spin_Goto.setMinimum(1)

    def set_value(self, progScreenSetting = None, unitCount = 0):
        self.disconnect_signal()
        self.unitCount = unitCount
        if progScreenSetting is not None:
            #**********
            #以下为改正设置错误的触发器设置项
            if "tigger" in progScreenSetting.keys():    # 拼写错误和内容错误的设置项目
                progScreenSetting.pop("tigger")
                progScreenSetting["trigger"] = []    # 没有触发器为空列表

            if not isinstance(progScreenSetting["trigger"],list):
                progScreenSetting["trigger"] = []
            #**********

            self.ProgScreenSetting = progScreenSetting
            self.backgroundDescribeText = self.ProgScreenSetting["background"]
            self.triggerList = self.ProgScreenSetting["trigger"]
        self.set_ui_value()

        self.connect_signal()

    def set_ui_value(self):
        self.label_bgDescribe.setText(self.backgroundDescribeText)
        self.pushButton.setStyleSheet(None)
        if self.backgroundDescribeText != "noBackground":
            self.checkBox_enableBg.setChecked(True)
            self.set_ui_enabled(True)
        else:
            self.checkBox_enableBg.setChecked(False)
            self.set_ui_enabled(False)
        if self.backgroundDescribeText.startswith("colorMask") or self.backgroundDescribeText.startswith("imgMask") or self.backgroundDescribeText.startswith("videoMask"):
            self.checkBox_mask.setChecked(True)

        self.spin_Unit.setMaximum(self.unitCount)


        if self.backgroundDescribeText.startswith("color"):
            self.comboBox_mode.setCurrentIndex(0)
            # 使用正则表达式匹配括号中的RGB值
            pattern = r"(?:colorMask|colorBackground)\(\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\)"
            match = re.search(pattern, self.backgroundDescribeText)
            print(match)
            if match:
                # 提取匹配到的三个数字并转换为整数
                r = max(0,min(255,int(match.group(1))))
                g = max(0,min(255,int(match.group(2))))
                b = max(0,min(255,int(match.group(3))))
                color =  (r, g, b)
                # print(color)
                self.pushButton.setStyleSheet(f"background-color: rgb{color}")

        elif self.backgroundDescribeText.startswith("img"):
            self.comboBox_mode.setCurrentIndex(1)
            # 匹配 imgMask 或 imgBackground 后面括号中的第二个参数
            pattern = r'(?:imgMask|imgBackground)\([^,]+,\s*(\d+)\s*\)'
            match = re.search(pattern, self.backgroundDescribeText)
            print(match)
            if match:
                self.comboBox_fill.setCurrentIndex(int(match.group(1)))
            
            
        self.show_tgTable()

    def set_background(self):
        mode = self.comboBox_mode.currentIndex()
        if mode == 0:    # 纯色背景
            self.set_background_color()
        elif mode == 1:
            self.set_background_img()

        if mode != 0:
            self.pushButton.setStyleSheet(None)


    def set_background_color(self):
        mask = self.checkBox_mask.isChecked()
        col = QColorDialog.getColor()
        if col.isValid():
            color = (col.red(), col.green(), col.blue())
            if mask:
                self.backgroundDescribeText = f"colorMask({color})"
            else:
                self.backgroundDescribeText = f"colorBackground({color})"

            self.pushButton.setStyleSheet(f"background-color: rgb{color}")
            self.label_bgDescribe.setText(self.backgroundDescribeText)

    def set_background_img(self, fill = None):
        mask = self.checkBox_mask.isChecked()
        if fill is not None:
            pattern = r'(?:imgMask|imgBackground)\("([^"]+)"'
            match = re.search(pattern, self.backgroundDescribeText)
            if match:
                file_name = match.group(1)
                if mask:
                    self.backgroundDescribeText = f"imgMask(\"{file_name}\",{fill})"
                else:
                    self.backgroundDescribeText = f"imgBackground(\"{file_name}\",{fill})"
        else:
            fill = self.comboBox_fill.currentIndex()
            if "background_folder" in self.Parent.settings:
                bfo = self.Parent.settings["background_folder"]
                if not os.path.exists(bfo):
                    bfo = "./Background"
                if os.path.exists(bfo):
                    file_dir,ok = QFileDialog.getOpenFileName(self,'打开',bfo,'图片 (*.jpg *.png)')
                    if ok:
                        file_name = os.path.basename(file_dir)
                        if mask:
                            self.backgroundDescribeText = f"imgMask(\"{file_name}\",{fill})"
                        else:
                            self.backgroundDescribeText = f"imgBackground(\"{file_name}\",{fill})"
                else:
                    msg = QMessageBox.warning(self,"提示","请在\"菜单栏\"中的\"更多功能\"选择\"指定背景文件夹\"后再设置背景。")
            else:
                msg = QMessageBox.warning(self,"提示","请在\"菜单栏\"中的\"更多功能\"选择\"指定背景文件夹\"后再设置背景。")
        self.label_bgDescribe.setText(self.backgroundDescribeText)

    def addTrigger(self):
        u = self.spin_Unit.value()
        c = self.spin_Count.value()
        to = self.spin_Goto.value()
        abst = self.chk_abs.isChecked()
        tg = {"u" : u , "c" : c , "to" : to , "abst" : abst}
        for i in range(len(self.triggerList)):
            if self.triggerList[i]["u"] == u:
                self.triggerList[i] = tg
                self.show_tgTable()
                return
        self.triggerList.append(tg)
        self.show_tgTable()

    def deleteTrigger(self):
        row = self.Parent.selected_row(self.tableWidget)
        if isinstance(row, int):
            self.triggerList.pop(row)
        self.show_tgTable()

    def get_setting(self):
        self.ProgScreenSetting["background"] = self.backgroundDescribeText
        self.ProgScreenSetting["trigger"] = self.triggerList

        return self.ProgScreenSetting



class MainWindow(QMainWindow, Ui_ControlPanel):
    thisFile_saveStat = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.settings = dict()
        self.currentFileDir = ""
        self.currentFileName = ""
        self.thisFileSaved = True
        self.currentLine = None
        self.currentProg = None
        self.currentDisplayProgIndex = None
        self.setWindowTitle("LED模拟器")
        self.setWindowIcon(QIcon("./resources/icon.ico"))
        #获取显示器分辨率大小
        self.desktop = QApplication.desktop()
        self.screenRect = self.desktop.screenGeometry()
        self.height = int(self.screenRect.height()*985/1648)
        self.width = int(self.height*1648/985)
        # self.setMaximumSize(self.screenRect.width(),self.screenRect.height())
        self.setMinimumSize(self.width,self.height)
        self.initUI()
        self.make_menu()
        self.read_setting()

    def initUI(self):
        self.BtnWidget = QWidget(self)
        self.verticalLayout_LayoutBtn.addWidget(self.BtnWidget)
        self.AboutWindow = AboutWindow()
        self.LineEditor = LineEditor()
        self.LineController = LineController(self)
        self.LineSettler = LineSettler(self)
        self.ProgramSheetManager = ProgramSheetManager(self)
        self.ProgramSettler = ProgramSettler(self)
        self.IconManager = IconManager(self)
        self.LedScreens = {
            "frontScreen":None,
            "backScreen":None,
            "frontSideScreen":None,
            "backSideScreen":None,
        }
        self.btn_saveFile.clicked.connect(self.save_file)
        self.btn_opFile.clicked.connect(self.open_file)
        self.btn_showSelectedScreen.clicked.connect(self.preview_screen)
        self.tableWidget_ProgramSheet.itemSelectionChanged.connect(self.on_prog_changed)
        self.tableWidget_ProgramSheet.pressed.connect(self.change_program)
        self.tableWidget_lineChoose.itemSelectionChanged.connect(self.on_line_changed)
        self.thisFile_saveStat.connect(self.set_window_title)

        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.getFps)
        self.timer1.start(1000)

    def on_line_changed(self):
        row = self.selected_row(self.tableWidget_lineChoose)
        self.currentLine = row
        print(f"当前选中线路：{self.currentLine}")
        # 事件统一管理
        self.close_all_screen()
        self.ProgramSheetManager.show_program()
        self.ProgramSettler.init_ProgramSetting()
        self.LineSettler.init_LineSetting()
        self.LineController.show_name_time()

    def on_prog_changed(self):
        row = self.selected_row(self.tableWidget_ProgramSheet)
        self.currentProg = row
        print(f"当前选中节目：{self.currentProg}")
        # 事件统一管理
        self.change_program()
        self.ProgramSheetManager.show_name_time()
        self.ProgramSettler.show_scnUnit()

    def set_window_title(self, thisFile_saved = False):
        self.thisFileSaved = thisFile_saved
        saved_sign = "[未保存]"
        if thisFile_saved:
            saved_sign = "[已保存]"
        ti = self.currentFileName + " " + saved_sign + " - LED模拟器"

        self.setWindowTitle(ti)

    def make_menu(self):
        fileMenu = self.menuBar().addMenu('文件')
        newAction = QAction('新建', self)
        newAction.triggered.connect(self.new_file)
        fileMenu.addAction(newAction)
        newAction = QAction('打开', self)
        newAction.triggered.connect(self.open_file)
        fileMenu.addAction(newAction)
        newAction = QAction('保存', self)
        newAction.triggered.connect(self.save_file)
        newAction.setShortcut('Ctrl+S')
        fileMenu.addAction(newAction)
        newAction = QAction('另存为', self)
        newAction.triggered.connect(self.save_another)
        fileMenu.addAction(newAction)
        exitAction = QAction('关闭', self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        fileMenu = self.menuBar().addMenu('显示屏')
        newAction = QAction('打开所有显示屏', self)
        newAction.triggered.connect(self.turn_on_all_screen)
        fileMenu.addAction(newAction)
        newAction = QAction('关闭所有显示屏', self)
        newAction.triggered.connect(self.close_all_screen)
        fileMenu.addAction(newAction)
        newAction = QAction('屏幕截图', self)
        newAction.triggered.connect(self.screenShot)
        fileMenu.addAction(newAction)
        newAction = QAction('置顶显示屏', self)
        newAction.triggered.connect(self.topMost)
        fileMenu.addAction(newAction)

        fileMenu = self.menuBar().addMenu('更多功能')
        newAction = QAction('指定背景文件夹', self)
        newAction.triggered.connect(self.set_background_folder)
        fileMenu.addAction(newAction)
        newAction = QAction('复制线路', self)
        newAction.triggered.connect(self.LineController.copy_busLine)
        fileMenu.addAction(newAction)
        newAction = QAction('关于', self)
        newAction.triggered.connect(self.AboutWindow.show)
        fileMenu.addAction(newAction)
        exitAction = QAction('退出', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

    def read_setting(self):
        setting_file = "./resources/settings.info"
        if os.path.exists(setting_file):
            with open(setting_file,'r',encoding = 'utf-8') as r:
                list_str = r.read()
                self.settings = ast.literal_eval(list_str)

    def save_setting(self):
        setting_file = "./resources/settings.info"
        with open(setting_file,'w',encoding = 'utf-8') as w:
            w.write(str(self.settings))

    def closeEvent(self,event):
        print(self.thisFileSaved)
        if not self.thisFileSaved:
            self.save_file(pop=True)
        # 删除屏幕截图文件夹中可能存在的GIF临时文件
        try:
            figure = os.listdir("./ScreenShots")
            for f in figure:
                if f.startswith("temp"):
                    tempGIF = os.path.join("./ScreenShots",f)
                    os.remove(tempGIF)
        except:
            pass
        self.close()

    def getFps(self):
        fps = []
        for s in self.LedScreens.values():
            try:
                if s.isVisible():
                    fps.append(s.get_fps())
            except Exception as e:
                pass
        if len(fps) != 0:
            msg = ""
            for i in range(len(fps)):
                msg+=f" FPS{i+1}: {fps[i]} "
            self.statusBar().showMessage(msg)

    def flush_table(self,tableWidgetObject,data):
        tableWidgetObject.setRowCount(0)
        for row in range(len(data)):
            tableWidgetObject.insertRow(row)
            for col in range(len(data[0])):
                item = QTableWidgetItem(str(data[row][col]))
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignCenter)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)    #设置为只可选择，但可拖动
                tableWidgetObject.setItem(row,col,item)

    def selected_row(self,tableWidgetObject):
        row_select = tableWidgetObject.selectedItems()
        if len(row_select) == 0:
            return
        row = row_select[0].row()
        return row
    
    def set_selected_row(self,tableWidgetObject,row):
        try:
            item = tableWidgetObject.item(row,0)
            tableWidgetObject.setCurrentItem(item)
        except Exception as e:
            print("set_selected_row,", e)
    
    def new_file(self):
        if os.path.exists(self.currentFileDir):
            button = QMessageBox.question(self, "对话框", "确定要新建文件吗？")
            if button == QMessageBox.No:
                return
        self.LineController.new_line()
        self.currentFileDir = ""
        self.currentFileName = "新建文件"
        self.thisFile_saveStat.emit(False)
    
    def save_another(self):
        filedir,ok = QFileDialog.getSaveFileName(self,'保存','./','路牌文件 (*.bsu)')
        if ok:
            self.currentFileDir = filedir
            self.currentFileName = os.path.basename(filedir)
            self.thisFile_saveStat.emit(True)
            with open(filedir,'w',encoding = 'utf-8') as w:
                w.write(str(self.LineEditor.LineInfoList))

        self.statusBar().showMessage(datetime.datetime.now().strftime("%Y%m%d %H:%M") + f"文件已保存到{self.currentFileDir}")
    
    def save_file(self,pop = False):
        if pop:
            button = QMessageBox.question(self, "对话框", "确定要保存吗？")
            if button == QMessageBox.No:
                return False
        if os.path.exists(self.currentFileDir):
            filedir = self.currentFileDir
            with open(filedir,'w',encoding = 'utf-8') as w:
                w.write(str(self.LineEditor.LineInfoList))
            self.thisFile_saveStat.emit(True)
        else:
            self.save_another()

        self.statusBar().showMessage(datetime.datetime.now().strftime("%Y%m%d %H:%M") + f"文件已保存到{self.currentFileDir}")
        return True

    def open_file(self):
        if os.path.exists(self.currentFileDir):
            button = QMessageBox.question(self, "对话框", "确定要打开另一个文件吗？")
            if button == QMessageBox.No:
                return
        file_dir,ok = QFileDialog.getOpenFileName(self,'打开','./','路牌文件 (*.bsu)')
        if ok:
            self.currentFileDir = file_dir
            self.currentFileName = os.path.basename(file_dir)
            self.thisFile_saveStat.emit(True)
            with open(file_dir,'r',encoding = 'utf-8') as r:
                list_str = r.read()
                self.LineEditor.LineInfoList = ast.literal_eval(list_str)
            self.flush_table(self.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.LineEditor.LineInfoList])
            self.flush_table(self.tableWidget_ProgramSheet,[])

    def get_currentScreen(self):
        screen = self.combo_LineScreens.currentText()  # 获取正在编辑的屏幕
        
        if screen not in screenLink.keys():
            screen = "前路牌"
        screen = screenLink[screen]
        return screen
    
    def force_changeProg(self, who):
        for scn in self.LedScreens.values():
            if scn is not None:
                if not (scn is who):
                    try:
                        scn.currentIndex = self.currentDisplayProgIndex
                        scn.programTimeout()
                        print(f"{scn.toDisplay}被迫切换节目{self.currentDisplayProgIndex+1}")
                    except Exception as e:
                        print(e)
    
    def change_currentDisplayProgIndex(self,who):
        print(f"当前节目：{self.currentDisplayProgIndex}+1，{who.toDisplay}请求更换节目至{who.currentIndex+1}")
        if self.currentDisplayProgIndex is None:
            self.currentDisplayProgIndex = who.currentIndex

        if self.currentDisplayProgIndex == who.currentIndex:
            self.force_changeProg(who)
        else:
            self.currentDisplayProgIndex = who.currentIndex
            # if who.currentPtime < 0: who的currentPtime早就更新了，直接全部强制更换节目
            self.force_changeProg(who)

    def turn_on_all_screen(self):
        self.currentDisplayProgIndex = 0
        self.close_all_screen()
        row = self.currentLine
        h = 0
        if isinstance(row,int):
            
            for screen in screenLink.values():
                try:
                    self.LedScreens[screen].close()
                except Exception as e:
                    pass
                    # print("turn_on_all_screen: ", e)
                if self.LineEditor.LineInfoList[row][screen]["enabled"]:
                    try:
                        scn = ScreenController(parent=self,flushRate=self.LineEditor.LineInfoList[row]["flushRate"],screenInfo={"colorMode":self.LineEditor.LineInfoList[row][screen]["colorMode"],"screenSize":self.LineEditor.LineInfoList[row][screen]["screenSize"]},screenProgramSheet=self.LineEditor.LineInfoList[row]["programSheet"],FontIconMgr=self.IconManager.FontMgr,toDisplay=screen)
                        scn.move(50,50+h)
                        h += self.LineEditor.LineInfoList[row][screen]["screenSize"][1]*self.LineEditor.LineInfoList[row][screen]["screenSize"][2][1]+60
                        self.LedScreens[screen] = scn
                    except Exception as e:
                        pass

    def close_all_screen(self):
        for s in self.LedScreens.values():
            try:
                s.close()
                s.deleteLater()
            except Exception as e:
                pass

    def preview_screen(self):
        self.currentDisplayProgIndex = None
        row = self.currentLine
        if isinstance(row,int):
            self.close_all_screen()
            screen = self.get_currentScreen()
            scn = ScreenController(parent=self, flushRate=self.LineEditor.LineInfoList[row]["flushRate"],screenInfo={"colorMode":self.LineEditor.LineInfoList[row][screen]["colorMode"],"screenSize":self.LineEditor.LineInfoList[row][screen]["screenSize"]},screenProgramSheet=self.LineEditor.LineInfoList[row]["programSheet"],FontIconMgr=self.IconManager.FontMgr,toDisplay=screen)
            scn.move(100,100)
            self.LedScreens[screen] = scn
        self.change_program()

    def set_background_folder(self):
        self.settings["background_folder"] = "./Background"
        _dir = QFileDialog.getExistingDirectory(self,"选取默认背景文件夹","./")
        if os.path.exists(_dir):
            self.settings["background_folder"] = _dir

        self.save_setting()

    def change_program(self):   # 切换正在显示的节目
        line_row = self.currentLine
        if isinstance(line_row,int):
            programSheet = self.LineEditor.LineInfoList[line_row]["programSheet"]
            row = self.currentProg
            if isinstance(row,int):
                self.currentDisplayProgIndex = row
                for screen in screenLink.values():
                    try:
                        if self.LineEditor.LineInfoList[line_row][screen]["enabled"]:
                            self.LedScreens[screen].screenProgramSheet = programSheet
                            self.LedScreens[screen].currentIndex = row
                            self.LedScreens[screen].programTimeout()
                        else:
                            self.LedScreens[screen].close()
                    except Exception as e:
                        pass

    def screenShot(self):
        screen = QApplication.primaryScreen()
        for name,scn in self.LedScreens.items():
            try:
                try:
                    os.makedirs("./ScreenShots")
                except Exception as e:
                    pass
                if scn.isVisible():
                    window_handle = scn.winId()
                    screenshot = screen.grabWindow(window_handle)
                    fileName = datetime.datetime.now().strftime(f"{name}_%H%M%S.png")
                    screenshot.save(os.path.join("./ScreenShots",fileName))
            except Exception as e:
                pass

    def topMost(self):
        for scn in self.LedScreens.values():
            try:
                if scn.isVisible():
                    flags = scn.windowFlags()
                    if flags & Qt.WindowStaysOnTopHint:
                        scn.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
                    else:
                        scn.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
                    scn.show()
                    scn.show()
            except Exception as e:
                pass

class IconManager():
    def __init__(self,parent):
        self.Parent = parent
        self.FontMgr = FontManager()
        self.IconLib = self.FontMgr.icon_dict
        self.data = []
        self.initUI()

    def initUI(self):
        # 图标管理表格
        self.Parent.tableWidget_Icons.verticalHeader().setVisible(False)
        self.Parent.tableWidget_Icons.setColumnCount(2)
        self.Parent.tableWidget_Icons.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.Parent.tableWidget_Icons.setSelectionMode(QAbstractItemView.SingleSelection)
        self.Parent.tableWidget_Icons.setHorizontalHeaderLabels(["图标代号","预览"])
        self.Parent.tableWidget_Icons.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.Parent.tableWidget_Icons.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.Parent.tableWidget_Icons.verticalHeader().setDefaultSectionSize(64)

        self.Parent.btn_LoadIcons.clicked.connect(self.add_icon)
        self.Parent.tableWidget_Icons.doubleClicked.connect(self.use_icom)

        self.flush_table()

    def flush_table(self):
        data = self.data = []
        for key,value in self.IconLib.items():
            data.append([key.strip("`"),value])
        self.Parent.tableWidget_Icons.setRowCount(0)
        for row in range(len(data)):
            self.Parent.tableWidget_Icons.insertRow(row)
            col = 0
            item = QTableWidgetItem(str(data[row][col]))
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignCenter)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)    #设置为只可选择
            self.Parent.tableWidget_Icons.setItem(row,col,item)
            col = 1
            item = QTableWidgetItem()
            item.setData(Qt.DecorationRole, QPixmap(str(data[row][col])))
            self.Parent.tableWidget_Icons.setItem(row, col, item)

    def add_icon(self):
        file_dir,ok = QFileDialog.getOpenFileName(self.Parent,'打开','./','图标信息 (*.info)')
        if ok:
            self.FontMgr.icon_info.add(file_dir)
            self.FontMgr.get_icon_list()
            self.IconLib = self.FontMgr.icon_dict
            self.flush_table()

    def use_icom(self):
        row = self.Parent.selected_row(self.Parent.tableWidget_Icons)
        if isinstance(row,int):
            ot = self.Parent.lineEdit_Text.text()
            ot = ot + "`" + self.data[row][0] + "`"
            self.Parent.lineEdit_Text.setText(ot)
    
class ProgramSheetManager():
    def __init__(self, parent):
        self.Parent = parent
        self.programSheet = []
        self.initUI()

    def initUI(self):
        # 节目单管理表格
        self.Parent.tableWidget_ProgramSheet.setColumnCount(2)
        self.Parent.tableWidget_ProgramSheet.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.Parent.tableWidget_ProgramSheet.setSelectionMode(QAbstractItemView.SingleSelection)
        self.Parent.tableWidget_ProgramSheet.setHorizontalHeaderLabels(["节目名称","持续时间"])
        self.Parent.tableWidget_ProgramSheet.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.Parent.tableWidget_ProgramSheet.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.Parent.tableWidget_ProgramSheet.verticalHeader().setDefaultSectionSize(18)

        self.Parent.spinBox.setMaximum(3600*24)
        self.Parent.spinBox.setMinimum(-1)

        self.Parent.tableWidget_ProgramSheet.rowMoved.connect(self.move_program)
        self.Parent.lineEdit_ProgramName.editingFinished.connect(self.change_name_time)
        self.Parent.spinBox.editingFinished.connect(self.change_name_time)
        self.Parent.btn_Add.clicked.connect(self.new_program)
        self.Parent.btn_MvUp_Program.clicked.connect(self.mv_up_program)
        self.Parent.btn_MvDn_Program.clicked.connect(self.mv_dn_program)
        self.Parent.btn_CopyProgram.clicked.connect(self.copy_program)
        self.Parent.btn_Remove.clicked.connect(self.del_program)

    def show_program(self):
        row = self.Parent.currentLine
        print("show_program:self.Parent.currentLine:",row)
        if isinstance(row,int):
            self.programSheet = self.Parent.LineEditor.LineInfoList[row]["programSheet"]
            data = [[p[0],p[1]] for p in self.programSheet]
            self.Parent.flush_table(self.Parent.tableWidget_ProgramSheet,data)

    def show_name_time(self):
        row = self.Parent.currentProg
        if isinstance(row,int):
            self.Parent.lineEdit_ProgramName.setText(self.programSheet[row][0])
            self.Parent.spinBox.setValue(self.programSheet[row][1])

    def change_name_time(self):
        row = self.Parent.currentProg
        if isinstance(row,int):
            name = self.Parent.lineEdit_ProgramName.text()
            time = self.Parent.spinBox.value()
            if self.programSheet[row][0] != name or self.programSheet[row][1] != time:
                self.programSheet[row][0] = self.Parent.lineEdit_ProgramName.text()
                self.programSheet[row][1] = self.Parent.spinBox.value()
                self.Parent.thisFile_saveStat.emit(False)
            self.show_program()
            self.Parent.set_selected_row(self.Parent.tableWidget_ProgramSheet,row)

    def new_program(self,):
        progName = self.Parent.lineEdit_ProgramName.text()
        sec = self.Parent.spinBox.value()
        
        row = self.Parent.currentLine
        if isinstance(row,int):
            sbp = [[],[]]
            sbpdict = dict()
            for screen in screenLink.values():
                if self.Parent.LineEditor.LineInfoList[row][screen]["enabled"]:
                    sbp = [[],[]]
                    for i in range(len(self.Parent.LineEditor.LineInfoList[row][screen]["screenUnit"])):
                        sbp[0].append(copy.deepcopy(self.Parent.LineEditor.LineInfoList[row][screen]["screenUnit"][i]))
                        sbp[1].append(copy.deepcopy(template_program_show))
                    sbpdict[screen] = sbp
            self.programSheet.append([progName,sec,sbpdict])
            self.Parent.lineEdit_ProgramName.setText("")
            self.Parent.spinBox.setValue(0)
            self.show_program()
            # print(self.programSheet)
            self.Parent.set_selected_row(self.Parent.tableWidget_ProgramSheet, len(self.programSheet)-1)
            self.Parent.thisFile_saveStat.emit(False)

    def del_program(self):
        row = self.Parent.currentProg
        if isinstance(row,int):
            self.programSheet.pop(row)
            self.Parent.thisFile_saveStat.emit(False)
        self.show_program()
        self.Parent.set_selected_row(self.Parent.tableWidget_ProgramSheet, max(0,row-1))

    def copy_program(self):
        row = self.Parent.currentProg
        if isinstance(row,int):
            self.programSheet.append(copy.deepcopy(self.programSheet[row]))
            self.Parent.thisFile_saveStat.emit(False)
        self.show_program()
        self.Parent.set_selected_row(self.Parent.tableWidget_ProgramSheet, len(self.programSheet)-1)

    def move_program(self,drag,drop):
        if drag != drop:
            # 保存要移动的数据
            moving_data = self.programSheet[drag]
            # 删除原位置的数据
            self.programSheet.pop(drag)
            # 在目标位置插入数据
            self.programSheet.insert(drop, moving_data)
            self.Parent.thisFile_saveStat.emit(False)
        self.show_program()
        self.Parent.set_selected_row(self.Parent.tableWidget_ProgramSheet, drop)

    def mv_up_program(self):
        row = self.Parent.currentProg
        if isinstance(row,int):
            if row > 0:
                self.programSheet[row],self.programSheet[row-1] = self.programSheet[row-1],self.programSheet[row]
                self.Parent.thisFile_saveStat.emit(False)
        self.show_program()
        self.Parent.set_selected_row(self.Parent.tableWidget_ProgramSheet, max(0,row-1))

    def mv_dn_program(self):
        row = self.Parent.currentProg
        if isinstance(row,int):
            if row < len(self.programSheet)-1:
                self.programSheet[row],self.programSheet[row+1] = self.programSheet[row+1],self.programSheet[row]
                self.Parent.thisFile_saveStat.emit(False)
        self.show_program()
        self.Parent.set_selected_row(self.Parent.tableWidget_ProgramSheet, min(len(self.programSheet)-1,row+1))

class ProgramSettler():
    def __init__(self, parent):
        self.Parent = parent
        self.FontMgr = FontManager()
        self.FontLib = self.FontMgr.font_dict.keys()
        self.ChFont = [c for c in self.FontLib if "asc" not in c.lower()]
        self.TtFont = [c for c in self.FontLib if "asc" not in c.lower() and "hzk" not in c.lower()]
        self.EngFont = [c for c in self.FontLib if "asc" in c.lower()]
        self.tmpBmp = []
        self.colorMode = "1"
        self.initUI()

    def initUI(self):
        # 屏幕分区管理表格
        self.Parent.tableWidget_Screens.setColumnCount(4)
        self.Parent.tableWidget_Screens.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.Parent.tableWidget_Screens.setSelectionMode(QAbstractItemView.SingleSelection)
        self.Parent.tableWidget_Screens.verticalHeader().setVisible(False)
        self.Parent.tableWidget_Screens.setHorizontalHeaderLabels(["屏幕名称","屏幕规格","灯珠规格","内容大小"])
        self.Parent.tableWidget_Screens.setColumnWidth(0,120)
        self.Parent.tableWidget_Screens.setColumnWidth(1,100)
        self.Parent.tableWidget_Screens.setColumnWidth(2,100)
        self.Parent.tableWidget_Screens.setColumnWidth(3,100)
        self.Parent.tableWidget_Screens.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.Parent.tableWidget_Screens.verticalHeader().setDefaultSectionSize(18)

        # 启用右键菜单
        self.Parent.tableWidget_Screens.setContextMenuPolicy(Qt.CustomContextMenu)
        self.Parent.tableWidget_Screens.customContextMenuRequested.connect(self.show_context_menu)

        self.Parent.combo_Font.addItems(self.ChFont)
        self.Parent.combo_ASCII_Font.addItems(self.EngFont)
        self.Parent.combo_Show.addItems(["静止","闪烁","向左滚动","向上滚动","向左移到中间","向左扇形圆形","向左开百叶窗","开水平窗户","向上移到中间","向上扇形圆形","向上开百叶窗","关水平窗户","中间向左移开","中间向上移开","跳跃向左移动","跳跃向上移动","向右滚动","向下滚动","向右移到中间","向右扇形圆形","向右开百叶窗","开竖直窗户","向下移到中间","向下扇形圆形","向下开百叶窗","关竖直窗户","中间向右移开","中间向下移开","跳跃向右移动","跳跃向下移动","上下反复跳跃移动",])
        self.Parent.combo_TextDirect.addItems(["横向","竖向"])
        self.Parent.combo_SingleColorChoose.addItems(template_monochromeColors.keys())

        self.Parent.spin_FontSize.setMaximum(64)
        self.Parent.spin_FontSize.setMinimum(6)
        self.Parent.spin_FontSize.setValue(16)
        self.Parent.spin_FontSize_2.setMaximum(64)
        self.Parent.spin_FontSize_2.setMinimum(6)
        self.Parent.spin_FontSize_2.setValue(16)
        self.Parent.spinBox_Argv_1.setMaximum(60)
        self.Parent.spinBox_Argv_1.setMinimum(1)
        self.Parent.spinBox_Argv_2.setMaximum(60)
        self.Parent.spinBox_Argv_2.setMinimum(1)
        self.Parent.spinBox_Argv_3.setMaximum(60)
        self.Parent.spinBox_Argv_3.setMinimum(0)
        self.Parent.spinBox_WordSpace.setMaximum(100)
        self.Parent.spinBox_WordSpace.setMinimum(-100)
        self.Parent.spinBox_BoldSizeX.setMaximum(4)
        self.Parent.spinBox_BoldSizeX.setMinimum(1)
        self.Parent.spinBox_BoldSizeY.setMaximum(4)
        self.Parent.spinBox_BoldSizeY.setMinimum(1)
        self.Parent.spinBox_Y_Offset.setMaximum(64)
        self.Parent.spinBox_Y_Offset.setMinimum(-64)
        self.Parent.spinBox_Y_Offset_2.setMaximum(64)
        self.Parent.spinBox_Y_Offset_2.setMinimum(-64)
        self.Parent.spinBox_X_Offset.setMaximum(65536)
        self.Parent.spinBox_X_Offset.setMinimum(-65536)
        self.Parent.spinBox_Y_GlobalOffset.setMaximum(65536)
        self.Parent.spinBox_Y_GlobalOffset.setMinimum(-65536)
        self.Parent.spinBox_Align_x.setMaximum(1)
        self.Parent.spinBox_Align_x.setMinimum(-1)
        self.Parent.spinBox_Align_y.setMaximum(1)
        self.Parent.spinBox_Align_y.setMinimum(-1)
        self.Parent.spinBox_Zoom.setMaximum(200)
        self.Parent.spinBox_Zoom.setMinimum(40)
        self.Parent.spinBox_Zoom.setValue(100)   

        self.Parent.tableWidget_ProgramSheet.pressed.connect(self.show_scnUnit)
        self.Parent.tableWidget_Screens.itemSelectionChanged.connect(self.show_progArgv)
        self.Parent.tableWidget_Screens.rowMoved.connect(self.move_scnUnitProg)
        self.Parent.combo_LineScreens.currentTextChanged.connect(self.show_scnUnit)
        self.Parent.btn_ok.clicked.connect(self.save_progArgv)
        self.Parent.btn_Colorful_ChooseColor.clicked.connect(self.get_color)
        self.Parent.combo_Show.currentTextChanged.connect(self.update_argv)
        self.Parent.checkBox_sysFont.stateChanged.connect(self.change_EngFont_set)
        self.Parent.btn_textSetting.clicked.connect(self.set_colorstr_multiLine)
        self.Parent.btn_screenSet.clicked.connect(self.set_screenSet)
        
        self.Parent.lineEdit_Text.editingFinished.connect(self.save_progArgv)

        self.Parent.btn_ok.setShortcut(Qt.Key_Return)

    def update_self_colorMode(self):
        row = self.Parent.currentLine
        if isinstance(row,int):
            screen = self.get_currentScreen()
            self.colorMode = self.Parent.LineEditor.LineInfoList[row][screen]["colorMode"]

    def set_screenSet(self):
        row = self.Parent.currentLine
        if isinstance(row,int):
            screen = self.get_currentScreen()
            row = self.Parent.currentProg
            if isinstance(row,int):
                unitCount = len(self.Parent.ProgramSheetManager.programSheet[row][2][screen][0])

                # print(self.Parent.ProgramSheetManager.programSheet[row])
                if len(self.Parent.ProgramSheetManager.programSheet[row][2][screen]) == 2:  # (原始版本数据)
                    ext_dict = dict()
                    self.Parent.ProgramSheetManager.programSheet[row][2][screen].append(ext_dict)  # 所有扩展功能必须加在这个extdict里，不能再添加列表项了（列表长度3）
                    # 查找 ext_dict 使用 self.Parent.ProgramSheetManager.programSheet[row][2][screen][2]

                if len(self.Parent.ProgramSheetManager.programSheet[row][2][screen]) == 3:
                    ext_dict = self.Parent.ProgramSheetManager.programSheet[row][2][screen][2]
                    # print(ext_dict)
                    if "ProgScreenSetting" in ext_dict.keys():
                        ProgScreenSetting = ext_dict["ProgScreenSetting"]
                    else:
                        ProgScreenSetting = None

                ProgSettingDialog = ProgramSettings(self.Parent)
                ProgSettingDialog.show()
                ProgSettingDialog.set_value(progScreenSetting=ProgScreenSetting, unitCount=unitCount)

                if ProgSettingDialog.exec_() == QDialog.Accepted:
                    ProgScreenSetting = ProgSettingDialog.get_setting()
                    self.Parent.ProgramSheetManager.programSheet[row][2][screen][2]["ProgScreenSetting"] = ProgScreenSetting  # ext_dict["ProgScreenSetting"]
                    self.Parent.change_program()
                    self.Parent.thisFile_saveStat.emit(False)
           
    def set_colorstr_multiLine(self):
        multiLine = False
        lineSpace = 1
        richText = [False,False]
        text = ""
        row = self.Parent.currentLine
        self.update_self_colorMode()
        if isinstance(row,int):
            screen = self.get_currentScreen()
            row = self.Parent.currentProg
            if isinstance(row,int):
                self.screenProgList = self.Parent.ProgramSheetManager.programSheet[row][2][screen][1]
                row = self.Parent.selected_row(self.Parent.tableWidget_Screens)
                if isinstance(row,int):
                    text = self.screenProgList[row]["text"]
                    if "multiLine" in self.screenProgList[row].keys():
                        multiLine = self.screenProgList[row]["multiLine"]
                    if "lineSpace" in self.screenProgList[row].keys():
                        lineSpace = self.screenProgList[row]["lineSpace"]
                    if "richText" in self.screenProgList[row].keys():
                        richText = self.screenProgList[row]["richText"]

                    ColorMultiLineDialog = ColorMultiLine()
                    ColorMultiLineDialog.show()
                    ColorMultiLineDialog.set_value(text,multiLine,lineSpace,self.colorMode,richText)
                    if ColorMultiLineDialog.exec_() == QDialog.Accepted:
                        text, multiLine, lineSpace, richText = ColorMultiLineDialog.get_edit_result()

                        self.screenProgList[row]["text"] = text
                        self.screenProgList[row]["multiLine"] = multiLine
                        self.screenProgList[row]["lineSpace"] = lineSpace
                        self.screenProgList[row]["richText"] = richText
                        self.Parent.change_program()
            self.Parent.thisFile_saveStat.emit(False)
        
        self.show_progArgv()

    def change_EngFont_set(self):
        if self.Parent.checkBox_sysFont.isChecked():
            self.Parent.combo_ASCII_Font.clear()
            self.Parent.combo_ASCII_Font.addItems(self.TtFont)
        else:
            self.Parent.combo_ASCII_Font.clear()
            self.Parent.combo_ASCII_Font.addItems(self.EngFont)

    def init_ProgramSetting(self):
        row = self.Parent.currentLine
        if isinstance(row,int):
            screens = ["前路牌","后路牌","前侧路牌","后侧路牌"]
            screens_have = [self.Parent.LineEditor.LineInfoList[row]["frontScreen"]["enabled"],self.Parent.LineEditor.LineInfoList[row]["backScreen"]["enabled"],self.Parent.LineEditor.LineInfoList[row]["frontSideScreen"]["enabled"],self.Parent.LineEditor.LineInfoList[row]["backSideScreen"]["enabled"]]
            self.Parent.combo_LineScreens.clear()

            for i in range(len(screens_have)):
                if screens_have[i]:
                    self.Parent.combo_LineScreens.addItem(screens[i])

            self.show_scnUnit()

    def get_currentScreen(self):
        screen = self.Parent.combo_LineScreens.currentText()
        
        if screen not in screenLink.keys():
            screen = "前路牌"
        screen = screenLink[screen]
        return screen
    
    def move_scnUnitProg(self,drag,drop):
        row = self.Parent.currentProg
        if isinstance(row,int):
            screen = self.get_currentScreen()
            screenUnitList = self.Parent.ProgramSheetManager.programSheet[row][2][screen][0]
            screenProgList = self.Parent.ProgramSheetManager.programSheet[row][2][screen][1]

            if drag != drop:
                # 保存要移动的数据
                moving_data_1 = screenUnitList[drag]
                moving_data_2 = screenProgList[drag]
                # 删除原位置的数据
                screenUnitList.pop(drag)
                screenProgList.pop(drag)
                # 在目标位置插入数据
                screenUnitList.insert(drop,moving_data_1)
                screenProgList.insert(drop,moving_data_2)

                self.Parent.thisFile_saveStat.emit(False)

            QTimer.singleShot(0, self.show_scnUnit)

    def show_context_menu(self, pos):
        # 获取点击的行
        row = self.Parent.tableWidget_Screens.rowAt(pos.y())
        if row < 0:
            return
        # 创建菜单
        menu = QMenu(self.Parent.tableWidget_Screens)
        # 添加菜单项
        action1 = QAction("导出图像", self.Parent.tableWidget_Screens)
        # 将动作添加到菜单
        menu.addAction(action1)
        # 连接动作信号
        action1.triggered.connect(lambda: self.save_img(row))
        # 显示菜单
        # 将窗口坐标转换为全局坐标
        global_pos = self.Parent.tableWidget_Screens.mapToGlobal(pos)
        menu.exec_(global_pos)

    def show_scnUnit(self, change_size = False, index = 0):
        data = []
        self.tmpBmp = []
        self.update_self_colorMode()
        row = self.Parent.currentProg
        if isinstance(row,int):
            screen = self.get_currentScreen()
            screenUnitList = self.Parent.ProgramSheetManager.programSheet[row][2][screen][0]
            screenProgList = self.Parent.ProgramSheetManager.programSheet[row][2][screen][1]

            size = min(len(screenProgList),len(screenUnitList))
            all = range(size)

            # 更改线路默认屏幕布局
            progrow = self.Parent.currentLine  # 当前选择的线路 注意变量为 progrow
            if isinstance(progrow,int):
                self.Parent.LineEditor.LineInfoList[progrow][screen]["screenUnit"] = copy.deepcopy(screenUnitList)
                self.Parent.combo_LineScreensForLayout.setCurrentText(self.Parent.combo_LineScreens.currentText())  # 当节目内容编辑的屏幕改变时，保持线路设置中的屏幕同步
                self.Parent.LineSettler.show_custom_layout_btn()
            else:
                self.Parent.flush_table(self.Parent.tableWidget_ProgramSheet,[])
                return

            for i in all:
                p = screenProgList[i]
                Creater = BmpCreater(self.Parent.IconManager.FontMgr,self.colorMode,p["color_RGB"],p["font"],p["ascFont"],p["sysFontOnly"],)
                _roll_asc = True
                if "rollAscii" in p.keys():
                    _roll_asc = p["rollAscii"]
                if "multiLine" in p.keys() and "lineSpace" in p.keys():
                    bmp = Creater.create_character(vertical=p["vertical"], roll_asc = _roll_asc, text=p["text"], ch_font_size=p["fontSize"], asc_font_size=p["ascFontSize"], ch_bold_size_x=p["bold"][0], ch_bold_size_y=p["bold"][1], space=p["spacing"], scale=p["scale"], auto_scale=p["autoScale"], scale_sys_font_only=p["scaleSysFontOnly"], new_width = screenUnitList[i]["pointNum"][0], new_height = screenUnitList[i]["pointNum"][1], y_offset = p["y_offset"], y_offset_asc = p["y_offset_asc"], style = p["align"], multi_line={"stat":p["multiLine"], "line_space": p["lineSpace"] })
                else:
                    bmp = Creater.create_character(vertical=p["vertical"], roll_asc = _roll_asc, text=p["text"], ch_font_size=p["fontSize"], asc_font_size=p["fontSize"], ch_bold_size_x=p["bold"][0], ch_bold_size_y=p["bold"][1], space=p["spacing"], scale=p["scale"], auto_scale=p["autoScale"], scale_sys_font_only=p["scaleSysFontOnly"], new_width = screenUnitList[i]["pointNum"][0], new_height = screenUnitList[i]["pointNum"][1], y_offset = p["y_offset"], y_offset_asc = p["y_offset"], style = p["align"])

                data.append([i+1,str(screenUnitList[i]["pointNum"]),str(screenUnitList[i]["pointSize"]),bmp.size])
                self.tmpBmp.append(bmp)

            current_row = self.Parent.selected_row(self.Parent.tableWidget_Screens)
            if current_row is None:
                current_row = 0
            # print(data)
            self.Parent.flush_table(self.Parent.tableWidget_Screens,data)
            self.Parent.set_selected_row(self.Parent.tableWidget_Screens,current_row)
        else:
            self.Parent.flush_table(self.Parent.tableWidget_Screens,[])

        ## 添加节目的地方和更改布局的地方
            
    def update_argv(self):
        mode = self.Parent.combo_Show.currentText()
        self.Parent.spinBox_Argv_1.setEnabled(True)
        self.Parent.spinBox_Argv_2.setEnabled(True)
        self.Parent.spinBox_Argv_3.setEnabled(True)
        if "滚动" in mode:
            self.Parent.label_Argv_1.setText("移动速度")
            self.Parent.label_Argv_2.setText("滚动对象间距")
            self.Parent.label_Argv_3.setText("步长")
            self.Parent.spinBox_Argv_1.setMaximum(60)
            self.Parent.spinBox_Argv_1.setMinimum(1)
            self.Parent.spinBox_Argv_2.setMaximum(256)
            self.Parent.spinBox_Argv_2.setMinimum(-1)
            self.Parent.spinBox_Argv_2.setValue(-1)
            self.Parent.spinBox_Argv_3.setMaximum(60)
            self.Parent.spinBox_Argv_3.setMinimum(1)
        elif "移到" in mode:
            self.Parent.label_Argv_1.setText("移动速度")
            self.Parent.label_Argv_2.setText("时间")
            self.Parent.label_Argv_3.setText("步长")
            self.Parent.spinBox_Argv_1.setMaximum(60)
            self.Parent.spinBox_Argv_1.setMinimum(1)
            self.Parent.spinBox_Argv_2.setMaximum(60)
            self.Parent.spinBox_Argv_2.setMinimum(1)
            self.Parent.spinBox_Argv_3.setMaximum(60)
            self.Parent.spinBox_Argv_3.setMinimum(1)
        elif "移开" in mode:
            self.Parent.label_Argv_1.setText("移动速度")
            self.Parent.label_Argv_2.setText("时间")
            self.Parent.label_Argv_3.setText("步长")
            self.Parent.spinBox_Argv_1.setMaximum(60)
            self.Parent.spinBox_Argv_1.setMinimum(1)
            self.Parent.spinBox_Argv_2.setMaximum(60)
            self.Parent.spinBox_Argv_2.setMinimum(1)
            self.Parent.spinBox_Argv_3.setMaximum(60)
            self.Parent.spinBox_Argv_3.setMinimum(1)
        elif "跳跃" in mode:
            self.Parent.label_Argv_1.setText("移动速度")
            self.Parent.label_Argv_2.setText("移动步长")
            self.Parent.label_Argv_3.setText("停靠时间")
            self.Parent.spinBox_Argv_1.setMaximum(60)
            self.Parent.spinBox_Argv_1.setMinimum(1)
            self.Parent.spinBox_Argv_2.setMaximum(32)
            self.Parent.spinBox_Argv_2.setMinimum(1)
            self.Parent.spinBox_Argv_3.setMaximum(60)
            self.Parent.spinBox_Argv_3.setMinimum(0)
        elif "扇形圆形" in mode:
            self.Parent.label_Argv_1.setText("移动速度")
            self.Parent.label_Argv_2.setText("移动步长")
            self.Parent.label_Argv_3.setText("连续移动？")
            self.Parent.spinBox_Argv_1.setMaximum(120)
            self.Parent.spinBox_Argv_1.setMinimum(1)
            self.Parent.spinBox_Argv_2.setMaximum(64)
            self.Parent.spinBox_Argv_2.setMinimum(2)
            self.Parent.spinBox_Argv_3.setMaximum(1)
            self.Parent.spinBox_Argv_3.setMinimum(0)
        elif "百叶窗" in mode:
            self.Parent.label_Argv_1.setText("速度")
            self.Parent.label_Argv_2.setText("窗户大小")
            self.Parent.label_Argv_3.setText("显示窗户？")
            self.Parent.spinBox_Argv_1.setMaximum(60)
            self.Parent.spinBox_Argv_1.setMinimum(1)
            self.Parent.spinBox_Argv_2.setMaximum(1024)
            self.Parent.spinBox_Argv_2.setMinimum(2)
            self.Parent.spinBox_Argv_3.setMaximum(1)
            self.Parent.spinBox_Argv_3.setMinimum(0)
        elif "窗户" in mode:
            self.Parent.label_Argv_1.setText("速度")
            self.Parent.label_Argv_2.setText("显示窗户？")
            self.Parent.label_Argv_3.setText("")
            self.Parent.spinBox_Argv_1.setMaximum(60)
            self.Parent.spinBox_Argv_1.setMinimum(1)
            self.Parent.spinBox_Argv_2.setMaximum(1)
            self.Parent.spinBox_Argv_2.setMinimum(0)
            self.Parent.spinBox_Argv_3.setEnabled(False)
        elif mode == "闪烁":
            self.Parent.label_Argv_1.setText("亮时长")
            self.Parent.label_Argv_2.setText("灭时长")
            self.Parent.label_Argv_3.setText("")
            self.Parent.spinBox_Argv_1.setMaximum(60)
            self.Parent.spinBox_Argv_1.setMinimum(1)
            self.Parent.spinBox_Argv_2.setMaximum(60)
            self.Parent.spinBox_Argv_2.setMinimum(1)
            self.Parent.spinBox_Argv_3.setEnabled(False)
        elif mode == "静止":
            self.Parent.label_Argv_1.setText("")
            self.Parent.label_Argv_2.setText("")
            self.Parent.label_Argv_3.setText("")
            self.Parent.spinBox_Argv_1.setEnabled(False)
            self.Parent.spinBox_Argv_2.setEnabled(False)
            self.Parent.spinBox_Argv_3.setEnabled(False)

    def show_progArgv(self):
        row = self.Parent.currentLine
        self.update_self_colorMode()
        if isinstance(row,int):
            screen = self.get_currentScreen()
            if self.colorMode == "1":
                self.Parent.combo_SingleColorChoose.setEnabled(True)
                self.Parent.btn_Colorful_ChooseColor.setEnabled(False)
            elif self.colorMode == "RGB":
                self.Parent.combo_SingleColorChoose.setEnabled(False)
                self.Parent.btn_Colorful_ChooseColor.setEnabled(True)
            row = self.Parent.currentProg
            if isinstance(row,int):
                self.screenProgList = self.Parent.ProgramSheetManager.programSheet[row][2][screen][1]
                row = self.Parent.selected_row(self.Parent.tableWidget_Screens)
                if isinstance(row,int):
                    self.update_argv()
                    self.Parent.combo_Font.setCurrentText(self.screenProgList[row]["font"])
                    self.Parent.spin_FontSize.setValue(self.screenProgList[row]["fontSize"])
                    self.Parent.checkBox_sysFont.setChecked(self.screenProgList[row]["sysFontOnly"])
                    self.Parent.combo_ASCII_Font.setCurrentText(self.screenProgList[row]["ascFont"])
                    self.Parent.combo_Show.setCurrentText(self.screenProgList[row]["appearance"])
                    self.Parent.combo_TextDirect.setCurrentText("竖向" if self.screenProgList[row]["vertical"] else "横向")
                    self.Parent.spinBox_Argv_1.setValue(self.screenProgList[row]["argv_1"])
                    self.Parent.spinBox_Argv_2.setValue(self.screenProgList[row]["argv_2"])
                    self.Parent.spinBox_WordSpace.setValue(self.screenProgList[row]["spacing"])
                    self.Parent.spinBox_BoldSizeX.setValue(self.screenProgList[row]["bold"][0])
                    self.Parent.spinBox_BoldSizeY.setValue(self.screenProgList[row]["bold"][1])
                    self.Parent.spinBox_Y_Offset.setValue(self.screenProgList[row]["y_offset"])
                    self.Parent.spinBox_Align_x.setValue(self.screenProgList[row]["align"][0])
                    self.Parent.spinBox_Align_y.setValue(self.screenProgList[row]["align"][1])
                    self.Parent.spinBox_Zoom.setValue(self.screenProgList[row]["scale"])
                    self.Parent.chk_AutoZoom.setChecked(self.screenProgList[row]["autoScale"])
                    self.Parent.chk_Argv1.setChecked(self.screenProgList[row]["scaleSysFontOnly"])
                    self.Parent.lineEdit_Text.setText(self.screenProgList[row]["text"])
                    self.Parent.combo_SingleColorChoose.setCurrentText(self.screenProgList[row]["color_1"])
                    color = (self.screenProgList[row]["color_RGB"][0], self.screenProgList[row]["color_RGB"][1], self.screenProgList[row]["color_RGB"][2])
                    self.Parent.btn_Colorful_ChooseColor.setStyleSheet(f"background-color: rgb{color}")

                    try:
                        self.Parent.spin_FontSize_2.setValue(self.screenProgList[row]["ascFontSize"])
                        self.Parent.checkBox_rollAscii.setChecked(self.screenProgList[row]["rollAscii"])
                        self.Parent.spinBox_Argv_3.setValue(self.screenProgList[row]["argv_3"])
                        self.Parent.spinBox_Y_Offset_2.setValue(self.screenProgList[row]["y_offset_asc"])
                        self.Parent.spinBox_X_Offset.setValue(self.screenProgList[row]["x_offset"])
                    except:
                        print("尝试读取1版数据")
                        self.screenProgList[row]["ascFontSize"] = 16
                        self.screenProgList[row]["argv_3"] = 1
                        self.screenProgList[row]["y_offset_asc"] = 0
                        self.screenProgList[row]["x_offset"] = 0

                    try:
                        self.Parent.spinBox_Y_GlobalOffset.setValue(self.screenProgList[row]["y_offset_global"])
                    except:
                        print("尝试读取2版数据") # 尚未开发完成

                    try:
                        if self.screenProgList[row]["richText"][0]:
                            o_str = self.screenProgList[row]["text"]
                            items = ast.literal_eval(o_str)
                            n_str = ""
                            for c in items:
                                n_str += c['char']
                            self.Parent.lineEdit_Text.setText(n_str)
                    except:
                        print("未找到富文本选项")

    def save_progArgv(self):
        r = self.Parent.currentProg
        row = None
        if isinstance(r,int):
            row = self.Parent.selected_row(self.Parent.tableWidget_Screens)
            if isinstance(row,int):
                self.screenProgList[row]["font"] = self.Parent.combo_Font.currentText()
                self.screenProgList[row]["fontSize"] = self.Parent.spin_FontSize.value()
                self.screenProgList[row]["ascFont"] = self.Parent.combo_ASCII_Font.currentText()
                self.screenProgList[row]["ascFontSize"] = self.Parent.spin_FontSize_2.value()
                self.screenProgList[row]["sysFontOnly"] = self.Parent.checkBox_sysFont.isChecked()
                self.screenProgList[row]["rollAscii"] = self.Parent.checkBox_rollAscii.isChecked()
                self.screenProgList[row]["appearance"] = self.Parent.combo_Show.currentText()
                self.screenProgList[row]["vertical"] = False if self.Parent.combo_TextDirect.currentText() == "横向" else True 
                self.screenProgList[row]["argv_1"] = self.Parent.spinBox_Argv_1.value()
                self.screenProgList[row]["argv_2"] = self.Parent.spinBox_Argv_2.value()
                self.screenProgList[row]["argv_3"] = self.Parent.spinBox_Argv_3.value()
                self.screenProgList[row]["spacing"] = self.Parent.spinBox_WordSpace.value()
                self.screenProgList[row]["bold"][0] = self.Parent.spinBox_BoldSizeX.value()
                self.screenProgList[row]["bold"][1] = self.Parent.spinBox_BoldSizeY.value()
                self.screenProgList[row]["y_offset"] = self.Parent.spinBox_Y_Offset.value()
                self.screenProgList[row]["y_offset_asc"] = self.Parent.spinBox_Y_Offset_2.value()
                self.screenProgList[row]["x_offset"] = self.Parent.spinBox_X_Offset.value()
                self.screenProgList[row]["y_offset_global"] = self.Parent.spinBox_Y_GlobalOffset.value()
                self.screenProgList[row]["align"][0] = self.Parent.spinBox_Align_x.value()
                self.screenProgList[row]["align"][1] = self.Parent.spinBox_Align_y.value()
                self.screenProgList[row]["scale"] = self.Parent.spinBox_Zoom.value()
                self.screenProgList[row]["autoScale"] = self.Parent.chk_AutoZoom.isChecked()
                self.screenProgList[row]["scaleSysFontOnly"] = self.Parent.chk_Argv1.isChecked()
                # self.screenProgList[row]["text"] = self.Parent.lineEdit_Text.text()  # 见下
                self.screenProgList[row]["color_1"] = self.Parent.combo_SingleColorChoose.currentText()

                r, g, b = self.screenProgList[row]["color_RGB"]
                #为适应彩色字符串修改
                simple_origin_text = self.Parent.lineEdit_Text.text()
                text_list_str = ""

                if "richText" in self.screenProgList[row].keys():
                    if self.screenProgList[row]["richText"][0]:    # 支持富文本
                        try:
                            text_list = ast.literal_eval(self.screenProgList[row]["text"])  # 并且实际上已经是字符串形式的列表
                            for i in text_list:
                                text_list_str += i["char"]
                                # print("i:",i,"text_list_str:",text_list_str)
                            if text_list_str != simple_origin_text:
                                color = ['#ff{:02X}{:02X}{:02X}'.format(r, g, b),text_list[0]["background"]]  # 如果一级界面上的字符串被再次编辑了，重新生成字符串列表，并保存为字符串形式，以第一个字符的颜色为基准
                                text_list = []
                                char_data = {
                                        'char': simple_origin_text,
                                        'foreground': color[0],
                                        'background': color[1]
                                    }
                                text_list.append(char_data)
                                self.screenProgList[row]["text"] = str(text_list)
                        except Exception as e:
                            print(e)
                    else:
                        self.screenProgList[row]["text"] = self.Parent.lineEdit_Text.text()
                else:
                    self.screenProgList[row]["text"] = self.Parent.lineEdit_Text.text()

            self.Parent.thisFile_saveStat.emit(False)

        self.Parent.change_program()     # 不可改变顺序
        self.show_scnUnit()

    def get_color(self):
        row = self.Parent.selected_row(self.Parent.tableWidget_Screens)
        if isinstance(row,int):
            col = QColorDialog.getColor()
            if col.isValid():
                color = [col.red(), col.green(), col.blue()]
                self.screenProgList[row]["color_RGB"] = color
                self.save_progArgv()
                self.show_progArgv()

    def save_img(self, index):
        row = self.Parent.currentLine
        self.update_self_colorMode()
        if isinstance(row,int):
            if self.colorMode == "1":
                extension = ["单色位图","bmp"]
            elif self.colorMode == "RGB":
                extension = ["便携式网络图形","png"]
            filedir,ok = QFileDialog.getSaveFileName(self.Parent,'导出图像','./',f'{extension[0]} (*.{extension[1]})')
            if ok:
                im = self.tmpBmp[index]
                if self.colorMode == "1":
                    im = im.point(lambda x: not x)  # 直接反转二值图像
                im.save(filedir)


class LineSettler():
    def __init__(self, parent):
        self.Parent = parent
        self.layoutHistoryCount = 0
        self.layoutHistory = []
        self.customLayouts = []
        self.customLButtons = []
        self.btn_w = 600
        self.btn_h = 220
        self.initUI()

    def initUI(self):
        self.Parent.statusBar().showMessage("请先添加线路，然后为各个路牌设置布局，再添加节目，选择节目后，再为屏幕的每个分区设置显示的内容！")
        self.Parent.btn_SaveChange.clicked.connect(self.ok_layout)
        self.Parent.combo_LayoutChoose.highlighted.connect(self.set_linemode_pixmap)
        self.Parent.combo_LayoutChoose.currentTextChanged.connect(self.flush_width_height_spinbox)
        self.Parent.combo_LineScreensForLayout.currentTextChanged.connect(self.flush_width_height_spinbox)
        self.Parent.btn_LineSet.clicked.connect(lambda:self.reset_layout(True))
        self.Parent.btn_LineReSet.clicked.connect(lambda:self.reset_layout(False))

        self.Parent.spin_Width_1.setMinimum(4)
        self.Parent.spin_Width_2.setMinimum(4)
        self.Parent.spin_Height_1.setMinimum(4)
        self.Parent.spin_Height_2.setMinimum(4)

        QTimer.singleShot(0, self.set_pixmap)

    def set_pixmap(self):
        self.Parent.BtnWidget.label = QLabel(parent=self.Parent.BtnWidget)
        pixmap = QPixmap("./resources/welcome.png")
        pixmap = pixmap.scaledToWidth(self.Parent.BtnWidget.size().width())
        self.Parent.BtnWidget.label.setPixmap(pixmap)
        self.Parent.BtnWidget.label.show()

    def flush_verticalLayout_LayoutBtn(self):
        for widget in self.Parent.BtnWidget.findChildren(QWidget):
            widget.deleteLater()

    def get_currentScreen(self):
        screen = self.Parent.combo_LineScreensForLayout.currentText()
        
        if screen not in screenLink.keys():
            screen = "前路牌"
        screen = screenLink[screen]
        return screen

    def flush_width_height_spinbox(self):
        # 还要改进，设置可设置的值的范围
        row = self.Parent.currentLine
        if isinstance(row,int):
            self.Parent.spin_Width_2.setEnabled(False)
            if self.Parent.combo_LayoutChoose.currentText() in ["布局2","布局3","布局4","布局6"]:
                self.Parent.spin_Height_1.setEnabled(True)
            elif self.Parent.combo_LayoutChoose.currentText() in ["布局1","布局5"]:
                self.Parent.spin_Height_1.setEnabled(False)
            self.Parent.spin_Height_2.setEnabled(False)
            screen = self.get_currentScreen()
            screenSize = [self.Parent.LineEditor.LineInfoList[row][screen]["screenSize"][0],self.Parent.LineEditor.LineInfoList[row][screen]["screenSize"][1]]
            self.Parent.spin_Width_1.setValue(int(80*screenSize[0]/224))
            self.Parent.spin_Width_1.setMaximum(screenSize[0])
            self.Parent.spin_Height_1.setValue(int(screenSize[1]))
            self.Parent.spin_Height_1.setMaximum(screenSize[1])

            if self.Parent.LineEditor.LineInfoList[row]["preset"] == "自定义":
                self.layoutHistory = []
                layout = self.init_layout()
                self.layoutHistory.append(layout)
                self.show_custom_layout_btn()
                self.layoutHistory.append(copy.deepcopy(self.customLayouts))

    def set_linemode_pixmap(self):
        row = self.Parent.currentLine
        if isinstance(row,int):
            mode = self.Parent.LineEditor.LineInfoList[row]["preset"]
            if mode == "北京公交":
                pixmap = QPixmap("./resources/preset_BeijingBus.png")
            elif mode == "普通":
                pixmap = QPixmap("./resources/preset_CommonBus.png")
            pixmap = pixmap.scaledToWidth(self.Parent.BtnWidget.size().width())
            self.Parent.BtnWidget.label = QLabel(parent=self.Parent.BtnWidget)
            self.Parent.BtnWidget.label.setPixmap(pixmap)
            self.Parent.BtnWidget.label.show()

    def init_LineSetting(self):
        row = self.Parent.currentLine
        if isinstance(row,int):
            mode = self.Parent.LineEditor.LineInfoList[row]["preset"]
            screens = ["前路牌","后路牌","前侧路牌","后侧路牌"]
            screens_have = [self.Parent.LineEditor.LineInfoList[row]["frontScreen"]["enabled"],self.Parent.LineEditor.LineInfoList[row]["backScreen"]["enabled"],self.Parent.LineEditor.LineInfoList[row]["frontSideScreen"]["enabled"],self.Parent.LineEditor.LineInfoList[row]["backSideScreen"]["enabled"]]
            self.Parent.combo_LineScreensForLayout.clear()
            self.Parent.combo_LayoutChoose.clear()
            self.flush_verticalLayout_LayoutBtn()

            for i in range(len(screens_have)):
                if screens_have[i]:
                    self.Parent.combo_LineScreensForLayout.addItem(screens[i])

            if mode in ["北京公交","普通"]:
                self.Parent.spin_Width_1.setEnabled(True)
                self.Parent.spin_Height_1.setEnabled(True)
                self.Parent.btn_LineSet.setEnabled(False)
                self.Parent.btn_LineReSet.setEnabled(False)
                self.set_linemode_pixmap()
                self.Parent.combo_LayoutChoose.setEnabled(True)
                self.Parent.combo_LayoutChoose.addItems(["布局1","布局2","布局3","布局4","布局5","布局6"])    # screen["layout"]
                self.Parent.btn_SaveChange.setEnabled(True)
            else:
                self.Parent.spin_Width_1.setEnabled(False)
                self.Parent.spin_Height_1.setEnabled(False)
                self.Parent.spin_Width_2.setEnabled(False)
                self.Parent.spin_Height_2.setEnabled(False)
                self.Parent.combo_LayoutChoose.setEnabled(False)
                self.Parent.btn_LineSet.setEnabled(True)
                self.Parent.btn_LineReSet.setEnabled(True)
                self.Parent.btn_SaveChange.setEnabled(False)
                self.layoutHistoryCount = 0
                self.layoutHistory = []
                
            self.flush_width_height_spinbox()

    def retranslate_screenUnit_size(self):
        row = -1    # 只在添加线路后使用一次
        
        if isinstance(row,int):            
            for scn in screenLink.values():
                colorMode = self.Parent.LineEditor.LineInfoList[row][scn]["colorMode"]
                scnSize = self.Parent.LineEditor.LineInfoList[row][scn]["screenSize"]
                pointKind = str(self.Parent.LineEditor.LineInfoList[row][scn]["screenSize"][2]).replace(" ","")
                pointKind = pointKindDict[pointKind]
                newScn = copy.deepcopy(template_screenInfo[pointKind+"_"+colorMode])
                newScn["pointNum"] = [scnSize[0],scnSize[1]]
                self.Parent.LineEditor.LineInfoList[row][scn]["screenUnit"] = [newScn]

    def show_custom_layout_btn(self):
        row = self.Parent.currentLine
        if isinstance(row,int):
            self.flush_verticalLayout_LayoutBtn()
            screen = self.get_currentScreen()
            widgetSize = [self.Parent.BtnWidget.size().width(),self.Parent.BtnWidget.size().height()]
            screenSize = [self.Parent.LineEditor.LineInfoList[row][screen]["screenSize"][0],self.Parent.LineEditor.LineInfoList[row][screen]["screenSize"][1]]
            screenScale = self.Parent.LineEditor.LineInfoList[row][screen]["screenSize"][2]
            colorMode = self.Parent.LineEditor.LineInfoList[row][screen]["colorMode"]
            self.btn_w = widgetSize[0]
            self.btn_h = int((self.btn_w * screenSize[1] * screenScale[1]) / (screenSize[0] * screenScale[0]))
            if self.btn_h > widgetSize[1]:
                self.btn_w = int(self.btn_w * widgetSize[1] / self.btn_h)
                self.btn_h = widgetSize[1]
            if len(self.Parent.LineEditor.LineInfoList[row][screen]["screenUnit"]) != 0:
                self.customLayouts = self.Parent.LineEditor.LineInfoList[row][screen]["screenUnit"]   # 该线路的默认屏幕布局

            if len(self.customLayouts) == 0:
                self.customLButtons = []
                self.customLButtons.append(QPushButton("1",self.Parent.BtnWidget))
                self.customLButtons[0].setGeometry(0,0,self.btn_w,self.btn_h)
                self.customLButtons[0].clicked.connect(lambda: self.onButtonClick(colorMode))
                self.customLButtons[0].show()
                self.customLayouts.append(copy.deepcopy(template_screenInfo["midSize_"+colorMode]))
                self.customLayouts[-1]["position"] = [0,0]
                self.customLayouts[-1]["pointNum"] = [int(screenSize[0]*screenScale[0]/self.customLayouts[-1]["scale"][0]),int(screenSize[1]*screenScale[1]/self.customLayouts[-1]["scale"][1])]
            else:
                self.customLButtons = []
                for i in range(len(self.customLayouts)):
                    x = int(self.customLayouts[i]["position"][0]*self.btn_w/(screenSize[0]*screenScale[0]))
                    y = int(self.customLayouts[i]["position"][1]*self.btn_h/(screenSize[1]*screenScale[1]))
                    w = int(self.customLayouts[i]["pointNum"][0]*self.customLayouts[i]["scale"][0]*self.btn_w/(screenSize[0]*screenScale[0]))
                    h = int(self.customLayouts[i]["pointNum"][1]*self.customLayouts[i]["scale"][1]*self.btn_h/(screenSize[1]*screenScale[1]))
                    self.customLButtons.append(QPushButton(f"{i+1}",self.Parent.BtnWidget))
                    self.customLButtons[-1].clicked.connect(lambda: self.onButtonClick(colorMode))
                    self.customLButtons[-1].setGeometry(x,y,w,h)
                    self.customLButtons[-1].show()
            # self.Parent.ProgramSettler.show_scnUnit()

    def init_layout(self):
        row = self.Parent.currentLine
        if isinstance(row,int):
            screen = self.get_currentScreen()
            colorMode = self.Parent.LineEditor.LineInfoList[row][screen]["colorMode"]
            screenSize = [self.Parent.LineEditor.LineInfoList[row][screen]["screenSize"][0],self.Parent.LineEditor.LineInfoList[row][screen]["screenSize"][1]]
            screenScale = self.Parent.LineEditor.LineInfoList[row][screen]["screenSize"][2]
            pointKind = str(screenScale).replace(" ","")
            pointKind = pointKindDict[pointKind]
            layout = []
            layout.append(copy.deepcopy(template_screenInfo[pointKind+"_"+colorMode]))
            layout[-1]["position"] = [0,0]
            layout[-1]["pointNum"] = [screenSize[0],screenSize[1]]

            return layout

    def reset_layout(self,p):
        row = self.Parent.currentLine
        if isinstance(row,int):
            if p and self.layoutHistoryCount > 0:
                self.layoutHistoryCount-=1
            if not p and self.layoutHistoryCount < len(self.layoutHistory)-1:
                self.layoutHistoryCount+=1
            # print(self.layoutHistoryCount,self.layoutHistory,"\n\n")
            self.customLButtons = []
            screen = self.get_currentScreen()
            if len(self.layoutHistory) > 0:
                try:
                    self.Parent.LineEditor.LineInfoList[row][screen]["screenUnit"] = copy.deepcopy(self.layoutHistory[self.layoutHistoryCount])
                    self.customLayouts = self.Parent.LineEditor.LineInfoList[row][screen]["screenUnit"]
                except:
                    print("撤回出错")

            self.show_custom_layout_btn()
            self.Parent.thisFile_saveStat.emit(False)

    def add_custom_layout_pre(self,index):
        old_pointNum = self.customLayouts[index]["pointNum"]
        old_scale = self.customLayouts[index]["scale"]
        return old_pointNum,old_scale

    def add_custom_layout(self,index,pointKind,colormode,wh = "w",w = 0,h = 0):
        row = self.Parent.currentLine
        if isinstance(row,int):
            self.Parent.ProgramSheetManager.show_program()
            old_pointNum = self.customLayouts[index]["pointNum"]
            old_scale = self.customLayouts[index]["scale"]
            to_add = copy.deepcopy(template_screenInfo[pointKind+"_"+colormode])
            pointScale = to_add["scale"]
            x0,y0 = self.customLayouts[index]["position"][0],self.customLayouts[index]["position"][1]
            if wh == "h":
                width = old_pointNum[0]*old_scale[0]
                height = old_pointNum[1]*old_scale[1]
                nwp = int(width/pointScale[0])
                nhp = h
                owp = old_pointNum[0]
                ohp = int((height-nhp*pointScale[1])/old_scale[1])
                ox = x0
                oy = y0+nhp*pointScale[1]
            elif wh == "w":            
                width = old_pointNum[0]*old_scale[0]
                height = old_pointNum[1]*old_scale[1]
                nwp = w
                nhp = int(height/pointScale[1])
                owp = int((width-nwp*pointScale[0])/old_scale[0])
                ohp = old_pointNum[1]
                ox = x0+nwp*pointScale[0]
                oy = y0
            if 0 in [owp,ohp,nwp,nhp]:
                return
            else:
                self.customLayouts[index]["position"] = [ox,oy]
                self.customLayouts[index]["pointNum"] = [owp,ohp]
                to_add["position"]=[x0,y0]
                to_add["pointNum"]=[nwp,nhp]
                to_add,self.customLayouts[index] = self.customLayouts[index],to_add
                self.customLayouts.append(to_add)

    def change_custom_layout(self,index,pointKind,colormode):
        old_pointNum = self.customLayouts[index]["pointNum"]
        old_scale = self.customLayouts[index]["scale"]
        to_add = copy.deepcopy(template_screenInfo[pointKind+"_"+colormode])
        pointScale = to_add["scale"]
        to_add["position"] = self.customLayouts[index]["position"]
        to_add["pointNum"] = [int(old_pointNum[0]*old_scale[0]/pointScale[0]),int(old_pointNum[1]*old_scale[1]/pointScale[1])]
        self.customLayouts[index] = to_add

    def onButtonClick(self,colormode):
        row = self.Parent.currentLine
        if isinstance(row,int):
            mode = self.Parent.LineEditor.LineInfoList[row]["preset"]
            if mode != "自定义":
                return
        # 识别哪个按钮被点击
        sender = self.Parent.sender()
        if sender in self.customLButtons:
            index = self.customLButtons.index(sender)
            opn,ops = self.add_custom_layout_pre(index)
            SelfDefineLayoutDialog = SelfDefineLayout(self.Parent)
            SelfDefineLayoutDialog.set_value(opn,ops)
            SelfDefineLayoutDialog.can_w_h()
            if SelfDefineLayoutDialog.exec_() == QDialog.Accepted:
                self.layoutHistory = self.layoutHistory[0:self.layoutHistoryCount+1]
                layout = SelfDefineLayoutDialog.combo_Layout.currentText()
                pointKind = SelfDefineLayoutDialog.combo_PointKind.currentText()
                pointKind = pointKindDict[pointKind]
                w = SelfDefineLayoutDialog.spin_SetWidth.value()
                h = SelfDefineLayoutDialog.spin_SetHeight.value()
                if layout == "更改屏幕":
                    self.change_custom_layout(index,pointKind,colormode)
                elif layout == "垂直布局":
                    self.add_custom_layout(index,pointKind,colormode,"h",w,h)
                elif layout == "水平布局":
                    self.add_custom_layout(index,pointKind,colormode,"w",w,h)
                self.layoutHistory.append(copy.deepcopy(self.customLayouts))
                self.layoutHistoryCount = len(self.layoutHistory)-1
                self.show_custom_layout_btn()
                self.Parent.thisFile_saveStat.emit(False)

    def get_scn_pos_size(self,row,screen,w1,h1,enable_mode = True):
        mode = self.Parent.LineEditor.LineInfoList[row]["preset"]
        self.Parent.LineEditor.LineInfoList[row][screen]["screenUnit"] = []
        screenSize = [self.Parent.LineEditor.LineInfoList[row][screen]["screenSize"][0],self.Parent.LineEditor.LineInfoList[row][screen]["screenSize"][1]]
        screenScale = self.Parent.LineEditor.LineInfoList[row][screen]["screenSize"][2]
        width = screenSize[0]*screenScale[0]
        height = screenSize[1]*screenScale[1]
        if enable_mode:
            if mode == "北京公交":
                sc = [screenScale,[int(4*screenScale[0]/3),2*screenScale[0]]]
            elif mode == "普通":
                sc = [screenScale,screenScale]
        else:
            sc = [screenScale,screenScale]
        p = [[0,0],[0,0],[0,0],[0,0],[0,0]]
        si = [[0,0],[0,0],[0,0],[0,0],[0,0]]
        p[0][0] = 0
        p[0][1] = 0
        p[1][0] = 0
        p[1][1] = h1*sc[0][1]
        p[2][0] = w1*sc[0][0]
        p[2][1] = 0
        p[3][0] = width-w1*sc[0][0]
        p[3][1] = 0
        p[4][0] = width-w1*sc[0][0]
        p[4][1] = h1*sc[0][1]
        si[0][0] = int(w1)
        si[0][1] = int(h1)
        si[1][0] = int(w1)
        si[1][1] = int((height-h1*sc[0][1])/sc[0][1])
        si[2][0] = int((width-2*w1*sc[0][0])/sc[1][0])
        si[2][1] = int(height/sc[1][1])
        si[3][0] = int(w1)
        si[3][1] = int(h1)
        si[4][0] = int(w1)
        si[4][1] = int((height-h1*sc[0][1])/sc[0][1])

        return p,si

    def get_toadd_screenunit(self,xy,npxnpy,sizeName,ColorMode,singColor):
        scname = sizeName+"_"+ColorMode
        scn = copy.deepcopy(template_screenInfo[scname])
        scn["position"] = xy
        scn["pointNum"] = npxnpy
        if ColorMode == "1":
            scn["color0"],scn["color1"] = template_monochromeColors[singColor]
        return scn

    def ok_layout(self):
        row = self.Parent.currentLine
        if isinstance(row,int):
            mode = self.Parent.LineEditor.LineInfoList[row]["preset"]
            self.Parent.ProgramSheetManager.show_program()
            layout = self.Parent.combo_LayoutChoose.currentText()
            screen = self.get_currentScreen()
            colorMode = self.Parent.LineEditor.LineInfoList[row][screen]["colorMode"]
            self.Parent.LineEditor.LineInfoList[row][screen]["layout"] = layout

            w1 = self.Parent.spin_Width_1.value()
            h1 = self.Parent.spin_Height_1.value()
            if screen in ["frontSideScreen","backSideScreen"]:
                scn_argv = self.get_scn_pos_size(row,screen,w1,h1,False)
            else:
                scn_argv = self.get_scn_pos_size(row,screen,w1,h1)
            to_add = []
            m_size = "bigSizeScaled" if mode == "北京公交" else "midSize"
            scn_size = "bigSize" if screen in ["frontSideScreen","backSideScreen"]  else "midSize"
            m_size = scn_size if screen in ["frontSideScreen","backSideScreen"]  else m_size
            if layout == "布局1":
                to_add.append(self.get_toadd_screenunit(scn_argv[0][0],scn_argv[1][0],scn_size,colorMode,"yellow"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][2],scn_argv[1][2],m_size,colorMode,"red"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][3],scn_argv[1][3],scn_size,colorMode,"yellow"))
            elif layout == "布局2":
                to_add.append(self.get_toadd_screenunit(scn_argv[0][0],scn_argv[1][0],scn_size,colorMode,"yellow"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][1],scn_argv[1][1],scn_size,colorMode,"yellow"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][2],scn_argv[1][2],m_size,colorMode,"red"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][3],[scn_argv[1][3][0],scn_argv[1][3][1]+scn_argv[1][4][1]],scn_size,colorMode,"yellow"))
            elif layout == "布局3":
                to_add.append(self.get_toadd_screenunit(scn_argv[0][0],[scn_argv[1][0][0],scn_argv[1][0][1]+scn_argv[1][1][1]],scn_size,colorMode,"yellow"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][2],scn_argv[1][2],m_size,colorMode,"red"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][3],scn_argv[1][3],scn_size,colorMode,"yellow"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][4],scn_argv[1][4],scn_size,colorMode,"yellow"))
            elif layout == "布局4":
                to_add.append(self.get_toadd_screenunit(scn_argv[0][0],scn_argv[1][0],scn_size,colorMode,"yellow"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][1],scn_argv[1][1],scn_size,colorMode,"yellow"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][2],scn_argv[1][2],m_size,colorMode,"red"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][3],scn_argv[1][3],scn_size,colorMode,"yellow"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][4],scn_argv[1][4],scn_size,colorMode,"yellow"))
            elif layout == "布局5":
                scn_argv = self.get_scn_pos_size(row,screen,w1,h1,False)
                to_add.append(self.get_toadd_screenunit(scn_argv[0][0],[scn_argv[1][0][0],scn_argv[1][0][1]+scn_argv[1][1][1]],scn_size,colorMode,"red"))
                to_add.append(self.get_toadd_screenunit(scn_argv[0][2],[scn_argv[1][2][0]+scn_argv[1][3][0],scn_argv[1][2][1]],scn_size,colorMode,"yellow"))
            elif layout == "布局6":
                scn_argv = self.get_scn_pos_size(row,screen,w1,h1,False)
                to_add.append(self.get_toadd_screenunit(scn_argv[0][0],[scn_argv[1][0][0],scn_argv[1][0][1]+scn_argv[1][1][1]],scn_size,colorMode,"red"))
                to_add.append(self.get_toadd_screenunit([scn_argv[0][2][0],scn_argv[0][3][1]],[scn_argv[1][2][0]+scn_argv[1][3][0],scn_argv[1][3][1]],scn_size,colorMode,"yellow"))
                to_add.append(self.get_toadd_screenunit([scn_argv[0][2][0],scn_argv[0][4][1]],[scn_argv[1][2][0]+scn_argv[1][3][0],scn_argv[1][4][1]],scn_size,colorMode,"yellow"))
            aim_add = []
            add_to = True
            for i in range(len(to_add)):
                if 0 not in to_add[i]["pointNum"]:
                    aim_add.append(to_add[i])
            for s in aim_add:
                for v in s["pointNum"]:
                    if v <= 0:
                        add_to = False
            if add_to:
                self.Parent.LineEditor.LineInfoList[row][screen]["screenUnit"] = aim_add
            else:
                self.Parent.LineEditor.LineInfoList[row][screen]["screenUnit"] = [copy.deepcopy(template_screenInfo["midSize_1"])]
            self.Parent.ProgramSettler.show_scnUnit()

            self.Parent.thisFile_saveStat.emit(False)
        self.set_linemode_pixmap()

class LineController():
    def __init__(self, parent):
        self.Parent = parent
        # 线路管理表格
        self.Parent.tableWidget_lineChoose.setColumnCount(3)
        self.Parent.tableWidget_lineChoose.setSelectionBehavior(QAbstractItemView.SelectRows)    #设置表格的选取方式是行选取
        self.Parent.tableWidget_lineChoose.setSelectionMode(QAbstractItemView.SingleSelection)    #设置选取方式为单个选取
        self.Parent.tableWidget_lineChoose.setHorizontalHeaderLabels(["线路名称","预设","刷新率"])   #设置行表头
        self.Parent.tableWidget_lineChoose.setColumnWidth(0,120)
        self.Parent.tableWidget_lineChoose.setColumnWidth(1,90)
        self.Parent.tableWidget_lineChoose.setColumnWidth(2,70)
        self.Parent.tableWidget_lineChoose.setEditTriggers(QAbstractItemView.NoEditTriggers)  #始终禁止编辑
        self.Parent.tableWidget_lineChoose.verticalHeader().setDefaultSectionSize(18)
        self.Parent.tableWidget_lineChoose.rowMoved.connect(self.onRowMoved)

        self.Parent.combo_FlushRate.addItems(["60","54","50","48","30","24","18","15"])

        self.Parent.LineNameEdit.editingFinished.connect(self.change_name_time)
        self.Parent.combo_FlushRate.currentTextChanged.connect(self.change_name_time)
        self.Parent.btn_newLine.clicked.connect(self.new_busLine_openDialog)
        self.Parent.btn_delLine.clicked.connect(self.del_busLine)
        self.Parent.btn_MvUp_BusLine.clicked.connect(self.mv_up_busLine)
        self.Parent.btn_MvDn_BusLine.clicked.connect(self.mv_dn_busLine)

    def show_name_time(self):
        row = self.Parent.currentLine
        if isinstance(row,int):
            dt = self.Parent.LineEditor.LineInfoList[row]
            self.Parent.LineNameEdit.setText(dt["lineName"])
            self.Parent.combo_FlushRate.setCurrentText(str(dt["flushRate"]))

    def change_name_time(self):
        row = self.Parent.currentLine
        if isinstance(row,int):
            n = self.Parent.LineNameEdit.text()
            f = int(self.Parent.combo_FlushRate.currentText())
            if self.Parent.LineEditor.LineInfoList[row]["lineName"] != n or self.Parent.LineEditor.LineInfoList[row]["flushRate"] != f:
                self.Parent.LineEditor.LineInfoList[row]["lineName"] = n
                self.Parent.LineEditor.LineInfoList[row]["flushRate"] = f
                self.Parent.thisFile_saveStat.emit(False)
            self.Parent.flush_table(self.Parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.Parent.LineEditor.LineInfoList])
            self.Parent.set_selected_row(self.Parent.tableWidget_lineChoose,row)

    def new_line(self):
        self.Parent.LineEditor.LineInfoList = []
        self.Parent.flush_table(self.Parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.Parent.LineEditor.LineInfoList])

        self.Parent.thisFile_saveStat.emit(False)

    def new_busLine_openDialog(self):
        dialog = NewALine(self.Parent)
        dialog.dataEntered.connect(self.new_busLine_EnterData)
        dialog.exec_()
        
    def new_busLine_EnterData(self,data):
        self.Parent.LineEditor.add_data(data)
        self.Parent.LineSettler.retranslate_screenUnit_size()
        self.Parent.flush_table(self.Parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.Parent.LineEditor.LineInfoList])
        self.Parent.set_selected_row(self.Parent.tableWidget_lineChoose,len(self.Parent.LineEditor.LineInfoList)-1)
        self.Parent.thisFile_saveStat.emit(False)

    def copy_busLine(self):
        row = self.Parent.currentLine
        if row is not None:
            self.Parent.LineEditor.copy_data(row)
            self.Parent.flush_table(self.Parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.Parent.LineEditor.LineInfoList])
            self.Parent.set_selected_row(self.Parent.tableWidget_lineChoose,len(self.Parent.LineEditor.LineInfoList)-1)
            self.Parent.thisFile_saveStat.emit(False)

    def del_busLine(self):
        row = self.Parent.currentLine
        if row is not None:
            self.Parent.LineEditor.remove_data(row)
            self.Parent.flush_table(self.Parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.Parent.LineEditor.LineInfoList])
            self.Parent.set_selected_row(self.Parent.tableWidget_lineChoose,max(0,row-1))
            self.Parent.thisFile_saveStat.emit(False)

    def onRowMoved(self,drag,drop):
        self.Parent.LineEditor.move_row(drag,drop)
        self.Parent.thisFile_saveStat.emit(False)
        self.Parent.flush_table(self.Parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.Parent.LineEditor.LineInfoList])
        self.Parent.set_selected_row(self.Parent.tableWidget_lineChoose,drop)

    def mv_up_busLine(self):
        row = self.Parent.currentLine
        if row is not None:
            self.Parent.LineEditor.mv_up(row)
            self.Parent.thisFile_saveStat.emit(False)
        self.Parent.flush_table(self.Parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.Parent.LineEditor.LineInfoList])
        self.Parent.set_selected_row(self.Parent.tableWidget_lineChoose,max(0,row-1))

    def mv_dn_busLine(self):
        row = self.Parent.currentLine
        if row is not None:
            self.Parent.LineEditor.mv_dn(row)
            self.Parent.thisFile_saveStat.emit(False)
        self.Parent.flush_table(self.Parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.Parent.LineEditor.LineInfoList])
        self.Parent.set_selected_row(self.Parent.tableWidget_lineChoose,min(len(self.Parent.LineEditor.LineInfoList)-1,row+1))

class LineEditor():
    def __init__(self):
        self.LineInfoList = []

    def add_data(self,linedata):
        if linedata[1] == "北京公交":
            lineInfo = copy.deepcopy(template_busLine_bjbus)
        elif linedata[1] == "普通":
            lineInfo = copy.deepcopy(template_busLine_common)
        else:
            lineInfo = copy.deepcopy(template_busLine_custom)
        lineInfo["lineName"],lineInfo["preset"],lineInfo["flushRate"] = linedata[0],linedata[1],linedata[2]
        lineInfo["frontScreen"]["enabled"],lineInfo["frontScreen"]["colorMode"],lineInfo["frontScreen"]["screenSize"][0],lineInfo["frontScreen"]["screenSize"][1],lineInfo["frontScreen"]["screenSize"][2] = linedata[3][0],linedata[3][1],linedata[3][2],linedata[3][3],linedata[3][4]
        lineInfo["backScreen"]["enabled"],lineInfo["backScreen"]["colorMode"],lineInfo["backScreen"]["screenSize"][0],lineInfo["backScreen"]["screenSize"][1],lineInfo["backScreen"]["screenSize"][2] = linedata[4][0],linedata[4][1],linedata[4][2],linedata[4][3],linedata[4][4]
        lineInfo["frontSideScreen"]["enabled"],lineInfo["frontSideScreen"]["colorMode"],lineInfo["frontSideScreen"]["screenSize"][0],lineInfo["frontSideScreen"]["screenSize"][1],lineInfo["frontSideScreen"]["screenSize"][2] = linedata[5][0],linedata[5][1],linedata[5][2],linedata[5][3],linedata[5][4]
        lineInfo["backSideScreen"]["enabled"],lineInfo["backSideScreen"]["colorMode"],lineInfo["backSideScreen"]["screenSize"][0],lineInfo["backSideScreen"]["screenSize"][1],lineInfo["backSideScreen"]["screenSize"][2] = linedata[6][0],linedata[6][1],linedata[6][2],linedata[6][3],linedata[6][4]
        self.LineInfoList.append(lineInfo)

    def remove_data(self,row):
        self.LineInfoList.pop(row)

    def copy_data(self,row):
        self.LineInfoList.append(copy.deepcopy(self.LineInfoList[row]))

    def move_row(self,drag,drop):
        if drag != drop:
            moving_data = self.LineInfoList[drag]
            self.LineInfoList.pop(drag)
            self.LineInfoList.insert(drop,moving_data)
    
    def mv_up(self,row):
        if row > 0:
            self.LineInfoList[row],self.LineInfoList[row-1] = self.LineInfoList[row-1],self.LineInfoList[row]

    def mv_dn(self,row):
        if row < len(self.LineInfoList)-1:
            self.LineInfoList[row],self.LineInfoList[row+1] = self.LineInfoList[row+1],self.LineInfoList[row]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MainWindow()
    myWindow.show()
    sys.exit(app.exec_())