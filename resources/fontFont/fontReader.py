from PIL import Image

font_path = "D:/Documents/NewCode/bmpfont/公交车路牌_V2.0_developing/resources/fontFont/ASC2010.font"
ascii_str = "=>>Hello World, New Font! I have a great story to tell you! 0123456789 Bus Terminal"
imglist = []

#-----------------------------------------------------------------
class ASC_file_reader():
    def __init__(self,font_path = "./ASC2412.font"):
        self.font_path = font_path
        self.font_hex_list = []
        self.bitmap_size = [0,0]
        self.preReadFontData()

    def preReadFontData(self):
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

    def findSingleAscii(self,asc):
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
        image = image.crop((-1,0,data[0],self.bitmap_size[1]))
        return image

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

def create_ascii_str(string):
    for c in ascii_str:
        imglist.append(FileReader.findSingleAscii(c))
    new_image = hconcat_images(imglist,0)
    new_image.save("测试生成.bmp")

if __name__ == "__main__":
    FileReader = ASC_file_reader(font_path)
    create_ascii_str(ascii_str)

