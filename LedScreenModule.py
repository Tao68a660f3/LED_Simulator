import sys, time, datetime, os, imageio, random, re, copy
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction
from PyQt5.QtGui import QPainter, QColor, QImage
from PyQt5.QtCore import QTimer, Qt, QThread, QRunnable, QThreadPool, pyqtSignal, QMutex, QWaitCondition, QObject
from PIL import Image
from ScreenInfo import *
from LineInfo import *
from BmpCreater import *

undefinedProgramSheet = [['测试信息', 900, {'frontScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'backScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'frontSideScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]],'backSideScreen': [[{'position': [0, 0], 'pointNum': [80, 24], 'pointSize': 4, 'scale': (6, 6)}], [{'font': '宋体', 'fontSize': 16, 'ascFont': 'ASCII_8-16', 'sysFontOnly': False, 'appearance': '向左滚动', 'vertical': False, 'argv_1': 1, 'argv_2': -1, 'spacing': 0, 'bold': [1, 1], 'y_offset': 0, 'align': [0, 0], 'scale': 100, 'autoScale': False, 'scaleSysFontOnly': False, 'text': r'欢迎使用LED模拟器 created by: Tao68a660f3 今天是 %Y年%m月%d日 %A 时间 %H时%M分', 'color_1': 'white', 'color_RGB': [255, 255, 0], 'bitmap': None}]]}]]

sector_area_eft = ["向右扇形圆形","向左扇形圆形","向下扇形圆形","向上扇形圆形"]
hwindow_area_eft = ["向左开百叶窗","向右开百叶窗","向上开百叶窗","向下开百叶窗","向左关百叶窗","向右关百叶窗","向上关百叶窗","向下关百叶窗"]
window_area_eft = ["开水平窗户","关水平窗户","开竖直窗户","关竖直窗户"]

GIF_TEMP_DIR = "./ScreenShots/temp"
GIF_OUTPUT_DIR = "./ScreenShots"

class SaveGifTask(QRunnable):
    def __init__(self, parent, frames, tmpGifNames, toDisplay, gifFps, temp, 
                 temp_dir=GIF_TEMP_DIR, 
                 output_dir=GIF_OUTPUT_DIR):
        super().__init__()
        self.parent = parent
        self.frames = frames.copy() if frames else []
        self.tmpGifNames = tmpGifNames
        self.toDisplay = toDisplay
        self.gifFps = gifFps
        self.temp = temp
        self.temp_dir = temp_dir  # 临时文件目录
        self.output_dir = output_dir  # 最终输出目录
        
        # 确保目录存在
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def _wait_for_file_ready(self, file_path, max_retries=10, delay=0.5):
        """等待文件就绪（存在且未被占用）"""
        retries = 0
        while retries < max_retries:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                time.sleep(delay)
                retries += 1
                continue
            
            # 检查文件是否可读
            try:
                with open(file_path, 'rb') as f:
                    # 尝试读取文件头
                    header = f.read(6)
                    # 检查是否是GIF文件头
                    if header in (b'GIF87a', b'GIF89a'):
                        return True
            except (IOError, OSError):
                # 文件可能被占用，等待后重试
                pass
            
            time.sleep(delay)
            retries += 1
        
        return False

    def _sort_files_by_timestamp(self, file_paths):
        """根据文件名中的时间戳对文件进行排序"""
        # 提取文件名中的时间戳部分
        def extract_timestamp(path):
            filename = os.path.basename(path)
            # 文件名格式: temp_{display}_YYYYmmddHHMMSS_ffffff.gif
            parts = filename.split('_')
            if len(parts) >= 3:
                # 组合日期和时间部分: YYYYmmddHHMMSS_ffffff
                return parts[2] + '_' + parts[3].split('.')[0]
            return filename  # 如果格式不符合预期，返回原始文件名
        
        # 按时间戳排序
        return sorted(file_paths, key=extract_timestamp)

    def run(self):
        try:
            # 保存未完成的帧（无论 temp 是 True 还是 False）
            if self.frames:
                # 生成唯一文件名（使用毫秒避免重复）
                temp_file = datetime.datetime.now().strftime(
                    f"temp_{self.toDisplay}_%Y%m%d%H%M%S_%f.gif"  # 添加毫秒避免重复
                )
                temp_path = os.path.join(self.temp_dir, temp_file)
                
                # 第一时刻记录临时文件路径
                self.tmpGifNames.append(temp_path)
                print(f"temped: {temp_file}")
                
                # 然后保存文件
                self.frames[0].save(
                    temp_path,
                    save_all=True,
                    append_images=self.frames[1:],
                    optimize=False,
                    duration=100,
                    loop=0,
                    disposal=2
                )
                
                self.frames = []  # 清空帧数据

            # 如果 temp=False，合并临时文件
            if not self.temp:
                # 去重处理：确保只处理唯一的文件
                unique_files = list(set(self.tmpGifNames))
                
                # 按时间戳排序文件
                sorted_files = self._sort_files_by_timestamp(unique_files)
                
                # 使用第一个临时文件的时间戳作为输出文件名基础
                if sorted_files:
                    base_name = os.path.basename(sorted_files[0])
                    # 提取时间戳部分: temp_{display}_YYYYmmddHHMMSS_ffffff.gif
                    parts = base_name.split('_')
                    if len(parts) >= 4:
                        # 组合日期和时间部分（到秒）
                        time_str = parts[2]  # 秒级时间戳
                    else:
                        time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                else:
                    time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                
                output_file = f"{self.toDisplay}_{time_str}_output.gif"
                output_path = os.path.join(self.output_dir, output_file)
                
                # 等待所有临时文件就绪
                all_ready = True
                print("Wait for all temped gif file ready...")
                for gif_path in sorted_files:
                    if not self._wait_for_file_ready(gif_path):
                        print(f"Timeout waiting for file: {gif_path}")
                        all_ready = False
                
                if all_ready:
                    print("All temped gif file are ready!")
                else:
                    raise Exception("Some temporary files are not ready for merging")
                
                # 合并所有临时文件
                print("Registered gif files (sorted):")
                for g in sorted_files:
                    print(g)
                
                combined_gif = imageio.get_writer(output_path, fps=self.gifFps, loop=0)
                for gif_path in sorted_files:
                    try:
                        with imageio.get_reader(gif_path) as gif_reader:
                            for frame in gif_reader:
                                combined_gif.append_data(frame)
                    except Exception as e:
                        print(f"Error reading temporary file {gif_path}: {e}")
                combined_gif.close()
                print(f"Success! {output_file}")

                # 清理临时文件
                print("Delete temped gif files...")
                for gif_path in sorted_files:
                    try:
                        if os.path.exists(gif_path):
                            os.remove(gif_path)
                        else:
                            print(f"File not found, skipping delete: {gif_path}")
                    except Exception as e:
                        print(f"Error deleting temporary file {gif_path}: {e}")
                
                # 清空原始列表（包含所有实例，包括可能的重复）
                self.tmpGifNames.clear()
                print("Done!")
                
        except Exception as e:
            print("Error in save_gif thread:", e)
            import traceback
            traceback.print_exc()

class Thread_BmpUpdater(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self._is_running = True

    def run(self):
        while True:
            self._mutex.lock()
            if not self._is_running:
                self._mutex.unlock()
                break
                
            # 替换time.sleep为Qt的等待机制
            if not self._condition.wait(self._mutex, 200):  # 200ms
                # 超时后执行任务
                if self.parent():
                    self.parent().checkTimeStr()
            self._mutex.unlock()

    def stop(self):
        self._mutex.lock()
        self._is_running = False
        self._condition.wakeAll()
        self._mutex.unlock()
        self.wait(1000)  # 等待最多1秒

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
        self.fpsCount_EN = 0
        self.fpsChkSecCalcNum = 2
        self.fpsCounter = 0
        self.commonFps = flushRate
        self.expectedFps = flushRate
        self.owingFps = 0
        self.gifFps = flushRate
        self.flushRate = 1000 // flushRate
        self.units = []
        self.old_units = []
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
        self.timer3.start(1000//self.fpsChkSecCalcNum)

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
        # 1. 停止定时器
        self.timer1.stop()
        self.timer2.stop()
        self.timer3.stop()
        
        # 2. 停止并删除线程
        self.stopThread_BmpUpdater()
        
        # 3. 断开所有信号
        self.disconnect_all_signals()
        
        # 4. 释放图像资源
        self.release_image_resources()
        
        # 5. 调用父类方法
        super().closeEvent(event)
        
        # 6. 强制删除
        self.deleteLater()
        
        # 7. 垃圾回收
        import gc
        gc.collect()

    def disconnect_all_signals(self):
        # 断开所有信号连接
        for child in self.findChildren(QObject):
            try:
                child.blockSignals(True)
                child.disconnect()
            except:
                pass

    def release_image_resources(self):
        # 释放PIL图像资源
        if hasattr(self, 'BackImg'):
            self.BackImg.close()
            del self.BackImg
        
        # 释放单元中的图像
        for unit in getattr(self, 'units', []):
            if hasattr(unit, 'Bitmap'):
                unit.Bitmap.close()
        self.units.clear()

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
        QTimer.singleShot(self.flushRate*2, self.start_recording_gif)

    def stop_recording_gif(self):
        self.gifRecording = False
        self.save_gif()

    def p_stop_recording_gif(self):
        self.progStopGif = True

    def save_gif(self, temp=False):
        task = SaveGifTask(
            parent=self,
            frames=self.gifFrames,
            tmpGifNames=self.tmpGifNames,
            toDisplay=self.toDisplay,
            gifFps=self.gifFps,
            temp=temp
        )
        self.gifFrames = []  # 清空帧（仅 temp=True 时需要）
        QThreadPool.globalInstance().start(task)

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
                oldStr = s.originalStr
                chWeekday = now.strftime("%A")
                newStr = re.sub(r"(?<!%)(%A)", chinese_week_day[chWeekday], oldStr )
                newStr = now.strftime(newStr)
                s.strftimedStr = newStr

                if s.strftimedStr != s.originalStr or s.strftimedStr != s.bmpSaysStr:
                    s.createFontImg()

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
        try:
            for s in self.Parent.LedScreens.values():
                t = s.currentScreenProgSet["trigger"]
                if isinstance(t,list) and len(t) > 0 and s is not self:
                    n_t += 1
                    # print(s,"+1")
        except Exception as e:
            print("everyscreen_hastrigger: ",e)
            
        return n_t
    
    def compare_ordered(self, list1, list2):
        # 比较两个列表是否完全相同（考虑顺序）
        if len(list1) != len(list2):
            return False
        
        def make_hashable(d):
            # 将字典转换为可哈希形式
            return tuple(sorted((k, tuple(v) if isinstance(v, list) else v) 
                            for k, v in d.items()))
        
        for i in range(len(list1)):
            if make_hashable(list1[i]) != make_hashable(list2[i]):
                return False
        
        return True
    
    def compare_dicts_ignore_keys(self, dict1, dict2, ignore_keys):
        """
        比较两个字典，忽略指定的键
        
        Args:
            dict1: 第一个字典
            dict2: 第二个字典
            ignore_keys: 要忽略的键（字符串或字符串列表）
        
        Returns:
            bool: 忽略指定键后是否相等
        """
        if isinstance(ignore_keys, str):
            ignore_keys = [ignore_keys]
        
        # 使用字典推导式过滤键
        filtered1 = {k: v for k, v in dict1.items() if k not in ignore_keys}
        filtered2 = {k: v for k, v in dict2.items() if k not in ignore_keys}
        
        return filtered1 == filtered2
    
    def check_two_programs_if_same_layout(self, selected_prog):    # 比较当前节目和目标节目是否相同布局
        now_prog_layout_list = []
        next_prog_layout_list = self.screenProgramSheet[self.currentIndex][2][self.toDisplay][0]
        
        for u in self.units:
            now_prog_layout_list.append(u.get_summary_data()[0])

        return self.compare_ordered(now_prog_layout_list, next_prog_layout_list)
    
    def program_inhert_exec(self, inhertLevel, newUnitAndProgram):
        self.old_units = copy.deepcopy(self.units)
        self.units = []
        if inhertLevel == 0:
            for i in range(min(len(newUnitAndProgram[0]),len(newUnitAndProgram[1]))):
                self.units.append(ScreenUnit(newUnitAndProgram[0][i],newUnitAndProgram[1][i],self.colorMode,self.offset,self.FontIconMgr))
        else:
            old_progsheetList = [u.progSheet for u in self.old_units]
            new_progsheetList = newUnitAndProgram[1]
            i_range = range(min(len(old_progsheetList), len(new_progsheetList)))
            ignore_keys = ["appearance"]

            if inhertLevel == 1:
                for i in i_range:
                    if self.compare_dicts_ignore_keys(old_progsheetList[i], new_progsheetList[i], ignore_keys):
                        a = self.old_units[i]
                        a.appearance = new_progsheetList[i]["appearance"]
                        self.units.append(a)
                    else:
                        self.units.append(ScreenUnit(newUnitAndProgram[0][i],newUnitAndProgram[1][i],self.colorMode,self.offset,self.FontIconMgr))
            if inhertLevel == 2:
                in_is = True
                for i in i_range:
                    if not self.compare_dicts_ignore_keys(old_progsheetList[i], new_progsheetList[i], ignore_keys):
                        in_is = False
                        break
                if in_is:
                    for i in i_range:
                        a = self.old_units[i]
                        a.appearance = new_progsheetList[i]["appearance"]
                        self.units.append(a)
                else:
                    for i in i_range:
                        self.units.append(ScreenUnit(newUnitAndProgram[0][i],newUnitAndProgram[1][i],self.colorMode,self.offset,self.FontIconMgr))

    def programTimeout(self):
        isSameLayout = False
        inhertLevel = 0

        self.disable_fpsCount()

#====================================================================================
#         print("测试：当前节目的上一个节目的相关信息：")
#         for u in self.units:
#             print(u.get_summary_data())
#====================================================================================

        if self.progStopGif:        # 录制GIF直到当前节目结束时，结束录制GIF
            self.progStopGif = False
            if self.gifRecording:
                self.stop_recording_gif()

        isSameLayout = self.check_two_programs_if_same_layout(self.currentIndex)

        self.currentBeginTime = time.time()
        self.runningTime = 0

        if self.isVisible() == True:
            if self.currentIndex in range(len(self.screenProgramSheet)):
                try:
                    self.currentPtime = self.screenProgramSheet[self.currentIndex][1]
                    newUnitAndProgram = self.screenProgramSheet[self.currentIndex][2][self.toDisplay]
                    if len(newUnitAndProgram) == 3:
                        ext_dict = newUnitAndProgram[2]
                        if "ProgScreenSetting" in ext_dict.keys():
                            self.currentScreenProgSet = ext_dict["ProgScreenSetting"]
                        else:
                            self.currentScreenProgSet = None
                    else:
                        self.currentScreenProgSet = None

                    if self.currentScreenProgSet is not None:
                        if "isorigin" in self.currentScreenProgSet.keys():
                            self.cntProgIsOrigin = self.currentScreenProgSet["isorigin"]
                        if "inherit" in self.currentScreenProgSet.keys():
                            inhertLevel = self.currentScreenProgSet["inherit"]
                            if not isSameLayout:
                                inhertLevel = 0

                    self.program_inhert_exec(inhertLevel, newUnitAndProgram)
                    
                    self.backgroundPerformer()

                except Exception as e:
                    print("programTimeout:", e)

        self.checkTimeStr()
        self.enable_fpsCount()

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

    def enable_fpsCount(self):
        self.fpsCount_EN = 1

    def disable_fpsCount(self):
        self.fpsCount_EN = 0

    def count_fps(self):
        if self.fpsCount_EN > 2:
            self.commonFps = (self.commonFps + self.fpsCounter*self.fpsChkSecCalcNum) // 2
            self.gifFps = min(int(self.commonFps*0.7+self.gifFps*0.3),50)
            self.setWindowTitle(f'{self.toDisplay} @ {self.commonFps} FPS')
        elif self.fpsCount_EN >= 1:
            self.fpsCount_EN += 1

        self.fpsCounter = 0

    def get_fps(self):
        fps = str(self.commonFps)
        # fps += f"  {self.toDisplay} GIF_Fps:({self.gifFps})  "
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
            obj.counter = obj.rollCounter // self.expectedFps
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
            if obj.showat <= obj.pointNum[0]:
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
                        if obj.rollCounter <= arg3*self.expectedFps:
                            obj.counter += obj.rollCounter // (arg3*self.expectedFps)
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.x = -obj.pointNum[0]+obj.Bitmap.size[0]
                        if obj.rollCounter > 2*arg3*self.expectedFps:
                            obj.rollCounter = 0
                else:
                    if obj.x+arg2 <= -obj.pointNum[0]+obj.Bitmap.size[0] and obj.rollCounter <= arg1:
                        obj.x = obj.x+arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= arg3*self.expectedFps:
                            obj.counter += obj.rollCounter // (arg3*self.expectedFps)
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.x = 0
                        if obj.rollCounter > 2*arg3*self.expectedFps:
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
                        if obj.rollCounter <= arg3*self.expectedFps:
                            obj.counter += obj.rollCounter // (arg3*self.expectedFps)
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.x = 0
                        if obj.rollCounter > 2*arg3*self.expectedFps:
                            obj.rollCounter = 0
                else:
                    if obj.x-arg2 >= 0 and obj.rollCounter <= arg1:
                        obj.x = obj.x-arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= arg3*self.expectedFps:
                            obj.counter += obj.rollCounter // (arg3*self.expectedFps)
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.x = -obj.pointNum[0]+obj.Bitmap.size[0]
                        if obj.rollCounter > 2*arg3*self.expectedFps:
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
                        if obj.rollCounter <= arg3*self.expectedFps:
                            obj.counter += obj.rollCounter // (arg3*self.expectedFps)
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.y = -obj.pointNum[1]+obj.Bitmap.size[1]
                        if obj.rollCounter > 2*arg3*self.expectedFps:
                            obj.rollCounter = 0
                else:
                    if obj.y+arg2 <= -obj.pointNum[1]+obj.Bitmap.size[1] and obj.rollCounter <= arg1:
                        obj.y = obj.y+arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= arg3*self.expectedFps:
                            obj.counter += obj.rollCounter // (arg3*self.expectedFps)
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.y = 0
                        if obj.rollCounter > 2*arg3*self.expectedFps:
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
                        if obj.rollCounter <= arg3*self.expectedFps:
                            obj.counter += obj.rollCounter // (arg3*self.expectedFps)
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.y = 0
                        if obj.rollCounter > 2*arg3*self.expectedFps:
                            obj.rollCounter = 0
                else:
                    if obj.y-arg2 >= 0 and obj.rollCounter <= arg1:
                        obj.y = obj.y-arg2
                        obj.rollCounter = 0
                    else:
                        if obj.rollCounter <= arg3*self.expectedFps:
                            obj.counter += obj.rollCounter // (arg3*self.expectedFps)
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.y = -obj.pointNum[1]+obj.Bitmap.size[1]
                        if obj.rollCounter > 2*arg3*self.expectedFps:
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
                            if obj.rollCounter > arg3*self.expectedFps:
                                obj.x = obj.x+arg2
                                obj.rollCounter = 0
                    else:
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.x = 0
                            obj.rollCounter = 0
                            obj.counter += 1
                else:
                    obj.counter = obj.rollCounter // self.expectedFps
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
                            if obj.rollCounter > arg3*self.expectedFps:
                                obj.x = obj.x-arg2
                                obj.rollCounter = 0
                    else:
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.x = -obj.pointNum[0]+obj.Bitmap.size[0]
                            obj.rollCounter = 0
                            obj.counter += 1
                else:
                    obj.counter = obj.rollCounter // self.expectedFps
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
                            if obj.rollCounter > arg3*self.expectedFps:
                                obj.y = obj.y+arg2
                                obj.rollCounter = 0
                    else:
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.y = 0
                            obj.rollCounter = 0
                            obj.counter += 1
                else:
                    obj.counter = obj.rollCounter // self.expectedFps
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
                            if obj.rollCounter > arg3*self.expectedFps:
                                obj.y = obj.y-arg2
                                obj.rollCounter = 0
                    else:
                        if obj.rollCounter > arg3*self.expectedFps:
                            obj.y = -obj.pointNum[1]+obj.Bitmap.size[1]
                            obj.rollCounter = 0
                            obj.counter += 1
                else:
                    obj.counter = obj.rollCounter // self.expectedFps
        elif appearance == "上下反复跳跃移动":
            obj.appear = True
            obj.x = pos0
            if obj.rollCounter < arg1:
                pass
            else:
                if obj.pointNum[1] > obj.Bitmap.size[1]:
                    if (obj.counter+1) % 2:
                        if obj.y+arg2 >= 0 and obj.rollCounter >= arg3*self.expectedFps:
                            obj.counter += 1
                        if obj.y+arg2 <= 0:
                            obj.y = obj.y+arg2
                            obj.rollCounter = 0
                    else:
                        if obj.y-arg2 <= -obj.pointNum[1]+obj.Bitmap.size[1] and obj.rollCounter >= arg3*self.expectedFps:
                            obj.counter += 1
                        if obj.y-arg2 >= -obj.pointNum[1]+obj.Bitmap.size[1]:
                            obj.y = obj.y-arg2
                            obj.rollCounter = 0
                else:
                    if (obj.counter+1) % 2:
                        if obj.y+arg2 >= -obj.pointNum[1]+obj.Bitmap.size[1] and obj.rollCounter >= arg3*self.expectedFps:
                            obj.counter += 1
                        if obj.y+arg2 <= -obj.pointNum[1]+obj.Bitmap.size[1]:
                            obj.y = obj.y+arg2
                            obj.rollCounter = 0
                    else:
                        if obj.y-arg2 <= 0 and obj.rollCounter >= arg3*self.expectedFps:
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
        self.progSheet = copy.deepcopy(progSheet)
        self.originalStr = self.progSheet["text"][:]
        self.strftimedStr = self.originalStr
        self.bmpSaysStr = ""
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

        if "滚动" in self.appearance:
            self.rollSpace = self.progSheet["argv_2"]
            if ("左" in self.appearance or "右"  in self.appearance):
                self.x = -self.pointNum[0]
            elif ("上" in self.appearance or "下"  in self.appearance):
                self.y = -self.pointNum[1]

        self.x += self.x_offset
        self.y += self.y_offset    # 一定要按这个顺序来：先计算滚动，再加偏移，再计算移到中间

        if "移到中间" in self.appearance:
            if "左" in self.appearance:
                self.x = -self.pointNum[0]
            elif "右"  in self.appearance:
                self.x = self.Bitmap.size[0]
            elif "上" in self.appearance:
                self.y = -self.pointNum[1]
            elif "下"  in self.appearance:
                self.y = self.Bitmap.size[1]

    def get_summary_data(self):    # 返回单元的布局信息和programsheet
        return [
            {
                "position":self.position,
                "pointNum":self.pointNum,
                "pointSize":self.pointSize,
                "scale":self.scale,
            },
            self.progSheet
        ]

    def createFontImg(self):
        self.bmpSaysStr = self.strftimedStr
        _roll_asc = True
        if "rollAscii" in self.progSheet.keys():
            _roll_asc = self.progSheet["rollAscii"]
        if "multiLine" in self.progSheet.keys() and "lineSpace" in self.progSheet.keys():
            self.Bitmap = self.BmpCreater.create_character(vertical=self.progSheet["vertical"], roll_asc = _roll_asc, text=self.bmpSaysStr, ch_font_size=self.progSheet["fontSize"], asc_font_size=self.progSheet["ascFontSize"], ch_bold_size_x=self.progSheet["bold"][0], ch_bold_size_y=self.progSheet["bold"][1], space=self.progSheet["spacing"], scale=self.progSheet["scale"], auto_scale=self.progSheet["autoScale"], scale_sys_font_only=self.progSheet["scaleSysFontOnly"], new_width = self.pointNum[0], new_height = self.pointNum[1], y_offset = self.progSheet["y_offset"], y_offset_asc = self.progSheet["y_offset_asc"], style = self.progSheet["align"], multi_line={"stat":self.progSheet["multiLine"], "line_space": self.progSheet["lineSpace"] })
        else:
            self.Bitmap = self.BmpCreater.create_character(vertical=self.progSheet["vertical"], roll_asc = _roll_asc, text=self.bmpSaysStr, ch_font_size=self.progSheet["fontSize"], asc_font_size=self.progSheet["fontSize"], ch_bold_size_x=self.progSheet["bold"][0], ch_bold_size_y=self.progSheet["bold"][1], space=self.progSheet["spacing"], scale=self.progSheet["scale"], auto_scale=self.progSheet["autoScale"], scale_sys_font_only=self.progSheet["scaleSysFontOnly"], new_width = self.pointNum[0], new_height = self.pointNum[1], y_offset = self.progSheet["y_offset"], y_offset_asc = self.progSheet["y_offset"], style = self.progSheet["align"])


if __name__ == '__main__':
    screenInfomation = {
        "flushRate":54,
        "screenInfo":{
            "colorMode":"1",    # "RGB","1"
            "screenSize":[144,16,(6,6)],
        },
        "screenProgramSheet":undefinedProgramSheet
    }
    screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["pointNum"] = screenInfomation['screenInfo']['screenSize'][:2]
    screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["scale"] = screenInfomation['screenInfo']['screenSize'][2]
    screenInfomation["screenProgramSheet"][0][2]["frontScreen"][0][0]["pointSize"] = int(screenInfomation['screenInfo']['screenSize'][2][0]*0.8)
    app = QApplication(sys.argv)
    ex = ScreenController(flushRate=screenInfomation["flushRate"],screenInfo=screenInfomation["screenInfo"],screenProgramSheet=[],FontIconMgr=FontManager(),toDisplay="frontScreen")
    sys.exit(app.exec_())

