import numpy as np
from PIL import Image, ImageChops

def read_font_data(font_path):
    with open(font_path, 'rb') as f:
        return f.read()

def extract_font_matrix(font_data, char_code):
    offset = char_code * 16
    font_matrix = [[font_data[i + offset] >> j & 1 for j in range(8)[::-1]] for i in range(16)]
    return np.array(font_matrix)

def generate_bitmap(font_path):
    font_data = read_font_data(font_path)
    bitmap = np.zeros((256, 128), dtype=np.uint8)
    for i in range(256):
        char_code = i
        font_matrix = extract_font_matrix(font_data, char_code)
        row = (i // 16) * 16
        col = (i % 16) * 8
        bitmap[row:row+16, col:col+8] = font_matrix * 255
    return bitmap

def save_bitmap(bitmap, output_path):
    img = Image.fromarray(bitmap)
    # img = img.convert('1')
    img = img.convert("L")
    img = ImageChops.invert(img)
    img = img.convert("1")
    img.save(output_path)

if __name__ == "__main__":
    font_path = "./ASC16.bin"  # 点阵字库的路径
    bitmap = generate_bitmap(font_path)
    save_bitmap(bitmap, "测试生成—asciiFont.bmp")
    print("位图已生成并保存为测试生成—asciiFont.bmp")
