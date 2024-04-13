import binascii
from PIL import Image

fontName = "hzk16s.bin"
gbk_str = "繁體字測試。欢迎乘坐２００路外环无人售票车！"
imglist = []

#-----------------------------------------------------------------

class HZK_FontReader():
    def __init__(self,fontPath):
        self.fontPath = fontPath
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
        
    def make_text_bmp(self,fontData):
        image_data = [255 if pixel == 1 else 0 for row in fontData for pixel in row]
        image = Image.new("1", (16, 16))
        image.putdata(image_data)
        return image
        
    def get_text_bmp(self,text):
        return(self.make_text_bmp(self.get_char_map(text)))
        
#-----------------------------------------------------------------
        
def hconcat_images(image_list,space):
    if len(image_list) == 0:
        return Image.new("1",(1,1))
    # 计算所有图像的最大高度和宽度之和
    max_height = max(image.height for image in image_list)
    total_width = sum(image.width for image in image_list)
    
    # 创建一个新的图像作为画布，背景为白色
    new_image = Image.new('1', (total_width+space*(len(image_list)-1), max_height))
    
    # 在新图像上依次粘贴每个图像
    x_offset = 0
    for image in image_list:
        # 计算每个图像粘贴的位置，使其顶部对齐
        y_offset = 0
        new_image.paste(image, (x_offset, y_offset))
        x_offset += image.width
        x_offset += space
    
    return new_image
        
if __name__ == "__main__":
    hzkReader = HZK_FontReader(fontName)
    for c in gbk_str:
        imglist.append(hzkReader.get_text_bmp(c))
    new_image = hconcat_images(imglist,0)
    new_image.save("测试生成.bmp")
    print(f"生成完毕，{gbk_str}，保存为\"测试生成.bmp\"")
        