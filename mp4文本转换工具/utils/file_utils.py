"""
文件处理工具函数
"""
import os
import tempfile
import shutil
from typing import Optional, Tuple


def create_safe_temp_dir(prefix: str = "whisper_") -> str:
    """创建安全的临时目录"""
    try:
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        print(f"[调试] 创建临时目录: {temp_dir}")
        return temp_dir
    except Exception as e:
        print(f"[错误] 创建临时目录失败: {e}")
        raise


def cleanup_temp_dir(temp_dir: str) -> bool:
    """清理临时目录"""
    try:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"[调试] 临时目录清理完成: {temp_dir}")
            return True
        return False
    except Exception as e:
        print(f"[警告] 清理临时目录失败: {e}")
        return False


def get_safe_filename(filepath: str, suffix: str = "") -> str:
    """获取安全的文件名"""
    try:
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        # 移除或替换不安全的字符
        safe_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name[:50]  # 限制长度
        
        if suffix:
            safe_name += f"_{suffix}"
        
        return safe_name if safe_name else "untitled"
    except Exception as e:
        print(f"[警告] 生成安全文件名失败: {e}")
        return "untitled"


def validate_video_file(filepath: str) -> Tuple[bool, str]:
    """验证视频文件"""
    if not filepath:
        return False, "文件路径为空"
    
    if not os.path.exists(filepath):
        return False, "文件不存在"
    
    if not os.path.isfile(filepath):
        return False, "路径不是有效文件"
    
    # 检查文件扩展名
    valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    file_ext = os.path.splitext(filepath)[1].lower()
    
    if file_ext not in valid_extensions:
        return False, f"不支持的文件格式: {file_ext}"
    
    # 检查文件大小
    try:
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            return False, "文件为空"
        if file_size > 10 * 1024 * 1024 * 1024:  # 10GB
            return False, "文件过大(超过10GB)"
    except Exception as e:
        return False, f"无法读取文件信息: {e}"
    
    return True, "文件有效"


def get_file_info(filepath: str) -> dict:
    """获取文件详细信息"""
    info = {
        'name': '',
        'size': 0,
        'size_str': '',
        'extension': '',
        'exists': False,
        'readable': False
    }
    
    try:
        if os.path.exists(filepath):
            info['exists'] = True
            info['name'] = os.path.basename(filepath)
            info['extension'] = os.path.splitext(filepath)[1].lower()
            
            file_size = os.path.getsize(filepath)
            info['size'] = file_size
            
            if file_size < 1024:
                info['size_str'] = f"{file_size} B"
            elif file_size < 1024 * 1024:
                info['size_str'] = f"{file_size / 1024:.1f} KB"
            elif file_size < 1024 * 1024 * 1024:
                info['size_str'] = f"{file_size / (1024 * 1024):.1f} MB"
            else:
                info['size_str'] = f"{file_size / (1024 * 1024 * 1024):.1f} GB"
            
            info['readable'] = os.access(filepath, os.R_OK)
    
    except Exception as e:
        print(f"[警告] 获取文件信息失败: {e}")
    
    return info
