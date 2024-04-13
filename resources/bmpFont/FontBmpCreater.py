# Draw ascii fonts
from PIL import Image, ImageDraw, ImageFont, ImageChops
font_size = 32
bold_size = 1
x_offset = 0
y_offset = -6
font_path = "arial.ttf"

# 创建一个Image对象
image = Image.new("1", (16*font_size, 16*font_size))  # 1-bit image (black and white)
# 获取字体对象
font = ImageFont.truetype(font_path, 36)
# 创建一个Draw对象
draw = ImageDraw.Draw(image)

# 设置字体，绘制文本，加粗
for i in range(16):
    for j in range(16):
        for k in range(bold_size):
            draw.text((j*font_size+k+x_offset, i*font_size+y_offset), chr(i*16+j), font=font, fill=1)

image = image.convert("L")
image = ImageChops.invert(image)
image = image.convert("1")

image.save("font.bmp")
