import subprocess
import importlib
import logging
import os

# 设置日志
logger = logging.getLogger(__name__)

# 检查依赖包版本
def check_package_version(package_name, import_name=None):
    """检查包版本，支持不同的导入名称"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', '未知版本')
        return True, version
    except ImportError as e:
        logger.debug(f"无法导入 {package_name}: {e}")
        return False, None

# 检查依赖包
MOVIEPY_AVAILABLE, MOVIEPY_VERSION = check_package_version('moviepy')
WHISPER_AVAILABLE, WHISPER_VERSION = check_package_version('openai-whisper', 'whisper')
PYDUB_AVAILABLE, PYDUB_VERSION = check_package_version('pydub')
TORCH_AVAILABLE, TORCH_VERSION = check_package_version('torch')

# 输出调试信息
if WHISPER_AVAILABLE:
    logger.info("Whisper模块加载成功")
else:
    logger.warning("Whisper模块未安装")

if PYDUB_AVAILABLE:
    logger.info("Pydub模块加载成功")
else:
    logger.warning(f"pydub警告: 无法加载")


def check_ffmpeg():
    """检查ffmpeg是否可用"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'], 
            capture_output=True, 
            check=True,
            timeout=10  # 添加超时
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_gpu_availability():
    """检查GPU可用性"""
    if not TORCH_AVAILABLE:
        return False, "PyTorch未安装"
    
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "未知"
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            return True, f"{gpu_name} ({gpu_memory:.1f}GB)"
        else:
            return False, "CUDA不可用"
    except Exception as e:
        return False, f"GPU检查失败: {e}"


def check_dependencies():
    """检查所有依赖并返回缺失的依赖列表"""
    missing_deps = []
    
    if not WHISPER_AVAILABLE:
        missing_deps.append("openai-whisper")
    
    if not MOVIEPY_AVAILABLE:
        missing_deps.append("moviepy")
    
    return missing_deps


def get_version_info():
    """获取所有版本信息"""
    gpu_available, gpu_info = check_gpu_availability()
    
    return {
        'moviepy': MOVIEPY_VERSION,
        'moviepy_available': MOVIEPY_AVAILABLE,
        'whisper': WHISPER_VERSION,
        'whisper_available': WHISPER_AVAILABLE,
        'pydub': PYDUB_VERSION,
        'pydub_available': PYDUB_AVAILABLE,
        'torch': TORCH_VERSION,
        'torch_available': TORCH_AVAILABLE,
        'ffmpeg': check_ffmpeg(),
        'gpu_available': gpu_available,
        'gpu_info': gpu_info
    }


def get_system_requirements():
    """获取系统要求检查结果"""
    info = get_version_info()
    
    requirements = {
        'essential': {
            'Python >= 3.7': True,  # 如果程序能运行，Python版本肯定OK
            'moviepy': info['moviepy_available'],
            'whisper': info['whisper_available'],
        },
        'recommended': {
            'ffmpeg': info['ffmpeg'],
            'torch (GPU支持)': info['torch_available'],
            'pydub (音频处理)': info['pydub_available'],
        },
        'optional': {
            'CUDA GPU': info['gpu_available'],
        }
    }
    
    return requirements


def check_file_size(file_path, max_size_gb=3):
    """检查文件大小是否超过限制"""
    if not os.path.exists(file_path):
        return False, 0, 0
    
    file_size = os.path.getsize(file_path)
    file_size_gb = file_size / (1024**3)
    
    needs_split = file_size_gb > max_size_gb
    segments_needed = int(file_size_gb / max_size_gb) + 1 if needs_split else 1
    
    return needs_split, file_size_gb, segments_needed


def estimate_audio_duration(file_path):
    """估算音频/视频文件时长"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return duration
        else:
            return None
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return None


def calculate_segment_duration(total_duration, file_size_gb, max_size_gb=3):
    """计算每个分段的时长"""
    if total_duration is None or file_size_gb <= max_size_gb:
        return total_duration, 1
    
    segments_needed = int(file_size_gb / max_size_gb) + 1
    segment_duration = total_duration / segments_needed
    
    return segment_duration, segments_needed
