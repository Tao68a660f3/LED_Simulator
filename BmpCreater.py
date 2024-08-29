from PIL import Image, ImageDraw, ImageFont, ImageChops
# import numpy as np
import binascii, re#, freetype

class ASC_font_Reader():
    def __init__(self,relative_path,font_path):
        self.font_path = font_path
        self.font_path = relative_path + self.font_path
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
    def __init__(self,relative_path,fontBmpPath):
        self.fontBmpPath = fontBmpPath
        self.fontBmpPath = relative_path + self.fontBmpPath
        self.fnt_img = Image.open(self.fontBmpPath)
        # print(self.fontBmpPath)
        self.ascii_size = [int(fontBmpPath.split(".")[-2].split("_")[1].split("-")[0]),int(fontBmpPath.split(".")[-2].split("_")[1].split("-")[1])]

    def get_text_bmp(self,asc,y_offset=0,*not_used_argv):
        value = ord(asc)
        x = value%16
        y = value//16
        ch = self.fnt_img.crop((x*self.ascii_size[0],y*self.ascii_size[1],(x+1)*self.ascii_size[0],(y+1)*self.ascii_size[1]))
        ch = ImageChops.invert(ch)
        ch = ch.convert('1')
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

            r = r+2 if r+2 <= self.ascii_size[0] else r+1
        else:
            l = 0
            r = self.ascii_size[0]

        ch = ch.crop((l,y_offset,r,ch.height+y_offset))

        return ch

class HZK_Font_Reader():
    def __init__(self,relative_path,fontPath):
        self.fontPath = fontPath
        self.fontPath = relative_path + self.fontPath
        self.KEYS = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]

    def get_char_map(self,text):
        rect_list = [[] for _ in range(16)]
        try:
            gb2312 = text.encode('gb2312')
        except:
            gb2312 = "　".encode('gb2312')
        hex_str = binascii.b2a_hex(gb2312)
        result = str(hex_str, encoding='utf-8')
        area = int('0x' + result[:2],16) - 0xA0
        index = int('0x' + result[2:],16) - 0xA0
        offset = (94 * (area-1) + (index-1)) * 32
        font_rect = None
        with open(self.fontPath, "rb") as f:
            f.seek(offset)
            font_rect = f.read(32)
        for k in range(len(font_rect) // 2):
            row_list = rect_list[k]
            for j in range(2):
                for i in range(8):
                    asc = font_rect[k * 2 + j]
                    flag = 1 if asc & self.KEYS[i] else 0
                    row_list.append(flag)
                    
        return rect_list
        
    def make_text_bmp(self,fontData,y_offset):
        image_data = [255 if pixel == 1 else 0 for row in fontData for pixel in row]
        image = Image.new("1", (16, 16))
        image.putdata(image_data)
        image = image.crop((0,y_offset,image.width,y_offset+image.height))
        return image
        
    def get_text_bmp(self,text,y_offset = 0,*not_used_argv):
        return self.make_text_bmp(self.get_char_map(text),y_offset)

class Sys_Font_Reader():
    def __init__(self,font_path):
        self.font = None
        self.font_path = font_path

    def is_Chinese(self,word):
        for ch in word:
            if '\u4e00' <= ch <= '\u9fff':
                return True
        return False

    def get_text_bmp(self,text,y_offset=0,font_size=16,xb=1,yb=1,scale=100):
        try:
            self.font = ImageFont.truetype(self.font_path, font_size)
        except:    # 字体打不开时暂时用宋体代替
            self.font = ImageFont.truetype("simsun", font_size)
        x_offseted_font = {"arial":2,"ARIALN":1,}
        scaled_font = {"FZYTK":72,}
        extra_size = int(0.2*font_size) if text.isascii() else 0
        s = text
        s = "█| "+s+" |█"
        ss = "█|  |█"

        # 创建一个Image对象
        image = Image.new("1", (1, 1))  # 1-bit image (black and white)
        draw = ImageDraw.Draw(image)
        # 计算文本的宽度和高度
        bbox = draw.textbbox((0, 0), s, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        # 多余的宽度
        bbox = draw.textbbox((0, 0), ss, font=self.font)
        delta_width = int((bbox[2] - bbox[0])*0.5)
        # delta_height = font_size-text_height

        offset = int(0.5*font_size)+int(0.5*extra_size)
        # print(s,offset,font_size,text_height,delta_y)
 
        image = Image.new("1", (text_width-2*delta_width, font_size+extra_size))#
        # 获取新的Draw对象
        draw = ImageDraw.Draw(image)

        for fnt in x_offseted_font.keys():
            if fnt in self.font_path:
                delta_width = delta_width - x_offseted_font[fnt]
        # 设置字体，绘制文本，加粗
        for i in range(xb):
            for j in range(yb):
                draw.text((i-delta_width, j+offset-y_offset), s, font=self.font, fill=1, anchor="lm")

        for fnt in scaled_font.keys():
            if fnt in self.font_path and self.is_Chinese(text):
                image = image.crop((int(image.width*(1-scaled_font[fnt]/100)*0.5),0,int(image.width*(1-(1-scaled_font[fnt]/100)*0.5)),image.height))

        ########################################
        # for x in range(image.width):
        #     print(int(delta_height/2),int(delta_height/2)+text_height-1)
        #     # x=0
        #     if int(delta_height/2) > 0:
        #         image.putpixel((x, int(delta_height/2)), 1)
        #     if int(delta_height/2)+text_height-1 < image.height:
        #         image.putpixel((x, int(delta_height/2)+text_height-1), 1)
        ########################################

        image = image.resize((int(image.width*scale/100),image.height),resample=Image.LANCZOS)

        return image
    
class FontManager():
    def __init__(self):
        self.font_info = {"./resources/font.info"}
        self.icon_info = {"./resources/icon.info"}
        self.font_dict = dict()
        self.icon_dict = dict()  # 字体和图标均不可重名
        self.flush_resources()

    def flush_resources(self):
        self.get_font_list()
        self.get_icon_list()

    def get_font_list(self):
        for font_info in self.font_info:
            with open(font_info,"r",encoding="utf-8") as f:
                file = f.readlines()
                folder = ""
                for i in range(len(file)):
                    if file[i].startswith("FONT"):
                        folder = file[i].split(",")[2][4:]
                    else:
                        font_file = file[i].split(",")[0]
                        font_name = file[i].split(",")[1]
                        self.font_dict[font_name] = folder+font_file
        # print(self.font_dict)

    def get_icon_list(self):
        for icon_info in self.icon_info:
            with open(icon_info,"r",encoding="utf-8") as f:
                file = f.readlines()
                folder = ""
                for i in range(len(file)):
                    if file[i].startswith("ICON"):
                        folder = file[i].split(",")[2][4:]
                    else:
                        icon_name = '`'+file[i].split(",")[0]+'`'
                        icon_file = file[i].split(",")[1]
                        self.icon_dict[icon_name] = folder+icon_file
        # print(self.icon_dict)

class BmpCreater():
    # 显示屏组件编写时，让图片默认位置是水平竖直均居中，如果横向滚动，竖直居中，竖直滚动，水平居中！
    # color_type:"RGB"和"1"两种
    def __init__(self,Manager=FontManager(),color_type="RGB",color=(255,255,255),ch_font="",asc_font="",only_sysfont = False,relative_path = ""):
        self.FontManager = Manager
        self.only_sysfont = only_sysfont
        self.relative_path = relative_path
        self.ch_font = self.FontManager.font_dict[ch_font]
        self.asc_font = self.FontManager.font_dict[asc_font]
        self.color_type = color_type
        self.color = (color[0],color[1],color[2])

        asc_font_type = self.asc_font.split(".")[-1].lower()
        ch_font_type = self.ch_font.split(".")[-1].lower()
        # if not self.only_sysfont:
        if asc_font_type == "font":
            self.ASC_Reader = ASC_font_Reader(self.relative_path,self.asc_font)
        elif asc_font_type == "bmp":
            self.ASC_Reader = ASC_Bmp_Reader(self.relative_path,self.asc_font)
        else:
            self.ASC_Reader = Sys_Font_Reader(self.asc_font)
        if ch_font_type == "bin":
            self.Ch_Reader = HZK_Font_Reader(self.relative_path,self.ch_font)
        else:
            self.Ch_Reader = Sys_Font_Reader(self.ch_font)

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

    def hconcat_images(self,image_list = [], vertical = False, space = 1, style = 0):
        # style: -1,0,1，对齐方式
        if len(image_list) == 0:
            return Image.new(self.color_type,(10,10))
        if not vertical:
            # 计算所有图像的最大高度和宽度之和
            total_height = max(image.height for image in image_list)
            total_width = sum(image.width for image in image_list)
            # 创建一个新的图像作为画布，背景为白色
            new_image = Image.new(self.color_type, (total_width+space*(len(image_list)-1), total_height))
        else:
            total_height = sum(image.height for image in image_list)
            total_width = max(image.width for image in image_list)
            new_image = Image.new(self.color_type, (total_width, total_height+space*(len(image_list)-1)))        
        # 在新图像上依次粘贴每个图像
        x_offset = 0
        y_offset = 0
        if style > 0:
            k = 0
        elif style == 0:
            k = 0.5
        else:
            k = 1
        for image in image_list:
            if vertical:
                x_offset = int(k*(total_width-image.width))
            else:
                y_offset = int(k*(total_height-image.height))
            # 计算每个图像粘贴的位置，使其顶部对齐
            new_image.paste(image, (x_offset, y_offset))
            if not vertical:
                x_offset += image.width
                x_offset += space
            else:
                y_offset += image.height
                y_offset += space        
        return new_image

    def create_character(self,vertical=False, roll_asc = False, text="", ch_font_size=16, asc_font_size=16, ch_bold_size_x=2, ch_bold_size_y=1, space=0, scale=100, auto_scale=False, scale_sys_font_only=False, new_width = None, new_height = None, y_offset = 0, y_offset_asc = 0, style = 0):
        IMAGES = []
        tasks = self.find_backtick_strings(text)
        for task in tasks:
            if task in self.FontManager.icon_dict.keys():
                ico = Image.open(self.relative_path+self.FontManager.icon_dict[task])
                if self.color_type == "1":
                    ico = ImageChops.invert(ico)
                    ico = ico.convert('1')
                IMAGES.append(ico)
            else:
                font_tasks = list(task)
                for chr in font_tasks:
                    if chr.isascii():
                        ch = self.ASC_Reader.get_text_bmp(chr,y_offset_asc,asc_font_size,ch_bold_size_x,ch_bold_size_y,100)
                    else:
                        if scale_sys_font_only:
                            sscale = scale
                        else:
                            sscale = 100
                        ch = self.Ch_Reader.get_text_bmp(chr,y_offset,ch_font_size,ch_bold_size_x,ch_bold_size_y,sscale)

                    if self.color_type == "RGB":
                        # 创建一个新的彩色图像，模式为RGB，大小与原图相同
                        cch = Image.new("RGB", ch.size, self.color)                        
                        # 将原图的非黑色部分（即白色部分）用指定颜色替换
                        for x in range(ch.width):
                            for y in range(ch.height):
                                if ch.getpixel((x, y)) != 0:  # 白色部分
                                    cch.putpixel((x, y), self.color)
                                else:  # 黑色部分，保持透明或设为其他颜色
                                    cch.putpixel((x, y), (0, 0, 0))  # 这里设置为黑色
                        ch = cch

                    if chr.isascii() and vertical and roll_asc:
                        ch = ch.transpose(Image.ROTATE_270)

                    IMAGES.append(ch)
        # 拼接图像
        new_image = self.hconcat_images(IMAGES,vertical,space,style)
        img_width = new_image.width
        img_height = new_image.height
        # 缩放图像横向宽度
        if (auto_scale and not scale_sys_font_only) and new_width != None and new_height != None:
            if len(text) <= 2*new_width/new_height and img_width > new_width:
                new_image = new_image.resize((new_width,img_height),resample=Image.LANCZOS)
            if len(text) > 2*new_width/new_height and img_width > new_width:
                new_image = new_image.resize((int(img_width*(new_height/2)/ch_font_size),img_height),resample=Image.LANCZOS)
        if (not auto_scale and not scale_sys_font_only):
            new_image = new_image.resize((int(img_width*scale/100),img_height),resample=Image.LANCZOS)
        # 保存图像
        return new_image
    
if __name__ == "__main__":
    ch_font="微软雅黑"
    asc_font=ch_font
    FontCreater = BmpCreater(Manager=FontManager(),color_type="RGB",color=(255,200,0),ch_font=ch_font,asc_font=asc_font,only_sysfont = 1,relative_path = "")
    font_img = FontCreater.create_character(vertical=0, roll_asc = False, text="`wheelchair32x32`铁皮青蛙提helloworld醒你sｄ¶ｆｅｉj：工人先锋号，青年文明号无障碍客车0123456789开过来了gj", ch_font_size=20, asc_font_size=24, ch_bold_size_x=1, ch_bold_size_y=1, space=0, scale=100, auto_scale=0, scale_sys_font_only=1, new_width = 120, new_height = 32, y_offset = 1, y_offset_asc = 0, style = 0)
    font_img.save("混合字体测试生成.bmp")

# 欢迎使用音乐播放器 真正的“电脑爱好者”都应该用自动播放而不是第三方弹窗。[doge][doge]
# 一二三亖-=_欢迎无障碍0123456789 My life花儿尽情地开吧
# 铁皮青蛙提醒你sｄ¶ｆｅｉj：工人先锋号，青年文明号无障碍客车0123456789开过来了gj