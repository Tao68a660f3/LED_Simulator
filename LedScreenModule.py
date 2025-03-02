import sys, time, datetime, os, imageio, random, re
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction
from PyQt5.QtGui import QPainter, QColor, QImage
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PIL import Image
from ScreenInfo import *
from LineInfo import *
from BmpCreater import *

undefinedProgramSheet = [['测试信息', 900, {'frontScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'backScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'frontSideScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'backSideScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]]}]]

sector_area_eft = ["向右扇形圆形","向左扇形圆形","向下扇形圆形","向上扇形圆形"]
hwindow_area_eft = ["向左开百叶窗","向右开百叶窗","向上开百叶窗","向下开百叶窗","向左关百叶窗","向右关百叶窗","向上关百叶窗","向下关百叶窗"]
window_area_eft = ["开水平窗户","关水平窗户","开竖直窗户","关竖直窗户"]

class Thread_BmpUpdater(QThread):
    def __init__(self, parent = None):
        super(Thread_BmpUpdater, self).__init__()
        self.myparent = parent
        self.is_running = True

    def run(self):
        print(self.is_running)
        while self.is_running:
            self.myparent.checkTimeStr()
            time.sleep(0.5)

    def stop(self):
        self.is_running = False

class ScreenController(QWidget):
    counterPlusOne = pyqtSignal()

    def __init__(self,flushRate,screenInfo,screenProgramSheet,toDisplay,FontIconMgr,parent = None):
        super().__init__()
        self.Parent = parent
        self.window_handle = self.winId()
        self.screen = QApplication.primaryScreen()
        self.BmpUpdater = Thread_BmpUpdater(self)
        self.BmpUpdater.finished.connect(self.BmpUpdater.deleteLater)
        self.settings = dict()
        self.offset = 16
        self.colorMode = screenInfo["colorMode"]
        self.screenSize = [screenInfo["screenSize"][0],screenInfo["screenSize"][1]]
        self.screenScale = screenInfo["screenSize"][2]
        self.screenProgramSheet = screenProgramSheet
        self.toDisplay = toDisplay
        self.FontIconMgr = FontIconMgr
        self.currentScreenProgSet = dict()
        self.maskMode = False
        self.keep_speed = False
        self.cntProgIsOrigin = True
        self.jumpFrom = 0
        self.currentIndex = 0
        self.currentPtime = 0
        self.currentBeginTime = 0
        self.runningTime = 0
        self.performFinish = False
        self.gifRecording = False
        self.progStopGif = False
        # self.endGifFrame = 0
        self.fpsCounter = 0
        self.commonFps = 0
        self.expectedFps = flushRate
        self.owingFps = 0
        self.gifFps = 0
        self.flushRate = 1000 // flushRate
        self.units = []
        self.gifFrames = []
        self.tmpGifNames = []
        self.BackImg = Image.new("RGB", (screenInfo["screenSize"][0],screenInfo["screenSize"][1]))

        if len(self.screenProgramSheet) == 0:
            self.screenProgramSheet = undefinedProgramSheet
            for s in {"frontScreen","backScreen","frontSideScreen","backSideScreen"}:
                self.screenProgramSheet[0][2][s][0][0]["pointNum"] = self.screenSize
                self.screenProgramSheet[0][2][s][0][0]["scale"] = self.screenScale
                self.screenProgramSheet[0][2][s][0][0]["pointSize"] = int(self.screenScale[0]*0.8)   # 为了方便起见点大小直接 *0.8

        self.BmpUpdater.start()

        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.update)
        self.timer1.start(self.flushRate)
        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.checkProgramTimeout)
        self.timer2.start(200)
        self.timer3 = QTimer(self)
        self.timer3.timeout.connect(self.count_fps)
        self.timer3.start(1000)

        self.read_setting()
        self.setWindowTitle(self.toDisplay)
        self.setWindowFlags(Qt.FramelessWindowHint) # 隐藏边框
        self.show()
        self.programTimeout()
        self.checkProgramTimeout()

        self.setContextMenuPolicy(Qt.CustomContextMenu) # 右键菜单
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.counterPlusOne.connect(self.triggerProgramTimeout)

    def read_setting(self):
        setting_file = "./resources/settings.info"
        if os.path.exists(setting_file):
            with open(setting_file,'r',encoding = 'utf-8') as r:
                list_str = r.read()
                self.settings = ast.literal_eval(list_str)

        if "keep_speed" in self.settings.keys():
            self.keep_speed = self.settings["keep_speed"]

    def stopThread_BmpUpdater(self):
        try:
            if self.BmpUpdater.isRunning():
                self.BmpUpdater.stop()
                self.BmpUpdater.quit()
                self.BmpUpdater.wait()
        except Exception as e:
            print("stopThread_BmpUpdater:", e)

    def showContextMenu(self, pos):
        contextMenu = QMenu(self)
        closeAction = QAction('关闭窗口', self)
        closeAction.triggered.connect(self.close)
        contextMenu.addAction(closeAction)
        topMostAction = QAction('窗口置顶', self)
        topMostAction.triggered.connect(self.top_most)
        contextMenu.addAction(topMostAction)
        scnshotAction = QAction('屏幕截图', self)
        scnshotAction.triggered.connect(self.screen_shot)
        contextMenu.addAction(scnshotAction)
        if not self.gifRecording:
            stGIFAction = QAction('开始录制GIF', self)
            stGIFAction.triggered.connect(self.start_recording_gif)
            contextMenu.addAction(stGIFAction)
            pstGIFAction = QAction('从节目开头开始录制GIF', self)
            pstGIFAction.triggered.connect(self.p_start_recording_gif)
            contextMenu.addAction(pstGIFAction)
        else:
            edGIFAction = QAction('结束录制GIF', self)
            edGIFAction.triggered.connect(self.stop_recording_gif)
            contextMenu.addAction(edGIFAction)
            pedGIFAction = QAction('节目完成后结束录制GIF', self)
            pedGIFAction.triggered.connect(self.p_stop_recording_gif)
            contextMenu.addAction(pedGIFAction)
            waitAction = QAction('结束请耐心等待(^_^)', self)
            waitAction.triggered.connect(self.stop_recording_gif)
            contextMenu.addAction(waitAction)

        contextMenu.exec_(self.mapToGlobal(pos))

    def mousePressEvent(self, e):
        # if self.gifRecording:
        #     self.endGifFrame = len(self.gifFrames)
        if e.buttons() == Qt.LeftButton:
            try:
                print(e.pos())
                self.mos = e.pos()
            except:
                pass
                
    def mouseMoveEvent(self, e):
        try:
            if e.buttons() == Qt.LeftButton and self.mos:
                self.move(self.mapToGlobal(e.pos() - self.mos))
            e.accept()
        except:
            pass

    def closeEvent(self, event):
        self.stopThread_BmpUpdater()
        self.deleteLater()

    def top_most(self):
        try:
            flags = self.windowFlags()
            if flags & Qt.WindowStaysOnTopHint:
                self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
            else:
                self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
            self.show()
            self.show()
        except Exception as e:
            pass

    def capture_screen(self):
        pixmap = self.screen.grabWindow(self.window_handle)
        # 将 QPixmap 转换为 QImage
        qimage = pixmap.toImage()
        # 确保 qimage 是 ARGB32 格式
        if qimage.format() != QImage.Format_ARGB32:
            qimage = qimage.convertToFormat(QImage.Format_ARGB32)
        
        # 获取 QImage 的字节数据
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        arr = np.array(ptr).reshape(qimage.height(), qimage.width(), 4)  # 4通道 (RGBA)

        # 转换通道顺序从 ARGB 到 RGBA
        arr = arr[..., [2, 1, 0, 3]]  # 将通道顺序从 ARGB 转换为 RGBA
        
        # 使用 PIL Image 从 NumPy 数组中读取图像
        pil_image = Image.fromarray(arr, 'RGBA')

        # img = ImageQt.fromqpixmap(pixmap)
        # print(type(pil_image))
        self.gifFrames.append(pil_image)
        # print(pil_image)
        if len(self.gifFrames) >= 200:
            self.save_gif(True)

    def screen_shot(self):
        self.capture_screen()
        fileName = datetime.datetime.now().strftime(f"{self.toDisplay}_%Y%m%d%H%M%S.png")
        self.gifFrames[0].save(os.path.join("./ScreenShots",fileName))

    def start_recording_gif(self):
        try:
            os.makedirs("./ScreenShots")
        except Exception as e:
            pass
        self.tmpGifNames = []
        self.gifFrames = []
        self.gifRecording = True

    def p_start_recording_gif(self):
        # if self.Parent is not None:
        #     self.Parent.change_currentDisplayProgIndex(self)
        self.programTimeout()
        self.start_recording_gif()

    def stop_recording_gif(self):
        self.gifRecording = False
        self.save_gif()

    def p_stop_recording_gif(self):
        self.progStopGif = True

    def save_gif(self, temp = False):
        if temp:
            try:
                fileName = datetime.datetime.now().strftime(f"temp_{self.toDisplay}_%Y%m%d%H%M%S.gif")
                self.gifFrames[0].save(os.path.join("./ScreenShots",fileName), save_all=True, append_images=self.gifFrames[1:], optimize=False, duration=100, loop=0, disposal=2)
                self.gifFrames = []
                self.tmpGifNames.append(fileName)
            except Exception as e:
                print("save_gif: ", e)
        else:
            self.save_gif(True)
            fileName = datetime.datetime.now().strftime(f"{self.toDisplay}_%Y%m%d%H%M%S_output.gif")
            combined_gif = imageio.get_writer(os.path.join("./ScreenShots",fileName), fps = self.gifFps, loop = 0)
            print(self.tmpGifNames)
            for g in self.tmpGifNames:
                g = os.path.join("./ScreenShots",g)
                gif = imageio.get_reader(g)
                for frame in gif:
                    combined_gif.append_data(frame)
                gif.close()
            
            combined_gif.close()

            for g in self.tmpGifNames:
                g = os.path.join("./ScreenShots",g)
                os.remove(g)

    def checkTimeStr(self):
        chinese_week_day = {
            'Monday': '星期一',
            'Tuesday': '星期二',
            'Wednesday': '星期三',
            'Thursday': '星期四',
            'Friday': '星期五',
            'Saturday': '星期六',
            'Sunday': '星期日'
        }
        try:
            for s in self.units:
                now = datetime.datetime.now()
                oldStr = s.progSheet["text"]
                chWeekday = now.strftime("%A")
                newStr = re.sub(r"(?<!%)(%A)", chinese_week_day[chWeekday], oldStr )
                # newStr = oldStr.replace("%A",chinese_week_day[chWeekday])
                # print(newStr)
                newStr = now.strftime(newStr)
                if newStr != s.tempStr:
                    s.progSheet["text"] = newStr
                    s.tempStr = newStr
                    s.createFontImg()
                    s.progSheet["text"] = oldStr
        except Exception as e:
            print("checkTimeStr:", e)

    def change_cntIndex(self, cntindex = 0, jmpfrom = None):
        if jmpfrom is None:
            if self.cntProgIsOrigin:
                self.jumpFrom = self.currentIndex
            self.currentIndex = cntindex
        else:
            self.currentIndex = cntindex
            self.jumpFrom = jmpfrom


    def normal_goto_prog(self):
        a = 0
        if self.currentIndex+1 <= len(self.screenProgramSheet)-1:
            a = self.currentIndex + 1
        else:
            a = 0
            self.performFinish = True
        self.change_cntIndex(cntindex=a)
        if self.Parent is not None:
            self.Parent.change_currentDisplayProgIndex(self)

    def checkProgramTimeout(self):
        self.runningTime = time.time() - self.currentBeginTime
        if self.runningTime >= self.currentPtime and self.currentPtime >= 0:
            if self.currentScreenProgSet is not None:
                # 这里不用改正触发器设置的错误（多次更改设计导致）
                trigger = self.currentScreenProgSet["trigger"]
                if isinstance(trigger,list):
                    if len(trigger) > 0:
                        tg = trigger[0]
                        self.get_jumpto_index(tg)
                        if self.Parent is not None:
                            self.Parent.change_currentDisplayProgIndex(self)
                        self.programTimeout()
                    else:
                        self.normal_goto_prog()
                        self.programTimeout()
            else:
                self.normal_goto_prog()
                self.programTimeout()

    def default_tg(self):
        num = []
        for u in self.units:
            num.append(u.counter)
        if self.currentPtime < 0 and max(num) >= 1:
            self.normal_goto_prog()
            self.programTimeout()

    def get_jumpto_index(self,tg):
        abst = True
        prange = 0
        gfrom = 0
        if "prange" in tg.keys():
            rg = tg["prange"]
            prange = random.randint(min(0,rg),max(0,rg))
        if "gfrom" in tg.keys():
            if tg["gfrom"]:
                gfrom = 1
        if "abst" in tg.keys():
            abst = tg["abst"]
        print("self.currentIndex =", self.currentIndex, "tg['to'] =", tg["to"], "prange =", prange, "self.jumpFrom =", self.jumpFrom, "gfrom =", gfrom)
        if abst:
            b = (self.currentIndex + tg["to"] + prange + (self.jumpFrom-self.currentIndex) * gfrom) % len(self.screenProgramSheet)
        else:
            b = (tg["to"] - 1 + prange) % len(self.screenProgramSheet)

        self.change_cntIndex(cntindex=b)

    def triggerProgramTimeout(self):
        if self.currentPtime < 0:
            if self.currentScreenProgSet is not None:
                # 这里不用改正触发器设置的错误（多次更改设计导致）
                trigger = self.currentScreenProgSet["trigger"]
                if isinstance(trigger,list):
                    if len(trigger) > 0:
                        for tg in trigger:
                            # print(self.units[tg["u"]-1].counter, tg["c"])
                            if self.units[tg["u"]-1].counter >= tg["c"]:
                                self.get_jumpto_index(tg)

                                self.programTimeout()
                                if self.Parent is not None:
                                    self.Parent.change_currentDisplayProgIndex(self)

                                break
                    else:
                        if self.otherscreen_hastrigger() == 0:
                            self.default_tg()
            else:
                if self.otherscreen_hastrigger() == 0:
                    self.default_tg()

    def otherscreen_hastrigger(self):
        n_t = 0
        for s in self.Parent.LedScreens.values():
            try:
                t = s.currentScreenProgSet["trigger"]
                if isinstance(t,list) and len(t) > 0 and s is not self:
                    n_t += 1
                    # print(s,"+1")
            except Exception as e:
                pass
                # print("everyscreen_hastrigger: ",e)
        return n_t
            

    def programTimeout(self):
        if self.progStopGif:        # 录制GIF直到当前节目结束
            self.progStopGif = False
            if self.gifRecording:
                self.stop_recording_gif()
        self.currentBeginTime = time.time()
        self.runningTime = 0
        if self.isVisible() == True:
            if self.currentIndex in range(len(self.screenProgramSheet)):
                try:
                    self.currentPtime = self.screenProgramSheet[self.currentIndex][1]
                    unitAndProgram = self.screenProgramSheet[self.currentIndex][2][self.toDisplay]
                    if len(unitAndProgram) == 3:
                        ext_dict = unitAndProgram[2]
                        if "ProgScreenSetting" in ext_dict.keys():
                            self.currentScreenProgSet = ext_dict["ProgScreenSetting"]
                        else:
                            self.currentScreenProgSet = None
                    else:
                        self.currentScreenProgSet = None

                    if self.currentScreenProgSet is not None:
                        if "isorigin" in self.currentScreenProgSet.keys():
                            self.cntProgIsOrigin = self.currentScreenProgSet["isorigin"]

                    self.units = []
                    for i in range(min(len(unitAndProgram[0]),len(unitAndProgram[1]))):
                        self.units.append(ScreenUnit(unitAndProgram[0][i],unitAndProgram[1][i],self.colorMode,self.offset,self.FontIconMgr))
                    self.backgroundPerformer()
                except Exception as e:
                    print("programTimeout:", e)

        self.checkTimeStr()

    def backgroundPerformer(self):
        self.maskMode = False
        
        if self.currentScreenProgSet is not None:
            #**********
            #以下为改正设置错误的触发器设置项
            if "tigger" in self.currentScreenProgSet.keys():    # 拼写错误和内容错误的设置项目
                self.currentScreenProgSet.pop("tigger")
                self.currentScreenProgSet["trigger"] = []    # 没有触发器为空列表

            if not isinstance(self.currentScreenProgSet["trigger"],list):
                self.currentScreenProgSet["trigger"] = []
            #**********

            backgroundDescribeText = self.currentScreenProgSet["background"]

            if backgroundDescribeText.startswith("colorMask") or backgroundDescribeText.startswith("imgMask") or backgroundDescribeText.startswith("videoMask"):
                self.maskMode = True

            if backgroundDescribeText.startswith("color"):
                # 使用正则表达式匹配括号中的RGB值
                pattern = r"(?:colorMask|colorBackground)\(\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\)"
                match = re.search(pattern, backgroundDescribeText)
                if match:
                    # 提取匹配到的三个数字并转换为整数
                    r = max(0,min(255,int(match.group(1))))
                    g = max(0,min(255,int(match.group(2))))
                    b = max(0,min(255,int(match.group(3))))
                    color =  (r, g, b)
                    self.BackImg = Image.new("RGB", (self.screenSize[0],self.screenSize[1]), color)
                    self.backgroundImgUpdater()

            elif backgroundDescribeText.startswith("img"):
                # 匹配函数名、文件名和数字参数
                pattern = r'(?:imgMask|imgBackground)\("([^"]+)",\s*(\d+)\s*\)'
                match = re.search(pattern, backgroundDescribeText)
                if match:
                    filename = match.group(1)  # 第一个参数（文件名）
                    fill = int(match.group(2))  # 第二个参数（数字）
                    if "background_folder" in self.settings.keys():
                        backImgDir = os.path.join(self.settings["background_folder"],filename)
                        if os.path.exists(backImgDir):
                            self.BackImg = Image.open(backImgDir)
                            if fill == 0:    # (["平铺","居中","填充","拉伸"])  # 0123
                                lim = self.BackImg.crop((0,0,min(self.BackImg.width,self.screenSize[0]),min(self.BackImg.height,self.screenSize[1])))
                                bim = Image.new("RGB", (self.screenSize[0],self.screenSize[1]), (0,0,0))
                                for x in range(int(bim.width/lim.width)+1):
                                    for y in range(int(bim.height/lim.height)+1):
                                        bim.paste(lim,(x*lim.width,y*lim.height))
                                self.BackImg = bim
                            elif fill == 1:
                                bim = Image.new("RGB", (self.screenSize[0],self.screenSize[1]), (0,0,0))
                                x = int(0.5*(bim.width-self.BackImg.width))
                                y = int(0.5*(bim.height-self.BackImg.height))
                                bim.paste(self.BackImg,(x,y))
                                self.BackImg = bim
                            elif fill == 2:
                                bim = Image.new("RGB", (self.screenSize[0],self.screenSize[1]), (0,0,0))
                                imratio = self.BackImg.width/self.BackImg.height
                                scratio = self.screenSize[0]/self.screenSize[1]
                                if imratio >= scratio:
                                    lim = self.BackImg.resize((int(imratio * self.screenSize[1]),self.screenSize[1]),resample=Image.BILINEAR)
                                else:
                                    lim = self.BackImg.resize((self.screenSize[0],int(self.screenSize[0]/imratio)),resample=Image.BILINEAR)
                                x = int(0.5*(bim.width-lim.width))
                                y = int(0.5*(bim.height-lim.height))
                                bim.paste(lim,(x,y))
                                self.BackImg = bim
                            elif fill == 3:
                                pass  # 默认实现的效果就是fill = 3
                            elif fill == 4:
                                bim = Image.new("RGB", (self.screenSize[0],self.screenSize[1]), (0,0,0))
                                imratio = self.BackImg.width/self.BackImg.height
                                scratio = self.screenSize[0]/self.screenSize[1]
                                if imratio >= scratio:
                                    lim = self.BackImg.resize((self.screenSize[0],int(self.screenSize[0]/imratio)),resample=Image.BILINEAR)
                                else:
                                    lim = self.BackImg.resize((int(imratio * self.screenSize[1]),self.screenSize[1]),resample=Image.BILINEAR)
                                x = int(0.5*(bim.width-lim.width))
                                y = int(0.5*(bim.height-lim.height))
                                bim.paste(lim,(x,y))
                                self.BackImg = bim


                            self.backgroundImgUpdater()

    def backgroundImgUpdater(self):
        sw,sh = self.screenSize[0]*self.screenScale[0], self.screenSize[1]*self.screenScale[1]
        imw,imh = self.BackImg.width,self.BackImg.height
        for u in self.units:
            ux,uy = u.position
            upn,usz = u.pointNum,u.scale
            tx,ty = int(ux*imw/sw),int(uy*imh/sh)
            tw,th = int(imw*upn[0]*usz[0]/sw),int(imh*upn[1]*usz[1]/sh)
            # print("转换坐标：",tx,ty,tw,th,"图像大小：",imw,imh)
            im = self.BackImg.crop((tx,ty,tx+tw,ty+th))
            if self.colorMode == "1":
                im = im.convert('1')
            im = im.resize((upn[0],upn[1]),resample=Image.BILINEAR)
            u.backBitmap = im


    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setPen(Qt.NoPen)
        self.flushScreen()
        self.drawBackground(qp)
        for s in self.units:
            self.drawScreen(s,qp)
        qp.end()
        if self.gifRecording and self.isVisible():
            self.capture_screen()
        
        self.fpsCounter += 1

    def flushScreen(self):
        if self.keep_speed:
            if self.commonFps > 0:
                f = max(1, self.expectedFps / self.commonFps)
            else:
                f = 1
            self.owingFps += (f - int(f))
            f = int(f)
            if self.owingFps > 1:
                f +=int(self.owingFps)
                self.owingFps -= int(self.owingFps)
        else:
            f = 1

        for u in self.units:   
            for _ in range(f):
                self.posTransFunc(u)
                u.rollCounter += 1

    def count_fps(self):
        self.commonFps = self.fpsCounter
        self.fpsCounter = 0
        self.setWindowTitle(f'{self.toDisplay} @ {self.commonFps} FPS')

    def get_fps(self):
        fps = self.commonFps
        self.gifFps = min(max(fps,self.gifFps),50)
        fps = str(fps)
        if self.gifRecording:
            fps += f"  {self.toDisplay} 正在录制GIF({self.gifFps})  "
        return fps

    def posTransFunc(self,obj):
        appearance = obj.appearance
        c0 = obj.counter

        arg1,arg2 = obj.progSheet["argv_1"],obj.progSheet["argv_2"]
        if "argv_3" in obj.progSheet.keys(): 
            arg3 = obj.progSheet["argv_3"]
        else:
            arg3 = 1   # 旧版节目单
        if not obj.progSheet["vertical"]:
            align = obj.progSheet["align"]
        else:
            align = obj.progSheet["align"][::-1]
        if align[0] == 0:
            pos0 = int(0.5*(obj.Bitmap.size[0] - obj.pointNum[0]))
            if (obj.Bitmap.size[0] - obj.pointNum[0]) % 2 == 1:
                pos0 -= 1
        elif align[0] < 0:
            pos0 = obj.Bitmap.size[0] - obj.pointNum[0]
        else:
            pos0 = 0
        if align[1] == 0:
            y0 = int(0.5*(obj.Bitmap.size[1]-obj.pointNum[1]))
        elif align[1] < 0:
            y0 = obj.Bitmap.size[1] - obj.pointNum[1]
        else:
            y0 = 0

        pos0 += obj.x_offset
        y0 += obj.y_offset

        sped = arg1 % 10 if arg1 % 10 != 0 else 1
        step = arg1 // 10 + 1
        
        if appearance == "静止":
            obj.appear = True
            obj.x = pos0
            obj.y = y0
            obj.counter = obj.rollCounter // (1000 // self.flushRate)
        elif appearance == "闪烁":
            obj.x = pos0
            obj.y = y0
            if obj.rollCounter <= arg1+1:
                obj.appear = True
            elif obj.rollCounter <= arg1+arg2+1:
                obj.appear = False
            else:
                obj.rollCounter = 1
                obj.counter += 1
        elif appearance == "向左滚动":
            obj.appear = True
            obj.y = y0
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if arg2 < 0:
                    if obj.x >= obj.Bitmap.size[0]:
                        obj.counter += 1
                    obj.x = obj.x+arg3 if obj.x < obj.Bitmap.size[0] else -obj.pointNum[0]
                else:
                    if obj.x > obj.Bitmap.size[0]+arg2:
                        obj.counter += 1
                    obj.x = obj.x+arg3 if obj.x <= obj.Bitmap.size[0]+arg2 else 1+arg3
        elif appearance == "向右滚动":
            obj.appear = True
            obj.y = y0
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if arg2 < 0:
                    if obj.x <= -obj.pointNum[0]:
                        obj.counter += 1
                    obj.x = obj.x-arg3 if obj.x > -obj.pointNum[0] else obj.Bitmap.size[0]
                else:
                    if obj.x < 2:
                        obj.counter += 1
                    obj.x = obj.x-arg3 if obj.x >= 1+arg3 else obj.Bitmap.size[0]+arg2
        elif appearance == "向上滚动":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if arg2 < 0:
                    if obj.y >= obj.Bitmap.size[1]:
                        obj.counter += 1
                    obj.y = obj.y+arg3 if obj.y < obj.Bitmap.size[1] else -obj.pointNum[1]
                else:
                    if obj.y > obj.Bitmap.size[1]+arg2:
                        obj.counter += 1
                    obj.y = obj.y+arg3 if obj.y <= obj.Bitmap.size[1]+arg2 else 1+arg3
        elif appearance == "向下滚动":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if arg2 < 0:
                    if obj.y <= -obj.pointNum[1]:
                        obj.counter += 1
                    obj.y = obj.y-arg3 if obj.y > -obj.pointNum[1] else obj.Bitmap.size[1]
                else:
                    if obj.y < 2:
                        obj.counter += 1
                    obj.y = obj.y-arg3 if obj.y >= 1+arg3 else obj.Bitmap.size[1]+arg2
        elif appearance == "向左移到中间":
            obj.appear = True
            obj.y = y0
            if obj.rollCounter == 0:
                obj.x = -obj.pointNum[0]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if obj.x < pos0:
                    obj.x = obj.x+arg3
                else:
                    obj.counter = 65535
        elif appearance == "向右移到中间":
            obj.appear = True
            obj.y = y0
            if obj.rollCounter == 0:
                obj.x = obj.Bitmap.size[0]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if obj.x > pos0:
                    obj.x = obj.x-arg3
                else:
                    obj.counter = 65535
        elif appearance == "向上移到中间":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter == 0:
                obj.y = -obj.pointNum[1]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if obj.y < y0:
                    obj.y = obj.y+arg3
                else:
                    obj.counter = 65535
        elif appearance == "向下移到中间":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter == 0:
                obj.y = obj.Bitmap.size[1]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if obj.y > y0:
                    obj.y = obj.y-arg3
                else:
                    obj.counter = 65535
        elif appearance in ["向左开百叶窗","向右开百叶窗","向上开百叶窗","向下开百叶窗","向左关百叶窗","向右关百叶窗","向上关百叶窗","向下关百叶窗"]:    # arg1~3: 速度，窗户大小，显示窗户？
            obj.appear = True
            obj.x = pos0
            obj.y = y0
            if obj.rollCounter < sped:
                pass
            else:
                if obj.showat <= arg2:
                    obj.showat += step
                    obj.rollCounter = 0
            if obj.showat >= arg2:
                obj.counter = 65535
        elif appearance in ["开水平窗户","关水平窗户"]:  # 速度，显示
            obj.appear = True
            obj.x = pos0
            obj.y = y0
            if obj.rollCounter < sped:
                pass
            else:
                if obj.showat <= obj.pointNum[0]//2:
                    obj.showat += step
                    obj.rollCounter = 0
            if obj.showat >= obj.pointNum[0]//2:
                obj.counter = 65535
        elif appearance in ["开竖直窗户","关竖直窗户"]:   # 速度，显示
            obj.appear = True
            obj.x = pos0
            obj.y = y0
            if obj.rollCounter < sped:
                pass
            else:
                if obj.showat <= obj.pointNum[1]//2:
                    obj.showat += step
                    obj.rollCounter = 0
            if obj.showat >= obj.pointNum[1]//2:
                obj.counter = 65535
        elif appearance in ["向左扇形圆形","向右扇形圆形"]:    # arg1~3: 速度，步长，连续？
            obj.appear = True
            obj.x = pos0
            obj.y = y0
            if obj.showat <= obj.pointNum[0]:
                if arg3 >= 1 and obj.rollCounter >= sped:
                    obj.showat += step
                    obj.rollCounter = 0
                elif arg3 < 1 and obj.rollCounter >= arg1:
                    obj.showat += arg2
                    if obj.rollCounter >= arg1:
                        obj.rollCounter = 0
            if obj.showat >= obj.pointNum[0]:
                obj.counter = 65535
        elif appearance in ["向上扇形圆形","向下扇形圆形"]:    # arg1~3: 速度，步长，连续？ 
            obj.appear = True
            obj.x = pos0
            obj.y = y0
            if obj.showat <= obj.pointNum[1]:
                if arg3 >= 1 and obj.rollCounter >= sped:
                    obj.showat += step
                    obj.rollCounter = 0
                elif arg3 < 1 and obj.rollCounter >= arg1:
                    obj.showat += arg2
                    if obj.rollCounter >= arg1:
                        obj.rollCounter = 0
            if obj.showat >= obj.pointNum[1]:
                obj.counter = 65535
        elif appearance == "中间向左移开":
            obj.appear = True
            obj.y = y0
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.x >= obj.Bitmap.size[0]:
                        obj.counter = 65535
                    obj.x = obj.x+arg3 if obj.x < obj.Bitmap.size[0] else obj.x
        elif appearance == "中间向右移开":
            obj.appear = True
            obj.y = y0
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.x <= -obj.pointNum[0]:
                        obj.counter = 65535
                    obj.x = obj.x-arg3 if obj.x > -obj.pointNum[0] else obj.x
        elif appearance == "中间向上移开":
            obj.appear = True
            obj.x = pos0
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.y >= obj.Bitmap.size[1]:
                        obj.counter = 65535
                    obj.y = obj.y+arg3 if obj.y < obj.Bitmap.size[1] else obj.y
        elif appearance == "中间向下移开":
            obj.appear = True
            obj.x = pos0
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.y <= -obj.pointNum[1]:
                        obj.counter = 65535
                    obj.y = obj.y-arg3 if obj.y > -obj.pointNum[1] else obj.y
        elif appearance == "跳跃向左移动":
            obj.appear = True
            obj.y = y0
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[0] > obj.Bitmap.size[0]:
                    if obj.x+arg2 <= 0 and obj.rollCounter <= arg1:
                        obj.x = obj.x+arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            obj.counter += obj.rollCounter // int(arg3*1000/self.flushRate)
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.x = -obj.pointNum[0]+obj.Bitmap.size[0]
                        if obj.rollCounter > 2*int(arg3*1000/self.flushRate):
                            obj.rollCounter = 0
                else:
                    if obj.x+arg2 <= -obj.pointNum[0]+obj.Bitmap.size[0] and obj.rollCounter <= arg1:
                        obj.x = obj.x+arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            obj.counter += obj.rollCounter // int(arg3*1000/self.flushRate)
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.x = 0
                        if obj.rollCounter > 2*int(arg3*1000/self.flushRate):
                            obj.rollCounter = 0
        elif appearance == "跳跃向右移动":
            obj.appear = True
            obj.y = y0
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[0] > obj.Bitmap.size[0]:
                    if obj.x-arg2 >= -obj.pointNum[0]+obj.Bitmap.size[0] and obj.rollCounter <= arg1:
                        obj.x = obj.x-arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            obj.counter += obj.rollCounter // int(arg3*1000/self.flushRate)
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.x = 0
                        if obj.rollCounter > 2*int(arg3*1000/self.flushRate):
                            obj.rollCounter = 0
                else:
                    if obj.x-arg2 >= 0 and obj.rollCounter <= arg1:
                        obj.x = obj.x-arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            obj.counter += obj.rollCounter // int(arg3*1000/self.flushRate)
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.x = -obj.pointNum[0]+obj.Bitmap.size[0]
                        if obj.rollCounter > 2*int(arg3*1000/self.flushRate):
                            obj.rollCounter = 0
        elif appearance == "跳跃向上移动":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[1] > obj.Bitmap.size[1]:
                    if obj.y+arg2 <= 0 and obj.rollCounter <= arg1:
                        obj.y = obj.y+arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            obj.counter += obj.rollCounter // int(arg3*1000/self.flushRate)
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.y = -obj.pointNum[1]+obj.Bitmap.size[1]
                        if obj.rollCounter > 2*int(arg3*1000/self.flushRate):
                            obj.rollCounter = 0
                else:
                    if obj.y+arg2 <= -obj.pointNum[1]+obj.Bitmap.size[1] and obj.rollCounter <= arg1:
                        obj.y = obj.y+arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            obj.counter += obj.rollCounter // int(arg3*1000/self.flushRate)
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.y = 0
                        if obj.rollCounter > 2*int(arg3*1000/self.flushRate):
                            obj.rollCounter = 0
        elif appearance == "跳跃向下移动":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[1] > obj.Bitmap.size[1]:
                    if obj.y-arg2 >= -obj.pointNum[1]+obj.Bitmap.size[1] and obj.rollCounter <= arg1:
                        obj.y = obj.y-arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            obj.counter += obj.rollCounter // int(arg3*1000/self.flushRate)
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.y = 0
                        if obj.rollCounter > 2*int(arg3*1000/self.flushRate):
                            obj.rollCounter = 0
                else:
                    if obj.y-arg2 >= 0 and obj.rollCounter <= arg1:
                        obj.y = obj.y-arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            obj.counter += obj.rollCounter // int(arg3*1000/self.flushRate)
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.y = -obj.pointNum[1]+obj.Bitmap.size[1]
                        if obj.rollCounter > 2*int(arg3*1000/self.flushRate):
                            obj.rollCounter = 0
        elif appearance == "向左翻屏":
            obj.appear = True
            obj.y = y0
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[0] < obj.Bitmap.size[0]:
                    if obj.x+arg2 <= -obj.pointNum[0]+obj.Bitmap.size[0]:
                        if obj.x % obj.pointNum[0] >= arg2:
                            if obj.rollCounter <= arg1:
                                obj.x = obj.x+arg2
                                obj.rollCounter = 0
                        else:
                            if obj.rollCounter > int(arg3*1000/self.flushRate):
                                obj.x = obj.x+arg2
                                obj.rollCounter = 0
                    else:
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.x = 0
                            obj.rollCounter = 0
                            obj.counter += 1
                else:
                    obj.counter = obj.rollCounter // (1000 // self.flushRate)
        elif appearance == "向右翻屏":
            obj.appear = True
            obj.y = y0
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[0] < obj.Bitmap.size[0]:
                    if obj.x-arg2 >= 0:
                        if obj.x % obj.pointNum[0] >= arg2:
                            if obj.rollCounter <= arg1:
                                obj.x = obj.x-arg2
                                obj.rollCounter = 0
                        else:
                            if obj.rollCounter > int(arg3*1000/self.flushRate):
                                obj.x = obj.x-arg2
                                obj.rollCounter = 0
                    else:
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.x = -obj.pointNum[0]+obj.Bitmap.size[0]
                            obj.rollCounter = 0
                            obj.counter += 1
                else:
                    obj.counter = obj.rollCounter // (1000 // self.flushRate)
        elif appearance == "向上翻屏":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[1] < obj.Bitmap.size[1]:
                    if obj.y+arg2 <= -obj.pointNum[1]+obj.Bitmap.size[1]:
                        if obj.y % obj.pointNum[1] >= arg2:
                            if obj.rollCounter <= arg1:
                                obj.y = obj.y+arg2
                                obj.rollCounter = 0
                        else:
                            if obj.rollCounter > int(arg3*1000/self.flushRate):
                                obj.y = obj.y+arg2
                                obj.rollCounter = 0
                    else:
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.y = 0
                            obj.rollCounter = 0
                            obj.counter += 1
                else:
                    obj.counter = obj.rollCounter // (1000 // self.flushRate)
        elif appearance == "向下翻屏":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[1] < obj.Bitmap.size[1]:
                    if obj.y-arg2 >= 0:
                        if obj.y % obj.pointNum[1] >= arg2:
                            if obj.rollCounter <= arg1:
                                obj.y = obj.y-arg2
                                obj.rollCounter = 0
                        else:
                            if obj.rollCounter > int(arg3*1000/self.flushRate):
                                obj.y = obj.y-arg2
                                obj.rollCounter = 0
                    else:
                        if obj.rollCounter > int(arg3*1000/self.flushRate):
                            obj.y = -obj.pointNum[1]+obj.Bitmap.size[1]
                            obj.rollCounter = 0
                            obj.counter += 1
                else:
                    obj.counter = obj.rollCounter // (1000 // self.flushRate)
        elif appearance == "上下反复跳跃移动":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[1] > obj.Bitmap.size[1]:
                    if (obj.counter+1) % 2:
                        if obj.y+arg2 >= 0 and obj.rollCounter >= int(arg3*1000/self.flushRate):
                            obj.counter += 1
                        if obj.y+arg2 <= 0:
                            obj.y = obj.y+arg2
                            obj.rollCounter = 0
                    else:
                        if obj.y-arg2 <= -obj.pointNum[1]+obj.Bitmap.size[1] and obj.rollCounter >= int(arg3*1000/self.flushRate):
                            obj.counter += 1
                        if obj.y-arg2 >= -obj.pointNum[1]+obj.Bitmap.size[1]:
                            obj.y = obj.y-arg2
                            obj.rollCounter = 0
                else:
                    if (obj.counter+1) % 2:
                        if obj.y+arg2 >= -obj.pointNum[1]+obj.Bitmap.size[1] and obj.rollCounter >= int(arg3*1000/self.flushRate):
                            obj.counter += 1
                        if obj.y+arg2 <= -obj.pointNum[1]+obj.Bitmap.size[1]:
                            obj.y = obj.y+arg2
                            obj.rollCounter = 0
                    else:
                        if obj.y-arg2 <= 0 and obj.rollCounter >= int(arg3*1000/self.flushRate):
                            obj.counter += 1
                        if obj.y-arg2 >= 0:
                            obj.y = obj.y-arg2
                            obj.rollCounter = 0
        if obj.counter != c0:
            self.counterPlusOne.emit()

    def is_point_in_ellipse(self, x, y, ex, ey, w, h):
        if x >= ex and x <= ex + w and y >= ey and y <= ey + h:
            return ((x-(ex+w/2))**2/(w/2)**2 + (y-(ey+h/2))**2/(h/2)**2) <= 1
        else:
            return False
    
    def is_point_above_line(self, point_x, point_y, line_x, line_y, angle_degrees):
        # 将角度转换为斜率
        # 避免90度和270度的情况（斜率无穷大）
        if angle_degrees == 90 or angle_degrees == 270:
            return point_x < line_x if angle_degrees == 90 else point_x > line_x
        
        # 计算斜率 k = tan(angle)
        k = -1    # 初始值，避免未定义
        if 0 <= angle_degrees < 90:
            k = angle_degrees / (90 - angle_degrees)
        elif 90 < angle_degrees <= 180:
            k = (180 - angle_degrees) / (angle_degrees - 90)
            k = -k
        elif 180 < angle_degrees <= 270:
            k = (angle_degrees - 180) / (270 - angle_degrees)
        else:  # 270 < angle_degrees < 360
            k = (360 - angle_degrees) / (angle_degrees - 270)
            k = -k
        
        # 计算直线方程 y = k(x - x1) + y1
        expected_y = k * (line_x - point_x) + line_y    # y轴向下
        
        # 如果实际y值小于预期y值，点在直线上方
        return point_y < expected_y

    def in_sector_area(self,unit,x,y):
        appearance = unit.appearance    # arg1~3: 速度，步长，连续？
        pointNum = unit.pointNum
        showat = unit.showat
        arg1,arg2 = unit.progSheet["argv_1"],unit.progSheet["argv_2"]
        if "argv_3" in unit.progSheet.keys(): 
            arg3 = unit.progSheet["argv_3"]
        else:
            arg3 = 1
        if arg3 >= 1:
            angle = int(90 * (abs(arg2 / 2 - (showat % arg2)))/arg2)
        else:
            if unit.rollCounter*2 > arg1:
                angle = 0
            else:
                angle = 45

        if appearance in ["向右扇形圆形","向左扇形圆形"]:
            d = pointNum[1]
            if "左" in appearance:
                x = pointNum[0] - x - 1
            ellipsepoint = [showat,0]
            linepoint = [showat + d // 2, (d // 2)+1]

            if y >= pointNum[1] // 2:
                y = pointNum[1] - y - 1

        elif appearance in ["向下扇形圆形","向上扇形圆形"]:
            d = pointNum[0]
            if "上" in appearance:
                y = pointNum[1] - y - 1

            ellipsepoint = [0,showat]
            linepoint = [(d // 2)+1, showat + d // 2]
            angle = 90 - angle

            if x >= pointNum[0] // 2:
                x = pointNum[0] - x - 1

        ispoint = self.is_point_in_ellipse(x+0.5,y+0.5,ellipsepoint[0],ellipsepoint[1],d,d) and self.is_point_above_line(x+1,y+1,linepoint[0],linepoint[1],angle)

        return ispoint
    
    def hiden_for_sector(self,unit,x,y):
        if "argv_3" in unit.progSheet.keys(): 
            arg3 = unit.progSheet["argv_3"]
        else:
            arg3 = 1
        arg3 = 1 if arg3 != 0 else 0

        if unit.appearance == "向右扇形圆形":
            return unit.appearance not in sector_area_eft or unit.appearance in sector_area_eft and x >= unit.showat + arg3 * int(0.5*unit.pointNum[1])
        elif unit.appearance == "向左扇形圆形":
            return unit.appearance not in sector_area_eft or unit.appearance in sector_area_eft and x <= unit.pointNum[0] - (unit.showat + arg3 * int(0.5*unit.pointNum[1]))
        elif unit.appearance == "向下扇形圆形":
            return unit.appearance not in sector_area_eft or unit.appearance in sector_area_eft and y >= unit.showat + arg3 * int(0.5*unit.pointNum[0])
        elif unit.appearance == "向上扇形圆形":
            return unit.appearance not in sector_area_eft or unit.appearance in sector_area_eft and y <= unit.pointNum[1] - (unit.showat + arg3 * int(0.5*unit.pointNum[0]))
        else:
            return False

    def in_hwindow_area(self,unit,x,y):
        appearance = unit.appearance     # arg1~3: 速度，窗户大小，显示窗户？
        if appearance not in hwindow_area_eft:
            return True
        pointNum = unit.pointNum
        showat = unit.showat
        arg1,arg2 = unit.progSheet["argv_1"],unit.progSheet["argv_2"]
        if "argv_3" in unit.progSheet.keys(): 
            arg3 = unit.progSheet["argv_3"]
        else:
            arg3 = 1

        if "开" in appearance:
            if appearance in ["向右开百叶窗","向左开百叶窗"]:
                if "左" in appearance:
                    x = pointNum[0] - x - 1
                return x % arg2 <= min(showat,arg2)
            if appearance in ["向下开百叶窗","向上开百叶窗"]:
                if "上" in appearance:
                    y = pointNum[1] - y - 1
                return y % arg2 <= min(showat,arg2)
        
        elif "关" in appearance:
            if appearance in ["向右关百叶窗","向左关百叶窗"]:
                if "左" in appearance:
                    x = pointNum[0] - x - 1
                return not (x % arg2 <= min(showat,arg2))
            if appearance in ["向下关百叶窗","向上关百叶窗"]:
                if "上" in appearance:
                    y = pointNum[1] - y - 1
                return not (y % arg2 <= min(showat,arg2))

    def on_hwindow(self,unit,x,y):
        appearance = unit.appearance     # arg1~3: 速度，窗户大小，显示窗户？
        if appearance not in hwindow_area_eft:
            return False
        pointNum = unit.pointNum
        showat = unit.showat
        arg1,arg2 = unit.progSheet["argv_1"],unit.progSheet["argv_2"]
        if "argv_3" in unit.progSheet.keys(): 
            arg3 = unit.progSheet["argv_3"]
        else:
            arg3 = 1
        if "开" in appearance:
            if appearance in ["向右开百叶窗","向左开百叶窗"]:
                if "左" in appearance:
                    x = pointNum[0] - x - 1
                return x % arg2 == min(showat,arg2) and arg3 == 1
            if appearance in ["向下开百叶窗","向上开百叶窗"]:
                if "上" in appearance:
                    y = pointNum[1] - y - 1
                return y % arg2 == min(showat,arg2) and arg3 == 1
        
        elif "关" in appearance:
            if appearance in ["向右关百叶窗","向左关百叶窗"]:
                if "左" in appearance:
                    x = pointNum[0] - x - 1
                return not (x % arg2 == min(showat,arg2)) and arg3 == 1
            if appearance in ["向下关百叶窗","向上关百叶窗"]:
                if "上" in appearance:
                    y = pointNum[1] - y - 1
                return not (y % arg2 == min(showat,arg2)) and arg3 == 1

    def in_window_area(self,unit,x,y):    # ["开水平窗户","关水平窗户","开竖直窗户","关竖直窗户"]
        appearance = unit.appearance     # arg1~3: 速度，显示窗户
        if appearance not in window_area_eft:
            return True
        pointNum = unit.pointNum
        showat = unit.showat
        # arg1,arg2 = unit.progSheet["argv_1"],unit.progSheet["argv_2"]

        if "水平" in appearance:
            if appearance == "开水平窗户":
                showat = pointNum[0]//2 - showat
                return x >= showat and x <= pointNum[0]-showat-1
            if appearance == "关水平窗户":
                return x <= showat or x >= pointNum[0]-showat-1
        
        elif "竖直" in appearance:
            if appearance == "开竖直窗户":
                showat = pointNum[1]//2 - showat
                return y >= showat and y <= pointNum[1]-showat-1
            if appearance == "关竖直窗户":
                return y <= showat or y >= pointNum[1]-showat-1

    def on_window(self,unit,x,y):
        appearance = unit.appearance     # arg1~3: 速度，显示窗户
        if appearance not in window_area_eft:
            return False
        pointNum = unit.pointNum
        showat = unit.showat
        arg2 = unit.progSheet["argv_2"]

        if "水平" in appearance:
            if "开" in appearance:
                showat = pointNum[0]//2 - showat
            return (x == showat or x == pointNum[0]-showat-1) and arg2 == 1 and showat < pointNum[0]//2

        elif "竖直" in appearance:
            if "开" in appearance:
                showat = pointNum[1]//2 - showat
            return (y == showat or y == pointNum[1]-showat-1) and arg2 == 1 and showat < pointNum[1]//2

    def drawBackground(self,qp):
        qp.setBrush(QColor(25,25,25))
        qp.drawRect(0,0,2*self.offset+self.screenSize[0]*self.screenScale[0],2*self.offset+self.screenSize[1]*self.screenScale[1])
        qp.setBrush(QColor(30,30,30))
        qp.drawRect(self.offset,self.offset,self.screenSize[0]*self.screenScale[0],self.screenSize[1]*self.screenScale[1])
        qp.setBrush(QColor(random.randint(30,200),random.randint(30,200),random.randint(30,200)))
        qp.drawRect(int(0.8*(2*self.offset+self.screenSize[0]*self.screenScale[0])),(2*self.offset+self.screenSize[1]*self.screenScale[1])-int(0.5*self.offset),1,1)
        qp.setBrush(QColor(random.randint(30,200),random.randint(30,200),random.randint(30,200)))
        qp.drawRect(int(0.8*(2*self.offset+self.screenSize[0]*self.screenScale[0])+10),(2*self.offset+self.screenSize[1]*self.screenScale[1])-int(0.5*self.offset),1,1)
        self.resize(2*self.offset+self.screenSize[0]*self.screenScale[0],2*self.offset+self.screenSize[1]*self.screenScale[1])

    def drawScreen(self, unit, qp):
        if not self.isVisible():
            return
        # 使用局部变量减少重复属性访问
        colorMode = self.colorMode
        rollSpace = unit.rollSpace
        bitmapSize = unit.Bitmap.size
        pointNum = unit.pointNum
        scale = unit.scale
        pointSize = unit.pointSize
        offset = unit.offset
        position = unit.position
        x_pos = unit.x
        y_pos = unit.y
        appear = unit.appear
        # 预先计算可能用到的颜色和参数
        if colorMode == "RGB":
            black = 60
            baseColor = QColor(black, black, black)
        else:
            baseColor = QColor(*unit.color_1[0])
        for y in range(pointNum[1]):
            for x in range(pointNum[0]):
                if unit.backBitmap is not None:
                    if x < unit.backBitmap.width and y < unit.backBitmap.height:
                        bac_color = unit.backBitmap.getpixel((x,y))
                else:
                    bac_color = 0 if colorMode == "1" else (0,0,0)
                qp.setBrush(baseColor)
                #------------------------------------------------
                try:
                    if rollSpace < 0 and x + x_pos in range(bitmapSize[0]) and y + y_pos in range(bitmapSize[1]) and appear:
                        color = unit.Bitmap.getpixel((x + x_pos, y + y_pos))
                    elif rollSpace >= 0 and ("左" in unit.appearance or "右"  in unit.appearance) and (x + x_pos) % (bitmapSize[0] + rollSpace) in range(bitmapSize[0]) and y + y_pos in range(bitmapSize[1]) and appear:
                        color = unit.Bitmap.getpixel(((x + x_pos) % (bitmapSize[0] + rollSpace), y + y_pos))
                    elif rollSpace >= 0 and ("上" in unit.appearance or "下"  in unit.appearance) and (y + y_pos) % (bitmapSize[1] + rollSpace) in range(bitmapSize[1]) and x + x_pos in range(bitmapSize[0]) and appear:
                        color = unit.Bitmap.getpixel((x + x_pos, (y + y_pos) % (bitmapSize[1] + rollSpace)))
                    else:
                        color = [0, 0, 0, 0] if colorMode == "RGB" else 0
                except:
                    color = [0, 0, 0, 0] if colorMode == "RGB" else 0
                #------------------------------------------------
                #------------------------------------------------
                if unit.appearance in hwindow_area_eft + window_area_eft + sector_area_eft:
                    #------------------------------------------------
                    if unit.appearance in hwindow_area_eft:
                        if not self.in_hwindow_area(unit,x,y):
                            color = [0, 0, 0, 0] if colorMode == "RGB" else 0
                        if self.on_hwindow(unit,x,y):
                            if unit.colorMode == "RGB":
                                color = unit.progSheet["color_RGB"][:]
                                color.append(255)
                            else:
                                color = 1
                    #------------------------------------------------
                    if unit.appearance in window_area_eft:
                        if not self.in_window_area(unit,x,y):
                            color = [0, 0, 0, 0] if colorMode == "RGB" else 0
                        if self.on_window(unit,x,y):
                            if unit.colorMode == "RGB":
                                color = unit.progSheet["color_RGB"][:]
                                color.append(255)
                            else:
                                color = 1
                    #------------------------------------------------
                    if unit.appearance in sector_area_eft:
                        if self.hiden_for_sector(unit,x,y):
                            color = [0, 0, 0, 0] if colorMode == "RGB" else 0
                        if self.in_sector_area(unit,x,y):
                            if unit.colorMode == "RGB":
                                color = unit.progSheet["color_RGB"][:]
                                color.append(255)
                            else:
                                color = 1
                #------------------------------------------------
                #------------------------------------------------
                if colorMode == "RGB" :
                    if unit.backBitmap is not None:
                        alpha = color[3]
                        if self.maskMode:
                            color = [int(bac_color[i] * alpha/255) for i in range(3)]
                        else:
                            color = [int(color[i] * alpha/255 + bac_color[i] * (255 - alpha)/255) for i in range(3)]
                        color = [black + int((255 - black) * c / 255) for c in color[0:3]]
                    else:
                        color = [black + int((255 - black) * c / 255) for c in color[0:3]]
                    qp.setBrush(QColor(*color))
                elif colorMode == "1":
                    if self.maskMode:
                        if bac_color & color:
                            qp.setBrush(QColor(*unit.color_1[1]))
                    else:
                        if bac_color | color and not bac_color & color:
                            qp.setBrush(QColor(*unit.color_1[1]))
                #------------------------------------------------
                ellipse_x = offset + position[0] + x * scale[0] + int(0.5 * (scale[0] - pointSize))
                ellipse_y = offset + position[1] + y * scale[1] + int(0.5 * (scale[1] - pointSize))
                qp.drawEllipse(ellipse_x, ellipse_y, pointSize, pointSize+1)

class ScreenUnit():
    def __init__(self,unitInfo,progSheet,colorMode,offset,FontIconMgr):
        self.offset = offset
        self.colorMode = colorMode
        self.position = unitInfo["position"]
        self.pointNum = unitInfo["pointNum"]
        self.pointSize = unitInfo["pointSize"]
        self.scale = unitInfo["scale"]
        self.progSheet = progSheet
        self.tempStr = ""
        self.appearance = self.progSheet["appearance"]
        self.FontIconMgr = FontIconMgr
        self.rollCounter = 0    # 屏幕每绘制一次就加一，可被procTransFunc重新置为零
        self.counter = 0
        self.x = 0
        self.y = 0
        self.x_offset = 0
        self.y_offset = 0
        self.appear = True
        self.showat = 0
        self.space = self.progSheet["spacing"]
        self.rollSpace = -1
        self.color_1 = template_monochromeColors[self.progSheet["color_1"]]
        self.color_RGB = self.progSheet["color_RGB"]
        self.Bitmap = Image.new(self.colorMode,(1,1))
        self.backBitmap = None
        self.BmpCreater = BmpCreater(self.FontIconMgr,self.colorMode,self.progSheet["color_RGB"],self.progSheet["font"],self.progSheet["ascFont"],self.progSheet["sysFontOnly"],)
        self.createFontImg()

        if "x_offset" in self.progSheet.keys():
            self.x_offset = self.progSheet["x_offset"]
        
        if not self.progSheet["vertical"]:
            align = self.progSheet["align"]
        else:
            align = self.progSheet["align"][::-1]
        if align[0] == 0:
            self.x = int(0.5*(self.Bitmap.size[0] - self.pointNum[0]))
            if (self.Bitmap.size[0] - self.pointNum[0]) % 2 == 1:
                self.x -= 1
        if align[1] == 0:
            self.y = int(0.5*(self.Bitmap.size[1]-self.pointNum[1]))
        if align[0] < 0:
            self.x = self.Bitmap.size[0] - self.pointNum[0]
        if align[1] < 0:
            self.y = self.Bitmap.size[1] - self.pointNum[1]
        if align[0] > 0:
            self.x = 0
        if align[1] > 0:
            self.y = 0

        if "y_offset_global" in self.progSheet.keys():
            self.y_offset = self.progSheet["y_offset_global"]

        self.x += self.x_offset
        self.y += self.y_offset

        if "滚动" in self.appearance:
            self.rollSpace = self.progSheet["argv_2"]
            if ("左" in self.appearance or "右"  in self.appearance):
                self.x = -self.pointNum[0]
            elif ("上" in self.appearance or "下"  in self.appearance):
                self.y = -self.pointNum[1]

        if "移到中间" in self.appearance:
            if "左" in self.appearance:
                self.x = -self.pointNum[0]
            elif "右"  in self.appearance:
                self.x = self.Bitmap.size[0]
            elif "上" in self.appearance:
                self.y = -self.pointNum[1]
            elif "下"  in self.appearance:
                self.y = self.Bitmap.size[1]

    def createFontImg(self):
        _roll_asc = True
        if "rollAscii" in self.progSheet.keys():
            _roll_asc = self.progSheet["rollAscii"]
        if "multiLine" in self.progSheet.keys() and "lineSpace" in self.progSheet.keys():
            self.Bitmap = self.BmpCreater.create_character(vertical=self.progSheet["vertical"], roll_asc = _roll_asc, text=self.progSheet["text"], ch_font_size=self.progSheet["fontSize"], asc_font_size=self.progSheet["ascFontSize"], ch_bold_size_x=self.progSheet["bold"][0], ch_bold_size_y=self.progSheet["bold"][1], space=self.progSheet["spacing"], scale=self.progSheet["scale"], auto_scale=self.progSheet["autoScale"], scale_sys_font_only=self.progSheet["scaleSysFontOnly"], new_width = self.pointNum[0], new_height = self.pointNum[1], y_offset = self.progSheet["y_offset"], y_offset_asc = self.progSheet["y_offset_asc"], style = self.progSheet["align"], multi_line={"stat":self.progSheet["multiLine"], "line_space": self.progSheet["lineSpace"] })
        else:
            self.Bitmap = self.BmpCreater.create_character(vertical=self.progSheet["vertical"], roll_asc = _roll_asc, text=self.progSheet["text"], ch_font_size=self.progSheet["fontSize"], asc_font_size=self.progSheet["fontSize"], ch_bold_size_x=self.progSheet["bold"][0], ch_bold_size_y=self.progSheet["bold"][1], space=self.progSheet["spacing"], scale=self.progSheet["scale"], auto_scale=self.progSheet["autoScale"], scale_sys_font_only=self.progSheet["scaleSysFontOnly"], new_width = self.pointNum[0], new_height = self.pointNum[1], y_offset = self.progSheet["y_offset"], y_offset_asc = self.progSheet["y_offset"], style = self.progSheet["align"])


if __name__ == '__main__':
    screenInfomation = {
        "flushRate":54,
        "screenInfo":{
            "colorMode":"1",    # "RGB","1"
            "screenSize":[128,16,(6,6)],
        },
        "screenProgramSheet":undefinedProgramSheet
    }
    screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["pointNum"] = screenInfomation['screenInfo']['screenSize'][:2]
    screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["scale"] = screenInfomation['screenInfo']['screenSize'][2]
    # screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["pointSize"] = int(screenInfomation['screenInfo']['screenSize'][2][0]*0.8) #应该有误，不需要这行代码
    app = QApplication(sys.argv)
    ex = ScreenController(flushRate=screenInfomation["flushRate"],screenInfo=screenInfomation["screenInfo"],screenProgramSheet=[],FontIconMgr=FontManager(),toDisplay="frontScreen")
    sys.exit(app.exec_())

