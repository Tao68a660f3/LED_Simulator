import os
import sys
from PIL import Image

def convert_images_to_hzk16(image_folder, output_file):
    """
    将有序的单色位图序列转换为HZK16字库文件
    
    参数:
        image_folder: 包含有序位图的文件夹
        output_file: 输出的HZK16字库文件路径
    """
    # 每个字符在图片中的位置和大小
    char_width = 16
    char_height = 16
    chars_per_row = 8  # 每行8个字
    rows_per_image = 2  # 每张图片2行
    
    # 初始化GB2312编码
    zone = 0xA1  # 区码起始
    bit = 0xA1   # 位码起始
    
    # 创建空白字库文件(完整大小)
    hzk_size = 94 * 94 * 32  # 理论最大大小
    hzk_data = bytearray(hzk_size)
    
    # 遍历所有图片文件(按文件名排序)
    image_files = sorted([f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.bmp', '.jpg'))])
    
    for img_file in image_files:
        try:
            img_path = os.path.join(image_folder, img_file)
            img = Image.open(img_path)
            if img.mode != '1':
                img = img.convert('1')  # 转换为单色位图
            
            # # 检查图片尺寸是否正确
            # if img.size != (128, 32):
            #     print(f"警告: 图片 {img_file} 尺寸不是128x32，跳过")
            #     continue
            # ==========
            # 强制截取左上角128x32
            img = img.crop((0, 0, 128, 32)) if (img.size[0] > 128 or img.size[1] > 32) else img
            # ==========
                
            # 处理图片中的每个字符(16个字符: 8x2)
            for row in range(rows_per_image):
                for col in range(chars_per_row):
                    # 计算字符在图片中的位置
                    x = col * char_width
                    y = row * char_height
                    
                    # 提取字符位图
                    char_img = img.crop((x, y, x + char_width, y + char_height))
                    
                    # 将字符转换为HZK16格式(32字节)
                    char_data = convert_char_to_hzk16(char_img)

                    # 对char_data所有字节按位取反
                    char_data = bytes([b ^ 0xFF for b in char_data])  # 每个字节与0xFF异或
                    
                    # 计算在HZK文件中的偏移量
                    offset = ((zone - 0xA1) * 94 + (bit - 0xA1)) * 32
                    
                    # 写入数据
                    hzk_data[offset:offset+32] = char_data
                    
                    # 更新编码(位码+1)
                    bit += 1
                    if bit > 0xFE:
                        bit = 0xA1
                        zone += 1
            
            print(f"已处理: {img_file} 当前编码: 区{zone:02X} 位{bit:02X}")
            
        except Exception as e:
            print(f"处理图片 {img_file} 时出错: {str(e)}")
    
    # 写入HZK16文件
    with open(output_file, 'wb') as f:
        f.write(hzk_data)
    
    print(f"字库文件已生成: {output_file}")
    print(f"总字符数: {len(image_files) * chars_per_row * rows_per_image}")

def convert_char_to_hzk16(char_img):
    """
    将16x16的单色字符图像转换为HZK16格式的32字节数据
    
    HZK16格式:
    每行2字节(16像素)，共16行=32字节
    位顺序: 高位在前，低位在后(MSB first)
    """
    char_data = bytearray(32)
    
    for y in range(16):
        # 每行2字节
        byte1 = 0
        byte2 = 0
        
        for x in range(8):
            # 左半字节(0-7像素)
            pixel = char_img.getpixel((x, y))
            if pixel == 0:  # 0表示黑色(有像素)
                byte1 |= (1 << (7 - x))
                
            # 右半字节(8-15像素)
            pixel = char_img.getpixel((x + 8, y))
            if pixel == 0:
                byte2 |= (1 << (7 - x))
        
        char_data[y * 2] = byte1
        char_data[y * 2 + 1] = byte2
    
    return char_data

if __name__ == "__main__":
    image_folder = input("输入图像文件夹路径：")
    output_file = input("输入保存文件名称：")
    
    convert_images_to_hzk16(image_folder, output_file)