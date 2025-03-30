from PIL import Image
import numpy as np

class ASC_file_writer:
    def __init__(self, bitmap_height=24):
        self.bitmap_height = bitmap_height  # 通常是24像素高
        
    def image_to_hex(self, image, ascii_value=35):  # 默认ASCII值为35 (#)
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
        
        # 确保高度正确
        if height != self.bitmap_height:
            raise ValueError(f"图像高度必须是{self.bitmap_height}像素")
            
        # 将图像转换为numpy数组（0和1）
        img_array = np.array(image)
        
        # 计算需要多少字节来存储宽度（向上取整到8的倍数）
        bytes_per_row = (width + 7) // 8
        
        # 初始化结果数组
        hex_values = []
        
        # 对每一行进行处理
        for row in range(height):
            byte_value = 0
            bit_count = 0
            
            # 处理这一行的每个像素
            for col in range(width):
                # 将位值左移
                byte_value = (byte_value << 1)
                
                # 如果是黑色像素（值为0），设置相应的位
                if img_array[row][col] == 0:
                    byte_value |= 1
                    
                bit_count += 1
                
                # 当积累了8位或达到行末时，保存字节
                if bit_count == 8 or col == width - 1:
                    # 如果是行末且未满8位，左移剩余的位
                    if col == width - 1 and bit_count < 8:
                        byte_value = byte_value << (8 - bit_count)
                    
                    # 与ASCII值异或
                    byte_value = byte_value ^ ascii_value
                    hex_values.append(byte_value)
                    
                    # 重置为下一个字节
                    byte_value = 0
                    bit_count = 0
        
        return width, hex_values
    
    def generate_font_string(self, image, ascii_value=35):
        """
        生成与原格式匹配的字符串输出
        """
        width, hex_values = self.image_to_hex(image, ascii_value)
        
        # 构建输出字符串
        output = []
        output.append(f"{ascii_value},")
        output.append(f"{width},")
        
        # 构建十六进制值字符串
        hex_str = ','.join(f"0x{x:02x}" for x in hex_values)
        output.append(f"{hex_str},")
        
        return '\n'.join(output)

if __name__ == "__main__":
    title = "ASC1616"
    w,h = 16,16
    # 创建转换器实例
    converter = ASC_file_writer(h)

    font_img = Image.open('./resources/bmpfont/ASCII_16-16_10.bmp')

    asc = 32

    # 读取测试图像
    test_image = font_img.crop(((asc%16)*w-1,(asc//16)*h,(asc%16)*w-1+w,(asc//16)*h+h))

    # 生成字符串
    result = converter.generate_font_string(test_image, ascii_value=asc)
    print(result)

    with open(f"{title}.font", "w", encoding = "ansi") as f:
        f.write(f"{title}\n")
        f.write(f"{w},{h},\n")
        for asc in range(128):
            image = font_img.crop(((asc%16)*w,(asc//16)*h,(asc%16)*w-1+w,(asc//16)*h+h))
            result = converter.generate_font_string(image, ascii_value=asc)
            f.write(f"{result}\n")

    f.close()