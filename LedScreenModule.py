﻿import sys, time, datetime
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import QTimer
from PIL import Image
from ScreenInfo import *
from LineInfo import *
from BmpCreater import *

undefinedProgramSheet = [['测试信息', 54, {'frontScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'red', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'backScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'red', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'frontSideScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'red', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'backSideScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'red', 'color_RGB': [255, 255, 0], 'bitmap': None}]]}]]

class ScreenController(QWidget):
    def __init__(self,flushRate,screenInfo,screenProgramSheet,toDisplay,FontIconMgr):
        super().__init__()
        self.offset = 30
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
        self.fpsCounter = 0
        self.units = []

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
        self.timer4 = QTimer(self)
        self.timer4.timeout.connect(self.flushScreen)
        self.timer4.start(self.flushRate)

        self.setWindowTitle(self.toDisplay)
        self.show()
        self.programTimeout()
        self.checkProgramTimeout()

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
                newStr = oldStr.replace("%A",chinese_week_day[chWeekday])
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
            if self.runningTime >= self.currentPtime:
                self.programTimeout()
            index = self.currentIndex-1 if self.currentIndex>0 else len(self.screenProgramSheet)-1
            if 3 in range(len(self.screenProgramSheet[index])):
                num = []
                for u in self.units:
                    num.append(u.counter)
                if max(num) >= self.screenProgramSheet[index][3]:
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
        self.drawBackground(qp)
        for s in self.units:
            self.drawScreen(s,qp)
        qp.end()
        self.fpsCounter += 1

    def flushScreen(self):
        for u in self.units:
            self.posTransFunc(u)
            u.rollCounter += 1

    def get_fps(self):
        fps = self.fpsCounter
        self.fpsCounter = 0
        return fps

    def posTransFunc(self,obj):
        appearance = obj.appearance

        arg1,arg2 = obj.progSheet["argv_1"],obj.progSheet["argv_2"]
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
            obj.x = pos0
        elif appearance == "闪烁":
            obj.x = pos0
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
                    obj.x = obj.x+1 if obj.x < obj.Bitmap.size[0] else -obj.pointNum[0]
                else:
                    if obj.x > obj.Bitmap.size[0]+arg2:
                        obj.counter += 1
                    obj.x = obj.x+1 if obj.x <= obj.Bitmap.size[0]+arg2 else 2
        elif appearance == "向左移到中间":
            obj.appear = True
            if obj.rollCounter == 0:
                obj.x = -obj.pointNum[0]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                obj.x = obj.x+1 if obj.x < pos0 else obj.x
        elif appearance == "向上移到中间":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter == 0:
                obj.y = -obj.pointNum[1]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                obj.y = obj.y+1 if obj.y < y0 else obj.y
        elif appearance == "中间向左移开":
            obj.appear = True
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.x >= obj.Bitmap.size[0]:
                        obj.counter += 1
                    obj.x = obj.x+1 if obj.x < obj.Bitmap.size[0] else obj.x
        elif appearance == "中间向上移开":
            obj.appear = True
            obj.x = pos0
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.y >= obj.Bitmap.size[1]:
                        obj.counter += 1
                    obj.y = obj.y+1 if obj.y < obj.Bitmap.size[1] else obj.y
        elif appearance == "跳跃向左移动":
            obj.appear = True
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if obj.pointNum[0] > obj.Bitmap.size[0]:
                    if obj.x+arg2 > 0:
                        obj.counter += 1
                    obj.x = obj.x+arg2 if obj.x+arg2 <= 0 else -obj.pointNum[0]+obj.Bitmap.size[0]
                else:
                    if obj.x+arg2 > -obj.pointNum[0]+obj.Bitmap.size[0]:
                        obj.counter += 1
                    obj.x = obj.x+arg2 if obj.x+arg2 <= -obj.pointNum[0]+obj.Bitmap.size[0] else 0
        elif appearance == "跳跃向上移动":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if obj.pointNum[1] > obj.Bitmap.size[1]:
                    if obj.y+arg2 > 0:
                        obj.counter += 1
                    obj.y = obj.y+arg2 if obj.y+arg2 <= 0 else -obj.pointNum[1]+obj.Bitmap.size[1]
                else:
                    if obj.y+arg2 > -obj.pointNum[1]+obj.Bitmap.size[1]:
                        obj.counter += 1
                    obj.y = obj.y+arg2 if obj.y+arg2 <= -obj.pointNum[1]+obj.Bitmap.size[1] else 0
        elif appearance == "向右滚动":
            obj.appear = True
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if arg2 < 0:
                    if obj.x <= -obj.pointNum[0]:
                        obj.counter += 1
                    obj.x = obj.x-1 if obj.x > -obj.pointNum[0] else obj.Bitmap.size[0]
                else:
                    if obj.x < 2:
                        obj.counter += 1
                    obj.x = obj.x-1 if obj.x >= 2 else obj.Bitmap.size[0]+arg2
        elif appearance == "向右移到中间":
            obj.appear = True
            if obj.rollCounter == 0:
                obj.x = obj.Bitmap.size[0]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                obj.x = obj.x-1 if obj.x > pos0 else obj.x
        elif appearance == "向下移到中间":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter == 0:
                obj.y = obj.Bitmap.size[1]
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                obj.y = obj.y-1 if obj.y > y0 else obj.y
        elif appearance == "中间向右移开":
            obj.appear = True
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.x <= -obj.pointNum[0]:
                        obj.counter += 1
                    obj.x = obj.x-1 if obj.x > -obj.pointNum[0] else obj.x
        elif appearance == "中间向下移开":
            obj.appear = True
            obj.x = pos0
            if time.time() - self.currentBeginTime > arg2:
                if obj.rollCounter < arg1:
                    pass
                else:
                    obj.rollCounter = 0
                    if obj.y <= -obj.pointNum[1]:
                        obj.counter += 1
                    obj.y = obj.y-1 if obj.y > -obj.pointNum[1] else obj.y
        elif appearance == "跳跃向右移动":
            obj.appear = True
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if obj.pointNum[0] > obj.Bitmap.size[0]:
                    if obj.x-arg2 < -obj.pointNum[0]+obj.Bitmap.size[0]:
                        obj.counter += 1
                    obj.x = obj.x-arg2 if obj.x-arg2 >= -obj.pointNum[0]+obj.Bitmap.size[0] else 0
                else:
                    if obj.x-arg2 < 0:
                        obj.counter += 1
                    obj.x = obj.x-arg2 if obj.x-arg2 >= 0 else -obj.pointNum[0]+obj.Bitmap.size[0]
        elif appearance == "跳跃向下移动":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter < arg1:
                pass
            else:
                obj.rollCounter = 0
                if obj.pointNum[1] > obj.Bitmap.size[1]:
                    if obj.y-arg2 < -obj.pointNum[1]+obj.Bitmap.size[1]:
                        obj.counter += 1
                    obj.y = obj.y-arg2 if obj.y-arg2 >= -obj.pointNum[1]+obj.Bitmap.size[1] else 0
                else:
                    if obj.y-arg2 < 0:
                        obj.counter += 1
                    obj.y = obj.y-arg2 if obj.y-arg2 >= 0 else -obj.pointNum[1]+obj.Bitmap.size[1]

    def drawBackground(self,qp):
        qp.setBrush(QColor(90,90,90))
        qp.drawRect(0,0,2*self.offset+self.screenSize[0]*self.screenScale[0],2*self.offset+self.screenSize[1]*self.screenScale[1])
        qp.setBrush(QColor(30,30,30))
        qp.drawRect(self.offset,self.offset,self.screenSize[0]*self.screenScale[0],self.screenSize[1]*self.screenScale[1])
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
            black = 80
            baseColor = QColor(black, black, black)
        else:
            baseColor = QColor(*unit.color_1[0])
        for y in range(pointNum[1]):
            for x in range(pointNum[0]):
                qp.setBrush(baseColor)
                if rollSpace < 0 and x + x_pos in range(bitmapSize[0]) and y + y_pos in range(bitmapSize[1]) and appear:
                    color = unit.Bitmap.getpixel((x + x_pos, y + y_pos))
                elif rollSpace >= 0 and (x + x_pos) % (bitmapSize[0] + rollSpace) in range(bitmapSize[0]) and y + y_pos in range(bitmapSize[1]) and appear:
                    color = unit.Bitmap.getpixel(((x + x_pos) % (bitmapSize[0] + rollSpace), y + y_pos))
                else:
                    color = [0, 0, 0] if colorMode == "RGB" else 0
                if colorMode == "RGB":
                    color = [black + int((255 - black) * c / 255) for c in color]
                    qp.setBrush(QColor(*color))
                elif colorMode == "1" and color != 0:
                    qp.setBrush(QColor(*unit.color_1[1]))
                ellipse_x = offset + position[0] + x * scale[0] + int(0.5 * (scale[0] - pointSize))
                ellipse_y = offset + position[1] + y * scale[1] + int(0.5 * (scale[1] - pointSize))
                qp.drawEllipse(ellipse_x, ellipse_y, pointSize, pointSize)

    # def drawScreen(self,unit,qp):
    #     if self.isVisible() == True:
    #         for y in range(unit.pointNum[1]):
    #             for x in range(unit.pointNum[0]):
    #                 if self.colorMode == "RGB": 
    #                     black = 80
    #                     qp.setBrush(QColor(black,black,black))
    #                 elif self.colorMode == "1":
    #                     qp.setBrush(QColor(unit.color_1[0][0],unit.color_1[0][1],unit.color_1[0][2]))

    #                 if (unit.rollSpace < 0 and x+unit.x in range(unit.Bitmap.size[0]) and y+unit.y in range(unit.Bitmap.size[1]) and unit.appear):
    #                     color = unit.Bitmap.getpixel((x+unit.x, y+unit.y))
    #                 elif (unit.rollSpace >= 0 and (x+unit.x)%(unit.Bitmap.size[0]+unit.rollSpace) in range(unit.Bitmap.size[0]) and y+unit.y in range(unit.Bitmap.size[1]) and unit.appear):
    #                     color = unit.Bitmap.getpixel(((x+unit.x)%(unit.Bitmap.size[0]+unit.rollSpace), y+unit.y))
    #                 else:
    #                     color = [0,0,0] if self.colorMode == "RGB" else 0
    #                 if self.colorMode == "RGB": 
    #                     black = 80
    #                     color = [black+int((255-black)*color[0]/255),black+int((255-black)*color[1]/255),black+int((255-black)*color[2]/255)]
    #                     qp.setBrush(QColor(color[0],color[1],color[2]))
    #                 elif self.colorMode == "1":
    #                     if color != 0:
    #                         qp.setBrush(QColor(unit.color_1[1][0],unit.color_1[1][1],unit.color_1[1][2]))
    #                     else:
    #                         qp.setBrush(QColor(unit.color_1[0][0],unit.color_1[0][1],unit.color_1[0][2]))

    #                 qp.drawEllipse(unit.offset+unit.position[0]+x*unit.scale[0]+int(0.5*(unit.scale[0]-unit.pointSize)),unit.offset+unit.position[1]+y*unit.scale[1]+int(0.5*(unit.scale[1]-unit.pointSize)),unit.pointSize,unit.pointSize)

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
        self.appear = True
        self.space = self.progSheet["spacing"]
        self.rollSpace = -1
        self.color_1 = template_monochromeColors[self.progSheet["color_1"]]
        self.color_RGB = self.progSheet["color_RGB"]
        self.Bitmap = Image.new(self.colorMode,(1,1))
        self.BmpCreater = BmpCreater(self.FontIconMgr,self.colorMode,self.progSheet["color_RGB"],self.progSheet["font"],self.progSheet["ascFont"],self.progSheet["sysFontOnly"],)
        self.createFontImg()
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
            self.x = -self.pointNum[0]                

    def createFontImg(self):
        self.Bitmap = self.BmpCreater.create_character(vertical=self.progSheet["vertical"], text=self.progSheet["text"], ch_font_size=self.progSheet["fontSize"], ch_bold_size_x=self.progSheet["bold"][0], ch_bold_size_y=self.progSheet["bold"][1], space=self.progSheet["spacing"], scale=self.progSheet["scale"], auto_scale=self.progSheet["autoScale"], scale_sys_font_only=self.progSheet["scaleSysFontOnly"], new_width = self.pointNum[0], new_height = self.pointNum[1], y_offset = self.progSheet["y_offset"], style = self.progSheet["align"][1])


if __name__ == '__main__':
    screenInfomation = {
        "flushRate":54,
        "screenInfo":{
            "colorMode":"RGB",    # "RGB","1"
            "screenSize":[224,32,(3,3)],
        },
        "screenProgramSheet":undefinedProgramSheet
    }
    screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["pointNum"] = screenInfomation['screenInfo']['screenSize'][:2]
    screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["scale"] = screenInfomation['screenInfo']['screenSize'][2]
    screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["pointSize"] = int(screenInfomation['screenInfo']['screenSize'][2][0]*0.8)
    app = QApplication(sys.argv)
    ex = ScreenController(flushRate=screenInfomation["flushRate"],screenInfo=screenInfomation["screenInfo"],screenProgramSheet=[],FontIconMgr=FontManager(),toDisplay="frontScreen")
    sys.exit(app.exec_())
