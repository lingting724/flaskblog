import os
import uuid
from PIL import Image
from flask import current_app
from pathlib import Path

def save_image(file, folder):
    """保存图片文件，返回文件路径
    
    Args:
        file: FileStorage对象
        folder: 保存的子目录名(posts或avatars)
    
    Returns:
        str: 相对于static目录的文件路径
    """
    # 生成随机文件名
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1].lower()
    
    # 获取上传目录的绝对路径
    upload_path = os.path.join(current_app.static_folder, 'uploads', folder)
    
    # 确保目录存在
    os.makedirs(upload_path, exist_ok=True)
    
    # 完整的文件保存路径
    filepath = os.path.join(upload_path, filename)
    
    # 保存并优化图片
    image = Image.open(file)
    
    # 等比例缩放大图片
    if max(image.size) > 1920:
        image.thumbnail((1920, 1920))
    
    # 保存图片，使用JPEG格式(如果原图是PNG且有透明通道则保留PNG格式)
    if image.format == 'PNG' and 'A' in image.getbands():
        image.save(filepath, 'PNG', optimize=True)
    else:
        image.convert('RGB').save(filepath, 'JPEG', quality=85, optimize=True)
    
    # 返回相对路径(使用正斜杠，确保URL正确)
    return '/'.join(['uploads', folder, filename]) 