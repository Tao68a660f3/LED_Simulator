import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
from matplotlib.backend_bases import MouseButton
from tkinter import Tk, filedialog
from tkinter.ttk import Button as TkButton

class PreciseDisplayExtractor:
    def __init__(self):
        # 初始化Tkinter（隐藏主窗口）
        self.root = Tk()
        self.root.withdraw()
        
        # 选择输入目录
        input_dir = filedialog.askdirectory(title="选择照片序列目录")
        if not input_dir:
            print("未选择目录，程序退出")
            exit()
        
        # 选择输出目录
        output_dir = filedialog.askdirectory(title="选择输出目录")
        if not output_dir:
            print("未选择输出目录，程序退出")
            exit()
        
        # 输入显示分辨率
        self.display_resolution = self.ask_resolution()
        
        # 初始化原有变量
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.threshold = 128
        self.corners = []
        self.current_img_idx = 0
        self.img_files = sorted([f for f in os.listdir(input_dir) 
                            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
        
        # 检查目录是否有效
        if not self.img_files:
            print("输入目录中没有找到支持的图片文件")
            exit()
        
        # 创建输出目录
        os.makedirs(os.path.join(output_dir, "sampled"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "binary"), exist_ok=True)
        
        # 初始化UI
        self.setup_ui()
        self.load_image()
        plt.show()

    def ask_resolution(self):
        """弹出对话框输入显示分辨率"""
        self.root.deiconify()  # 显示Tkinter窗口
        
        width, height = 144, 32  # 默认值
        
        def on_confirm():
            nonlocal width, height
            try:
                width = int(width_entry.get())
                height = int(height_entry.get())
                self.root.quit()
            except ValueError:
                pass
        
        # 创建输入对话框
        from tkinter import Label, Entry
        Label(self.root, text="宽度:").grid(row=0, column=0)
        width_entry = Entry(self.root)
        width_entry.insert(0, str(width))
        width_entry.grid(row=0, column=1)
        
        Label(self.root, text="高度:").grid(row=1, column=0)
        height_entry = Entry(self.root)
        height_entry.insert(0, str(height))
        height_entry.grid(row=1, column=1)
        
        TkButton(self.root, text="确定", command=on_confirm).grid(row=2, columnspan=2)
        
        self.root.mainloop()
        self.root.withdraw()
        
        return (width, height)
    
    def setup_ui(self):
        """设置增强版交互式界面"""
        self.fig = plt.figure(figsize=(16, 9), facecolor='lightgray')
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        
        # 调整整体布局边距
        plt.subplots_adjust(left=0.05, right=0.95, bottom=0.1, top=0.9, wspace=0.3, hspace=0.4)
        
        # 主图像区域 (支持缩放和平移)
        self.ax_img = plt.subplot2grid((3, 4), (0, 0), colspan=3, rowspan=2)
        self.ax_img.set_title("原始图像 (点击标记四个角点: 左上→右上→右下→左下)")
        self.ax_img.set_xticks([])
        self.ax_img.set_yticks([])
        self.img_display = None
        self.press = None
        self.xlim = None
        self.ylim = None
        
        # 采样预览区域
        self.ax_preview = plt.subplot2grid((3, 4), (0, 3))
        self.ax_preview.set_title("采样预览")
        self.ax_preview.set_xticks([])
        self.ax_preview.set_yticks([])
        
        # 二值化预览区域
        self.ax_binary = plt.subplot2grid((3, 4), (1, 3))
        self.ax_binary.set_title("二值化预览")
        self.ax_binary.set_xticks([])
        self.ax_binary.set_yticks([])
        
        # 阈值调节滑块 (占用2列宽度)
        ax_thresh = plt.subplot2grid((3, 4), (2, 0), colspan=2)
        self.thresh_slider = Slider(
            ax=ax_thresh,
            label='二值化阈值',
            valmin=0,
            valmax=255,
            valinit=self.threshold,
            valstep=1
        )
        self.thresh_slider.on_changed(self.update_threshold)
        
        # 控制按钮区域 (使用绝对坐标精确定位)
        btn_width, btn_height = 0.1, 0.075
        btn_bottom = 0.05
        
        # 清除按钮
        ax_clear = plt.axes([0.5, btn_bottom, btn_width, btn_height])
        self.btn_clear = Button(ax_clear, '清除标记', color='lightgoldenrodyellow')
        self.btn_clear.on_clicked(self.clear_markers)
        
        # 上一张按钮
        ax_prev = plt.axes([0.62, btn_bottom, btn_width, btn_height])
        self.btn_prev = Button(ax_prev, '上一张', color='lightblue')
        self.btn_prev.on_clicked(self.prev_image)
        
        # 下一张按钮
        ax_next = plt.axes([0.74, btn_bottom, btn_width, btn_height])
        self.btn_next = Button(ax_next, '下一张', color='lightgreen')
        self.btn_next.on_clicked(self.next_image)
        
        # 添加状态显示区域
        self.ax_status = plt.axes([0.86, btn_bottom, 0.1, btn_height])
        self.ax_status.axis('off')
        self.status_text = self.ax_status.text(0.5, 0.5, "就绪", 
                                            ha='center', va='center')
        
        plt.tight_layout()
    
    def load_image(self):
        """加载当前图片并保持缩放状态"""
        if self.current_img_idx >= len(self.img_files):
            print("已处理所有图片")
            plt.close()
            return
        
        img_path = os.path.join(self.input_dir, self.img_files[self.current_img_idx])
        self.original_img = cv2.imread(img_path)
        if self.original_img is None:
            print(f"无法读取图片: {img_path}")
            return
            
        self.original_img_rgb = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2RGB)
        
        # 显示原始图像
        self.ax_img.clear()
        self.img_display = self.ax_img.imshow(self.original_img_rgb)
        self.ax_img.set_title(f"原始图像 {self.current_img_idx + 1}/{len(self.img_files)} ({self.img_files[self.current_img_idx]})")
        
        # 恢复或初始化视图范围
        if self.xlim and self.ylim:
            self.ax_img.set_xlim(self.xlim)
            self.ax_img.set_ylim(self.ylim)
        else:
            self.xlim = self.ax_img.get_xlim()
            self.ylim = self.ax_img.get_ylim()
        
        # 如果已有标记点，重新绘制
        if self.corners:
            self.draw_markers_and_grid()
        
        self.fig.canvas.draw()
    
    def on_click(self, event):
        """处理图像点击事件"""
        if event.inaxes != self.ax_img:
            return
        
        # 右键拖动平移
        if event.button == MouseButton.RIGHT:
            self.press = event.xdata, event.ydata
            return
        
        # 左键添加标记点
        if event.button == MouseButton.LEFT:
            x, y = int(round(event.xdata)), int(round(event.ydata))
            
            if len(self.corners) < 4:
                self.corners.append([x, y])
                self.draw_markers_and_grid()
            
            self.fig.canvas.draw()
    
    def on_motion(self, event):
        """处理鼠标移动事件（用于平移）"""
        if event.inaxes != self.ax_img or self.press is None:
            return
        
        if event.button == MouseButton.RIGHT:
            dx = event.xdata - self.press[0]
            dy = event.ydata - self.press[1]
            
            self.xlim = (self.xlim[0] - dx, self.xlim[1] - dx)
            self.ylim = (self.ylim[0] - dy, self.ylim[1] - dy)
            
            self.ax_img.set_xlim(self.xlim)
            self.ax_img.set_ylim(self.ylim)
            self.press = event.xdata, event.ydata
            self.fig.canvas.draw()
    
    def on_scroll(self, event):
        """处理滚轮缩放事件"""
        if event.inaxes != self.ax_img:
            return
        
        # 获取当前鼠标位置对应的数据坐标
        x, y = event.xdata, event.ydata
        
        # 计算缩放比例
        scale_factor = 1.1 if event.button == 'up' else 0.9
        
        # 更新范围（以鼠标位置为中心）
        self.xlim = (x - (x - self.xlim[0]) * scale_factor,
                     x + (self.xlim[1] - x) * scale_factor)
        self.ylim = (y - (y - self.ylim[0]) * scale_factor,
                     y + (self.ylim[1] - y) * scale_factor)
        
        self.ax_img.set_xlim(self.xlim)
        self.ax_img.set_ylim(self.ylim)
        self.fig.canvas.draw()
    
    def draw_markers_and_grid(self):
        """绘制标记点和网格"""
        self.ax_img.clear()
        self.ax_img.imshow(self.original_img_rgb)
        self.ax_img.set_title(f"原始图像 {self.current_img_idx + 1}/{len(self.img_files)} ({self.img_files[self.current_img_idx]})")
        self.ax_img.set_xlim(self.xlim)
        self.ax_img.set_ylim(self.ylim)
        
        # 绘制标记点
        for i, (x, y) in enumerate(self.corners):
            self.ax_img.plot(x, y, 'ro', markersize=8)
            self.ax_img.text(x+10, y+10, str(i+1), color='red', fontsize=12, 
                           bbox=dict(facecolor='white', alpha=0.7))
        
        # 连接标记点
        if len(self.corners) > 1:
            for i in range(len(self.corners)-1):
                x1, y1 = self.corners[i]
                x2, y2 = self.corners[i+1]
                self.ax_img.plot([x1, x2], [y1, y2], 'r-', linewidth=1)
            if len(self.corners) == 4:
                x1, y1 = self.corners[-1]
                x2, y2 = self.corners[0]
                self.ax_img.plot([x1, x2], [y1, y2], 'r-', linewidth=1)
        
        # 如果四个点都已标记，绘制网格和采样点
        if len(self.corners) == 4:
            dst_w, dst_h = self.display_resolution
            corners_np = np.array(self.corners, dtype=np.float32)
            
            # 预计算网格线
            grid_lines_x = []  # 垂直网格线
            grid_lines_y = []  # 水平网格线
            
            # 计算垂直网格线
            for x in range(dst_w + 1):
                nx = x / dst_w
                top = corners_np[0] + (corners_np[1] - corners_np[0]) * nx
                bottom = corners_np[3] + (corners_np[2] - corners_np[3]) * nx
                grid_lines_x.append((top, bottom))
                self.ax_img.plot([top[0], bottom[0]], [top[1], bottom[1]], 'g-', linewidth=0.5)
            
            # 计算水平网格线
            for y in range(dst_h + 1):
                ny = y / dst_h
                left = corners_np[0] + (corners_np[3] - corners_np[0]) * ny
                right = corners_np[1] + (corners_np[2] - corners_np[1]) * ny
                grid_lines_y.append((left, right))
                self.ax_img.plot([left[0], right[0]], [left[1], right[1]], 'g-', linewidth=0.5)
            
            # 绘制采样点并预览结果
            sampled_img = np.zeros((dst_h, dst_w, 3), dtype=np.uint8)
            sample_points = []
            
            for y in range(dst_h):
                for x in range(dst_w):
                    # 获取当前网格的四条边
                    left_line = grid_lines_x[x]
                    right_line = grid_lines_x[x+1]
                    top_line = grid_lines_y[y]
                    bottom_line = grid_lines_y[y+1]
                    
                    # 计算网格四个角点
                    top_left = left_line[0] + (left_line[1] - left_line[0]) * (y / dst_h)
                    top_right = right_line[0] + (right_line[1] - right_line[0]) * (y / dst_h)
                    bottom_left = left_line[0] + (left_line[1] - left_line[0]) * ((y+1) / dst_h)
                    bottom_right = right_line[0] + (right_line[1] - right_line[0]) * ((y+1) / dst_h)
                    
                    # 计算网格中心点
                    center_x = int(round((top_left[0] + top_right[0] + bottom_left[0] + bottom_right[0]) / 4))
                    center_y = int(round((top_left[1] + top_right[1] + bottom_left[1] + bottom_right[1]) / 4))
                    sample_points.append((center_x, center_y))
                    
                    # 绘制采样点
                    self.ax_img.plot(center_x, center_y, 'bo', markersize=3, alpha=0.5)
                    
                    # 采样像素
                    if 0 <= center_x < self.original_img.shape[1] and 0 <= center_y < self.original_img.shape[0]:
                        sampled_img[y, x] = self.original_img[center_y, center_x]
            
            # 更新预览
            self.update_preview(sampled_img)
    
    def update_preview(self, sampled_img):
        """更新采样和二值化预览"""
        # 转换为灰度并二值化
        gray_img = cv2.cvtColor(sampled_img, cv2.COLOR_BGR2GRAY)
        _, binary_img = cv2.threshold(gray_img, self.threshold, 255, cv2.THRESH_BINARY)
        
        # 显示采样结果
        self.ax_preview.clear()
        self.ax_preview.imshow(cv2.cvtColor(sampled_img, cv2.COLOR_BGR2RGB))
        self.ax_preview.set_title(f"采样预览 ({self.display_resolution[0]}x{self.display_resolution[1]})")
        self.ax_preview.set_xticks([])
        self.ax_preview.set_yticks([])
        
        # 显示二值化结果
        self.ax_binary.clear()
        self.ax_binary.imshow(binary_img, cmap='gray')
        self.ax_binary.set_title(f"阈值: {self.threshold}")
        self.ax_binary.set_xticks([])
        self.ax_binary.set_yticks([])
        
        self.fig.canvas.draw()
    
    def update_threshold(self, val):
        """更新阈值并刷新预览"""
        self.threshold = int(val)
        if len(self.corners) == 4:
            # 重新采样并更新预览
            dst_w, dst_h = self.display_resolution
            corners_np = np.array(self.corners, dtype=np.float32)
            
            # 预计算网格线
            grid_lines_x = []  # 垂直网格线
            grid_lines_y = []  # 水平网格线
            
            # 计算垂直网格线
            for x in range(dst_w + 1):
                nx = x / dst_w
                top = corners_np[0] + (corners_np[1] - corners_np[0]) * nx
                bottom = corners_np[3] + (corners_np[2] - corners_np[3]) * nx
                grid_lines_x.append((top, bottom))
            
            # 计算水平网格线
            for y in range(dst_h + 1):
                ny = y / dst_h
                left = corners_np[0] + (corners_np[3] - corners_np[0]) * ny
                right = corners_np[1] + (corners_np[2] - corners_np[1]) * ny
                grid_lines_y.append((left, right))
            
            # 执行精确采样
            sampled_img = np.zeros((dst_h, dst_w, 3), dtype=np.uint8)
            
            for y in range(dst_h):
                for x in range(dst_w):
                    # 获取当前网格的四条边
                    left_line = grid_lines_x[x]
                    right_line = grid_lines_x[x+1]
                    top_line = grid_lines_y[y]
                    bottom_line = grid_lines_y[y+1]
                    
                    # 计算网格四个角点
                    top_left = left_line[0] + (left_line[1] - left_line[0]) * (y / dst_h)
                    top_right = right_line[0] + (right_line[1] - right_line[0]) * (y / dst_h)
                    bottom_left = left_line[0] + (left_line[1] - left_line[0]) * ((y+1) / dst_h)
                    bottom_right = right_line[0] + (right_line[1] - right_line[0]) * ((y+1) / dst_h)
                    
                    # 计算网格中心点
                    center_x = int(round((top_left[0] + top_right[0] + bottom_left[0] + bottom_right[0]) / 4))
                    center_y = int(round((top_left[1] + top_right[1] + bottom_left[1] + bottom_right[1]) / 4))
                    
                    # 采样像素
                    if 0 <= center_x < self.original_img.shape[1] and 0 <= center_y < self.original_img.shape[0]:
                        sampled_img[y, x] = self.original_img[center_y, center_x]
            
            # 更新预览
            self.update_preview(sampled_img)
    
    def clear_markers(self, event):
        """清除所有标记点"""
        self.corners = []
        self.load_image()
        self.ax_preview.clear()
        self.ax_preview.set_title("采样预览")
        self.ax_preview.set_xticks([])
        self.ax_preview.set_yticks([])
        
        self.ax_binary.clear()
        self.ax_binary.set_title("二值化预览")
        self.ax_binary.set_xticks([])
        self.ax_binary.set_yticks([])
        
        self.fig.canvas.draw()
    
    def save_current_results(self):
        """保存当前处理结果"""
        if len(self.corners) != 4:
            print("请先标记四个角点")
            return
        
        dst_w, dst_h = self.display_resolution
        corners_np = np.array(self.corners, dtype=np.float32)
        
        # 预计算网格线
        grid_lines_x = []  # 垂直网格线
        grid_lines_y = []  # 水平网格线
        
        # 计算垂直网格线
        for x in range(dst_w + 1):
            nx = x / dst_w
            top = corners_np[0] + (corners_np[1] - corners_np[0]) * nx
            bottom = corners_np[3] + (corners_np[2] - corners_np[3]) * nx
            grid_lines_x.append((top, bottom))
        
        # 计算水平网格线
        for y in range(dst_h + 1):
            ny = y / dst_h
            left = corners_np[0] + (corners_np[3] - corners_np[0]) * ny
            right = corners_np[1] + (corners_np[2] - corners_np[1]) * ny
            grid_lines_y.append((left, right))
        
        # 执行精确采样
        sampled_img = np.zeros((dst_h, dst_w, 3), dtype=np.uint8)
        
        for y in range(dst_h):
            for x in range(dst_w):
                # 获取当前网格的四条边
                left_line = grid_lines_x[x]
                right_line = grid_lines_x[x+1]
                top_line = grid_lines_y[y]
                bottom_line = grid_lines_y[y+1]
                
                # 计算网格四个角点
                top_left = left_line[0] + (left_line[1] - left_line[0]) * (y / dst_h)
                top_right = right_line[0] + (right_line[1] - right_line[0]) * (y / dst_h)
                bottom_left = left_line[0] + (left_line[1] - left_line[0]) * ((y+1) / dst_h)
                bottom_right = right_line[0] + (right_line[1] - right_line[0]) * ((y+1) / dst_h)
                
                # 计算网格中心点
                center_x = int(round((top_left[0] + top_right[0] + bottom_left[0] + bottom_right[0]) / 4))
                center_y = int(round((top_left[1] + top_right[1] + bottom_left[1] + bottom_right[1]) / 4))
                
                # 采样像素
                if 0 <= center_x < self.original_img.shape[1] and 0 <= center_y < self.original_img.shape[0]:
                    sampled_img[y, x] = self.original_img[center_y, center_x]
        
        # 转换为灰度并二值化
        gray_img = cv2.cvtColor(sampled_img, cv2.COLOR_BGR2GRAY)
        _, binary_img = cv2.threshold(gray_img, self.threshold, 255, cv2.THRESH_BINARY)
        
        # 保存结果
        base_name = os.path.splitext(self.img_files[self.current_img_idx])[0]
        cv2.imwrite(os.path.join(self.output_dir, "sampled", f"{base_name}_sampled.png"), sampled_img)
        cv2.imwrite(os.path.join(self.output_dir, "binary", f"{base_name}_binary.png"), binary_img)
        
        print(f"已保存 {self.img_files[self.current_img_idx]} 的处理结果")
    
    def next_image(self, event):
        """处理下一张图片"""
        if len(self.corners) == 4:
            self.save_current_results()
        
        if self.current_img_idx < len(self.img_files) - 1:
            self.current_img_idx += 1
            self.load_image()
        else:
            print("已是最后一张图片")
    
    def prev_image(self, event):
        """处理上一张图片"""
        if self.current_img_idx > 0:
            self.current_img_idx -= 1
            self.load_image()
        else:
            print("已是第一张图片")

# 使用示例
if __name__ == "__main__":
    # 设置Matplotlib的字体参数
    plt.rcParams['font.family'] = 'SimSun'  # 选择一个支持中文的字体

    # 启动交互式处理工具
    processor = PreciseDisplayExtractor()