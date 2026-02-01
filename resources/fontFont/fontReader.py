from PIL import Image
import struct

font_path = "./resources/fontFont/ASC1608.font"
bin_fon_path = "./resources/fontFont/MY_FONT.BIN"
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

def export_to_custom_bin(reader, output_path):
    # 1. 获取基本参数
    h = reader.bitmap_size[1]
    max_w = max(reader.font_hex_list[i][0] for i in range(len(reader.font_hex_list)))
    # 计算每个字符占用的字节数 (比如 16x8 就是 16字节)
    bytes_per_char = h * ((max_w + 7) // 8)

    print(f"正在转换字体: 高度={h}, 最大宽度={max_w}, 每字符字节={bytes_per_char}")

    with open(output_path, "wb") as f:
        # --- A. 写入 Header (16字节) ---
        f.write(b'FONT')  # Magic Number
        # <BBH 代表: 1字节高度, 1字节宽, 2字节(uint16)每字符字节数
        f.write(struct.pack('<BBH', h, max_w, bytes_per_char)) 
        f.write(b'\x00' * 8) # 预留位填充

        # --- B. 写入宽度表 (256字节) ---
        # 遍历 0-255，取出 reader.font_hex_list 里的宽度
        widths = [min(max_w, reader.font_hex_list[i][0]) for i in range(256)]
        f.write(bytearray(widths))

        # --- C. 写入点阵数据 (256 * bytes_per_char) ---
        for i in range(256):
            # 获取解密后的数据 (直接在这里做 ^ i)
            raw_data = reader.font_hex_list[i][1]
            decrypted_data = [b ^ i for b in raw_data]
            f.write(bytearray(decrypted_data))

    print(f"转换完成！文件保存至: {output_path}")

def verify_font_bin(bin_path, test_chars="!W$38"):
    try:
        with open(bin_path, "rb") as f:
            # 1. 解析 Header (16字节)
            header = f.read(16)
            if len(header) < 16 or header[0:4] != b'FONT':
                print("错误: 不是有效的 FONT 文件")
                return

            # <BBH: 1字节高度, 1字节最大宽, 2字节每字符字节数
            height, actual_max_w, bpc = struct.unpack('<BBH', header[4:8])
            
            # 计算每一行占用多少字节 (关键！)
            row_stride = (actual_max_w + 7) // 8
            
            print(f"--- 字库验证信息 ---")
            print(f"高度: {height} px | 最大宽: {actual_max_w} px")
            print(f"每行跨度: {row_stride} 字节 | 总字节/字符: {bpc}")
            print("-" * 30)

            # 2. 读取宽度表 (256字节)
            width_table = list(f.read(256))

            # 3. 验证测试字符
            for char in test_chars:
                ascii_code = ord(char)
                char_w = width_table[ascii_code]
                
                # 计算寻址偏移
                offset = 16 + 256 + (ascii_code * bpc)
                f.seek(offset)
                char_data = f.read(bpc)

                print(f"\n字符: '{char}' (ASCII: {ascii_code}), 实际宽度: {char_w} px")
                
                # 4. 逐行打印点阵
                for h_idx in range(height):
                    line_str = ""
                    # 拿到这一行的字节数据块
                    row_data_bytes = char_data[h_idx * row_stride : (h_idx + 1) * row_stride]
                    
                    # 遍历该字符的有效像素列
                    for col_idx in range(char_w):
                        # 计算当前列属于这一行的第几个字节，以及位偏移
                        byte_pos = col_idx // 8
                        bit_pos = 7 - (col_idx % 8)
                        
                        if row_data_bytes[byte_pos] & (1 << bit_pos):
                            line_str += "* " # 命中的像素
                        else:
                            line_str += "  " # 空白
                    print(line_str)
                    
    except FileNotFoundError:
        print(f"错误: 找不到文件 {bin_path}")

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
    # create_ascii_str(ascii_str)
    export_to_custom_bin(FileReader, bin_fon_path)
    verify_font_bin(bin_fon_path, test_chars="Hello world!")


