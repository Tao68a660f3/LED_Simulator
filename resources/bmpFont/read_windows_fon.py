import pygame
from PIL import Image

def generate_font_table(font_path, font_size=16, output_path="font_table.png"):
    """
    生成 ASCII 可打印字符表 (16x16)，严格按 ASCII 值定位
    :param font_path: 字体文件路径 (.fon/.ttf)
    :param font_size: 字体大小（像素）
    :param output_path: 输出图片路径
    """
    pygame.init()
    
    try:
        font = pygame.font.Font(font_path, font_size)
    except Exception as e:
        print(f"字体加载失败: {e}")
        return False

    # ASCII 可打印字符范围 (0x20~0x7F)
    chars = [chr(i) for i in range(0x20, 0x80)]
    
    # 计算最大字符尺寸（避免格子大小不一）
    max_width, max_height = 0, 0
    for char in chars:
        try:
            char_surface = font.render(char, True, (0, 0, 0))
            w, h = char_surface.get_size()
            max_width = max(max_width, w)
            max_height = max(max_height, h)
        except:
            continue  # 跳过无法渲染的字符

    max_width = 16

    # 创建大图 (16行 x 16列)
    table_width = max_width * 16
    table_height = max_height * 16
    table_surface = pygame.Surface((table_width, table_height))
    table_surface.fill((255, 255, 255))  # 白色背景

    # 渲染每个字符（按 ASCII 值计算行列）
    for char in chars:
        i = ord(char)
        row = i // 16  # 从0x20开始计算行
        col = i % 16    # 从0x20开始计算列
        x = col * max_width
        y = row * max_height
        
        try:
            char_surface = font.render(char, True, (0, 0, 0))
            # 居中显示字符
            offset_x = (max_width - char_surface.get_width()) // 2
            offset_y = (max_height - char_surface.get_height()) // 2
            table_surface.blit(char_surface, (x + offset_x, y + offset_y))
        except:
            print(f"跳过无法渲染的字符: {char} (ASCII: {i})")
            continue

    # 保存图片
    pygame.image.save(table_surface, output_path)
    print(f"字符表已保存到: {output_path}")
    pygame.quit()
    return True

# 使用示例
if __name__ == "__main__":
    font_path = "c:\Windows\Fonts\S8514SYS.FON"  # 替换为你的字体路径
    generate_font_table(font_path, font_size=16, output_path="font_table.png")