"""
照片自动添加时间戳程序
功能：从文件名中提取时间，并将时间添加到照片右下角
"""

import os
import re
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def extract_date_from_filename(filename):
    """
    从文件名中提取日期
    支持多种格式：
    1. 有分隔符：2022.09.21, 2022-09-21, 2022_09_21
    2. 找到年份后跟月日：IMG_xxx20250904.jpg → 2025.09.04
    """
    # 移除文件扩展名
    name_without_ext = os.path.splitext(filename)[0]

    # 方法1：先尝试有分隔符的格式（优先级更高，更准确）
    patterns = [
        r'(\d{4})[.\-_](\d{2})[.\-_](\d{2})',  # 2022.09.21, 2022-09-21, 2022_09_21
    ]

    for pattern in patterns:
        match = re.search(pattern, name_without_ext)
        if match:
            year, month, day = match.groups()
            if _is_valid_date(year, month, day):
                return f"{year}.{month}.{day}"

    # 方法2：查找年份（2020-2099），后面紧跟4位数字作为月日
    # 匹配格式：年份(4位) + 月日(4位)
    pattern = r'(20[2-9]\d)(\d{4})'
    match = re.search(pattern, name_without_ext)
    if match:
        year = match.group(1)  # 例如：2025
        month_day = match.group(2)  # 例如：0904
        month = month_day[:2]  # 09
        day = month_day[2:]  # 04
        if _is_valid_date(year, month, day):
            return f"{year}.{month}.{day}"

    return None


def _is_valid_date(year, month, day):
    """
    验证日期是否有效
    年份：2000-2099（可根据需要调整）
    月份：01-12
    日期：01-31
    """
    try:
        y = int(year)
        m = int(month)
        d = int(day)
        # 验证年份范围（可根据实际需求调整）
        if y < 2000 or y > 2099:
            return False
        # 验证月份
        if m < 1 or m > 12:
            return False
        # 验证日期
        if d < 1 or d > 31:
            return False
        return True
    except ValueError:
        return False


def get_times_new_roman_font(size):
    """获取Times New Roman字体"""
    # Windows系统字体路径
    font_paths = [
        r"C:\Windows\Fonts\times.ttf",
        r"C:\Windows\Fonts\timesbd.ttf",
        r"C:\Windows\Fonts\TIMES.TTF",
        r"C:\Windows\Fonts\TIMESBD.TTF",
    ]

    font_path = None
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break

    if font_path:
        return ImageFont.truetype(font_path, size)
    else:
        print("警告：未找到Times New Roman字体，使用默认字体")
        return ImageFont.load_default()


def add_timestamp_to_image(image_path, output_path, date_string):
    """
    在图片右下角添加时间戳
    :param image_path: 原图路径
    :param output_path: 输出路径
    :param date_string: 日期字符串，格式为2022.09.21
    """
    # 打开图片，保持原始质量
    with Image.open(image_path) as img:
        # 确保图片模式正确（如果是RGBA且需要处理透明度）
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 创建绘图对象
        draw = ImageDraw.Draw(img)

        # 字体大小根据图片尺寸自动调整
        # 基础字体大小为图片短边的3%
        font_size = max(20, int(min(img.size) * 0.03))
        font = get_times_new_roman_font(font_size)

        # 获取文本边界框以计算文本大小
        bbox = draw.textbbox((0, 0), date_string, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 计算右下角位置（留出边距）
        margin = min(img.size) // 50  # 边距为图片尺寸的2%
        x = img.width - text_width - margin
        y = img.height - text_height - margin

        # 绘制阴影效果（可选，增强可读性）
        shadow_offset = max(1, font_size // 30)
        draw.text((x + shadow_offset, y + shadow_offset), date_string,
                 font=font, fill=(0, 0, 0, 128))  # 半透明黑色阴影

        # 绘制主文本（白色）
        draw.text((x, y), date_string, font=font, fill=(255, 255, 255))

        # 保存图片，保持原始质量
        img.save(output_path, quality=95, optimize=False, subsampling=0)
        print(f"已处理: {os.path.basename(image_path)} -> {date_string}")


def process_photos(input_dir, output_dir=None):
    """
    处理目录中的所有照片
    :param input_dir: 输入目录
    :param output_dir: 输出目录（如果为None，则在输入目录下创建output文件夹）
    """
    input_path = Path(input_dir)

    if output_dir is None:
        output_path = input_path / "output"
    else:
        output_path = Path(output_dir)

    # 创建输出目录
    output_path.mkdir(exist_ok=True)

    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}

    # 获取所有图片文件
    image_files = [f for f in input_path.iterdir()
                   if f.is_file() and f.suffix.lower() in image_extensions]

    if not image_files:
        print(f"在 {input_dir} 中未找到图片文件")
        return

    print(f"找到 {len(image_files)} 张图片")

    success_count = 0
    skip_count = 0

    for image_file in image_files:
        # 从文件名提取日期
        date_string = extract_date_from_filename(image_file.name)

        if date_string is None:
            print(f"跳过: {image_file.name} (无法从文件名提取日期)")
            skip_count += 1
            continue

        # 输出文件路径
        output_file = output_path / image_file.name

        try:
            add_timestamp_to_image(str(image_file), str(output_file), date_string)
            success_count += 1
        except Exception as e:
            print(f"错误: 处理 {image_file.name} 时出错: {e}")

    print(f"\n处理完成!")
    print(f"成功: {success_count} 张")
    print(f"跳过: {skip_count} 张")
    print(f"输出目录: {output_path}")


def main():
    """主函数"""
    # 默认处理当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 50)
    print("照片自动添加时间戳程序")
    print("=" * 50)
    print(f"当前目录: {current_dir}")
    print()

    # 处理当前目录下的所有照片
    process_photos(current_dir)

    print()
    input("按任意键退出...")


if __name__ == "__main__":
    main()
