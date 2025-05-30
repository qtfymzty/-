"""
Faster-Whisper 转录器
专门处理 Faster-Whisper 模型的语音识别
"""

import os
import traceback
from typing import Optional, Dict, Any, Callable

from .base_transcriber import BaseTranscriber

# 导入 Faster-Whisper
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    WhisperModel = None


class FasterWhisperTranscriber(BaseTranscriber):
    """Faster-Whisper 转录器"""
    
    def __init__(self, model_name: str = "base"):
        super().__init__(model_name)
        self.device = "cpu"
        self.compute_type = "int8"  # 计算类型: float16, int8, int8_float16
        
    def load_model(self, progress_callback: Optional[Callable] = None, 
                  status_callback: Optional[Callable] = None) -> bool:
        """加载 Faster-Whisper 模型"""
        try:
            if not FASTER_WHISPER_AVAILABLE:
                raise Exception("Faster-Whisper 未安装，请运行: pip install faster-whisper")
            
            if status_callback:
                status_callback(f"正在加载 Faster-Whisper 模型: {self.model_name}")
            
            print(f"[调试] 开始加载 Faster-Whisper 模型: {self.model_name}")
            
            if progress_callback:
                progress_callback(20)
            
            # 加载模型
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type
            )
            
            if progress_callback:
                progress_callback(100)
            
            self.is_loaded = True
            
            if status_callback:
                status_callback(f"Faster-Whisper 模型 {self.model_name} 加载完成")
            
            print(f"[调试] Faster-Whisper 模型加载成功: {self.model_name}")
            return True
            
        except Exception as e:
            error_msg = f"Faster-Whisper 模型加载失败: {str(e)}"
            print(f"[错误] {error_msg}")
            print(f"[错误跟踪] {traceback.format_exc()}")
            if status_callback:
                status_callback(f"{error_msg}")
            raise Exception(error_msg)
    
    def transcribe_audio(self, audio_path: str, 
                        progress_callback: Optional[Callable] = None,
                        status_callback: Optional[Callable] = None,
                        **kwargs) -> str:
        """使用 Faster-Whisper 转录音频"""
        
        if not self.is_loaded:
            raise Exception("Faster-Whisper 模型未加载，请先调用 load_model()")
        
        # 验证音频文件
        is_valid, msg = self.validate_audio_file(audio_path)
        if not is_valid:
            raise Exception(msg)
        
        try:
            if status_callback:
                status_callback(f"使用 Faster-Whisper {self.model_name} 开始转录...")
            
            print(f"[调试] Faster-Whisper 开始转录音频: {audio_path}")
            
            if progress_callback:
                progress_callback(10)
            
            # 获取转录参数
            language = kwargs.get('language')
            beam_size = kwargs.get('beam_size', 3)
            temperature = kwargs.get('temperature', 0.0)
            
            if status_callback:
                status_callback(f"正在转录音频...")
            
            if progress_callback:
                progress_callback(50)
            
            # 执行转录
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                beam_size=beam_size,
                temperature=temperature
            )
            
            # 收集转录结果
            transcribed_text = ""
            segment_count = 0
            
            for segment in segments:
                transcribed_text += segment.text + " "
                segment_count += 1
                
                # 更新进度
                if progress_callback and segment_count % 10 == 0:
                    current_progress = min(90, 50 + (segment_count * 2))
                    progress_callback(current_progress)
            
            transcribed_text = transcribed_text.strip()
            
            if progress_callback:
                progress_callback(100)
            
            if status_callback:
                status_callback(f"Faster-Whisper 转录完成，识别了 {len(transcribed_text)} 个字符")
            
            print(f"[调试] Faster-Whisper 转录完成，文本长度: {len(transcribed_text)}")
            print(f"[调试] 处理了 {segment_count} 个音频片段")
            print(f"[调试] 转录文本预览: {transcribed_text[:100]}...")
            
            return transcribed_text
            
        except Exception as e:
            error_msg = f"Faster-Whisper 转录失败: {str(e)}"
            print(f"[错误] {error_msg}")
            print(f"[错误跟踪] {traceback.format_exc()}")
            if status_callback:
                status_callback(f"{error_msg}")
            raise Exception(error_msg)
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": self.model_name,
            "engine": "Faster-Whisper",
            "loaded": self.is_loaded,
            "description": "基于 CTranslate2 的高速 Whisper 实现",
            "supported_languages": ["多语言支持", "中文", "英文等99种语言"],
            "features": ["高速转录", "低内存占用", "CPU优化", "批处理支持"],
            "device": self.device,
            "compute_type": self.compute_type,
            "status": "已加载" if self.is_loaded else "未加载"
        }
    
    def set_device(self, device: str):
        """设置设备 (cpu/cuda)"""
        self.device = device
        print(f"[调试] Faster-Whisper 设备设置为: {device}")
    
    def set_compute_type(self, compute_type: str):
        """设置计算类型"""
        self.compute_type = compute_type
        print(f"[调试] Faster-Whisper 计算类型设置为: {compute_type}")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.model:
                del self.model
                self.model = None
            self.is_loaded = False
            print(f"[调试] Faster-Whisper 转录器资源已清理")
        except Exception as e:
            print(f"[警告] 清理 Faster-Whisper 资源时出错: {e}")


def test_faster_whisper_availability() -> tuple[bool, str]:
    """测试 Faster-Whisper 是否可用"""
    try:
        from faster_whisper import WhisperModel
        return True, "Faster-Whisper 可用"
    except ImportError:
        return False, "Faster-Whisper 未安装，请运行: pip install faster-whisper"
    except Exception as e:
        return False, f"Faster-Whisper 测试失败: {str(e)}"


if __name__ == "__main__":
    # 测试代码
    available, message = test_faster_whisper_availability()
    print(f"Faster-Whisper 可用性测试: {available} - {message}")
    
    if available:
        transcriber = FasterWhisperTranscriber()
        info = transcriber.get_model_info()
        print(f"模型信息: {info}")
