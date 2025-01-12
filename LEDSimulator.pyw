import sys, os, ast, copy, datetime
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QMainWindow, QAbstractItemView, QTableWidgetItem, QHeaderView, QFileDialog, QPushButton, QLabel, QColorDialog, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon, QTextCharFormat
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

#适配高分辨率
# QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

# 屏幕尺寸相关信息
pointKindDict = {"(6,6)":"midSize","(8,8)":"bigSize","(8,12)":"bigSizeScaled","(6,8)":"midSizeScaled68","(8,10)":"midSizeScaled810","(3,3)":"miniSize","(4,4)":"smallSize","(4,6)":"smallSizeScaled"}
ledTypes = [i for i in pointKindDict.keys()]
scales = [ast.literal_eval(i) for i in ledTypes]

screenLink = {"前路牌":"frontScreen","后路牌":"backScreen","前侧路牌":"frontSideScreen","后侧路牌":"backSideScreen"}


class AboutWindow(QWidget,Ui_Form):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("关于")
        pixmap = QPixmap("./resources/welcome2.png")
        pixmap = pixmap.scaledToWidth(360)
        self.label_6.setPixmap(pixmap)

class NewALine(QDialog,Ui_NewALine):
    dataEntered = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.initUI()
        self.setWindowTitle("LED模拟器 新建线路")

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

class MainWindow(QMainWindow, Ui_ControlPanel):
    thisFile_saveStat = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.currentFileDir = ""
        self.currentFileName = ""
        self.thisFileSaved = True
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
        self.tableWidget_ProgramSheet.itemSelectionChanged.connect(self.change_program)
        self.tableWidget_ProgramSheet.pressed.connect(self.change_program)
        self.tableWidget_lineChoose.itemSelectionChanged.connect(self.close_all_screen)
        self.thisFile_saveStat.connect(self.set_window_title)

        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.getFps)
        self.timer1.start(1000)

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

    def turn_on_all_screen(self):
        self.close_all_screen()
        row = self.selected_row(self.tableWidget_lineChoose)
        h = 0
        if isinstance(row,int):
            
            for screen in screenLink.values():
                try:
                    screen.close()
                except Exception as e:
                    print("turn_on_all_screen: ", e)
                if self.LineEditor.LineInfoList[row][screen]["enabled"]:
                    try:
                        scn = ScreenController(flushRate=self.LineEditor.LineInfoList[row]["flushRate"],screenInfo={"colorMode":self.LineEditor.LineInfoList[row][screen]["colorMode"],"screenSize":self.LineEditor.LineInfoList[row][screen]["screenSize"]},screenProgramSheet=self.LineEditor.LineInfoList[row]["programSheet"],FontIconMgr=self.IconManager.FontMgr,toDisplay=screen)
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
        row = self.selected_row(self.tableWidget_lineChoose)
        if isinstance(row,int):
            self.close_all_screen()
            screen = self.get_currentScreen()
            scn = ScreenController(flushRate=self.LineEditor.LineInfoList[row]["flushRate"],screenInfo={"colorMode":self.LineEditor.LineInfoList[row][screen]["colorMode"],"screenSize":self.LineEditor.LineInfoList[row][screen]["screenSize"]},screenProgramSheet=self.LineEditor.LineInfoList[row]["programSheet"],FontIconMgr=self.IconManager.FontMgr,toDisplay=screen)
            scn.move(100,100)
            self.LedScreens[screen] = scn
        self.change_program()

    def change_program(self):   # 切换正在显示的节目
        line_row = self.selected_row(self.tableWidget_lineChoose)
        if isinstance(line_row,int):
            programSheet = self.LineEditor.LineInfoList[line_row]["programSheet"]
            row = self.selected_row(self.tableWidget_ProgramSheet)
            if isinstance(row,int):
                
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
        self.parent = parent
        self.FontMgr = FontManager()
        self.IconLib = self.FontMgr.icon_dict
        self.data = []
        self.initUI()

    def initUI(self):
        # 图标管理表格
        self.parent.tableWidget_Icons.verticalHeader().setVisible(False)
        self.parent.tableWidget_Icons.setColumnCount(2)
        self.parent.tableWidget_Icons.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parent.tableWidget_Icons.setSelectionMode(QAbstractItemView.SingleSelection)
        self.parent.tableWidget_Icons.setHorizontalHeaderLabels(["图标代号","预览"])
        self.parent.tableWidget_Icons.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.parent.tableWidget_Icons.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.parent.tableWidget_Icons.verticalHeader().setDefaultSectionSize(64)

        self.parent.btn_LoadIcons.clicked.connect(self.add_icon)
        self.parent.tableWidget_Icons.doubleClicked.connect(self.use_icom)

        self.flush_table()

    def flush_table(self):
        data = self.data = []
        for key,value in self.IconLib.items():
            data.append([key.strip("`"),value])
        self.parent.tableWidget_Icons.setRowCount(0)
        for row in range(len(data)):
            self.parent.tableWidget_Icons.insertRow(row)
            col = 0
            item = QTableWidgetItem(str(data[row][col]))
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignCenter)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)    #设置为只可选择
            self.parent.tableWidget_Icons.setItem(row,col,item)
            col = 1
            item = QTableWidgetItem()
            item.setData(Qt.DecorationRole, QPixmap(str(data[row][col])))
            self.parent.tableWidget_Icons.setItem(row, col, item)

    def add_icon(self):
        file_dir,ok = QFileDialog.getOpenFileName(self.parent,'打开','./','图标信息 (*.info)')
        if ok:
            self.FontMgr.icon_info.add(file_dir)
            self.FontMgr.get_icon_list()
            self.IconLib = self.FontMgr.icon_dict
            self.flush_table()

    def use_icom(self):
        row = self.parent.selected_row(self.parent.tableWidget_Icons)
        if isinstance(row,int):
            ot = self.parent.lineEdit_Text.text()
            ot = ot + "`" + self.data[row][0] + "`"
            self.parent.lineEdit_Text.setText(ot)
    
class ProgramSheetManager():
    def __init__(self, parent):
        self.parent = parent
        self.programSheet = []
        self.initUI()

    def initUI(self):
        # 节目单管理表格
        self.parent.tableWidget_ProgramSheet.setColumnCount(2)
        self.parent.tableWidget_ProgramSheet.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parent.tableWidget_ProgramSheet.setSelectionMode(QAbstractItemView.SingleSelection)
        self.parent.tableWidget_ProgramSheet.setHorizontalHeaderLabels(["节目名称","持续时间"])
        self.parent.tableWidget_ProgramSheet.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.parent.tableWidget_ProgramSheet.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.parent.tableWidget_ProgramSheet.verticalHeader().setDefaultSectionSize(18)

        self.parent.spinBox.setMaximum(3600*24)
        self.parent.spinBox.setMinimum(-1)

        self.parent.tableWidget_lineChoose.itemSelectionChanged.connect(self.show_program)
        self.parent.tableWidget_ProgramSheet.itemSelectionChanged.connect(self.show_name_time)
        self.parent.tableWidget_ProgramSheet.rowMoved.connect(self.move_program)
        self.parent.lineEdit_ProgramName.editingFinished.connect(self.change_name_time)
        self.parent.spinBox.editingFinished.connect(self.change_name_time)
        self.parent.btn_Add.clicked.connect(self.new_program)
        self.parent.btn_MvUp_Program.clicked.connect(self.mv_up_program)
        self.parent.btn_MvDn_Program.clicked.connect(self.mv_dn_program)
        self.parent.btn_CopyProgram.clicked.connect(self.copy_program)
        self.parent.btn_Remove.clicked.connect(self.del_program)

    def show_program(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            self.programSheet = self.parent.LineEditor.LineInfoList[row]["programSheet"]
            data = [[p[0],p[1]] for p in self.programSheet]
            self.parent.flush_table(self.parent.tableWidget_ProgramSheet,data)

    def show_name_time(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            self.parent.lineEdit_ProgramName.setText(self.programSheet[row][0])
            self.parent.spinBox.setValue(self.programSheet[row][1])

    def change_name_time(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            name = self.parent.lineEdit_ProgramName.text()
            time = self.parent.spinBox.value()
            if self.programSheet[row][0] != name or self.programSheet[row][1] != time:
                self.programSheet[row][0] = self.parent.lineEdit_ProgramName.text()
                self.programSheet[row][1] = self.parent.spinBox.value()
                self.parent.thisFile_saveStat.emit(False)
            self.show_program()
            item = self.parent.tableWidget_ProgramSheet.item(row,0)
            self.parent.tableWidget_ProgramSheet.setCurrentItem(item)

    def new_program(self,):
        progName = self.parent.lineEdit_ProgramName.text()
        sec = self.parent.spinBox.value()
        
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            sbp = [[],[]]
            sbpdict = dict()
            for screen in screenLink.values():
                if self.parent.LineEditor.LineInfoList[row][screen]["enabled"]:
                    sbp = [[],[]]
                    for i in range(len(self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"])):
                        sbp[0].append(copy.deepcopy(self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"][i]))
                        sbp[1].append(copy.deepcopy(template_program_show))
                    sbpdict[screen] = sbp
            self.programSheet.append([progName,sec,sbpdict])
            self.parent.lineEdit_ProgramName.setText("")
            self.parent.spinBox.setValue(0)
            self.show_program()
            # print(self.programSheet)
            self.parent.thisFile_saveStat.emit(False)

    def del_program(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            self.programSheet.pop(row)
            self.parent.thisFile_saveStat.emit(False)
        self.show_program()

    def copy_program(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            self.programSheet.append(copy.deepcopy(self.programSheet[row]))
            self.parent.thisFile_saveStat.emit(False)
        self.show_program()

    def move_program(self,drag,drop):
        if drag != drop:
            self.programSheet.insert(drop,self.programSheet[drag])
            if drag < drop:
                self.programSheet.pop(drag)
            if drag > drop:
                self.programSheet.pop(drag+1)
            self.parent.thisFile_saveStat.emit(False)
        self.show_program()

    def mv_up_program(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            if row > 0:
                self.programSheet[row],self.programSheet[row-1] = self.programSheet[row-1],self.programSheet[row]
                self.parent.thisFile_saveStat.emit(False)
        self.show_program()

    def mv_dn_program(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            if row < len(self.programSheet)-1:
                self.programSheet[row],self.programSheet[row+1] = self.programSheet[row+1],self.programSheet[row]
                self.parent.thisFile_saveStat.emit(False)
        self.show_program()

class ProgramSettler():
    def __init__(self, parent):
        self.parent = parent
        self.FontMgr = FontManager()
        self.FontLib = self.FontMgr.font_dict.keys()
        self.ChFont = [c for c in self.FontLib if "asc" not in c.lower()]
        self.TtFont = [c for c in self.FontLib if "asc" not in c.lower() and "hzk" not in c.lower()]
        self.EngFont = [c for c in self.FontLib if "asc" in c.lower()]
        self.initUI()

    def initUI(self):
        # 屏幕分区管理表格
        self.parent.tableWidget_Screens.setColumnCount(4)
        self.parent.tableWidget_Screens.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parent.tableWidget_Screens.setSelectionMode(QAbstractItemView.SingleSelection)
        self.parent.tableWidget_Screens.verticalHeader().setVisible(False)
        self.parent.tableWidget_Screens.setHorizontalHeaderLabels(["屏幕名称","屏幕规格","灯珠规格","内容大小"])
        self.parent.tableWidget_Screens.setColumnWidth(0,120)
        self.parent.tableWidget_Screens.setColumnWidth(1,100)
        self.parent.tableWidget_Screens.setColumnWidth(2,100)
        self.parent.tableWidget_Screens.setColumnWidth(3,100)
        self.parent.tableWidget_Screens.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.parent.tableWidget_Screens.verticalHeader().setDefaultSectionSize(18)

        self.parent.combo_Font.addItems(self.ChFont)
        self.parent.combo_ASCII_Font.addItems(self.EngFont)
        self.parent.combo_Show.addItems(["静止","闪烁","向左滚动","向上滚动","向左移到中间","向上移到中间","中间向左移开","中间向上移开","跳跃向左移动","跳跃向上移动","向右滚动","向下滚动","向右移到中间","向下移到中间","中间向右移开","中间向下移开","跳跃向右移动","跳跃向下移动","上下反复跳跃移动",])
        self.parent.combo_TextDirect.addItems(["横向","竖向"])
        self.parent.combo_SingleColorChoose.addItems(template_monochromeColors.keys())

        self.parent.spin_FontSize.setMaximum(64)
        self.parent.spin_FontSize.setMinimum(6)
        self.parent.spin_FontSize.setValue(16)
        self.parent.spin_FontSize_2.setMaximum(64)
        self.parent.spin_FontSize_2.setMinimum(6)
        self.parent.spin_FontSize_2.setValue(16)
        self.parent.spinBox_Argv_1.setMaximum(60)
        self.parent.spinBox_Argv_1.setMinimum(1)
        self.parent.spinBox_Argv_2.setMaximum(60)
        self.parent.spinBox_Argv_2.setMinimum(1)
        self.parent.spinBox_Argv_3.setMaximum(60)
        self.parent.spinBox_Argv_3.setMinimum(0)
        self.parent.spinBox_WordSpace.setMaximum(100)
        self.parent.spinBox_WordSpace.setMinimum(-100)
        self.parent.spinBox_BoldSizeX.setMaximum(4)
        self.parent.spinBox_BoldSizeX.setMinimum(1)
        self.parent.spinBox_BoldSizeY.setMaximum(4)
        self.parent.spinBox_BoldSizeY.setMinimum(1)
        self.parent.spinBox_Y_Offset.setMaximum(64)
        self.parent.spinBox_Y_Offset.setMinimum(-64)
        self.parent.spinBox_Y_Offset_2.setMaximum(64)
        self.parent.spinBox_Y_Offset_2.setMinimum(-64)
        self.parent.spinBox_X_Offset.setMaximum(65536)
        self.parent.spinBox_X_Offset.setMinimum(-65536)
        self.parent.spinBox_Y_GlobalOffset.setMaximum(65536)
        self.parent.spinBox_Y_GlobalOffset.setMinimum(-65536)
        self.parent.spinBox_Align_x.setMaximum(1)
        self.parent.spinBox_Align_x.setMinimum(-1)
        self.parent.spinBox_Align_y.setMaximum(1)
        self.parent.spinBox_Align_y.setMinimum(-1)
        self.parent.spinBox_Zoom.setMaximum(200)
        self.parent.spinBox_Zoom.setMinimum(40)
        self.parent.spinBox_Zoom.setValue(100)   

        self.parent.tableWidget_lineChoose.itemSelectionChanged.connect(self.init_ProgramSetting)
        self.parent.tableWidget_ProgramSheet.itemSelectionChanged.connect(self.show_scnUnit)
        self.parent.tableWidget_ProgramSheet.pressed.connect(self.show_scnUnit)
        self.parent.tableWidget_Screens.itemSelectionChanged.connect(self.show_progArgv)
        self.parent.tableWidget_Screens.rowMoved.connect(self.move_scnUnitProg)
        self.parent.combo_LineScreens.currentTextChanged.connect(self.show_scnUnit)
        self.parent.btn_ok.clicked.connect(self.save_progArgv)
        self.parent.btn_Colorful_ChooseColor.clicked.connect(self.get_color)
        self.parent.combo_Show.currentTextChanged.connect(self.update_argv)
        self.parent.checkBox_sysFont.stateChanged.connect(self.change_EngFont_set)
        self.parent.btn_textSetting.clicked.connect(self.set_colorstr_multiLine)
        
        self.parent.lineEdit_Text.editingFinished.connect(self.save_progArgv)

        self.parent.btn_ok.setShortcut(Qt.Key_Return)

    def set_colorstr_multiLine(self):
        colorMode = "1"
        multiLine = False
        lineSpace = 1
        richText = [False,False]
        text = ""
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            screen = self.get_currentScreen()
            colorMode = self.parent.LineEditor.LineInfoList[row][screen]["colorMode"]
            row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
            if isinstance(row,int):
                self.screenProgList = self.parent.ProgramSheetManager.programSheet[row][2][screen][1]
                row = self.parent.selected_row(self.parent.tableWidget_Screens)
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
                    ColorMultiLineDialog.set_value(text,multiLine,lineSpace,colorMode,richText)
                    if ColorMultiLineDialog.exec_() == QDialog.Accepted:
                        text, multiLine, lineSpace, richText = ColorMultiLineDialog.get_edit_result()

                        self.screenProgList[row]["text"] = text
                        self.screenProgList[row]["multiLine"] = multiLine
                        self.screenProgList[row]["lineSpace"] = lineSpace
                        self.screenProgList[row]["richText"] = richText
                        self.parent.change_program()
            self.parent.thisFile_saveStat.emit(False)
        
        self.show_progArgv()

    def change_EngFont_set(self):
        if self.parent.checkBox_sysFont.isChecked():
            self.parent.combo_ASCII_Font.clear()
            self.parent.combo_ASCII_Font.addItems(self.TtFont)
        else:
            self.parent.combo_ASCII_Font.clear()
            self.parent.combo_ASCII_Font.addItems(self.EngFont)

    def init_ProgramSetting(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            screens = ["前路牌","后路牌","前侧路牌","后侧路牌"]
            screens_have = [self.parent.LineEditor.LineInfoList[row]["frontScreen"]["enabled"],self.parent.LineEditor.LineInfoList[row]["backScreen"]["enabled"],self.parent.LineEditor.LineInfoList[row]["frontSideScreen"]["enabled"],self.parent.LineEditor.LineInfoList[row]["backSideScreen"]["enabled"]]
            self.parent.combo_LineScreens.clear()

            for i in range(len(screens_have)):
                if screens_have[i]:
                    self.parent.combo_LineScreens.addItem(screens[i])

            self.show_scnUnit()

    def get_currentScreen(self):
        screen = self.parent.combo_LineScreens.currentText()
        
        if screen not in screenLink.keys():
            screen = "前路牌"
        screen = screenLink[screen]
        return screen
    
    def move_scnUnitProg(self,drag,drop):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            screen = self.get_currentScreen()
            screenUnitList = self.parent.ProgramSheetManager.programSheet[row][2][screen][0]
            screenProgList = self.parent.ProgramSheetManager.programSheet[row][2][screen][1]

            if drag != drop:
                screenUnitList.insert(drop,screenUnitList[drag])
                screenProgList.insert(drop,screenProgList[drag])

                if drag < drop:
                    screenUnitList.pop(drag)
                    screenProgList.pop(drag)

                if drag > drop:
                    screenUnitList.pop(drag+1)
                    screenProgList.pop(drag+1)

                self.parent.thisFile_saveStat.emit(False)

            QTimer.singleShot(0, self.show_scnUnit)


    def show_scnUnit(self):
        data = []
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            screen = self.get_currentScreen()
            screenUnitList = self.parent.ProgramSheetManager.programSheet[row][2][screen][0]
            screenProgList = self.parent.ProgramSheetManager.programSheet[row][2][screen][1]

            # 更改线路默认屏幕布局
            progrow = self.parent.selected_row(self.parent.tableWidget_lineChoose)  # 当前选择的线路 注意变量为 progrow
            if isinstance(progrow,int):
                self.parent.LineEditor.LineInfoList[progrow][screen]["screenUnit"] = copy.deepcopy(screenUnitList)
                self.parent.combo_LineScreensForLayout.setCurrentText(self.parent.combo_LineScreens.currentText())  # 当节目内容编辑的屏幕改变时，保持线路设置中的屏幕同步
                self.parent.LineSettler.show_custom_layout_btn()
            else:
                self.parent.flush_table(self.parent.tableWidget_ProgramSheet,[])
                return

            for i in range(min(len(screenProgList),len(screenUnitList))):
                p = screenProgList[i]
                Creater = BmpCreater(self.parent.IconManager.FontMgr,"1",(255,255,255),p["font"],p["ascFont"],p["sysFontOnly"],)
                _roll_asc = True
                if "rollAscii" in p.keys():
                    _roll_asc = p["rollAscii"]
                if "multiLine" in p.keys() and "lineSpace" in p.keys():
                    bmp = Creater.create_character(vertical=p["vertical"], roll_asc = _roll_asc, text=p["text"], ch_font_size=p["fontSize"], asc_font_size=p["ascFontSize"], ch_bold_size_x=p["bold"][0], ch_bold_size_y=p["bold"][1], space=p["spacing"], scale=p["scale"], auto_scale=p["autoScale"], scale_sys_font_only=p["scaleSysFontOnly"], new_width = screenUnitList[i]["pointNum"][0], new_height = screenUnitList[i]["pointNum"][1], y_offset = p["y_offset"], y_offset_asc = p["y_offset_asc"], style = p["align"], multi_line={"stat":p["multiLine"], "line_space": p["lineSpace"] })
                else:
                    bmp = Creater.create_character(vertical=p["vertical"], roll_asc = _roll_asc, text=p["text"], ch_font_size=p["fontSize"], asc_font_size=p["fontSize"], ch_bold_size_x=p["bold"][0], ch_bold_size_y=p["bold"][1], space=p["spacing"], scale=p["scale"], auto_scale=p["autoScale"], scale_sys_font_only=p["scaleSysFontOnly"], new_width = screenUnitList[i]["pointNum"][0], new_height = screenUnitList[i]["pointNum"][1], y_offset = p["y_offset"], y_offset_asc = p["y_offset"], style = p["align"])
                data.append([i+1,str(screenUnitList[i]["pointNum"]),str(screenUnitList[i]["pointSize"]),bmp.size])

            current_row = self.parent.selected_row(self.parent.tableWidget_Screens)
            if current_row is None:
                current_row = 0
            # print(data)
            self.parent.flush_table(self.parent.tableWidget_Screens,data)
            self.parent.tableWidget_Screens.setCurrentItem(self.parent.tableWidget_Screens.item(current_row,0))
        else:
            self.parent.flush_table(self.parent.tableWidget_Screens,[])

        ## 添加节目的地方和更改布局的地方
            
    def update_argv(self):
        mode = self.parent.combo_Show.currentText()
        self.parent.spinBox_Argv_1.setEnabled(True)
        self.parent.spinBox_Argv_2.setEnabled(True)
        self.parent.spinBox_Argv_3.setEnabled(True)
        if "滚动" in mode:
            self.parent.label_Argv_1.setText("移动速度")
            self.parent.label_Argv_2.setText("滚动对象间距")
            self.parent.label_Argv_3.setText("步长")
            self.parent.spinBox_Argv_1.setMaximum(60)
            self.parent.spinBox_Argv_1.setMinimum(1)
            self.parent.spinBox_Argv_2.setMaximum(256)
            self.parent.spinBox_Argv_2.setMinimum(-1)
            self.parent.spinBox_Argv_2.setValue(-1)
            self.parent.spinBox_Argv_3.setMaximum(60)
            self.parent.spinBox_Argv_3.setMinimum(1)
        elif "移到" in mode:
            self.parent.label_Argv_1.setText("移动速度")
            self.parent.label_Argv_2.setText("时间")
            self.parent.label_Argv_3.setText("步长")
            self.parent.spinBox_Argv_1.setMaximum(60)
            self.parent.spinBox_Argv_1.setMinimum(1)
            self.parent.spinBox_Argv_2.setMaximum(60)
            self.parent.spinBox_Argv_2.setMinimum(1)
            self.parent.spinBox_Argv_3.setMaximum(60)
            self.parent.spinBox_Argv_3.setMinimum(1)
        elif "移开" in mode:
            self.parent.label_Argv_1.setText("移动速度")
            self.parent.label_Argv_2.setText("时间")
            self.parent.label_Argv_3.setText("步长")
            self.parent.spinBox_Argv_1.setMaximum(60)
            self.parent.spinBox_Argv_1.setMinimum(1)
            self.parent.spinBox_Argv_2.setMaximum(60)
            self.parent.spinBox_Argv_2.setMinimum(1)
            self.parent.spinBox_Argv_3.setMaximum(60)
            self.parent.spinBox_Argv_3.setMinimum(1)
        elif "跳跃" in mode:
            self.parent.label_Argv_1.setText("移动速度")
            self.parent.label_Argv_2.setText("移动步长")
            self.parent.label_Argv_3.setText("停靠时间")
            self.parent.spinBox_Argv_1.setMaximum(60)
            self.parent.spinBox_Argv_1.setMinimum(1)
            self.parent.spinBox_Argv_2.setMaximum(32)
            self.parent.spinBox_Argv_2.setMinimum(1)
            self.parent.spinBox_Argv_3.setMaximum(60)
            self.parent.spinBox_Argv_3.setMinimum(0)
        elif mode == "闪烁":
            self.parent.label_Argv_1.setText("亮时长")
            self.parent.label_Argv_2.setText("灭时长")
            self.parent.label_Argv_3.setText("")
            self.parent.spinBox_Argv_1.setMaximum(60)
            self.parent.spinBox_Argv_1.setMinimum(1)
            self.parent.spinBox_Argv_2.setMaximum(60)
            self.parent.spinBox_Argv_2.setMinimum(1)
            self.parent.spinBox_Argv_3.setEnabled(False)
        elif mode == "静止":
            self.parent.label_Argv_1.setText("")
            self.parent.label_Argv_2.setText("")
            self.parent.label_Argv_3.setText("")
            self.parent.spinBox_Argv_1.setEnabled(False)
            self.parent.spinBox_Argv_2.setEnabled(False)
            self.parent.spinBox_Argv_3.setEnabled(False)

    def show_progArgv(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            screen = self.get_currentScreen()
            colorMode = self.parent.LineEditor.LineInfoList[row][screen]["colorMode"]
            if colorMode == "1":
                self.parent.combo_SingleColorChoose.setEnabled(True)
                self.parent.btn_Colorful_ChooseColor.setEnabled(False)
            elif colorMode == "RGB":
                self.parent.combo_SingleColorChoose.setEnabled(False)
                self.parent.btn_Colorful_ChooseColor.setEnabled(True)
            row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
            if isinstance(row,int):
                self.screenProgList = self.parent.ProgramSheetManager.programSheet[row][2][screen][1]
                row = self.parent.selected_row(self.parent.tableWidget_Screens)
                if isinstance(row,int):
                    self.update_argv()
                    self.parent.combo_Font.setCurrentText(self.screenProgList[row]["font"])
                    self.parent.spin_FontSize.setValue(self.screenProgList[row]["fontSize"])
                    self.parent.checkBox_sysFont.setChecked(self.screenProgList[row]["sysFontOnly"])
                    self.parent.combo_ASCII_Font.setCurrentText(self.screenProgList[row]["ascFont"])
                    self.parent.combo_Show.setCurrentText(self.screenProgList[row]["appearance"])
                    self.parent.combo_TextDirect.setCurrentText("竖向" if self.screenProgList[row]["vertical"] else "横向")
                    self.parent.spinBox_Argv_1.setValue(self.screenProgList[row]["argv_1"])
                    self.parent.spinBox_Argv_2.setValue(self.screenProgList[row]["argv_2"])
                    self.parent.spinBox_WordSpace.setValue(self.screenProgList[row]["spacing"])
                    self.parent.spinBox_BoldSizeX.setValue(self.screenProgList[row]["bold"][0])
                    self.parent.spinBox_BoldSizeY.setValue(self.screenProgList[row]["bold"][1])
                    self.parent.spinBox_Y_Offset.setValue(self.screenProgList[row]["y_offset"])
                    self.parent.spinBox_Align_x.setValue(self.screenProgList[row]["align"][0])
                    self.parent.spinBox_Align_y.setValue(self.screenProgList[row]["align"][1])
                    self.parent.spinBox_Zoom.setValue(self.screenProgList[row]["scale"])
                    self.parent.chk_AutoZoom.setChecked(self.screenProgList[row]["autoScale"])
                    self.parent.chk_Argv1.setChecked(self.screenProgList[row]["scaleSysFontOnly"])
                    self.parent.lineEdit_Text.setText(self.screenProgList[row]["text"])
                    self.parent.combo_SingleColorChoose.setCurrentText(self.screenProgList[row]["color_1"])
                    color = (self.screenProgList[row]["color_RGB"][0], self.screenProgList[row]["color_RGB"][1], self.screenProgList[row]["color_RGB"][2])
                    self.parent.btn_Colorful_ChooseColor.setStyleSheet(f"background-color: rgb{color}")

                    try:
                        self.parent.spin_FontSize_2.setValue(self.screenProgList[row]["ascFontSize"])
                        self.parent.checkBox_rollAscii.setChecked(self.screenProgList[row]["rollAscii"])
                        self.parent.spinBox_Argv_3.setValue(self.screenProgList[row]["argv_3"])
                        self.parent.spinBox_Y_Offset_2.setValue(self.screenProgList[row]["y_offset_asc"])
                        self.parent.spinBox_X_Offset.setValue(self.screenProgList[row]["x_offset"])
                    except:
                        print("尝试读取1版数据")
                        self.screenProgList[row]["ascFontSize"] = 16
                        self.screenProgList[row]["argv_3"] = 1
                        self.screenProgList[row]["y_offset_asc"] = 0
                        self.screenProgList[row]["x_offset"] = 0

                    try:
                        self.parent.spinBox_Y_GlobalOffset.setValue(self.screenProgList[row]["y_offset_global"])
                    except:
                        print("尝试读取2版数据") # 尚未开发完成

                    try:
                        if self.screenProgList[row]["richText"][0]:
                            o_str = self.screenProgList[row]["text"]
                            items = ast.literal_eval(o_str)
                            n_str = ""
                            for c in items:
                                n_str += c['char']
                            self.parent.lineEdit_Text.setText(n_str)
                    except:
                        print("未找到富文本选项")

    def save_progArgv(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            row = self.parent.selected_row(self.parent.tableWidget_Screens)
            if isinstance(row,int):
                self.screenProgList[row]["font"] = self.parent.combo_Font.currentText()
                self.screenProgList[row]["fontSize"] = self.parent.spin_FontSize.value()
                self.screenProgList[row]["ascFont"] = self.parent.combo_ASCII_Font.currentText()
                self.screenProgList[row]["ascFontSize"] = self.parent.spin_FontSize_2.value()
                self.screenProgList[row]["sysFontOnly"] = self.parent.checkBox_sysFont.isChecked()
                self.screenProgList[row]["rollAscii"] = self.parent.checkBox_rollAscii.isChecked()
                self.screenProgList[row]["appearance"] = self.parent.combo_Show.currentText()
                self.screenProgList[row]["vertical"] = False if self.parent.combo_TextDirect.currentText() == "横向" else True 
                self.screenProgList[row]["argv_1"] = self.parent.spinBox_Argv_1.value()
                self.screenProgList[row]["argv_2"] = self.parent.spinBox_Argv_2.value()
                self.screenProgList[row]["argv_3"] = self.parent.spinBox_Argv_3.value()
                self.screenProgList[row]["spacing"] = self.parent.spinBox_WordSpace.value()
                self.screenProgList[row]["bold"][0] = self.parent.spinBox_BoldSizeX.value()
                self.screenProgList[row]["bold"][1] = self.parent.spinBox_BoldSizeY.value()
                self.screenProgList[row]["y_offset"] = self.parent.spinBox_Y_Offset.value()
                self.screenProgList[row]["y_offset_asc"] = self.parent.spinBox_Y_Offset_2.value()
                self.screenProgList[row]["x_offset"] = self.parent.spinBox_X_Offset.value()
                self.screenProgList[row]["y_offset_global"] = self.parent.spinBox_Y_GlobalOffset.value()
                self.screenProgList[row]["align"][0] = self.parent.spinBox_Align_x.value()
                self.screenProgList[row]["align"][1] = self.parent.spinBox_Align_y.value()
                self.screenProgList[row]["scale"] = self.parent.spinBox_Zoom.value()
                self.screenProgList[row]["autoScale"] = self.parent.chk_AutoZoom.isChecked()
                self.screenProgList[row]["scaleSysFontOnly"] = self.parent.chk_Argv1.isChecked()
                # self.screenProgList[row]["text"] = self.parent.lineEdit_Text.text()  # 见下
                self.screenProgList[row]["color_1"] = self.parent.combo_SingleColorChoose.currentText()

                r, g, b = self.screenProgList[row]["color_RGB"]
                #为适应彩色字符串修改
                simple_origin_text = self.parent.lineEdit_Text.text()
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
                        self.screenProgList[row]["text"] = self.parent.lineEdit_Text.text()
                else:
                    self.screenProgList[row]["text"] = self.parent.lineEdit_Text.text()

            self.parent.thisFile_saveStat.emit(False)

        self.parent.change_program()     # 不可改变顺序
        self.show_scnUnit()
        


    def get_color(self):
        row = self.parent.selected_row(self.parent.tableWidget_Screens)
        if isinstance(row,int):
            col = QColorDialog.getColor()
            if col.isValid():
                color = [col.red(), col.green(), col.blue()]
                self.screenProgList[row]["color_RGB"] = color
                self.save_progArgv()
                self.show_progArgv()
    
class LineSettler():
    def __init__(self, parent):
        self.parent = parent
        self.layoutHistoryCount = 0
        self.layoutHistory = []
        self.customLayouts = []
        self.customLButtons = []
        self.btn_w = 600
        self.btn_h = 220
        self.initUI()

    def initUI(self):
        self.parent.statusBar().showMessage("请先添加线路，然后为各个路牌设置布局，再添加节目，选择节目后，再为屏幕的每个分区设置显示的内容！")
        self.parent.btn_SaveChange.clicked.connect(self.ok_layout)
        self.parent.tableWidget_lineChoose.itemSelectionChanged.connect(self.init_LineSetting)
        self.parent.combo_LayoutChoose.highlighted.connect(self.set_linemode_pixmap)
        self.parent.combo_LayoutChoose.currentTextChanged.connect(self.flush_width_height_spinbox)
        self.parent.combo_LineScreensForLayout.currentTextChanged.connect(self.flush_width_height_spinbox)
        self.parent.btn_LineSet.clicked.connect(lambda:self.reset_layout(True))
        self.parent.btn_LineReSet.clicked.connect(lambda:self.reset_layout(False))

        self.parent.spin_Width_1.setMinimum(4)
        self.parent.spin_Width_2.setMinimum(4)
        self.parent.spin_Height_1.setMinimum(4)
        self.parent.spin_Height_2.setMinimum(4)

        QTimer.singleShot(0, self.set_pixmap)

    def set_pixmap(self):
        self.parent.BtnWidget.label = QLabel(parent=self.parent.BtnWidget)
        pixmap = QPixmap("./resources/welcome.png")
        pixmap = pixmap.scaledToWidth(self.parent.BtnWidget.size().width())
        self.parent.BtnWidget.label.setPixmap(pixmap)
        self.parent.BtnWidget.label.show()

    def flush_verticalLayout_LayoutBtn(self):
        for widget in self.parent.BtnWidget.findChildren(QWidget):
            widget.deleteLater()

    def get_currentScreen(self):
        screen = self.parent.combo_LineScreensForLayout.currentText()
        
        if screen not in screenLink.keys():
            screen = "前路牌"
        screen = screenLink[screen]
        return screen

    def flush_width_height_spinbox(self):
        # 还要改进，设置可设置的值的范围
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            self.parent.spin_Width_2.setEnabled(False)
            if self.parent.combo_LayoutChoose.currentText() in ["布局2","布局3","布局4","布局6"]:
                self.parent.spin_Height_1.setEnabled(True)
            elif self.parent.combo_LayoutChoose.currentText() in ["布局1","布局5"]:
                self.parent.spin_Height_1.setEnabled(False)
            self.parent.spin_Height_2.setEnabled(False)
            screen = self.get_currentScreen()
            screenSize = [self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][0],self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][1]]
            self.parent.spin_Width_1.setValue(int(80*screenSize[0]/224))
            self.parent.spin_Width_1.setMaximum(screenSize[0])
            self.parent.spin_Height_1.setValue(int(screenSize[1]))
            self.parent.spin_Height_1.setMaximum(screenSize[1])

            if self.parent.LineEditor.LineInfoList[row]["preset"] == "自定义":
                self.layoutHistory = []
                layout = self.init_layout()
                self.layoutHistory.append(layout)
                self.show_custom_layout_btn()
                self.layoutHistory.append(copy.deepcopy(self.customLayouts))

    def set_linemode_pixmap(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            mode = self.parent.LineEditor.LineInfoList[row]["preset"]
            if mode == "北京公交":
                pixmap = QPixmap("./resources/preset_BeijingBus.png")
            elif mode == "普通":
                pixmap = QPixmap("./resources/preset_CommonBus.png")
            pixmap = pixmap.scaledToWidth(self.parent.BtnWidget.size().width())
            self.parent.BtnWidget.label = QLabel(parent=self.parent.BtnWidget)
            self.parent.BtnWidget.label.setPixmap(pixmap)
            self.parent.BtnWidget.label.show()

    def init_LineSetting(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            mode = self.parent.LineEditor.LineInfoList[row]["preset"]
            screens = ["前路牌","后路牌","前侧路牌","后侧路牌"]
            screens_have = [self.parent.LineEditor.LineInfoList[row]["frontScreen"]["enabled"],self.parent.LineEditor.LineInfoList[row]["backScreen"]["enabled"],self.parent.LineEditor.LineInfoList[row]["frontSideScreen"]["enabled"],self.parent.LineEditor.LineInfoList[row]["backSideScreen"]["enabled"]]
            self.parent.combo_LineScreensForLayout.clear()
            self.parent.combo_LayoutChoose.clear()
            self.flush_verticalLayout_LayoutBtn()

            for i in range(len(screens_have)):
                if screens_have[i]:
                    self.parent.combo_LineScreensForLayout.addItem(screens[i])

            if mode in ["北京公交","普通"]:
                self.parent.spin_Width_1.setEnabled(True)
                self.parent.spin_Height_1.setEnabled(True)
                self.parent.btn_LineSet.setEnabled(False)
                self.parent.btn_LineReSet.setEnabled(False)
                self.set_linemode_pixmap()
                self.parent.combo_LayoutChoose.setEnabled(True)
                self.parent.combo_LayoutChoose.addItems(["布局1","布局2","布局3","布局4","布局5","布局6"])    # screen["layout"]
                self.parent.btn_SaveChange.setEnabled(True)
            else:
                self.parent.spin_Width_1.setEnabled(False)
                self.parent.spin_Height_1.setEnabled(False)
                self.parent.spin_Width_2.setEnabled(False)
                self.parent.spin_Height_2.setEnabled(False)
                self.parent.combo_LayoutChoose.setEnabled(False)
                self.parent.btn_LineSet.setEnabled(True)
                self.parent.btn_LineReSet.setEnabled(True)
                self.parent.btn_SaveChange.setEnabled(False)
                self.layoutHistoryCount = 0
                self.layoutHistory = []
                
            self.flush_width_height_spinbox()

    def retranslate_screenUnit_size(self):
        row = -1    # 只在添加线路后使用一次
        
        if isinstance(row,int):            
            for scn in screenLink.values():
                colorMode = self.parent.LineEditor.LineInfoList[row][scn]["colorMode"]
                scnSize = self.parent.LineEditor.LineInfoList[row][scn]["screenSize"]
                pointKind = str(self.parent.LineEditor.LineInfoList[row][scn]["screenSize"][2]).replace(" ","")
                pointKind = pointKindDict[pointKind]
                newScn = copy.deepcopy(template_screenInfo[pointKind+"_"+colorMode])
                newScn["pointNum"] = [scnSize[0],scnSize[1]]
                self.parent.LineEditor.LineInfoList[row][scn]["screenUnit"] = [newScn]

    def show_custom_layout_btn(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            self.flush_verticalLayout_LayoutBtn()
            screen = self.get_currentScreen()
            widgetSize = [self.parent.BtnWidget.size().width(),self.parent.BtnWidget.size().height()]
            screenSize = [self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][0],self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][1]]
            screenScale = self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][2]
            colorMode = self.parent.LineEditor.LineInfoList[row][screen]["colorMode"]
            self.btn_w = widgetSize[0]
            self.btn_h = int((self.btn_w * screenSize[1] * screenScale[1]) / (screenSize[0] * screenScale[0]))
            if self.btn_h > widgetSize[1]:
                self.btn_w = int(self.btn_w * widgetSize[1] / self.btn_h)
                self.btn_h = widgetSize[1]
            if len(self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"]) != 0:
                self.customLayouts = self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"]   # 该线路的默认屏幕布局

            if len(self.customLayouts) == 0:
                self.customLButtons = []
                self.customLButtons.append(QPushButton("1",self.parent.BtnWidget))
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
                    self.customLButtons.append(QPushButton(f"{i+1}",self.parent.BtnWidget))
                    self.customLButtons[-1].clicked.connect(lambda: self.onButtonClick(colorMode))
                    self.customLButtons[-1].setGeometry(x,y,w,h)
                    self.customLButtons[-1].show()
            # self.parent.ProgramSettler.show_scnUnit()

    def init_layout(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            screen = self.get_currentScreen()
            colorMode = self.parent.LineEditor.LineInfoList[row][screen]["colorMode"]
            screenSize = [self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][0],self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][1]]
            screenScale = self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][2]
            pointKind = str(screenScale).replace(" ","")
            pointKind = pointKindDict[pointKind]
            layout = []
            layout.append(copy.deepcopy(template_screenInfo[pointKind+"_"+colorMode]))
            layout[-1]["position"] = [0,0]
            layout[-1]["pointNum"] = [screenSize[0],screenSize[1]]

            return layout

    def reset_layout(self,p):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
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
                    self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"] = copy.deepcopy(self.layoutHistory[self.layoutHistoryCount])
                    self.customLayouts = self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"]
                except:
                    print("撤回出错")

            self.show_custom_layout_btn()
            self.parent.thisFile_saveStat.emit(False)

    def add_custom_layout_pre(self,index):
        old_pointNum = self.customLayouts[index]["pointNum"]
        old_scale = self.customLayouts[index]["scale"]
        return old_pointNum,old_scale

    def add_custom_layout(self,index,pointKind,colormode,wh = "w",w = 0,h = 0):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            self.parent.ProgramSheetManager.show_program()
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
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            mode = self.parent.LineEditor.LineInfoList[row]["preset"]
            if mode != "自定义":
                return
        # 识别哪个按钮被点击
        sender = self.parent.sender()
        if sender in self.customLButtons:
            index = self.customLButtons.index(sender)
            opn,ops = self.add_custom_layout_pre(index)
            SelfDefineLayoutDialog = SelfDefineLayout(self.parent)
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
                self.parent.thisFile_saveStat.emit(False)

    def get_scn_pos_size(self,row,screen,w1,h1,enable_mode = True):
        mode = self.parent.LineEditor.LineInfoList[row]["preset"]
        self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"] = []
        screenSize = [self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][0],self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][1]]
        screenScale = self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][2]
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
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            mode = self.parent.LineEditor.LineInfoList[row]["preset"]
            self.parent.ProgramSheetManager.show_program()
            layout = self.parent.combo_LayoutChoose.currentText()
            screen = self.get_currentScreen()
            colorMode = self.parent.LineEditor.LineInfoList[row][screen]["colorMode"]
            self.parent.LineEditor.LineInfoList[row][screen]["layout"] = layout

            w1 = self.parent.spin_Width_1.value()
            h1 = self.parent.spin_Height_1.value()
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
                self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"] = aim_add
            else:
                self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"] = [copy.deepcopy(template_screenInfo["midSize_1"])]
            self.parent.ProgramSettler.show_scnUnit()

            self.parent.thisFile_saveStat.emit(False)
        self.set_linemode_pixmap()

class LineController():
    def __init__(self, parent):
        self.parent = parent
        # 线路管理表格
        self.parent.tableWidget_lineChoose.setColumnCount(3)
        self.parent.tableWidget_lineChoose.setSelectionBehavior(QAbstractItemView.SelectRows)    #设置表格的选取方式是行选取
        self.parent.tableWidget_lineChoose.setSelectionMode(QAbstractItemView.SingleSelection)    #设置选取方式为单个选取
        self.parent.tableWidget_lineChoose.setHorizontalHeaderLabels(["线路名称","预设","刷新率"])   #设置行表头
        self.parent.tableWidget_lineChoose.setColumnWidth(0,120)
        self.parent.tableWidget_lineChoose.setColumnWidth(1,90)
        self.parent.tableWidget_lineChoose.setColumnWidth(2,70)
        self.parent.tableWidget_lineChoose.setEditTriggers(QAbstractItemView.NoEditTriggers)  #始终禁止编辑
        self.parent.tableWidget_lineChoose.verticalHeader().setDefaultSectionSize(18)
        self.parent.tableWidget_lineChoose.rowMoved.connect(self.onRowMoved)

        self.parent.combo_FlushRate.addItems(["60","54","50","48","30","24","18","15"])

        self.parent.LineNameEdit.editingFinished.connect(self.change_name_time)
        self.parent.combo_FlushRate.currentTextChanged.connect(self.change_name_time)
        self.parent.tableWidget_lineChoose.clicked.connect(self.show_name_time)
        self.parent.btn_newLine.clicked.connect(self.new_busLine_openDialog)
        self.parent.btn_delLine.clicked.connect(self.del_busLine)
        self.parent.btn_MvUp_BusLine.clicked.connect(self.mv_up_busLine)
        self.parent.btn_MvDn_BusLine.clicked.connect(self.mv_dn_busLine)

    def show_name_time(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            dt = self.parent.LineEditor.LineInfoList[row]
            self.parent.LineNameEdit.setText(dt["lineName"])
            self.parent.combo_FlushRate.setCurrentText(str(dt["flushRate"]))

    def change_name_time(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            n = self.parent.LineNameEdit.text()
            f = int(self.parent.combo_FlushRate.currentText())
            if self.parent.LineEditor.LineInfoList[row]["lineName"] != n or self.parent.LineEditor.LineInfoList[row]["flushRate"] != f:
                self.parent.LineEditor.LineInfoList[row]["lineName"] = n
                self.parent.LineEditor.LineInfoList[row]["flushRate"] = f
                self.parent.thisFile_saveStat.emit(False)
            self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.parent.LineEditor.LineInfoList])
            self.parent.tableWidget_lineChoose.setCurrentItem(self.parent.tableWidget_lineChoose.item(row,0))

    def new_line(self):
        self.parent.LineEditor.LineInfoList = []
        self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.parent.LineEditor.LineInfoList])

        self.parent.thisFile_saveStat.emit(False)

    def new_busLine_openDialog(self):
        dialog = NewALine(self.parent)
        dialog.dataEntered.connect(self.new_busLine_EnterData)
        dialog.exec_()
        
    def new_busLine_EnterData(self,data):
        self.parent.LineEditor.add_data(data)
        self.parent.LineSettler.retranslate_screenUnit_size()
        self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.parent.LineEditor.LineInfoList])
        self.parent.thisFile_saveStat.emit(False)

    def copy_busLine(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if row != None:
            self.parent.LineEditor.copy_data(row)
            self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.parent.LineEditor.LineInfoList])
            self.parent.thisFile_saveStat.emit(False)

    def del_busLine(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if row != None:
            self.parent.LineEditor.remove_data(row)
            self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.parent.LineEditor.LineInfoList])
            self.parent.thisFile_saveStat.emit(False)

    def onRowMoved(self,drag,drop):
        self.parent.LineEditor.move_row(drag,drop)
        self.parent.thisFile_saveStat.emit(False)
        self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.parent.LineEditor.LineInfoList])

    def mv_up_busLine(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if row != None:
            self.parent.LineEditor.mv_up(row)
            self.parent.thisFile_saveStat.emit(False)
        self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.parent.LineEditor.LineInfoList])

    def mv_dn_busLine(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if row != None:
            self.parent.LineEditor.mv_dn(row)
            self.parent.thisFile_saveStat.emit(False)
        self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.parent.LineEditor.LineInfoList])

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
        if drag == drop:
            return
        self.LineInfoList.insert(drop,self.LineInfoList[drag])
        if drag < drop:
            self.LineInfoList.pop(drag)
        if drag > drop:
            self.LineInfoList.pop(drag+1)
    
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