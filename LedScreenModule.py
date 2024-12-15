import sys, time, datetime, os, imageio, random, re
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction
from PyQt5.QtGui import QPainter, QColor, QImage
from PyQt5.QtCore import QTimer, Qt
from PIL import Image
from ScreenInfo import *
from LineInfo import *
from BmpCreater import *

undefinedProgramSheet = [['测试信息', 900, {'frontScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'backScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'frontSideScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'backSideScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]]}]]

class ScreenController(QWidget):
    def __init__(self,flushRate,screenInfo,screenProgramSheet,toDisplay,FontIconMgr):
        super().__init__()
        self.window_handle = self.winId()
        self.screen = QApplication.primaryScreen()
        self.offset = 16
        self.flushRate = int(1000/flushRate)
        self.colorMode = screenInfo["colorMode"]
        self.screenSize = [screenInfo["screenSize"][0],screenInfo["screenSize"][1]]
        self.screenScale = screenInfo["screenSize"][2]
        self.screenProgramSheet = screenProgramSheet
        self.toDisplay = toDisplay
        self.FontIconMgr = FontIconMgr
        self.currentIndex = 0
        self.currentPtime = 0
        self.currentBeginTime = 0
        self.runningTime = 0
        self.performFinish = False
        self.gifRecording = False
        # self.endGifFrame = 0
        self.fpsCounter = 0
        self.commonFps = flushRate
        self.units = []
        self.gifFrames = []
        self.tmpGifNames = []

        if len(self.screenProgramSheet) == 0:
            self.screenProgramSheet = undefinedProgramSheet
            for s in {"frontScreen","backScreen","frontSideScreen","backSideScreen"}:
                self.screenProgramSheet[0][2][s][0][0]["pointNum"] = self.screenSize
                self.screenProgramSheet[0][2][s][0][0]["scale"] = self.screenScale
                self.screenProgramSheet[0][2][s][0][0]["pointSize"] = int(self.screenScale[0]*0.8)

        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.update)
        self.timer1.start(self.flushRate)
        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.checkProgramTimeout)
        self.timer2.start(200)
        self.timer3 = QTimer(self)
        self.timer3.timeout.connect(self.checkTimeStr)
        self.timer3.start(1000)


        self.setWindowTitle(self.toDisplay)
        self.setWindowFlags(Qt.FramelessWindowHint) # 隐藏边框
        self.show()
        self.programTimeout()
        self.checkProgramTimeout()

        self.setContextMenuPolicy(Qt.CustomContextMenu) # 右键菜单
        self.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, pos):
        contextMenu = QMenu(self)
        newAction = QAction('关闭窗口', self)
        newAction.triggered.connect(self.close)
        contextMenu.addAction(newAction)
        newAction = QAction('窗口置顶', self)
        newAction.triggered.connect(self.top_most)
        contextMenu.addAction(newAction)
        newAction = QAction('屏幕截图', self)
        newAction.triggered.connect(self.screen_shot)
        contextMenu.addAction(newAction)
        if not self.gifRecording:
            newAction = QAction('开始录制GIF', self)
            newAction.triggered.connect(self.start_recording_gif)
            contextMenu.addAction(newAction)
        else:
            newAction = QAction('结束录制GIF', self)
            newAction.triggered.connect(self.stop_recording_gif)
            contextMenu.addAction(newAction)
            newAction = QAction('结束请耐心等待(^_^)', self)
            newAction.triggered.connect(self.stop_recording_gif)
            contextMenu.addAction(newAction)

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

    def stop_recording_gif(self):
        self.gifRecording = False
        self.save_gif()

    def save_gif(self, temp = False):
        if temp:
            try:
                fileName = datetime.datetime.now().strftime(f"temp_{self.toDisplay}_%Y%m%d%H%M%S.gif")
                self.gifFrames[0].save(os.path.join("./ScreenShots",fileName), save_all=True, append_images=self.gifFrames[1:], optimize=False, duration=0.1, loop=0)
                self.gifFrames = []
                self.tmpGifNames.append(fileName)
            except Exception as e:
                print(e)
        else:
            self.save_gif(True)
            fileName = datetime.datetime.now().strftime(f"{self.toDisplay}_%Y%m%d%H%M%S_output.gif")
            combined_gif = imageio.get_writer(os.path.join("./ScreenShots",fileName), fps = self.commonFps, loop = 0)
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
                newStr = now.strftime(newStr)
                if newStr != s.tempStr:
                    s.progSheet["text"] = newStr
                    s.tempStr = newStr
                    s.createFontImg()
                    s.progSheet["text"] = oldStr
        except Exception as e:
            print(e)
        
    def checkProgramTimeout(self):
        try:
            self.runningTime = time.time() - self.currentBeginTime
            if self.runningTime >= self.currentPtime and self.currentPtime >= 0:
                self.programTimeout()
            index = self.currentIndex-1 if self.currentIndex>0 else len(self.screenProgramSheet)-1
            if 3 in range(len(self.screenProgramSheet[index])) or self.currentPtime < 0:
                num = []
                for u in self.units:
                    num.append(u.counter)
                if self.currentPtime < 0 and max(num) >= 1:
                    self.programTimeout()
                if max(num) >= self.screenProgramSheet[index][3] and self.currentPtime >= 0:
                    self.programTimeout()
        except Exception as e:
            print(e)

    def programTimeout(self):
        self.currentBeginTime = time.time()
        self.runningTime = 0
        if self.isVisible() == True:
            if self.currentIndex in range(len(self.screenProgramSheet)):
                try:
                    self.currentPtime = self.screenProgramSheet[self.currentIndex][1]
                    unitAndProgram = self.screenProgramSheet[self.currentIndex][2][self.toDisplay]
                    self.units = []
                    for i in range(min(len(unitAndProgram[0]),len(unitAndProgram[1]))):
                        self.units.append(ScreenUnit(unitAndProgram[0][i],unitAndProgram[1][i],self.colorMode,self.offset,self.FontIconMgr))
                except Exception as e:
                    print(e)
            if self.currentIndex+1 <= len(self.screenProgramSheet)-1:
                self.currentIndex += 1
            else:
                self.currentIndex = 0
                self.performFinish = True
        self.checkTimeStr()

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
        for u in self.units:
            self.posTransFunc(u)
            u.rollCounter += 1

    def get_fps(self):
        fps = self.fpsCounter
        self.commonFps = int(0.5*(self.commonFps+fps))
        self.fpsCounter = 0
        fps = str(fps)
        if self.gifRecording:
            fps += f"  {self.toDisplay} 正在录制GIF  "
        self.setWindowTitle(f'{self.toDisplay} @ {fps} FPS')
        return fps

    def posTransFunc(self,obj):
        appearance = obj.appearance

        arg1,arg2 = obj.progSheet["argv_1"],obj.progSheet["argv_2"]
        try:
            arg3 = obj.progSheet["argv_3"]
        except:
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
        
        if appearance == "静止":
            obj.appear = True
            obj.x = pos0 + obj.x_offset
        elif appearance == "闪烁":
            obj.x = pos0 + obj.x_offset
            if obj.rollCounter <= arg1+1:
                obj.appear = True
            elif obj.rollCounter <= arg1+arg2+1:
                obj.appear = False
            else:
                obj.rollCounter = 1
                obj.counter += 1
        elif appearance == "向左滚动":
            obj.appear = True
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
        elif appearance == "向左移到中间":
            obj.appear = True
            if obj.rollCounter == 0:
                obj.x = -obj.pointNum[0]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                obj.x = obj.x+arg3 if obj.x < pos0 else obj.x
        elif appearance == "向上移到中间":
            obj.appear = True
            obj.x = pos0 + obj.x_offset
            if obj.rollCounter == 0:
                obj.y = -obj.pointNum[1]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                obj.y = obj.y+arg3 if obj.y < y0 else obj.y
        elif appearance == "中间向左移开":
            obj.appear = True
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.x >= obj.Bitmap.size[0]:
                        obj.counter += 1
                    obj.x = obj.x+arg3 if obj.x < obj.Bitmap.size[0] else obj.x
        elif appearance == "中间向上移开":
            obj.appear = True
            obj.x = pos0 + obj.x_offset
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.y >= obj.Bitmap.size[1]:
                        obj.counter += 1
                    obj.y = obj.y+arg3 if obj.y < obj.Bitmap.size[1] else obj.y
        elif appearance == "跳跃向左移动":
            obj.appear = True
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[0] > obj.Bitmap.size[0]:
                    if obj.x+arg2 > 0:
                        obj.counter += 1
                    if obj.x+arg2 <= 0 and obj.rollCounter <= arg1:
                        obj.x = obj.x+arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            return
                        obj.x = -obj.pointNum[0]+obj.Bitmap.size[0]
                        if obj.rollCounter <= 2*int(arg3*1000/self.flushRate):
                            return
                        obj.rollCounter = 0
                else:
                    if obj.x+arg2 > -obj.pointNum[0]+obj.Bitmap.size[0]:
                        obj.counter += 1
                    if obj.x+arg2 <= -obj.pointNum[0]+obj.Bitmap.size[0] and obj.rollCounter <= arg1:
                        obj.x = obj.x+arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            return
                        obj.x = 0
                        if obj.rollCounter <= 2*int(arg3*1000/self.flushRate):
                            return
                        obj.rollCounter = 0
        elif appearance == "跳跃向上移动":
            obj.appear = True
            obj.x = pos0 + obj.x_offset
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[1] > obj.Bitmap.size[1]:
                    if obj.y+arg2 > 0:
                        obj.counter += 1
                    if obj.y+arg2 <= 0 and obj.rollCounter <= arg1:
                        obj.y = obj.y+arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            return
                        obj.y = -obj.pointNum[1]+obj.Bitmap.size[1]
                        if obj.rollCounter <= 2*int(arg3*1000/self.flushRate):
                            return
                        obj.rollCounter = 0
                else:
                    if obj.y+arg2 > -obj.pointNum[1]+obj.Bitmap.size[1]:
                        obj.counter += 1
                    if obj.y+arg2 <= -obj.pointNum[1]+obj.Bitmap.size[1] and obj.rollCounter <= arg1:
                        obj.y = obj.y+arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            return
                        obj.y = 0
                        if obj.rollCounter <= 2*int(arg3*1000/self.flushRate):
                            return
                        obj.rollCounter = 0
        elif appearance == "向右滚动":
            obj.appear = True
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
        elif appearance == "向右移到中间":
            obj.appear = True
            if obj.rollCounter == 0:
                obj.x = obj.Bitmap.size[0]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                obj.x = obj.x-arg3 if obj.x > pos0 else obj.x
        elif appearance == "向下移到中间":
            obj.appear = True
            obj.x = pos0 + obj.x_offset
            if obj.rollCounter == 0:
                obj.y = obj.Bitmap.size[1]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                obj.y = obj.y-arg3 if obj.y > y0 else obj.y
        elif appearance == "中间向右移开":
            obj.appear = True
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.x <= -obj.pointNum[0]:
                        obj.counter += 1
                    obj.x = obj.x-arg3 if obj.x > -obj.pointNum[0] else obj.x
        elif appearance == "中间向下移开":
            obj.appear = True
            obj.x = pos0 + obj.x_offset
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.y <= -obj.pointNum[1]:
                        obj.counter += 1
                    obj.y = obj.y-arg3 if obj.y > -obj.pointNum[1] else obj.y
        elif appearance == "跳跃向右移动":
            obj.appear = True
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[0] > obj.Bitmap.size[0]:
                    if obj.x-arg2 < -obj.pointNum[0]+obj.Bitmap.size[0]:
                        obj.counter += 1
                    if obj.x-arg2 >= -obj.pointNum[0]+obj.Bitmap.size[0] and obj.rollCounter <= arg1:
                        obj.x = obj.x-arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            return
                        obj.x = 0
                        if obj.rollCounter <= 2*int(arg3*1000/self.flushRate):
                            return
                        obj.rollCounter = 0
                else:
                    if obj.x-arg2 < 0:
                        obj.counter += 1
                    if obj.x-arg2 >= 0 and obj.rollCounter <= arg1:
                        obj.x = obj.x-arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            return
                        obj.x = -obj.pointNum[0]+obj.Bitmap.size[0]
                        if obj.rollCounter <= 2*int(arg3*1000/self.flushRate):
                            return
                        obj.rollCounter = 0
        elif appearance == "跳跃向下移动":
            obj.appear = True
            obj.x = pos0 + obj.x_offset
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[1] > obj.Bitmap.size[1]:
                    if obj.y-arg2 < -obj.pointNum[1]+obj.Bitmap.size[1]:
                        obj.counter += 1
                    if obj.y-arg2 >= -obj.pointNum[1]+obj.Bitmap.size[1] and obj.rollCounter <= arg1:
                        obj.y = obj.y-arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            return
                        obj.y = 0
                        if obj.rollCounter <= 2*int(arg3*1000/self.flushRate):
                            return
                        obj.rollCounter = 0
                else:
                    if obj.y-arg2 < 0:
                        obj.counter += 1
                    if obj.y-arg2 >= 0 and obj.rollCounter <= arg1:
                        obj.y = obj.y-arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= int(arg3*1000/self.flushRate):
                            return
                        obj.y = -obj.pointNum[1]+obj.Bitmap.size[1]
                        if obj.rollCounter <= 2*int(arg3*1000/self.flushRate):
                            return
                        obj.rollCounter = 0
        elif appearance == "上下反复跳跃移动":
            obj.appear = True
            obj.x = pos0 + obj.x_offset
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
                            return
                    else:
                        if obj.y-arg2 <= -obj.pointNum[1]+obj.Bitmap.size[1] and obj.rollCounter >= int(arg3*1000/self.flushRate):
                            obj.counter += 1
                        if obj.y-arg2 >= -obj.pointNum[1]+obj.Bitmap.size[1]:
                            obj.y = obj.y-arg2
                            obj.rollCounter = 0
                        else:
                            return
                else:
                    if (obj.counter+1) % 2:
                        if obj.y+arg2 >= -obj.pointNum[1]+obj.Bitmap.size[1] and obj.rollCounter >= int(arg3*1000/self.flushRate):
                            obj.counter += 1
                        if obj.y+arg2 <= -obj.pointNum[1]+obj.Bitmap.size[1]:
                            obj.y = obj.y+arg2
                            obj.rollCounter = 0
                        else:
                            return
                    else:
                        if obj.y-arg2 <= 0 and obj.rollCounter >= int(arg3*1000/self.flushRate):
                            obj.counter += 1
                        if obj.y-arg2 >= 0:
                            obj.y = obj.y-arg2
                            obj.rollCounter = 0
                        else:
                            return

    def drawBackground(self,qp):
        qp.setBrush(QColor(25,25,25))
        qp.drawRect(0,0,2*self.offset+self.screenSize[0]*self.screenScale[0],2*self.offset+self.screenSize[1]*self.screenScale[1])
        qp.setBrush(QColor(30,30,30))
        qp.drawRect(self.offset,self.offset,self.screenSize[0]*self.screenScale[0],self.screenSize[1]*self.screenScale[1])
        qp.setBrush(QColor(random.randint(30,200),random.randint(30,200),random.randint(30,200)))
        qp.drawRect(int(0.8*(2*self.offset+self.screenSize[0]*self.screenScale[0])),(2*self.offset+self.screenSize[1]*self.screenScale[1])-int(0.5*self.offset),4,4)
        qp.setBrush(QColor(random.randint(30,200),random.randint(30,200),random.randint(30,200)))
        qp.drawRect(int(0.8*(2*self.offset+self.screenSize[0]*self.screenScale[0])+10),(2*self.offset+self.screenSize[1]*self.screenScale[1])-int(0.5*self.offset),4,4)
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
                qp.setBrush(baseColor)
                if rollSpace < 0 and x + x_pos in range(bitmapSize[0]) and y + y_pos in range(bitmapSize[1]) and appear:
                    color = unit.Bitmap.getpixel((x + x_pos, y + y_pos))
                elif rollSpace >= 0 and ("左" in unit.appearance or "右"  in unit.appearance) and (x + x_pos) % (bitmapSize[0] + rollSpace) in range(bitmapSize[0]) and y + y_pos in range(bitmapSize[1]) and appear:
                    color = unit.Bitmap.getpixel(((x + x_pos) % (bitmapSize[0] + rollSpace), y + y_pos))
                elif rollSpace >= 0 and ("上" in unit.appearance or "下"  in unit.appearance) and (y + y_pos) % (bitmapSize[1] + rollSpace) in range(bitmapSize[1]) and x + x_pos in range(bitmapSize[0]) and appear:
                    color = unit.Bitmap.getpixel((x + x_pos, (y + y_pos) % (bitmapSize[1] + rollSpace)))
                else:
                    color = [0, 0, 0] if colorMode == "RGB" else 0
                if colorMode == "RGB" and color != [0,0,0]:
                    color = [black + int((255 - black) * c / 255) for c in color]
                    qp.setBrush(QColor(*color))
                elif colorMode == "1" and color != 0:
                    qp.setBrush(QColor(*unit.color_1[1]))
                ellipse_x = offset + position[0] + x * scale[0] + int(0.5 * (scale[0] - pointSize))
                ellipse_y = offset + position[1] + y * scale[1] + int(0.5 * (scale[1] - pointSize))
                qp.drawEllipse(ellipse_x, ellipse_y, pointSize, pointSize)

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
        self.rollCounter = 0
        self.counter = 0
        self.x = 0
        self.y = 0
        self.x_offset = 0
        self.appear = True
        self.space = self.progSheet["spacing"]
        self.rollSpace = -1
        self.color_1 = template_monochromeColors[self.progSheet["color_1"]]
        self.color_RGB = self.progSheet["color_RGB"]
        self.Bitmap = Image.new(self.colorMode,(1,1))
        self.BmpCreater = BmpCreater(self.FontIconMgr,self.colorMode,self.progSheet["color_RGB"],self.progSheet["font"],self.progSheet["ascFont"],self.progSheet["sysFontOnly"],)
        self.createFontImg()

        try:
            self.x_offset = self.progSheet["x_offset"]
        except:
            pass
            # print("旧版程序不可设置出现位置")
        
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

        if "滚动" in self.progSheet["appearance"]:
            self.rollSpace = self.progSheet["argv_2"]
            if ("左" in self.appearance or "右"  in self.appearance):
                self.x = -self.pointNum[0]
            elif ("上" in self.appearance or "下"  in self.appearance):
                self.y = -self.pointNum[1]

        if "滚" in self.progSheet["appearance"] or "移" in self.progSheet["appearance"] or "跳" in self.progSheet["appearance"]:
            if ("左" in self.appearance or "右"  in self.appearance):
                self.x += self.x_offset
            elif ("上" in self.appearance or "下"  in self.appearance):
                self.y += self.x_offset

    def createFontImg(self):
        try:
            self.Bitmap = self.BmpCreater.create_character(vertical=self.progSheet["vertical"], roll_asc = self.progSheet["rollAscii"], text=self.progSheet["text"], ch_font_size=self.progSheet["fontSize"], asc_font_size=self.progSheet["ascFontSize"], ch_bold_size_x=self.progSheet["bold"][0], ch_bold_size_y=self.progSheet["bold"][1], space=self.progSheet["spacing"], scale=self.progSheet["scale"], auto_scale=self.progSheet["autoScale"], scale_sys_font_only=self.progSheet["scaleSysFontOnly"], new_width = self.pointNum[0], new_height = self.pointNum[1], y_offset = self.progSheet["y_offset"], y_offset_asc = self.progSheet["y_offset_asc"], style = self.progSheet["align"][1])
        except:
            # print("旧版节目单")
            self.Bitmap = self.BmpCreater.create_character(vertical=self.progSheet["vertical"], roll_asc = True, text=self.progSheet["text"], ch_font_size=self.progSheet["fontSize"], asc_font_size=self.progSheet["fontSize"], ch_bold_size_x=self.progSheet["bold"][0], ch_bold_size_y=self.progSheet["bold"][1], space=self.progSheet["spacing"], scale=self.progSheet["scale"], auto_scale=self.progSheet["autoScale"], scale_sys_font_only=self.progSheet["scaleSysFontOnly"], new_width = self.pointNum[0], new_height = self.pointNum[1], y_offset = self.progSheet["y_offset"], y_offset_asc = self.progSheet["y_offset"], style = self.progSheet["align"][1])


if __name__ == '__main__':
    screenInfomation = {
        "flushRate":54,
        "screenInfo":{
            "colorMode":"1",    # "RGB","1"
            "screenSize":[224,32,(6,6)],
        },
        "screenProgramSheet":undefinedProgramSheet
    }
    screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["pointNum"] = screenInfomation['screenInfo']['screenSize'][:2]
    screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["scale"] = screenInfomation['screenInfo']['screenSize'][2]
    screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["pointSize"] = int(screenInfomation['screenInfo']['screenSize'][2][0]*0.8)
    app = QApplication(sys.argv)
    ex = ScreenController(flushRate=screenInfomation["flushRate"],screenInfo=screenInfomation["screenInfo"],screenProgramSheet=[],FontIconMgr=FontManager(),toDisplay="frontScreen")
    sys.exit(app.exec_())

