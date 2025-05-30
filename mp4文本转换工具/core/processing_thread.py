"""
处理线程模块 - 向后兼容性包装器
实际实现在 enhanced_processing_thread.py 中
"""

from .enhanced_processing_thread import EnhancedProcessingThread

# 为了向后兼容，使用别名
ProcessingThread = EnhancedProcessingThread

__all__ = ['ProcessingThread', 'EnhancedProcessingThread']
