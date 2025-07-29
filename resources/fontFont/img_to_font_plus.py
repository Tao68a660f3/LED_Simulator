from PIL import Image
import numpy as np

class ASC_file_writer:
    def __init__(self, bitmap_height=24):
        self.bitmap_height = bitmap_height  # 通常是24像素高
        
    def image_to_hex(self, image, ascii_value=35, auto_width = False):  # 默认ASCII值为35 (#)
        """
        将图像转换为十六进制格式
        :param image: PIL Image对象，应该是二值图像（黑白）
        :param ascii_value: ASCII字符值
        :return: (width, hex_values)
        """
        # 确保图像是二值图像
        if image.mode != '1':
            image = image.convert('1')
            
        # 获取图像尺寸
        width = image.width
        height = image.height

        chr_width = width
        stt = 0
        
        # 确保高度正确
        if height != self.bitmap_height:
            raise ValueError(f"图像高度必须是{self.bitmap_height}像素")
            
        # 将图像转换为numpy数组（0和1）
        img_array = np.array(image)
        
        # 计算需要多少字节来存储宽度（向上取整到8的倍数）
        bytes_per_row = (width + 7) // 8
        
        # 初始化结果数组
        hex_values = []

        # 自动确认宽度
        if auto_width:
            x1, x2 = 0, 0
            flag = True
            for col in range(width):
                for row in range(height):
                    if img_array[row][width - col - 1] == 0:
                        x2 = width - col
                        flag = False
                        break
                if not flag:
                    break
            flag = True
            for col in range(width):
                for row in range(height):
                    if img_array[row][col] == 0:
                        x1 = col
                        flag = False
                        break
                if not flag:
                    break
            tmp = x2 - x1
            if tmp > 0:
                chr_width = tmp
                stt = x1
            else:
                chr_width = int(0.25 * width)
        
        # 对每一行进行处理
        for row in range(height):
            byte_value = 0
            bit_count = 0
            
            # 处理这一行的每个像素
            for col in range(stt % 8, bytes_per_row * 8):
                # 将位值左移
                byte_value = (byte_value << 1)
                
                if col < width:
                    # 如果是黑色像素（值为0），设置相应的位
                    if img_array[row][col] == 0:
                        byte_value |= 1
                    
                bit_count += 1
                
                # 当积累了8位或达到行末时，保存字节
                if bit_count == 8 or col == bytes_per_row * 8 - 1:
                    # 如果是行末且未满8位，左移剩余的位
                    if col == bytes_per_row * 8 - 1 and bit_count < 8:
                        byte_value = byte_value << (8 - bit_count)
                    
                    # 与ASCII值异或
                    byte_value = byte_value ^ ascii_value
                    hex_values.append(byte_value)
                    
                    # 重置为下一个字节
                    byte_value = 0
                    bit_count = 0
        
        return chr_width, hex_values
    
    def generate_font_string(self, image, ascii_value=35, auto_width = False):
        """
        生成与原格式匹配的字符串输出
        """
        width, hex_values = self.image_to_hex(image, ascii_value, auto_width)
        
        # 构建输出字符串
        output = []
        output.append(f"{ascii_value},")
        output.append(f"{width},")
        
        # 构建十六进制值字符串
        hex_str = ','.join(f"0x{x:02x}" for x in hex_values)
        output.append(f"{hex_str},")
        
        return '\n'.join(output)

def main():
    title = "ASC1616"
    w,h = 16,16
    bmp_file = './resources/bmpfont/ASCII_16-16_10.bmp'
    auto_width = False
    
    bmp_file = input("输入bmp图像路径（如./resources/bmpfont/ASCII_16-16_10.bmp，不需要引号）:")
    title = input("输入字体名称（如ASC1616）:")
    w = int(input("输入方格宽度:"))
    h = int(input("输入方格高度:"))
    _auto = input("自动字符宽度?(y/n):")
    if _auto.lower() == "y":
        auto_width = True
    # 创建转换器实例
    converter = ASC_file_writer(h)

    font_img = Image.open(bmp_file)

    asc = 48

    # # 读取测试图像
    # test_image = font_img.crop(((asc%16)*w-1,(asc//16)*h,(asc%16)*w-1+w,(asc//16)*h+h))

    # # 生成字符串
    # result = converter.generate_font_string(test_image, ascii_value=asc, auto_width=auto_width)
    # print(result)

    with open(f"{title}.font", "w", encoding = "ansi") as f:
        f.write(f"{title},\n")
        f.write(f"{(w + 7) // 8 * 8},{h},\n")
        for asc in range(128):
            image = font_img.crop(((asc%16)*w,(asc//16)*h,(asc%16)*w+w,(asc//16)*h+h))
            result = converter.generate_font_string(image, ascii_value=asc, auto_width=auto_width)
            f.write(f"{result}\n")

    f.close()
    
    print(f"转换成功：{title}.font\n")

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(e)
