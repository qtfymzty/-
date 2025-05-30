import os
import tempfile
import time
from PyQt5.QtCore import QThread, pyqtSignal
from moviepy import VideoFileClip

# 导入增强的处理线程
from .enhanced_processing_thread import EnhancedProcessingThread

# 为了保持向后兼容，使用增强版本作为默认处理线程
ProcessingThread = EnhancedProcessingThread
