from PIL import Image, ImageDraw, ImageFont, ImageChops
import numpy as np
import binascii, re, os, ast, struct #, freetype

class BMP_SCALE_BOLD_HELPER():
    def __init__(self):
        pass

    def scale_mono_bitmap_horizontal(self, image, scale_x):
        """
        单色位图水平缩放算法
        支持传入 '1' 模式的 PIL 图像
        
        Args:
            image: PIL Image对象（'1' 模式单色位图）
            scale_x: 水平缩放比例（百分比，小于100表示缩小）
        
        Returns:
            缩放后的PIL Image对象（'1' 模式）
        """
        # 确保输入是 '1' 模式
        if image.mode != '1':
            image = image.convert('1')
        
        # 转换为numpy数组进行处理
        img_array = np.array(image)
        height, width = img_array.shape
        
        # 计算新宽度
        new_width = max(1, int(width * scale_x / 100))
        
        # 创建新图像数组（初始全0）
        new_img_array = np.zeros((height, new_width), dtype=np.uint8)
        
        # 从原图的每一列出发，计算它应该映射到新图的哪一列
        for x_old in range(width):
            # 计算这一列在新图中的位置
            x_new = int(x_old * new_width / width)
            
            # 确保不越界
            if x_new >= new_width:
                x_new = new_width - 1
            
            # 将原图的这一列"或"到新图的对应列
            for y in range(height):
                # 检查像素值是否为"白色"（在单色位图中可能是True或255）
                if img_array[y, x_old]:  # 直接使用布尔判断
                    new_img_array[y, x_new] = 255  # 设置新图对应位置为白色
        
        # 转换回PIL Image
        result_image = Image.fromarray(new_img_array, mode='L').convert('1')
        return result_image
    
    def bold_image(self, image, xb, yb):
        # 创建加粗后的图像
        bold_image = image.copy()
        
        # 水平加粗
        for i in range(1, xb):
            # 创建一个临时图像，将原图像向右平移i像素
            shifted = Image.new("1", image.size, 0)
            # 计算平移后的区域
            if i < image.width:
                # 从原图像复制区域到平移后的位置
                box_from = (0, 0, image.width - i, image.height)
                box_to = (i, 0, image.width, image.height)
                region = image.crop(box_from)
                shifted.paste(region, box_to)
            
            # 合并图像
            bold_image = ImageChops.logical_or(bold_image, shifted)
        
        # 垂直加粗
        for i in range(1, yb):
            # 创建一个临时图像，将原图像向下平移i像素
            shifted = Image.new("1", image.size, 0)
            # 计算平移后的区域
            if i < image.height:
                # 从原图像复制区域到平移后的位置
                box_from = (0, 0, image.width, image.height - i)
                box_to = (0, i, image.width, image.height)
                region = image.crop(box_from)
                shifted.paste(region, box_to)
            
            # 合并图像
            bold_image = ImageChops.logical_or(bold_image, shifted)
        
        return bold_image

class ASC_bin_reader:
    def __init__(self, bin_path):
        self.is_ready = False
        self.font_data = None
        self.height = 0
        self.width = 0
        self.bpc = 0
        self.config = 0
        self.is_vert_scan = False
        self.is_lsb = False
        self.stride = 0
        self.width_table = []
        self._load_bin(bin_path)

    def _load_bin(self, bin_path):
        try:
            if not os.path.exists(bin_path): return
            with open(bin_path, "rb") as f:
                magic = f.read(4)
                if magic != b'FONT': return
                
                self.height = struct.unpack('<B', f.read(1))[0]
                self.width = struct.unpack('<B', f.read(1))[0]
                self.bpc = struct.unpack('<H', f.read(2))[0]
                self.config = struct.unpack('<B', f.read(1))[0]
                f.read(7)  # 跳过保留位
                
                self.is_vert_scan = (self.config & 0x02) != 0  # Bit 1
                self.is_lsb = (self.config & 0x04) != 0        # Bit 2
                
                if self.is_vert_scan:
                    self.stride = (self.height + 7) // 8
                else:
                    self.stride = (self.width + 7) // 8
                
                self.width_table = list(f.read(256))
                self.font_data = f.read()
                self.is_ready = True
        except Exception as e:
            print(f"Load Error: {e}")

    def get_text_bmp(self, asc, y_offset=0, *not_used_argv) -> Image.Image:
        if not self.is_ready or not asc:
            return Image.new("1", (10, 10), 0)

        ascii_code = ord(asc[0]) if isinstance(asc, str) else int(asc)
        char_w = self.width_table[ascii_code]
        
        start_offset = ascii_code * self.bpc
        char_data = self.font_data[start_offset:start_offset + self.bpc]
        
        img = Image.new("1", (self.width, self.height), 0)
        pixels = img.load()
        
        main_limit = self.width if self.is_vert_scan else self.height
        sub_limit = self.height if self.is_vert_scan else self.width
        
        for m in range(main_limit):
            for s in range(sub_limit):
                byte_pos = m * self.stride + (s // 8)
                bit_pos = (s % 8) if self.is_lsb else (7 - (s % 8))
                
                if byte_pos < len(char_data):
                    if (char_data[byte_pos] >> bit_pos) & 1:
                        res_x = m if self.is_vert_scan else s
                        res_y = s if self.is_vert_scan else m
                        
                        if res_x < self.width and res_y < self.height:
                            pixels[res_x, res_y] = 1
        
        if char_w < self.width:
            img = img.crop((0, 0, char_w, self.height))

        ext_w = 0
        if not self.config & 0x01:
            ext_w = 1

        img = img.crop((0, y_offset, img.width + ext_w, y_offset + img.height))
        
        return img
    
class ASC_font_Reader():
    def __init__(self,font_path):
        self.font_path = font_path
        self.font_hex_list = []
        self.bitmap_size = [0,0]
        self.pread_font_data()

    def pread_font_data(self):
        with open(self.font_path,"r",encoding='ansi') as fontdata:
            font_hex_data = fontdata.readlines()
        self.bitmap_size = [int(font_hex_data[1].split(',')[0]),int(font_hex_data[1].split(',')[1])]
        font_hex_data = font_hex_data[2:]
        self.font_hex_list = [[int(self.bitmap_size[0]/2),[int('0x20',16) for _ in range(int(self.bitmap_size[0]/8*self.bitmap_size[1]))]] for _ in range(256)]
        for i in range(0,len(font_hex_data),3):
            ascii_value = int(font_hex_data[i].strip().split(',')[0])
            char_width = int(font_hex_data[i+1].strip().split(',')[0])
            char_hex_str = font_hex_data[i+2].strip().split(',')[:-1]
            char_hex_value = [int(s,16) for s in char_hex_str]
            self.font_hex_list[ascii_value] = [char_width,char_hex_value]

    def get_text_bmp(self,asc,y_offset = 0,*not_used_argv):
        data = self.font_hex_list[ord(asc)]
        bitlist = []
        for i in range(self.bitmap_size[1]):
            row = []
            for j in range(int(self.bitmap_size[0]/8)):
                row = row + [(data[1][i*int(self.bitmap_size[0]/8)+j] ^ ord(asc)) >> bit & 1 for bit in range(8)[::-1]]
            bitlist.append(row)
        image_data = [255 if pixel == 1 else 0 for row in bitlist for pixel in row]
        image = Image.new("1", (self.bitmap_size[0], self.bitmap_size[1]))
        image.putdata(image_data)
        image = image.crop((0,y_offset,data[0]+1,y_offset+self.bitmap_size[1]))
        return image
    
class ASC_Bmp_Reader():
    def __init__(self,fontBmpPath):
        self.fontBmpPath = fontBmpPath
        self.fnt_img = Image.open(self.fontBmpPath)
        # print(self.fontBmpPath)
        self.ascii_size = [int(fontBmpPath.split(".")[-2].split("_")[1].split("-")[0]),int(fontBmpPath.split(".")[-2].split("_")[1].split("-")[1])]

    def get_text_bmp(self,asc,y_offset=0,*not_used_argv):
        value = ord(asc)
        x = value%16
        y = value//16
        ch = self.fnt_img.crop((x*self.ascii_size[0],y*self.ascii_size[1],(x+1)*self.ascii_size[0],(y+1)*self.ascii_size[1]))
        ch = ch.convert('1')
        ch = ch.point(lambda x: not x)  # 直接反转二值图像
        
        l = self.ascii_size[0]-1    ####!!
        r = 0
        if self.ascii_size[0] == self.ascii_size[1]:
            for y in range(ch.size[1]):
                for x in range(ch.size[0]):
                    if ch.getpixel((x,y)) != 0:
                        if x <= l:
                            l = x
                        if x >= r:
                            r = x
            if r<l:
                tmp = l
                l = r
                r = tmp

                if asc == " ":
                    r = l+int(0.25*self.ascii_size[0])    ####!!
                
            else:
                if asc == " ":
                    ch = Image.new("1", (r-l, ch.height))
                    r -= 1

            r = r+2 if r+2 <= self.ascii_size[0] else r+1
        else:
            l = 0
            r = self.ascii_size[0]

        ch = ch.crop((l,y_offset,r,ch.height+y_offset))

        return ch

class HZK_Font_Reader():
    def __init__(self, fontPath, is_klscale):
        self.fontPath = fontPath
        self.is_klscale = is_klscale
        self.font_size = 16  # 默认16
        self.HELPER = BMP_SCALE_BOLD_HELPER()
        self._init_font_params()
        
        # 验证文件存在
        with open(self.fontPath, "rb") as f:
            pass

    def _init_font_params(self):
        """根据字体大小初始化参数"""
        self.bytes_per_char = (self.font_size * self.font_size) // 8
        self.char_width = self.font_size
        self.char_height = self.font_size
        self.KEYS = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]

    def get_char_map(self, text):
        try:
            gb2312 = text.encode('gb2312')
        except:
            gb2312 = "　".encode('gb2312')
        
        hex_str = binascii.b2a_hex(gb2312)
        result = str(hex_str, encoding='utf-8')
        area = int('0x' + result[:2], 16) - 0xA0
        index = int('0x' + result[2:], 16) - 0xA0
        
        # 计算偏移量
        offset = (94 * (area-1) + (index-1)) * self.bytes_per_char
        
        # 初始化字符点阵
        rect_list = [[] for _ in range(self.char_height)]
        
        # 读取字体数据
        with open(self.fontPath, "rb") as f:
            f.seek(offset)
            font_rect = f.read(self.bytes_per_char)
        
        # 每行字节数
        bytes_per_row = self.char_width // 8
        
        for row in range(self.char_height):
            row_list = rect_list[row]
            for byte_idx in range(bytes_per_row):
                byte_data = font_rect[row * bytes_per_row + byte_idx]
                for bit in range(8):
                    flag = 1 if byte_data & self.KEYS[bit] else 0
                    row_list.append(flag)
        
        return rect_list
        
    def make_text_bmp(self, fontData, y_offset, xb=1, yb=1, scale=100, scale_y=100):
        # 创建图像数据
        image_data = [255 if pixel == 1 else 0 for row in fontData for pixel in row]
        image = Image.new("1", (self.char_width, self.char_height))
        image.putdata(image_data)
        
        # 裁剪到指定偏移量
        image = image.crop((0, y_offset, image.width, y_offset + image.height))
        
        if self.is_klscale and scale < 100:
            image = self.HELPER.scale_mono_bitmap_horizontal(image, scale)

            if scale_y != 100:
                new_height = int(image.height * scale_y / 100)
                image = image.resize((image.width, new_height), resample=Image.LANCZOS)

            # 加粗处理
            if xb > 1 or yb > 1:
                image = self.HELPER.bold_image(image, xb, yb)
            
        else:
            # 加粗处理
            if xb > 1 or yb > 1:
                image = self.HELPER.bold_image(image, xb, yb)
            
            # 缩放处理
            if scale != 100 or scale_y != 100:
                new_width = int(image.width * scale / 100)
                new_height = int(image.height * scale_y / 100)
                image = image.resize((new_width, new_height), resample=Image.LANCZOS)
        
        return image
        
    def get_text_bmp(self, text, y_offset=0, font_size=16, xb=1, yb=1, scale=100, scale_y=100, *not_used_argv):
        self.font_size = font_size
        self._init_font_params()
        try:
            bmp = self.make_text_bmp(self.get_char_map(text), y_offset, xb, yb, scale, scale_y)
        except Exception as e:
            print(f"get_text_bmp in HZK_Font_Reader: {e}")
            bmp = Image.new("1",(font_size, font_size))
        return bmp
    
    def set_font_size(self, font_size):
        """设置字体大小"""
        self.font_size = font_size
        self._init_font_params()

class Sys_Font_Reader():
    def __init__(self,font_path,is_klscale):
        self.font = None
        self.font_path = font_path
        self.is_klscale = is_klscale
        self.HELPER = BMP_SCALE_BOLD_HELPER()

    def is_Chinese(self,word):
        for ch in word:
            if '\u4e00' <= ch <= '\u9fff':
                return True
        return False

    def get_text_bmp(self,text,y_offset=0,font_size=16,xb=1,yb=1,scale=100, scale_y=100, *not_used_argv):
        try:
            self.font = ImageFont.truetype(self.font_path, font_size)
        except:    # 字体打不开时暂时用宋体代替
            self.font = ImageFont.truetype("simsun", font_size)
        scaled_font = {"FZYTK":72,}
        extra_size = int(0.2*font_size) if text.isascii() else 0  # 加高ASCII字体以防止字符不完整
        extra_size = 0
        s = text
        s = "+ "+s
        ss = "+ "
        adjusted_height = [0,0]

        # 创建一个Image对象
        image = Image.new("1", (1, 1))  # 1-bit image (black and white)
        draw = ImageDraw.Draw(image)
        # 计算文本的宽度和高度
        bbox = draw.textbbox((0, 0), s, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        # 多余的宽度
        bbox = draw.textbbox((0, 0), ss, font=self.font)
        delta_width = bbox[2] - bbox[0]
        # delta_height = font_size-text_height

        offset = int(0.5*font_size)+int(0.5*extra_size)
        # print(s,offset,font_size,text_height,delta_y)

        # 获取参考字符的高度
        chars = [s,ss]
        for i in range(len(chars)):
            t = chars[i]
            image = Image.new("1", (text_width-delta_width, font_size+extra_size))
            # 获取新的Draw对象
            draw = ImageDraw.Draw(image)
            draw.text((0, offset-y_offset), t, font=self.font, fill=1, anchor="lm")
            for x in range(image.width):
                for y in range(image.height):
                    if image.getpixel((x,y)):
                        adjusted_height[i] = y
                        break
                else:
                    continue
                break

        # 加粗超过2时处理尺寸
        if xb >= 2:
            text_width += (xb - 2)
        if yb >= 2:
            extra_size += (yb - 2)

        image = Image.new("1", (text_width-delta_width, font_size+extra_size))
        # 获取新的Draw对象
        draw = ImageDraw.Draw(image)

        if self.is_klscale and scale < 100:
            draw.text((-delta_width, offset-y_offset+(-adjusted_height[0]+adjusted_height[1])), s, font=self.font, fill=1, anchor="lm")

            for fnt in scaled_font.keys():
                if fnt in self.font_path and self.is_Chinese(text):
                    image = image.crop((1+int(image.width*(1-scaled_font[fnt]/100)*0.5),0,int(image.width*(1-(1-scaled_font[fnt]/100)*0.5)),image.height))

            image = self.HELPER.scale_mono_bitmap_horizontal(image, scale)

            if scale_y != 100:
                new_height = int(image.height * scale_y / 100)
                image = image.resize((image.width, new_height), resample=Image.LANCZOS)

            # 加粗处理
            if xb > 1 or yb > 1:
                image = self.HELPER.bold_image(image, xb, yb)

        else:
            # 设置字体，绘制文本，加粗
            for i in range(xb):
                for j in range(yb):
                    draw.text((i-delta_width, j+offset-y_offset+(-adjusted_height[0]+adjusted_height[1])), s, font=self.font, fill=1, anchor="lm")

            for fnt in scaled_font.keys():
                if fnt in self.font_path and self.is_Chinese(text):
                    image = image.crop((1+int(image.width*(1-scaled_font[fnt]/100)*0.5),0,int(image.width*(1-(1-scaled_font[fnt]/100)*0.5)),image.height))

            # 缩放处理
            if scale != 100 or scale_y != 100:
                new_width = int(image.width * scale / 100)
                new_height = int(image.height * scale_y / 100)
                image = image.resize((new_width, new_height), resample=Image.LANCZOS)

        return image
    
class FontManager():
    def __init__(self):
        self.font_info = {"./resources/font.info"}
        self.icon_info = {"./resources/icon.info"}
        self.font_dict = dict()
        self.icon_dict = dict()  # 字体和图标均不可重名
        self.AscFont = []
        self.HzkFont = []
        self.SysFont = []
        self.flush_resources()

    def flush_resources(self):
        self.get_font_list()
        self.get_icon_list()

    def get_font_list(self):
        for font_info in self.font_info:
            try:
                with open(font_info, "r", encoding="utf-8") as f:
                    folder = None
                    ftype = None
                    for line in f:
                        line = line.strip("\ufeff").strip()
                        
                        # 跳过空行和注释
                        if not line or line.startswith("#"):
                            continue
                        
                        # 处理FONT行
                        if line.startswith("FONT"):
                            parts = line.split(",")
                            if len(parts) >= 3:
                                ftype = parts[1]
                                folder = parts[2][4:]  # 获取文件夹路径
                            continue
                        
                        # 处理字体定义行
                        if folder is not None and ftype is not None:
                            parts = line.split(",")
                            if len(parts) >= 3:
                                font_file = parts[0].strip()
                                font_name = parts[1].strip()
                                self.font_dict[font_name] = folder+font_file
                                if ftype == "ASCII_FONT":
                                    self.AscFont.append(font_name)
                                elif ftype == "SYS_FONT":
                                    self.SysFont.append(font_name)
                                elif ftype == "HZK_FONT":
                                    self.HzkFont.append(font_name)
            except Exception as e:
                print(f"Error processing {font_info}: {e}")
        # print(self.font_dict)

    def get_icon_list(self):
        for icon_info in self.icon_info:
            try:
                with open(icon_info, "r", encoding="utf-8") as f:
                    folder = None
                    for line in f:
                        line = line.strip("\ufeff").strip()
                        
                        # 跳过空行和注释
                        if not line or line.startswith("#"):
                            continue
                        
                        # 处理ICON行
                        if line.startswith("ICON"):
                            parts = line.split(",")
                            if len(parts) >= 3:
                                folder = parts[2][4:]  # 获取文件夹路径
                                if folder.lower() == "default":
                                    folder = os.path.dirname(icon_info)
                            continue
                        
                        # 处理图标定义行
                        if folder is not None:
                            parts = line.split(",")
                            if len(parts) >= 3:
                                icon_name = f'`{parts[0].strip()}`'
                                icon_file = parts[1].strip()
                                self.icon_dict[icon_name] = os.path.join(folder, icon_file)
            except Exception as e:
                print(f"Error processing {icon_info}: {e}")
        # print(self.icon_dict)

class BmpCreater():
    # 显示屏组件编写时，让图片默认位置是水平竖直均居中，如果横向滚动，竖直居中，竖直滚动，水平居中！
    # color_type:"RGB"和"1"两种
    def __init__(self,Manager=None,color_type="RGB",color=(255,255,255),ch_font="",asc_font="",only_sysfont = False,klscale = False):
        self.lineBreakChr = ["\n","\u2029"]
        self.only_sysfont = only_sysfont
        self.klscale = klscale
        self.color_type = color_type
        self.color = (color[0],color[1],color[2],255)

        if Manager is None:
            self.FontManager = FontManager()
        else:
            self.FontManager = Manager

        try:
            try:
                self.ch_font = self.FontManager.font_dict[ch_font]
            except:
                self.ch_font = self.FontManager.font_dict["宋体"]
            try:
                self.asc_font = self.FontManager.font_dict[asc_font]
            except:
                self.asc_font = self.FontManager.font_dict["宋体"]

            asc_font_type = self.asc_font.split(".")[-1].lower()
            ch_font_type = self.ch_font.split(".")[-1].lower()
            # if not self.only_sysfont:
            try:
                if asc_font_type == "font":
                    self.ASC_Reader = ASC_font_Reader(self.asc_font)
                elif asc_font_type == "bmp":
                    self.ASC_Reader = ASC_Bmp_Reader(self.asc_font)
                elif asc_font_type == "bin":
                    self.ASC_Reader = ASC_bin_reader(self.asc_font)
                else:
                    self.ASC_Reader = Sys_Font_Reader(self.asc_font, self.klscale)
            except:
                self.ASC_Reader = Sys_Font_Reader(self.asc_font, self.klscale)
            try:
                if ch_font_type == "hzk":
                    self.Ch_Reader = HZK_Font_Reader(self.ch_font, self.klscale)
                else:
                    self.Ch_Reader = Sys_Font_Reader(self.ch_font, self.klscale)
            except:
                self.Ch_Reader = Sys_Font_Reader(self.asc_font, self.klscale)
        except Exception as e:
            print(f"BmpCreater Init: Can not find font, {e}")

    def find_backtick_strings(self,s):
        ordered_strings = []
        start = 0
        for match in re.finditer(r'(`[^`]*`)', s):
            # 添加反引号之前的字符串（如果存在）
            if match.start() > start:
                ordered_strings.append(s[start:match.start()])
            # 添加反引号包围的字符串
            ordered_strings.append(match.group(1))
            start = match.end()
        # 添加最后一个反引号之后的字符串（如果存在）
        if start < len(s):
            ordered_strings.append(s[start:])
        return ordered_strings

    def hconcat_images(self,image_list = [], vertical = False, space = 1, style = [0, 0], multi_line = {"stat":False, "line_space": 0, "exp_size": []}):
        # print(multi_line)
        line_space = multi_line["line_space"]
        exp_size = multi_line["exp_size"]
        default_color = None
        reverse = False
        if not vertical:
            sstyle = style[1]
        else:
            sstyle = style[0]
        

        if line_space < 0 and len(exp_size) == 1:
            reverse = True
            line_space = -line_space

        if self.color_type == "RGB":
            color_type = "RGBA"
            default_color = (0,0,0,0)
        elif self.color_type == "1":
            color_type = "1"
            default_color = 0
        # style: -1,0,1，对齐方式 左中右或上中下
        if len(image_list) == 0:
            return Image.new(color_type, (10,10), default_color)
        
        if multi_line["stat"] == False:  # 自身调用时，"stat"定义为False，"line_space"为原先值（再传过来），"exp_size"定义为[multi_line["line_space"]]， 这样其长度为1，与不使用多行，但传递了"line_space"的情况分开
            # print("拼图第1种情况",len(image_list))
            pmc = False   # percented_multiline_combine，以百分数表示的行距，如1.5->150%
            if len(exp_size) == 1 :
                pmc = True          # 表示第二次把每一行的图片拼合

            if not vertical:
                # 计算所有图像的最大高度和宽度之和
                total_height = max(image["img"].height for image in image_list)
                total_width = sum(image["img"].width for image in image_list)
                # 创建一个新的图像作为画布，背景为白色
                if space >= 0 and not pmc:
                    new_image = Image.new(color_type, (total_width+space*(len(image_list)-1), total_height), default_color)
                elif space >= -100 or pmc:
                    if len(image_list) > 1:
                        if pmc:
                            for im in image_list[:-1]:
                                total_width += int(im["img"].width * (line_space - 1))
                            if total_width == 0:
                                total_width += im["img"].width
                        else:
                            total_width = 0
                            for im in image_list[:-1]:
                                total_width += int(im["img"].width * (100 + space) / 100)
                            total_width += im["img"].width
                    new_image = Image.new(color_type, (total_width, total_height), default_color)
            else:
                total_height = sum(image["img"].height for image in image_list)
                total_width = max(image["img"].width for image in image_list)
                if space >= 0 and not pmc:
                    new_image = Image.new(color_type, (total_width, total_height+space*(len(image_list)-1)), default_color)
                elif space >= -100 or pmc:
                    if len(image_list) > 1:                    
                        if pmc:
                            for im in image_list[:-1]:
                                total_height += int(im["img"].height * (line_space - 1))
                            if total_height == 0:
                                total_height += im["img"].height
                        else:
                            total_height = 0
                            for im in image_list[:-1]:
                                total_height += int(im["img"].height * (100 + space) / 100)
                            total_height += im["img"].height
                    new_image = Image.new(color_type, (total_width, total_height), default_color)
            # 在新图像上依次粘贴每个图像
            x_offset = 0
            y_offset = 0
            real_x = 0
            real_y = 0
            if sstyle > 0:    # style指定图片的对齐方式
                k = 0
            elif sstyle == 0:
                k = 0.5
            else:
                k = 1
            for image in image_list:
                if vertical:
                    x_offset = int(k*(total_width-image["img"].width))
                else:
                    y_offset = int(k*(total_height-image["img"].height))

                if reverse and len(exp_size) == 1:
                    if vertical:
                        real_y = total_height - image["img"].height - y_offset
                        real_x = x_offset
                    else:
                        real_x = total_width - image["img"].width - x_offset
                        real_y = y_offset
                else:
                    real_y = y_offset
                    real_x = x_offset
                        
                # print(reverse and len(exp_size) == 1, x_offset,y_offset," ",real_x,real_y)

                # 计算每个图像粘贴的位置
                new_image.paste(image["img"], (real_x, real_y), image["img"])
                if not vertical:
                    if space >= 0 and not pmc:
                        x_offset += image["img"].width
                        x_offset += space
                    elif space >= -100 and not pmc:
                        x_offset += int(image["img"].width * (100 + space) / 100)
                    if pmc:
                        x_offset += int(image["img"].width * line_space)
                else:
                    if space >= 0 and not pmc:
                        y_offset += image["img"].height
                        y_offset += space
                    elif space >= -100 and not pmc:
                        y_offset += int(image["img"].height * (100 + space) / 100)
                    if pmc:
                        y_offset += int(image["img"].height * line_space)

            return new_image
        
        elif multi_line["stat"] == True and len(exp_size) == 2:
            # print("拼图第2种情况",len(image_list))
            li = []
            t_li = []
            t_li_size = 0
            if not vertical:    # 水平排列分成多行
                exps = exp_size[0]
            else:    # 垂直排列为多列
                exps = exp_size[1]

            auto_s_ed = False
            for i in range(len(image_list)):
                if i+1 < len(image_list):
                    next = image_list[i+1]["img"]
                else:
                    next = None
                current_size = 0
                next_size = 0
                if not vertical:    # 水平排列分成多行
                    current_size = image_list[i]["img"].width
                    if next is not None:
                        next_size = next.width
                else:    # 垂直排列为多列
                    current_size = image_list[i]["img"].height
                    if next is not None:
                        next_size = next.height

                cnt_chr = image_list[i]["chr"]
                pre_chr = image_list[i-1]["chr"] if i-1 >= 0 else None
                nxt_chr = image_list[i+1]["chr"] if i+1 < len(image_list) else None

                # print(i)
                this_take_size = 0
                next_take_size = 0
                if space > 0:
                    this_take_size = space + current_size
                    next_take_size = space + next_size
                elif space >= -100:
                    this_take_size = int(current_size * ((100 + space) / 100))
                    next_take_size = int(next_size * ((100 + space) / 100))

                oldst = 0
                oldst = space if space > 0 else 0

                if cnt_chr not in self.lineBreakChr:
                    if t_li_size == 0 or t_li_size + this_take_size <= exps + oldst:
                        t_li.append({"img": image_list[i]["img"], "chr": None})
                        t_li_size += this_take_size

                s = False
                if cnt_chr not in self.lineBreakChr:    # 不是换行符
                    if t_li_size + next_take_size > exps + oldst:  # 下一个字符在行尾，s用于换行
                        s = True
                        auto_s_ed = True
                    if i+1 == len(image_list):    # 所有字符的最后一个字符
                        s = True
                        auto_s_ed = True
                        
                else:  # 换行符
                    if len(t_li) == 0:
                        if not auto_s_ed:
                            t_li.append({"img": image_list[i]["img"], "chr": None})
                            s = True
                            auto_s_ed = False
                        if auto_s_ed:
                            auto_s_ed = False
                    else:
                        s = True
                        auto_s_ed = False

                if s:    # 换行操作
                    line_img = self.hconcat_images(t_li, vertical, space, style, {"stat": False, "line_space": line_space, "exp_size": exp_size})
                    li.append({"img": line_img, "chr": None})
                    t_li = []
                    t_li_size = 0

            return self.hconcat_images(li, not vertical, space, style, {"stat": False, "line_space": line_space, "exp_size": [line_space]})
            
        else:
            # print("拼图第3种情况")
            return Image.new(color_type,(10,10), default_color)
        
    def fill_image_with_color(self, task_1 = "0", image = Image.new("1", (10,10)), foc = (255, 255, 255, 255), bac = (0, 0, 0, 0)):
        # 创建一个新的彩色图像，模式为RGBA，大小与原图相同
        im = Image.new("RGBA", image.size)
        if task_1 == "0":
            # 将原图的非黑色部分（即白色部分）用指定颜色替换
            for x in range(image.width):
                for y in range(image.height):
                    if image.getpixel((x, y)) != 0:  # 白色部分
                        im.putpixel((x, y), self.color)
                    else:  # 黑色部分，保持透明或设为其他颜色
                        im.putpixel((x, y), (0, 0, 0, 0))  # 这里设置为黑色
        else:
            for x in range(image.width):
                for y in range(image.height):
                    if image.getpixel((x, y)) != 0:
                        im.putpixel((x, y), foc)
                    else:
                        im.putpixel((x, y), bac)
            
        return im

    def create_character(self,vertical=False, roll_asc = False, text="", ch_font_size=16, asc_font_size=16, ch_bold_size_x=2, ch_bold_size_y=1, space=0, scale=100, scale_y = 100, auto_scale=False, scale_sys_font_only=False, new_width = None, new_height = None, y_offset = 0, y_offset_asc = 0, style = [0, 0], multi_line = {"stat":False, "line_space": 0 }):
        try:
            IMAGES = []
            tasks = []
            foc = (255, 255, 255, 255)
            bac = (0, 0, 0, 0)

            if text == "":
                text = " "

            if scale_sys_font_only:
                sscale = scale
                sscale_y = scale_y
            else:
                sscale = 100
                sscale_y = 100

            try:
                coloredstritems = ast.literal_eval(text)
                s = ""
                for coloredstr in coloredstritems:
                    task = [self.find_backtick_strings(coloredstr['char']),coloredstr['foreground'],coloredstr['background']]
                    tasks.append(task)
                    s += coloredstr['char']
                text = s    # 将有颜色的字符串提取出来给缩放部分使用
            except:
                tasks = [[self.find_backtick_strings(text),"0","0"]]  # [任务列表，前景色，背景色]
            # print(tasks)
            for task in tasks:
                # 获取前景色背景色
                if task[1] != "0":
                    tup = (3, 5, 7, 1)
                    fore_col_hex = task[1]
                    if len(task[1]) == 7 :
                        fore_col_hex = "#ff" + fore_col_hex[1:]
                    foc = tuple(int(fore_col_hex[i:i+2], 16) for i in tup)
                    if task[2] != "0":
                        back_col_hex = task[2]
                        if len(task[2]) == 7 :
                            back_col_hex = "#ff" + back_col_hex[1:]
                        bac = tuple(int(back_col_hex[i:i+2], 16) for i in tup)
                    else:
                        bac = (0, 0, 0, 0)

                # print(task)
                # print(self.FontManager.icon_dict.keys())

                for sub_task in task[0]:   # sub_task：剪开了的字符串
                    # print(sub_task)
                    if sub_task in self.FontManager.icon_dict.keys():
                        try:
                            ico = Image.open(self.FontManager.icon_dict[sub_task])
                            if self.color_type == "1":
                                ico = ico.convert('1')
                                ico = ico.point(lambda x: not x)  # 直接反转二值图像
                            elif self.color_type == "RGB":
                                if ico.mode == "1":
                                    ico = ico.point(lambda x: not x)  # 直接反转二值图像
                                    ico = self.fill_image_with_color(task[1], ico, foc, bac)
                                else:
                                    ico = ico.convert("RGBA")
                            icon = {"img": ico, "chr": None}
                            IMAGES.append(icon)
                        except:
                            pass     
                    else:
                        font_tasks = list(sub_task)

                        for chr in font_tasks:
                            this_chr = chr
                            if chr in self.lineBreakChr:
                                chr = " "
                            if chr.isascii():
                                ch = self.ASC_Reader.get_text_bmp(chr,y_offset_asc,asc_font_size,ch_bold_size_x,ch_bold_size_y,sscale,sscale_y)
                            else:
                                ch = self.Ch_Reader.get_text_bmp(chr,y_offset,ch_font_size,ch_bold_size_x,ch_bold_size_y,sscale,sscale_y)

                            if self.color_type == "RGB":
                                ch = self.fill_image_with_color(task[1], ch, foc, bac)

                            if chr.isascii() and vertical and roll_asc:
                                ch = ch.transpose(Image.ROTATE_270)

                            IMAGES.append({"img": ch, "chr": this_chr})
            # 拼接图像
            if new_width is not None and new_height is not None:
                exp_size = [new_width, new_height]
            else:
                exp_size = []
            multi_line["exp_size"] = exp_size
            new_image = self.hconcat_images(IMAGES,vertical,space,style,multi_line)
            img_width = new_image.width
            img_height = new_image.height
            # 缩放图像横向宽度
            if (auto_scale and not scale_sys_font_only) and new_width != None and new_height != None:
                if len(text) <= 2*new_width/new_height and img_width > new_width:
                    new_image = new_image.resize((new_width,int(img_height*scale_y/100)),resample=Image.BOX)
                if len(text) > 2*new_width/new_height and img_width > new_width:
                    new_image = new_image.resize((int(img_width*min(100,(new_height/2)/ch_font_size)),int(img_height*scale_y/100)),resample=Image.BOX)
            if (not auto_scale and not scale_sys_font_only):
                new_image = new_image.resize((int(img_width*scale/100),int(img_height*scale_y/100)),resample=Image.BOX)
        except Exception as e:
            print(f"BmpCreater.create_character():{e}")
            new_image = Image.new(self.color_type, (16,16))
        # 保存图像
        return new_image
    
if __name__ == "__main__":
    # t = "[{'char': '在本文中，', 'foreground': '#ffffff', 'background': '0'}, {'char': '我们', 'foreground': '#ffab81', 'background': '0'}, {'char': '介绍了', 'foreground': '#75ffca', 'background': '0'}, {'char': '四种', 'foreground': '#395dff', 'background': '0'}, {'char': '将单个文件', 'foreground': '#ffffff', 'background': '0'}, {'char': '恢复到', 'foreground': '#ff40b6', 'background': '0'}, {'char': '以前版本', 'foreground': '#ffff00', 'background': '0'}, {'char': '的方法', 'foreground': '#ffffff', 'background': '0'}]"
    # t = '\n\n换行测试\n测试开始\n第一项：\n第二项：\n\n第三项：\n测试文本\n第四项：\n测试文本\n\n第五项：\n测试文本\n\n\n第六项：\n测试文本测试文本\n第七项：\n测试文本测试文本\n\n第八项：\n测试文本测试文本\n\n\n测试结束\n\n'
    t = "Hello World!"
#     t = '''\n\n　！＂＃＄％＆＇（）＊＋，－．／\n\n
# ０１２３４５６７８９：；＜＝＞？
# ＠ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯ
# ＰＱＲＳＴＵＶＷＸＹＺ［＼］＾＿
# ｀ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏ
# ｐｑｒｓｔｕｖｗｘｙｚ｛｜｝～　'''
    ch_font="宋体"
    asc_font="14 px"
    FontCreater = BmpCreater(Manager=FontManager(),color_type="RGB",color=(255,255,0),ch_font=ch_font,asc_font=asc_font,only_sysfont = 1, klscale=True)
    font_img = FontCreater.create_character(vertical=False, roll_asc = False, text=t, ch_font_size=24, asc_font_size=16, ch_bold_size_x=1, ch_bold_size_y=1, space=0, scale=80, scale_y=100, auto_scale=False, scale_sys_font_only=True, new_width = 128, new_height = 32, y_offset = 0, y_offset_asc = 0, style = [-1,0], multi_line = {"stat":True, "line_space": 1.0 })
    font_img.save("混合字体测试生成.bmp")

# 欢迎使用音乐播放器 真正的“电脑爱好者”都应该用自动播放而不是第三方弹窗。[doge][doge]
# 一二三亖-=_欢迎无障碍0123456789 My life花儿尽情地开吧
# 铁皮青蛙提醒你sｄ¶ｆｅｉj：工人先锋号，青年文明号无障碍客车0123456789开过来了gj
