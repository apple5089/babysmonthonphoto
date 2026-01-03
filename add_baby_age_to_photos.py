"""
照片自动添加宝宝月份程序
功能：从文件名中提取日期，计算宝宝年龄，添加到照片下方正中间
出生日期：2025年9月2日
"""

import os
import re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


# 宝宝出生日期
BIRTH_DATE = datetime(2025, 9, 2)


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
                return datetime(int(year), int(month), int(day))

    # 方法2：查找年份（2020-2099），后面紧跟4位数字作为月日
    pattern = r'(20[2-9]\d)(\d{4})'
    match = re.search(pattern, name_without_ext)
    if match:
        year = int(match.group(1))
        month_day = match.group(2)
        month = int(month_day[:2])
        day = int(month_day[2:])
        if _is_valid_date(year, month, day):
            return datetime(year, month, day)

    return None


def _is_valid_date(year, month, day):
    """验证日期是否有效"""
    try:
        y = int(year)
        m = int(month)
        d = int(day)
        if y < 2000 or y > 2099:
            return False
        if m < 1 or m > 12:
            return False
        if d < 1 or d > 31:
            return False
        return True
    except ValueError:
        return False


def calculate_age(photo_date):
    """
    计算宝宝年龄（按实际月日计算）
    :param photo_date: 照片日期
    :return: 年龄描述字符串
    """
    if photo_date < BIRTH_DATE:
        # 出生前
        days_before = (BIRTH_DATE - photo_date).days
        return f"距离出生{days_before}天"
    else:
        # 出生后 - 按实际日期计算月数和天数
        years = photo_date.year - BIRTH_DATE.year
        months = photo_date.month - BIRTH_DATE.month
        days = photo_date.day - BIRTH_DATE.day

        # 如果天数为负，需要从月份借位
        if days < 0:
            months -= 1
            # 获取上个月的天数
            if photo_date.month == 1:
                prev_month = 12
                prev_year = photo_date.year - 1
            else:
                prev_month = photo_date.month - 1
                prev_year = photo_date.year

            # 计算上个月有多少天
            if prev_month in [1, 3, 5, 7, 8, 10, 12]:
                days_in_prev_month = 31
            elif prev_month in [4, 6, 9, 11]:
                days_in_prev_month = 30
            else:  # 2月
                # 判断闰年
                if (prev_year % 4 == 0 and prev_year % 100 != 0) or (prev_year % 400 == 0):
                    days_in_prev_month = 29
                else:
                    days_in_prev_month = 28

            days = days_in_prev_month + days

        # 如果月数为负，需要从年份借位
        if months < 0:
            months += 12
            years -= 1

        # 转换为总月数
        total_months = years * 12 + months

        if total_months == 0:
            return f"{days}天"
        elif days == 0:
            return f"{total_months}个月"
        else:
            return f"{total_months}个月{days}天"


def get_times_new_roman_font(size):
    """获取支持中文的字体"""
    # Windows系统字体路径 - 优先使用中文字体
    font_paths = [
        r"C:\Windows\Fonts\msyh.ttf",          # 微软雅黑
        r"C:\Windows\Fonts\msyhbd.ttf",        # 微软雅黑粗体
        r"C:\Windows\Fonts\simhei.ttf",        # 黑体
        r"C:\Windows\Fonts\simsun.ttc",        # 宋体
        r"C:\Windows\Fonts\simkai.ttf",        # 楷体
        r"C:\Windows\Fonts\times.ttf",         # Times New Roman (不含中文，备用)
    ]

    font_path = None
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break

    if font_path:
        return ImageFont.truetype(font_path, size)
    else:
        print("警告：未找到中文字体，使用默认字体（可能无法正确显示中文）")
        return ImageFont.load_default()


def add_age_to_image(image_path, output_path, age_string):
    """
    在图片下方正中间添加宝宝年龄
    :param image_path: 原图路径
    :param output_path: 输出路径
    :param age_string: 年龄字符串
    """
    # 打开图片，保持原始质量
    with Image.open(image_path) as img:
        # 确保图片模式正确
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 创建绘图对象
        draw = ImageDraw.Draw(img)

        # 字体大小根据图片尺寸自动调整（与原脚本一致）
        font_size = max(20, int(min(img.size) * 0.03))
        font = get_times_new_roman_font(font_size)

        # 获取文本边界框以计算文本大小
        bbox = draw.textbbox((0, 0), age_string, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 计算下方正中间位置（留出边距）
        margin = min(img.size) // 50  # 边距为图片尺寸的2%
        x = (img.width - text_width) // 2  # 水平居中
        y = img.height - text_height - margin  # 底部对齐

        # 绘制阴影效果（与原脚本一致）
        shadow_offset = max(1, font_size // 30)
        draw.text((x + shadow_offset, y + shadow_offset), age_string,
                 font=font, fill=(0, 0, 0, 128))  # 半透明黑色阴影

        # 绘制主文本（白色）
        draw.text((x, y), age_string, font=font, fill=(255, 255, 255))

        # 保存图片，保持原始质量
        img.save(output_path, quality=95, optimize=False, subsampling=0)
        print(f"已处理: {os.path.basename(image_path)} -> {age_string}")


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
    print(f"宝宝出生日期: {BIRTH_DATE.strftime('%Y年%m月%d日')}")
    print()

    success_count = 0
    skip_count = 0

    for image_file in image_files:
        # 从文件名提取日期
        photo_date = extract_date_from_filename(image_file.name)

        if photo_date is None:
            print(f"跳过: {image_file.name} (无法从文件名提取日期)")
            skip_count += 1
            continue

        # 计算年龄
        age_string = calculate_age(photo_date)

        # 输出文件路径
        output_file = output_path / image_file.name

        try:
            add_age_to_image(str(image_file), str(output_file), age_string)
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
    print("照片自动添加宝宝月份程序")
    print("=" * 50)
    print(f"当前目录: {current_dir}")
    print(f"宝宝出生日期: 2025年9月2日")
    print()

    # 处理当前目录下的所有照片
    process_photos(current_dir)

    print()
    input("按任意键退出...")


if __name__ == "__main__":
    main()
