from PIL import Image, ImageDraw, ImageFont
# import numpy as np
import binascii, re, os, ast #, freetype

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
        f = open(self.fontPath, "rb")
        f.close()
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
        scaled_font = {"FZYTK":72,}
        extra_size = int(0.2*font_size) if text.isascii() else 0  # 加高ASCII字体以防止字符不完整
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

        image = Image.new("1", (text_width-delta_width, font_size+extra_size))
        # 获取新的Draw对象
        draw = ImageDraw.Draw(image)

        # 设置字体，绘制文本，加粗
        for i in range(xb):
            for j in range(yb):
                draw.text((i-delta_width, j+offset-y_offset+(-adjusted_height[0]+adjusted_height[1])), s, font=self.font, fill=1, anchor="lm")

        for fnt in scaled_font.keys():
            if fnt in self.font_path and self.is_Chinese(text):
                image = image.crop((int(image.width*(1-scaled_font[fnt]/100)*0.5),0,int(image.width*(1-(1-scaled_font[fnt]/100)*0.5)),image.height))

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
                pattern = re.compile(r".*?,.*?,")
                for i in range(len(file)):
                    if file[i].startswith("ICON"):
                        folder = file[i].split(",")[2][4:]
                        # print(folder,icon_info)
                        if folder.lower() == "default":
                            folder = os.path.dirname(icon_info)
                    else:
                        match_result = pattern.match(file[i])[0]
                        icon_name = '`'+match_result.split(",")[0]+'`'
                        icon_file = match_result.split(",")[1]
                        self.icon_dict[icon_name] = os.path.join(folder,icon_file)
                        # print(icon_file,self.icon_dict[icon_name])
        # print(self.icon_dict)

class BmpCreater():
    # 显示屏组件编写时，让图片默认位置是水平竖直均居中，如果横向滚动，竖直居中，竖直滚动，水平居中！
    # color_type:"RGB"和"1"两种
    def __init__(self,Manager=FontManager(),color_type="RGB",color=(255,255,255),ch_font="",asc_font="",only_sysfont = False,relative_path = ""):
        self.FontManager = Manager
        self.only_sysfont = only_sysfont
        self.relative_path = relative_path
        try:
            self.ch_font = self.FontManager.font_dict[ch_font]
        except:
            self.ch_font = self.FontManager.font_dict["宋体"]
        try:
            self.asc_font = self.FontManager.font_dict[asc_font]
        except:
            self.asc_font = self.FontManager.font_dict["宋体"]
        self.color_type = color_type
        self.color = (color[0],color[1],color[2],255)

        asc_font_type = self.asc_font.split(".")[-1].lower()
        ch_font_type = self.ch_font.split(".")[-1].lower()
        # if not self.only_sysfont:
        try:
            if asc_font_type == "font":
                self.ASC_Reader = ASC_font_Reader(self.relative_path,self.asc_font)
            elif asc_font_type == "bmp":
                self.ASC_Reader = ASC_Bmp_Reader(self.relative_path,self.asc_font)
            else:
                self.ASC_Reader = Sys_Font_Reader(self.asc_font)
        except:
            self.ASC_Reader = Sys_Font_Reader(self.asc_font)
        try:
            if ch_font_type == "bin":
                self.Ch_Reader = HZK_Font_Reader(self.relative_path,self.ch_font)
            else:
                self.Ch_Reader = Sys_Font_Reader(self.ch_font)
        except:
            self.Ch_Reader = Sys_Font_Reader(self.asc_font)  

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
            for i in range(len(image_list)):
                if not vertical:    # 水平排列分成多行
                    current_size = image_list[i]["img"].width
                else:    # 垂直排列为多列
                    current_size = image_list[i]["img"].height

                # print(i)

                if t_li_size < exps and image_list[i]["chr"] not in ["\n","\u2029"]:
                    t_li.append({"img": image_list[i]["img"], "chr": None})
                    t_li_size += current_size
                    if space > 0:
                        t_li_size += space
                    elif space >= -100:
                        v = t_li_size + int(current_size * (space / 100))
                        if v > 0:
                            t_li_size = v

                if t_li_size + current_size > exps or i+1 == len(image_list) or image_list[i]["chr"] in ["\n","\u2029"]:
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

    def create_character(self,vertical=False, roll_asc = False, text="", ch_font_size=16, asc_font_size=16, ch_bold_size_x=2, ch_bold_size_y=1, space=0, scale=100, auto_scale=False, scale_sys_font_only=False, new_width = None, new_height = None, y_offset = 0, y_offset_asc = 0, style = [0, 0], multi_line = {"stat":False, "line_space": 0 }):
        IMAGES = []
        tasks = []
        foc = (255, 255, 255, 255)
        bac = (0, 0, 0, 0)

        if text == "":
            text = " "

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
                        ico = Image.open(self.relative_path+self.FontManager.icon_dict[sub_task])
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
                        if chr.isascii():
                            ch = self.ASC_Reader.get_text_bmp(chr,y_offset_asc,asc_font_size,ch_bold_size_x,ch_bold_size_y,100)
                        else:
                            if scale_sys_font_only:
                                sscale = scale
                            else:
                                sscale = 100
                            ch = self.Ch_Reader.get_text_bmp(chr,y_offset,ch_font_size,ch_bold_size_x,ch_bold_size_y,sscale)

                        if self.color_type == "RGB":
                            ch = self.fill_image_with_color(task[1], ch, foc, bac)

                        if chr.isascii() and vertical and roll_asc:
                            ch = ch.transpose(Image.ROTATE_270)

                        IMAGES.append({"img": ch, "chr": chr})
        # 拼接图像
        if new_width != None and new_height != None and not auto_scale:
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
                new_image = new_image.resize((new_width,img_height),resample=Image.BOX)
            if len(text) > 2*new_width/new_height and img_width > new_width:
                new_image = new_image.resize((int(img_width*(new_height/2)/ch_font_size),img_height),resample=Image.BOX)
        if (not auto_scale and not scale_sys_font_only):
            new_image = new_image.resize((int(img_width*scale/100),img_height),resample=Image.BOX)
        # 保存图像
        return new_image
    
if __name__ == "__main__":
    # t = "[{'char': '在本文中，', 'foreground': '#ffffff', 'background': '0'}, {'char': '我们', 'foreground': '#ffab81', 'background': '0'}, {'char': '介绍了', 'foreground': '#75ffca', 'background': '0'}, {'char': '四种', 'foreground': '#395dff', 'background': '0'}, {'char': '将单个文件', 'foreground': '#ffffff', 'background': '0'}, {'char': '恢复到', 'foreground': '#ff40b6', 'background': '0'}, {'char': '以前版本', 'foreground': '#ffff00', 'background': '0'}, {'char': '的方法', 'foreground': '#ffffff', 'background': '0'}]"
    t = "西四丁字街"
    ch_font="宋体"
    asc_font="Arial"
    FontCreater = BmpCreater(Manager=FontManager(),color_type="RGB",color=(255,255,0),ch_font=ch_font,asc_font=asc_font,only_sysfont = 1,relative_path = "")
    font_img = FontCreater.create_character(vertical=False, roll_asc = False, text=t, ch_font_size=24, asc_font_size=24, ch_bold_size_x=1, ch_bold_size_y=1, space=0, scale=100, auto_scale=True, scale_sys_font_only=0, new_width = 80, new_height = 32, y_offset = 0, y_offset_asc = 0, style = [0,0], multi_line = {"stat":False, "line_space": 1.1 })
    font_img.save("混合字体测试生成.bmp")

# 欢迎使用音乐播放器 真正的“电脑爱好者”都应该用自动播放而不是第三方弹窗。[doge][doge]
# 一二三亖-=_欢迎无障碍0123456789 My life花儿尽情地开吧
# 铁皮青蛙提醒你sｄ¶ｆｅｉj：工人先锋号，青年文明号无障碍客车0123456789开过来了gj