"""
基础转录器抽象类
定义所有转录器的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
import os


class BaseTranscriber(ABC):
    """转录器基类，定义统一接口"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.is_loaded = False
        
    @abstractmethod
    def load_model(self, progress_callback: Optional[Callable] = None, 
                  status_callback: Optional[Callable] = None) -> bool:
        """加载模型"""
        pass
    
    @abstractmethod
    def transcribe_audio(self, audio_path: str, 
                        progress_callback: Optional[Callable] = None,
                        status_callback: Optional[Callable] = None,
                        **kwargs) -> str:
        """转录音频文件"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """清理资源"""
        pass
    
    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self.is_loaded
    
    def validate_audio_file(self, audio_path: str) -> tuple[bool, str]:
        """验证音频文件"""
        if not os.path.exists(audio_path):
            return False, f"音频文件不存在: {audio_path}"
        
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            return False, "音频文件为空"
        
        if file_size < 1024:  # 小于1KB
            return False, f"音频文件太小 ({file_size} bytes)"
        
        return True, "音频文件验证通过"
    
    def get_engine_name(self) -> str:
        """获取引擎名称"""
        return self.__class__.__name__.replace('Transcriber', '')
