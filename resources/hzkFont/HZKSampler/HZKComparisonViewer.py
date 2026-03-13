import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class HZKViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("HZK字库比较工具")
        
        # 初始化变量
        self.hzk_files = [None, None]
        self.current_offset = 0
        self.max_offset = 94 * 94 * 32 - 32  # 最大合法偏移量
        
        # 创建UI
        self.create_widgets()
        
    def create_widgets(self):
        # 文件选择区域
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=10)
        
        tk.Button(file_frame, text="打开标准HZK", command=lambda: self.load_hzk(0)).grid(row=0, column=0, padx=5)
        tk.Button(file_frame, text="打开自定义HZK", command=lambda: self.load_hzk(1)).grid(row=0, column=1, padx=5)
        
        self.file_labels = [
            tk.Label(file_frame, text="未加载", width=40, anchor="w"),
            tk.Label(file_frame, text="未加载", width=40, anchor="w")
        ]
        self.file_labels[0].grid(row=1, column=0, padx=5)
        self.file_labels[1].grid(row=1, column=1, padx=5)
        
        # 显示区域
        display_frame = tk.Frame(self.root)
        display_frame.pack(pady=10)
        
        # 标准字库显示
        tk.Label(display_frame, text="标准HZK").grid(row=0, column=0)
        self.std_canvas = tk.Canvas(display_frame, width=160, height=160, bg="white")
        self.std_canvas.grid(row=1, column=0, padx=10)
        
        # 自定义字库显示
        tk.Label(display_frame, text="自定义HZK").grid(row=0, column=1)
        self.custom_canvas = tk.Canvas(display_frame, width=160, height=160, bg="white")
        self.custom_canvas.grid(row=1, column=1, padx=10)
        
        # 信息显示
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=10)
        
        self.offset_label = tk.Label(info_frame, text="偏移量: 0x000000 (区:0xA1 位:0xA1)")
        self.offset_label.pack()
        
        # 导航控制
        nav_frame = tk.Frame(self.root)
        nav_frame.pack(pady=10)
        
        tk.Button(nav_frame, text="上一个字", command=self.prev_char).grid(row=0, column=0, padx=5)
        tk.Button(nav_frame, text="下一个字", command=self.next_char).grid(row=0, column=1, padx=5)
        
        jump_frame = tk.Frame(nav_frame)
        jump_frame.grid(row=0, column=2, padx=5)
        
        tk.Label(jump_frame, text="跳转到偏移量:").pack(side="left")
        self.offset_entry = tk.Entry(jump_frame, width=10)
        self.offset_entry.pack(side="left")
        tk.Button(jump_frame, text="跳转", command=self.jump_to_offset).pack(side="left")
    
    def load_hzk(self, index):
        file_path = filedialog.askopenfilename(title=f"选择{'标准' if index == 0 else '自定义'}HZK文件")
        if file_path:
            self.hzk_files[index] = file_path
            self.file_labels[index].config(text=os.path.basename(file_path))
            if all(self.hzk_files):
                self.show_current_char()
    
    def show_current_char(self):
        if not all(self.hzk_files):
            return
            
        # 计算区码和位码
        zone = self.current_offset // (94 * 32) + 0xA1
        bit = (self.current_offset % (94 * 32)) // 32 + 0xA1
        
        # 更新偏移量显示
        self.offset_label.config(
            text=f"偏移量: 0x{self.current_offset:06X} (区:0x{zone:02X} 位:0x{bit:02X})"
        )
        
        # 显示两个字库的字符
        for i, canvas in enumerate([self.std_canvas, self.custom_canvas]):
            char_data = self.read_char_data(self.hzk_files[i])
            img = self.render_char(char_data)
            self.display_image(canvas, img)
    
    def read_char_data(self, file_path):
        try:
            with open(file_path, "rb") as f:
                f.seek(self.current_offset)
                return f.read(32)
        except:
            return bytes(32)  # 返回空字符
    
    def render_char(self, char_data):
        print(f"当前字符数据（十六进制）: {char_data.hex()}")  # 调试输出
        """将32字节的HZK数据转换为16x16图像"""
        # 创建空白图像（白色背景）
        img = Image.new("1", (16, 16), 1)  # 1=白，0=黑
        pixels = img.load()
        
        print(f"字符数据: {char_data.hex()}")  # 调试输出
        
        # 逐行处理16行数据
        for y in range(16):
            # 获取该行的两个字节
            byte1 = char_data[y * 2] if y * 2 < len(char_data) else 0
            byte2 = char_data[y * 2 + 1] if y * 2 + 1 < len(char_data) else 0
            
            # 打印当前行数据（二进制格式）
            bin1 = bin(byte1)[2:].zfill(8)
            bin2 = bin(byte2)[2:].zfill(8)
            print(f"行 {y:2d}: {bin1} {bin2}")
            
            # 处理每行的16个像素（8个像素/字节）
            for x in range(8):
                # 处理左半字节（x: 0-7）
                if byte1 & (1 << (7 - x)):
                    pixels[x, y] = 0  # 设置黑色像素
                else:
                    pixels[x, y] = 1  # 保持白色背景
                
                # 处理右半字节（x: 8-15）
                if byte2 & (1 << (7 - x)):
                    pixels[x + 8, y] = 0  # 设置黑色像素
                else:
                    pixels[x + 8, y] = 1  # 保持白色背景
        
        # # 保存原始图像用于调试
        # debug_path = f"debug_char_{self.current_offset}.png"
        # img.save(debug_path)
        # print(f"调试图像已保存: {debug_path}")
        
        # 放大显示
        return img.resize((160, 160), Image.NEAREST)
    
    def display_image(self, canvas, img):
        """在Canvas上显示图像"""
        canvas.delete("all")
        
        # 确保图像是PhotoImage兼容格式
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        tk_img = ImageTk.PhotoImage(img)
        
        # 关键：保持引用防止垃圾回收
        if not hasattr(canvas, "image_references"):
            canvas.image_references = []
        canvas.image_references.append(tk_img)
        
        # 在画布中央显示图像
        canvas.create_image(80, 80, image=tk_img)
        
        # 添加调试网格
        for i in range(0, 160, 10):  # 每10像素一条线
            canvas.create_line(i, 0, i, 160, fill="gray")
            canvas.create_line(0, i, 160, i, fill="gray")
    
    def prev_char(self):
        self.current_offset = max(0, self.current_offset - 32)
        self.show_current_char()
    
    def next_char(self):
        self.current_offset = min(self.max_offset, self.current_offset + 32)
        self.show_current_char()
    
    def jump_to_offset(self):
        try:
            offset_str = self.offset_entry.get().strip()
            if offset_str.startswith("0x"):
                offset = int(offset_str[2:], 16)
            else:
                offset = int(offset_str)
            
            # 确保偏移量合法
            offset = max(0, min(self.max_offset, offset))
            # 对齐到32字节边界
            offset = (offset // 32) * 32
            
            self.current_offset = offset
            self.show_current_char()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的偏移量（十进制或0x开头的十六进制）")

if __name__ == "__main__":
    root = tk.Tk()
    app = HZKViewer(root)
    root.mainloop()