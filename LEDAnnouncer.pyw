import sys, os, ast, copy, datetime
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QMainWindow, QAbstractItemView, QTableWidgetItem, QHeaderView, QFileDialog, QPushButton, QLabel, QColorDialog, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSignal, Qt
from BmpCreater import FontManager
from AnnouncerPanel import Ui_ControlPanel
from SelfDefineScreenDialog import Ui_SelfDefineScreen
from ScreenInfo import *
from LineInfo import *
from LedScreenModule import *
from About import *

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

class SelfDefineLayout(QDialog,Ui_SelfDefineScreen):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("选择要添加的屏幕")
        self.combo_Layout.addItems(["更改屏幕","水平布局","垂直布局"])
        self.combo_PointKind.addItems(["(6,6)","(8,8)","(8,12)","(3,3)","(4,4)","(4,6)"])

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

class MainWindow(QMainWindow, Ui_ControlPanel):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.currentFileDir = ""
        self.setupUi(self)
        self.initUI()
        self.make_menu()
        self.setWindowTitle("LED模拟器")
        self.setWindowIcon(QIcon("./resources/icon.ico"))

    def initUI(self):
        self.AboutWindow = AboutWindow()
        self.BtnWidget = QWidget(self)
        self.verticalLayout_LayoutBtn.addWidget(self.BtnWidget)
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
        self.tableWidget_ProgramSheet.itemSelectionChanged.connect(self.change_program)
        self.tableWidget_ProgramSheet.pressed.connect(self.change_program)
        self.tableWidget_lineChoose.itemSelectionChanged.connect(self.close_all_screen)
        self.btn_NewFile.clicked.connect(self.new_file)

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

        # 创建一个子菜单
        # impMenu = QMenu('导入', self)
        # impAct = QAction('导入邮件', self)
        # impMenu.addAction(impAct)
        # # 将子菜单添加到菜单
        # fileMenu.addMenu(impMenu)
        # # 添加分隔符
        # fileMenu.addSeparator()

    def flush_table(self,tableWidgetObject,data):
        tableWidgetObject.setRowCount(0)
        for row in range(len(data)):
            tableWidgetObject.insertRow(row)
            for col in range(len(data[0])):
                item = QTableWidgetItem(str(data[row][col]))
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignCenter)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)    #设置为只可选择
                tableWidgetObject.setItem(row,col,item)

    def selected_row(self,tableWidgetObject):
        row_select = tableWidgetObject.selectedItems()
        if len(row_select) == 0:
            return
        row = row_select[0].row()
        return row
    
    def new_file(self):
        button = QMessageBox.question(self, "对话框", "确定要新建文件吗？")
        if button == QMessageBox.No:
            return
        self.LineController.new_line()
    
    def save_another(self):
        filedir,ok = QFileDialog.getSaveFileName(self,'保存','./','报站文件 (*.asu)')
        if ok:
            self.currentFileDir = filedir
            with open(filedir,'w',encoding = 'utf-8') as w:
                w.write(str(self.LineEditor.LineInfoList))
    
    def save_file(self):
        button = QMessageBox.question(self, "对话框", "确定要保存吗？")
        if button == QMessageBox.No:
            return
        if os.path.exists(self.currentFileDir):
            filedir = self.currentFileDir
            with open(filedir,'w',encoding = 'utf-8') as w:
                w.write(str(self.LineEditor.LineInfoList))
        else:
            self.save_another()

    def open_file(self):
        if os.path.exists(self.currentFileDir):
            button = QMessageBox.question(self, "对话框", "确定要打开另一个文件吗？")
            if button == QMessageBox.No:
                return
        file_dir,ok = QFileDialog.getOpenFileName(self,'打开','./','报站文件 (*.asu)')
        if ok:
            self.currentFileDir = file_dir
            with open(file_dir,'r',encoding = 'utf-8') as r:
                list_str = r.read()
                self.LineEditor.LineInfoList = ast.literal_eval(list_str)
            self.flush_table(self.tableWidget_lineChoose,[[i["lineName"],i["preset"],i["flushRate"]] for i in self.LineEditor.LineInfoList])

    def turn_on_all_screen(self):
        row = self.selected_row(self.tableWidget_lineChoose)
        h = 0
        if isinstance(row,int):
            screenLink = {"走字屏":"Screen"}
            for screen in screenLink.values():
                try:
                    screen.close()
                except:
                    pass
                if self.LineEditor.LineInfoList[row][screen]["enabled"]:
                    try:
                        scn = ScreenController(flushRate=self.LineEditor.LineInfoList[row]["flushRate"],screenInfo={"colorMode":self.LineEditor.LineInfoList[row][screen]["colorMode"],"screenSize":self.LineEditor.LineInfoList[row][screen]["screenSize"]},screenProgramSheet=self.LineEditor.LineInfoList[row]["programSheet"],FontIconMgr=self.IconManager.FontMgr,toDisplay=screen)
                        scn.move(50,50+h)
                        h += self.LineEditor.LineInfoList[row][screen]["screenSize"][1]*self.LineEditor.LineInfoList[row][screen]["screenSize"][2][1]+120
                        self.LedScreens[screen] = scn
                    except:
                        pass

    def close_all_screen(self):
        for s in self.LedScreens.values():
            try:
                s.close()
            except:
                pass

    def preview_screen(self):
        row = self.selected_row(self.tableWidget_lineChoose)
        if isinstance(row,int):
            screen = "Screen"
            scn = ScreenController(flushRate=self.LineEditor.LineInfoList[row]["flushRate"],screenInfo={"colorMode":self.LineEditor.LineInfoList[row][screen]["colorMode"],"screenSize":self.LineEditor.LineInfoList[row][screen]["screenSize"]},screenProgramSheet=self.LineEditor.LineInfoList[row]["programSheet"],FontIconMgr=self.IconManager.FontMgr,toDisplay=screen)
            scn.move(100,100)
            self.LedScreens[screen] = scn

    def change_program(self):
        line_row = self.selected_row(self.tableWidget_lineChoose)
        if isinstance(line_row,int):
            programSheet = self.LineEditor.LineInfoList[line_row]["programSheet"]
            row = self.selected_row(self.tableWidget_ProgramSheet)
            if isinstance(row,int):
                screenLink = {"走字屏":"Screen"}
                for screen in screenLink.values():
                    try:
                        if self.LineEditor.LineInfoList[line_row][screen]["enabled"]:
                            self.LedScreens[screen].screenProgramSheet = programSheet
                            self.LedScreens[screen].currentIndex = row
                            self.LedScreens[screen].programTimeout()
                        else:
                            self.LedScreens[screen].close()
                    except:
                        pass

    def screenShot(self):
        screen = QApplication.primaryScreen()
        for name,scn in self.LedScreens.items():
            try:
                try:
                    os.makedirs("./ScreenShots")
                except:
                    pass
                if scn.isVisible():
                    window_handle = scn.winId()
                    screenshot = screen.grabWindow(window_handle)
                    fileName = datetime.datetime.now().strftime(f"{name}_%H%M%S.png")
                    screenshot.save(os.path.join("./ScreenShots",fileName))
            except:
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
            except:
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
        self.parent.tableWidget_ProgramSheet.setColumnCount(3)
        self.parent.tableWidget_ProgramSheet.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parent.tableWidget_ProgramSheet.setSelectionMode(QAbstractItemView.SingleSelection)
        self.parent.tableWidget_ProgramSheet.setHorizontalHeaderLabels(["节目名称","持续时间","次数"])
        self.parent.tableWidget_ProgramSheet.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.parent.tableWidget_ProgramSheet.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.parent.tableWidget_ProgramSheet.verticalHeader().setDefaultSectionSize(18)

        self.parent.spinBox.setMaximum(3600*24)
        self.parent.spinBox_n.setMaximum(100)
        self.parent.spinBox.setMinimum(0)
        self.parent.spinBox_n.setMinimum(1)

        self.parent.tableWidget_lineChoose.itemSelectionChanged.connect(self.show_program)
        self.parent.tableWidget_ProgramSheet.itemSelectionChanged.connect(self.show_name_time)
        self.parent.lineEdit_ProgramName.editingFinished.connect(self.change_name_time)
        self.parent.spinBox.editingFinished.connect(self.change_name_time)
        self.parent.spinBox_n.editingFinished.connect(self.change_name_time)
        self.parent.btn_Add.clicked.connect(self.new_program)
        self.parent.btn_MvUp_Program.clicked.connect(self.mv_up_program)
        self.parent.btn_MvDn_Program.clicked.connect(self.mv_dn_program)
        self.parent.btn_CopyProgram.clicked.connect(self.copy_program)
        self.parent.btn_Remove.clicked.connect(self.del_program)

    def show_program(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            self.programSheet = self.parent.LineEditor.LineInfoList[row]["programSheet"]
            data = [[p[0],p[1],p[3]] for p in self.programSheet]
            self.parent.flush_table(self.parent.tableWidget_ProgramSheet,data)

    def show_name_time(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            self.parent.lineEdit_ProgramName.setText(self.programSheet[row][0])
            self.parent.spinBox.setValue(self.programSheet[row][1])
            self.parent.spinBox_n.setValue(self.programSheet[row][3])

    def change_name_time(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            self.programSheet[row][0] = self.parent.lineEdit_ProgramName.text()
            self.programSheet[row][1] = self.parent.spinBox.value()
            self.programSheet[row][3] = self.parent.spinBox_n.value()
            self.show_program()
            item = self.parent.tableWidget_ProgramSheet.item(row,0)
            self.parent.tableWidget_ProgramSheet.setCurrentItem(item)

    def new_program(self,):
        progName = self.parent.lineEdit_ProgramName.text()
        sec = self.parent.spinBox.value()
        n = self.parent.spinBox_n.value()
        screenLink = {"走字屏":"Screen"}
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
            self.programSheet.append([progName,sec,sbpdict,n])
            self.parent.lineEdit_ProgramName.setText("")
            self.parent.spinBox.setValue(0)
            self.show_program()
            # # # print(self.programSheet)

    def del_program(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            self.programSheet.pop(row)
        self.show_program()

    def copy_program(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            self.programSheet.append(copy.deepcopy(self.programSheet[row]))
        self.show_program()

    def mv_up_program(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            if row > 0:
                self.programSheet[row],self.programSheet[row-1] = self.programSheet[row-1],self.programSheet[row]
        self.show_program()

    def mv_dn_program(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            if row < len(self.programSheet)-1:
                self.programSheet[row],self.programSheet[row+1] = self.programSheet[row+1],self.programSheet[row]
        self.show_program()

class ProgramSettler():
    def __init__(self, parent):
        self.parent = parent
        self.FontMgr = FontManager()
        self.FontLib = self.FontMgr.font_dict.keys()
        self.ChFont = [c for c in self.FontLib if "asc" not in c.lower()]
        self.EngFont = [c for c in self.FontLib if "asc" in c.lower()]
        self.initUI()

    def initUI(self):
        # 屏幕分区管理表格
        self.parent.tableWidget_Screens.setColumnCount(3)
        self.parent.tableWidget_Screens.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parent.tableWidget_Screens.setSelectionMode(QAbstractItemView.SingleSelection)
        self.parent.tableWidget_Screens.verticalHeader().setVisible(False)
        self.parent.tableWidget_Screens.setHorizontalHeaderLabels(["屏幕名称","屏幕规格","灯珠规格"])
        self.parent.tableWidget_Screens.setColumnWidth(0,120)
        self.parent.tableWidget_Screens.setColumnWidth(1,100)
        self.parent.tableWidget_Screens.setColumnWidth(2,100)
        self.parent.tableWidget_Screens.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.parent.tableWidget_Screens.verticalHeader().setDefaultSectionSize(18)

        self.parent.combo_Font.addItems(self.ChFont)
        self.parent.combo_ASCII_Font.addItems(self.EngFont)
        self.parent.combo_Show.addItems(["静止","闪烁","向左滚动","向左移到中间","向上移到中间","中间向左移开","中间向上移开","跳跃向左移动","跳跃向上移动","向右滚动","向右移到中间","向下移到中间","中间向右移开","中间向下移开","跳跃向右移动","跳跃向下移动",])
        self.parent.combo_TextDirect.addItems(["横向","竖向"])
        self.parent.combo_SingleColorChoose.addItems(template_monochromeColors.keys())

        self.parent.spin_FontSize.setMaximum(64)
        self.parent.spin_FontSize.setMinimum(6)
        self.parent.spin_FontSize.setValue(16)
        self.parent.spinBox_Argv_1.setMaximum(60)
        self.parent.spinBox_Argv_1.setMinimum(1)
        self.parent.spinBox_Argv_2.setMaximum(60)
        self.parent.spinBox_Argv_2.setMinimum(1)
        self.parent.spinBox_WordSpace.setMaximum(100)
        self.parent.spinBox_WordSpace.setMinimum(0)
        self.parent.spinBox_BoldSizeX.setMaximum(4)
        self.parent.spinBox_BoldSizeX.setMinimum(1)
        self.parent.spinBox_BoldSizeY.setMaximum(4)
        self.parent.spinBox_BoldSizeY.setMinimum(1)
        self.parent.spinBox_Y_Offset.setMaximum(64)
        self.parent.spinBox_Y_Offset.setMinimum(-64)
        self.parent.spinBox_Align_x.setMaximum(1)
        self.parent.spinBox_Align_x.setMinimum(-1)
        self.parent.spinBox_Align_y.setMaximum(1)
        self.parent.spinBox_Align_y.setMinimum(-1)
        self.parent.spinBox_Zoom.setMaximum(200)
        self.parent.spinBox_Zoom.setMinimum(40)
        self.parent.spinBox_Zoom.setValue(100)       

        self.parent.tableWidget_lineChoose.itemSelectionChanged.connect(self.init_ProgramSetting)
        self.parent.tableWidget_ProgramSheet.itemSelectionChanged.connect(self.show_scnUnit)
        self.parent.tableWidget_Screens.itemSelectionChanged.connect(self.show_progArgv)
        self.parent.btn_ok.clicked.connect(self.save_progArgv)
        self.parent.btn_Colorful_ChooseColor.clicked.connect(self.get_color)
        self.parent.combo_Show.currentTextChanged.connect(self.update_two_argv)

    def init_ProgramSetting(self):
        self.show_scnUnit()
        
    def show_scnUnit(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            screen = "Screen"
            screenUnitList = self.parent.ProgramSheetManager.programSheet[row][2][screen][0]
            data = [[i+1,str(screenUnitList[i]["pointNum"]),str(screenUnitList[i]["pointSize"])] for i in range(len(screenUnitList))]
            self.parent.flush_table(self.parent.tableWidget_Screens,data)
        else:
            self.parent.flush_table(self.parent.tableWidget_Screens,[])

        ## 添加节目的地方和更改布局的地方
            
    def update_two_argv(self):
        mode = self.parent.combo_Show.currentText()
        self.parent.spinBox_Argv_1.setEnabled(True)
        self.parent.spinBox_Argv_2.setEnabled(True)
        if "滚动" in mode:
            self.parent.label_Argv_1.setText("移动速度")
            self.parent.label_Argv_2.setText("滚动对象间距")
            self.parent.spinBox_Argv_1.setMaximum(60)
            self.parent.spinBox_Argv_1.setMinimum(1)
            self.parent.spinBox_Argv_2.setMaximum(60)
            self.parent.spinBox_Argv_2.setMinimum(-1)
            self.parent.spinBox_Argv_2.setValue(-1)
        elif "移到" in mode:
            self.parent.label_Argv_1.setText("移动速度")
            self.parent.label_Argv_2.setText("时间")
            self.parent.spinBox_Argv_1.setMaximum(60)
            self.parent.spinBox_Argv_1.setMinimum(1)
            self.parent.spinBox_Argv_2.setMaximum(60)
            self.parent.spinBox_Argv_2.setMinimum(1)
        elif "移开" in mode:
            self.parent.label_Argv_1.setText("移动速度")
            self.parent.label_Argv_2.setText("时间")
            self.parent.spinBox_Argv_1.setMaximum(60)
            self.parent.spinBox_Argv_1.setMinimum(1)
            self.parent.spinBox_Argv_2.setMaximum(60)
            self.parent.spinBox_Argv_2.setMinimum(1)
        elif "跳跃" in mode:
            self.parent.label_Argv_1.setText("移动速度")
            self.parent.label_Argv_2.setText("移动步长")
            self.parent.spinBox_Argv_1.setMaximum(60)
            self.parent.spinBox_Argv_1.setMinimum(1)
            self.parent.spinBox_Argv_2.setMaximum(32)
            self.parent.spinBox_Argv_2.setMinimum(1)
        elif mode == "闪烁":
            self.parent.label_Argv_1.setText("亮时长")
            self.parent.label_Argv_2.setText("灭时长")
            self.parent.spinBox_Argv_1.setMaximum(60)
            self.parent.spinBox_Argv_1.setMinimum(1)
            self.parent.spinBox_Argv_2.setMaximum(60)
            self.parent.spinBox_Argv_2.setMinimum(1)
        elif mode == "静止":
            self.parent.label_Argv_1.setText("")
            self.parent.label_Argv_2.setText("")
            self.parent.spinBox_Argv_1.setEnabled(False)
            self.parent.spinBox_Argv_2.setEnabled(False)

    def show_progArgv(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            screen = "Screen"
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
                    self.parent.combo_Font.setCurrentText(self.screenProgList[row]["font"])
                    self.parent.spin_FontSize.setValue(self.screenProgList[row]["fontSize"])
                    self.parent.combo_ASCII_Font.setCurrentText(self.screenProgList[row]["ascFont"])
                    self.parent.checkBox_sysFont.setChecked(self.screenProgList[row]["sysFontOnly"])
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
                    self.update_two_argv()

    def save_progArgv(self):
        row = self.parent.selected_row(self.parent.tableWidget_ProgramSheet)
        if isinstance(row,int):
            row = self.parent.selected_row(self.parent.tableWidget_Screens)
            if isinstance(row,int):
                self.screenProgList[row]["font"] = self.parent.combo_Font.currentText()
                self.screenProgList[row]["fontSize"] = self.parent.spin_FontSize.value()
                self.screenProgList[row]["ascFont"] = self.parent.combo_ASCII_Font.currentText()
                self.screenProgList[row]["sysFontOnly"] = self.parent.checkBox_sysFont.isChecked()
                self.screenProgList[row]["appearance"] = self.parent.combo_Show.currentText()
                self.screenProgList[row]["vertical"] = False if self.parent.combo_TextDirect.currentText() == "横向" else True 
                self.screenProgList[row]["argv_1"] = self.parent.spinBox_Argv_1.value()
                self.screenProgList[row]["argv_2"] = self.parent.spinBox_Argv_2.value()
                self.screenProgList[row]["spacing"] = self.parent.spinBox_WordSpace.value()
                self.screenProgList[row]["bold"][0] = self.parent.spinBox_BoldSizeX.value()
                self.screenProgList[row]["bold"][1] = self.parent.spinBox_BoldSizeY.value()
                self.screenProgList[row]["y_offset"] = self.parent.spinBox_Y_Offset.value()
                self.screenProgList[row]["align"][0] = self.parent.spinBox_Align_x.value()
                self.screenProgList[row]["align"][1] = self.parent.spinBox_Align_y.value()
                self.screenProgList[row]["scale"] = self.parent.spinBox_Zoom.value()
                self.screenProgList[row]["autoScale"] = self.parent.chk_AutoZoom.isChecked()
                self.screenProgList[row]["scaleSysFontOnly"] = self.parent.chk_Argv1.isChecked()
                self.screenProgList[row]["text"] = self.parent.lineEdit_Text.text()
                self.screenProgList[row]["color_1"] = self.parent.combo_SingleColorChoose.currentText()

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
        self.customLayouts = []
        self.customLButtons = []
        self.btn_w = 350
        self.btn_h = 72
        self.initUI()

    def initUI(self):
        pixmap = QPixmap("./resources/welcome.png")
        self.parent.BtnWidget.label = QLabel(parent=self.parent.BtnWidget)
        self.parent.BtnWidget.label.setGeometry(0,-40,400,150)
        self.parent.BtnWidget.label.setPixmap(pixmap)
        self.parent.BtnWidget.label.setScaledContents(True)
        self.parent.combo_ScreenColor.addItems(["彩色屏幕","单色屏幕"])
        self.parent.combo_FLedType.addItems(["(6,6)","(8,8)","(8,12)","(3,3)","(4,4)","(4,6)"])
        self.parent.combo_FlushRate.addItems(["60","54","50","48","30","24","18","15"])

        self.parent.tableWidget_lineChoose.itemSelectionChanged.connect(self.init_LineSetting)
        self.parent.tableWidget_lineChoose.pressed.connect(self.init_LineSetting)
        self.parent.btn_LineSet.clicked.connect(self.reset_layout)

        self.parent.spin_Width_1.setMinimum(32)
        self.parent.spin_Width_2.setMinimum(16)
        self.parent.spin_Width_1.setMaximum(512)
        self.parent.spin_Width_2.setMaximum(128)

    def flush_verticalLayout_LayoutBtn(self):
        for widget in self.parent.BtnWidget.findChildren(QWidget):
            widget.deleteLater()

    def init_LineSetting(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            screen = "Screen"
            screenSize = [self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][0],self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][1]]
            pointKind = str(self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][2]).replace(" ","")
            colorMode = self.parent.LineEditor.LineInfoList[row][screen]["colorMode"]
            flushRate = self.parent.LineEditor.LineInfoList[row]["flushRate"]
            self.parent.spin_Width_1.setValue(screenSize[0])
            self.parent.spin_Width_2.setValue(screenSize[1])
            self.parent.combo_ScreenColor.setCurrentText("彩色屏幕" if colorMode == "RGB" else "单色屏幕")
            self.parent.combo_FLedType.setCurrentText(pointKind)
            self.parent.combo_FlushRate.setCurrentText(str(flushRate))
            self.show_custom_layout_btn()

    def retranslate_screenUnit_size(self):
        row = -1    # 只在添加线路后使用一次
        screenLink = {"走字屏":"Screen"}
        if isinstance(row,int):            
            for scn in screenLink.values():
                colorMode = self.parent.LineEditor.LineInfoList[row][scn]["colorMode"]
                scnSize = self.parent.LineEditor.LineInfoList[row][scn]["screenSize"]
                pointKind = str(self.parent.LineEditor.LineInfoList[row][scn]["screenSize"][2]).replace(" ","")
                pointKindDict = {"(3,3)":"miniSize","(4,4)":"smallSize","(4,6)":"smallSizeScaled","(6,6)":"midSize","(8,8)":"bigSize","(8,12)":"bigSizeScaled"}
                pointKind = pointKindDict[pointKind]
                newScn = copy.deepcopy(template_screenInfo[pointKind+"_"+colorMode])
                newScn["pointNum"] = [scnSize[0],scnSize[1]]
                self.parent.LineEditor.LineInfoList[row][scn]["screenUnit"] = [newScn]

    def show_custom_layout_btn(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            self.flush_verticalLayout_LayoutBtn()
            screen = "Screen"
            screenSize = [self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][0],self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][1]]
            screenScale = self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][2]
            colorMode = self.parent.LineEditor.LineInfoList[row][screen]["colorMode"]
            self.btn_w = 350
            self.btn_h = int(self.btn_w*screenSize[1]/screenSize[0])
            if self.btn_h > 72:
                self.btn_w = int(self.btn_w * 72 / self.btn_h)
                self.btn_h = 72
            if len(self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"]) != 0:
                self.customLayouts = self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"]

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
            self.parent.ProgramSettler.show_scnUnit()
            print(self.parent.BtnWidget.size())

    def reset_layout(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if isinstance(row,int):
            self.customLButtons = []
            screen = "Screen"
            self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"] = []
            self.customLayouts = self.parent.LineEditor.LineInfoList[row][screen]["screenUnit"]
            colorMode = self.parent.LineEditor.LineInfoList[row][screen]["colorMode"]
            screenSize = [self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][0],self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][1]]
            screenScale = self.parent.LineEditor.LineInfoList[row][screen]["screenSize"][2]
            pointKind = str(screenScale).replace(" ","")
            pointKindDict = {"(3,3)":"miniSize","(4,4)":"smallSize","(4,6)":"smallSizeScaled","(6,6)":"midSize","(8,8)":"bigSize","(8,12)":"bigSizeScaled"}
            pointKind = pointKindDict[pointKind]
            self.customLayouts.append(copy.deepcopy(template_screenInfo[pointKind+"_"+colorMode]))
            self.customLayouts[-1]["position"] = [0,0]
            self.customLayouts[-1]["pointNum"] = [screenSize[0],screenSize[1]]
            self.show_custom_layout_btn()

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
        # 识别哪个按钮被点击
        sender = self.parent.sender()
        if sender in self.customLButtons:
            index = self.customLButtons.index(sender)
            opn,ops = self.add_custom_layout_pre(index)
            SelfDefineLayoutDialog = SelfDefineLayout(self.parent)
            SelfDefineLayoutDialog.set_value(opn,ops)
            SelfDefineLayoutDialog.can_w_h()
            if SelfDefineLayoutDialog.exec_() == QDialog.Accepted:
                layout = SelfDefineLayoutDialog.combo_Layout.currentText()
                pointKind = SelfDefineLayoutDialog.combo_PointKind.currentText()
                pointKindDict = {"(3,3)":"miniSize","(4,4)":"smallSize","(4,6)":"smallSizeScaled","(6,6)":"midSize","(8,8)":"bigSize","(8,12)":"bigSizeScaled"}
                pointKind = pointKindDict[pointKind]
                w = SelfDefineLayoutDialog.spin_SetWidth.value()
                h = SelfDefineLayoutDialog.spin_SetHeight.value()
                if layout == "更改屏幕":
                    self.change_custom_layout(index,pointKind,colormode)
                elif layout == "垂直布局":
                    self.add_custom_layout(index,pointKind,colormode,"h",w,h)
                elif layout == "水平布局":
                    self.add_custom_layout(index,pointKind,colormode,"w",w,h)
                self.show_custom_layout_btn()

class LineController():
    def __init__(self, parent):
        self.parent = parent
        # 线路管理表格
        self.parent.tableWidget_lineChoose.setColumnCount(2)
        self.parent.tableWidget_lineChoose.setSelectionBehavior(QAbstractItemView.SelectRows)    #设置表格的选取方式是行选取
        self.parent.tableWidget_lineChoose.setSelectionMode(QAbstractItemView.SingleSelection)    #设置选取方式为单个选取
        self.parent.tableWidget_lineChoose.setHorizontalHeaderLabels(["站名","备注"])   #设置行表头
        self.parent.tableWidget_lineChoose.setColumnWidth(0,120)
        self.parent.tableWidget_lineChoose.setColumnWidth(1,90)
        self.parent.tableWidget_lineChoose.setEditTriggers(QAbstractItemView.NoEditTriggers)  #始终禁止编辑
        self.parent.tableWidget_lineChoose.verticalHeader().setDefaultSectionSize(18)

        self.parent.btn_newStop.clicked.connect(self.new_busLine_EnterData)
        self.parent.btn_delLine.clicked.connect(self.del_busLine)
        self.parent.btn_MvUp_BusLine.clicked.connect(self.mv_up_busLine)
        self.parent.btn_MvDn_BusLine.clicked.connect(self.mv_dn_busLine)

    def new_line(self):
        self.parent.LineEditor.LineInfoList = []
        pointKind = self.parent.combo_FLedType.currentText()[1:-1].split(",")
        self.parent.LineEditor.ScreenRound = [self.parent.spin_Width_1.value(),self.parent.spin_Width_2.value(),(int(pointKind[0]),int(pointKind[1]))]
        self.parent.LineEditor.flushRate = int(self.parent.combo_FlushRate.currentText())
        self.parent.LineEditor.colorMode = "RGB" if self.parent.combo_ScreenColor.currentText() == "彩色屏幕" else "1" 
        self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["stationName"],i["remark"]] for i in self.parent.LineEditor.LineInfoList])

    def new_busLine_EnterData(self):
        data = {"stationName":self.parent.lineEdit.text()}
        self.parent.LineEditor.add_data(data)
        self.parent.LineSettler.retranslate_screenUnit_size()
        self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["stationName"],i["remark"]] for i in self.parent.LineEditor.LineInfoList])

    def copy_busLine(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if row != None:
            self.parent.LineEditor.copy_data(row)
            self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["stationName"],i["remark"]] for i in self.parent.LineEditor.LineInfoList])

    def del_busLine(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if row != None:
            self.parent.LineEditor.remove_data(row)
            self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["stationName"],i["remark"]] for i in self.parent.LineEditor.LineInfoList])

    def mv_up_busLine(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if row != None:
            self.parent.LineEditor.mv_up(row)
        self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["stationName"],i["remark"]] for i in self.parent.LineEditor.LineInfoList])

    def mv_dn_busLine(self):
        row = self.parent.selected_row(self.parent.tableWidget_lineChoose)
        if row != None:
            self.parent.LineEditor.mv_dn(row)
        self.parent.flush_table(self.parent.tableWidget_lineChoose,[[i["stationName"],i["remark"]] for i in self.parent.LineEditor.LineInfoList])

class LineEditor():
    def __init__(self):
        self.LineInfoList = []
        self.ScreenRound = [144,16,(8,8)]
        self.flushRate = 50
        self.colorMode = "RGB"

    def add_data(self,linedata):
        lineInfo = copy.deepcopy(template_station)
        lineInfo["stationName"] = linedata["stationName"]
        lineInfo["Screen"]["screenSize"] = self.ScreenRound
        lineInfo["Screen"]["colorMode"] = self.colorMode
        lineInfo["flushRate"] = self.flushRate
        self.LineInfoList.append(lineInfo)

    def remove_data(self,row):
        self.LineInfoList.pop(row)

    def copy_data(self,row):
        self.LineInfoList.append(copy.deepcopy(self.LineInfoList[row]))
    
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