import ctypes
from ctypes import wintypes
import os
import struct
from PIL import Image

gdi32 = ctypes.windll.gdi32
user32 = ctypes.windll.user32

def extract_font_name_from_system(hdc, font_path):
    """
    通过 Windows 字体引擎直接读取并解码该字体登记的真实 FaceName
    """
    # 尝试直接从文件名获取线索
    hint_name = os.path.splitext(os.path.basename(font_path))[0]
    
    # 1. 尝试获取 'name' 标签表的数据 (Tag: 'name' 对应的 Big-Endian 整数是 0x6E616D65)
    # 通过 GetFontData 读取，如果返回 -1 说明系统没认这个字体
    size = gdi32.GetFontData(hdc, 0x6E616D65, 0, None, 0)
    if size <= 0 or size == 0xFFFFFFFF:
        return hint_name # 没读到就拿文件名顶替
        
    buf = ctypes.create_string_buffer(size)
    gdi32.GetFontData(hdc, 0x6E616D65, 0, buf, size)
    data = buf.raw

    # 2. 解析 OpenType 'name' 表格式
    if len(data) < 6:
        return hint_name
    format_selector, count, string_offset = struct.unpack(">HHH", data[:6])
    
    # 存储所有捞出来的名字候选
    names = {}
    
    # 3. 遍历所有名称记录 (Name Record 结构为 12 字节)
    for i in range(count):
        offset = 6 + i * 12
        if offset + 12 > len(data):
            break
        platform_id, encoding_id, language_id, name_id, length, name_offset = struct.unpack(
            ">HHHHHH", data[offset:offset+12]
        )
        
        # We only care about Font Family Name (name_id == 1) or Full Font Name (name_id == 4)
        if name_id in (1, 4):
            start = string_offset + name_offset
            end = start + length
            name_bytes = data[start:end]
            
            try:
                # 关键：根据不同的平台和编码表进行硬解码
                if platform_id == 3 and encoding_id == 1: # Windows Unicode BMP
                    name_str = name_bytes.decode('utf-16-be').strip('\x00')
                elif platform_id == 3 and encoding_id == 0: # Windows Symbol
                    name_str = name_bytes.decode('utf-16-be').strip('\x00')
                elif platform_id == 1: # Macintosh
                    name_str = name_bytes.decode('mac-roman').strip('\x00')
                else:
                    # 汉鼎等老字体的终极杀招：直接用本地 GBK 强解其原始字节流
                    name_str = name_bytes.decode('gbk', errors='ignore').strip('\x00')
                
                if name_str:
                    names[(platform_id, language_id, name_id)] = name_str
            except:
                pass

    # 4. 筛选最佳名称优先级：
    # 优先找中国大陆/台湾区域的中文名称(language_id 2052是简体, 1028是繁体)，其次是英文名(1033)
    priority = [
        lambda k: k[1] == 2052 and k[2] == 1, # 简体中文 Family Name
        lambda k: k[1] == 1028 and k[2] == 1, # 繁体中文 Family Name
        lambda k: k[1] == 2052 and k[2] == 4, # 简体中文 Full Name
        lambda k: k[2] == 1 and k[0] == 3,     # 任何 Windows 平台的 Family Name
        lambda k: k[2] == 1,                  # 任何 Family Name
    ]
    
    for cond in priority:
        matches = [names[k] for k in names if cond(k)]
        if matches:
            return matches[0]
            
    return hint_name


def render_char_to_image_gdi(text, font_path, font_size, canvas_w, canvas_h, scale_x=100, scale_y=100, offset_x=0, offset_y=0):
    font_added = False
    if os.path.exists(font_path):
        # 物理注册
        gdi32.AddFontResourceExW(font_path, 0x10, 0)
        font_added = True

    # 创建临时上下文用来嗅探字体真名
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    
    # 关键：先尝试临时用文件名创建一下，激活字体上下文
    hint_name = os.path.splitext(os.path.basename(font_path))[0]
    h_temp_font = gdi32.CreateFontW(-font_size, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 3, 0, hint_name)
    h_old_temp = gdi32.SelectObject(hdc_mem, h_temp_font)
    
    # 【全自动核心】：直接扒出汉鼎简姚体在底层注册的真名
    font_name = extract_font_name_from_system(hdc_mem, font_path)
    
    # 释放临时嗅探句柄
    gdi32.SelectObject(hdc_mem, h_old_temp)
    gdi32.DeleteObject(h_temp_font)

    # ---------------- 真正的目标画布渲染 ----------------
    hbitmap = gdi32.CreateCompatibleBitmap(hdc_screen, canvas_w, canvas_h)
    h_old_bmp = gdi32.SelectObject(hdc_mem, hbitmap)

    h_brush = gdi32.CreateSolidBrush(0)
    rect = wintypes.RECT(0, 0, canvas_w, canvas_h)
    user32.FillRect(hdc_mem, ctypes.byref(rect), h_brush)
    gdi32.DeleteObject(h_brush)

    calculated_height = int(font_size * (scale_y / 100.0))
    calculated_width = int((font_size * 0.5) * (scale_x / 100.0))

    # 喂入 100% 挖掘出来的精准真名
    h_font = gdi32.CreateFontW(
        -calculated_height, calculated_width, 0, 0, 400, 
        0, 0, 0, 1, 0, 0, 3, 0, font_name
    )
    h_old_font = gdi32.SelectObject(hdc_mem, h_font)

    gdi32.SetTextColor(hdc_mem, 0xFFFFFF)
    gdi32.SetBkMode(hdc_mem, 1)
    draw_rect = wintypes.RECT(offset_x, offset_y, canvas_w, canvas_h)
    user32.DrawTextW(hdc_mem, text, -1, ctypes.byref(draw_rect), 0)

    # 提取像素
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG), ("biYPelsPerMeter", wintypes.LONG),
                    ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]
        
    buf = (ctypes.c_ubyte * (canvas_w * canvas_h * 4))()
    bmi = BITMAPINFOHEADER(biSize=ctypes.sizeof(BITMAPINFOHEADER), biWidth=canvas_w, biHeight=-canvas_h, 
                           biPlanes=1, biBitCount=32, biCompression=0)
    gdi32.GetDIBits(hdc_mem, hbitmap, 0, canvas_h, buf, ctypes.byref(bmi), 0)

    img = Image.frombytes('RGBA', (canvas_w, canvas_h), bytes(buf), 'raw', 'BGRA')
    final_img = img.convert("RGB")

    gdi32.SelectObject(hdc_mem, h_old_font)
    gdi32.DeleteObject(h_font)
    gdi32.SelectObject(hdc_mem, h_old_bmp)
    gdi32.DeleteObject(hbitmap)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)

    if font_added:
        gdi32.RemoveFontResourceExW(font_path, 0x10, 0)

    return final_img

if __name__ == "__main__":
    path = r"simsun.ttc"
    img = render_char_to_image_gdi("中", path, 24, 16, 24, 67, 100, 0, 0)
    img.save(r".\resources\truetypeFont\GDITest.png")