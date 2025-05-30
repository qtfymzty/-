"""
OpenAI Whisper 转录器
专门处理 OpenAI Whisper 模型的语音识别
"""

import os
import traceback
from typing import Optional, Dict, Any, Callable

from .base_transcriber import BaseTranscriber

# 导入 Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None


class WhisperTranscriber(BaseTranscriber):
    """OpenAI Whisper 转录器"""
    
    def __init__(self, model_name: str = "base"):
        super().__init__(model_name)
        self.device = "cpu"  # 可以设置为 "cuda" 如果有GPU
        
    def load_model(self, progress_callback: Optional[Callable] = None, 
                  status_callback: Optional[Callable] = None) -> bool:
        """加载 Whisper 模型"""
        try:
            if not WHISPER_AVAILABLE:
                raise Exception("OpenAI Whisper 未安装，请运行: pip install openai-whisper")
            
            if status_callback:
                status_callback(f"正在加载 OpenAI Whisper 模型: {self.model_name}")
            
            print(f"[调试] 开始加载 OpenAI Whisper 模型: {self.model_name}")
            
            if progress_callback:
                progress_callback(20)
            
            # 加载模型
            self.model = whisper.load_model(self.model_name, device=self.device)
            
            if progress_callback:
                progress_callback(100)
            
            self.is_loaded = True
            
            if status_callback:
                status_callback(f"OpenAI Whisper 模型 {self.model_name} 加载完成 ✓")
            
            print(f"[调试] OpenAI Whisper 模型加载成功: {self.model_name}")
            return True
            
        except Exception as e:
            error_msg = f"OpenAI Whisper 模型加载失败: {str(e)}"
            print(f"[错误] {error_msg}")
            print(f"[错误跟踪] {traceback.format_exc()}")
            if status_callback:
                status_callback(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def transcribe_audio(self, audio_path: str, 
                        progress_callback: Optional[Callable] = None,
                        status_callback: Optional[Callable] = None,
                        **kwargs) -> str:
        """使用 OpenAI Whisper 转录音频"""
        
        if not self.is_loaded:
            raise Exception("Whisper 模型未加载，请先调用 load_model()")
        
        # 验证音频文件
        is_valid, msg = self.validate_audio_file(audio_path)
        if not is_valid:
            raise Exception(msg)
        
        try:
            if status_callback:
                status_callback(f"🎯 使用 OpenAI Whisper {self.model_name} 开始转录...")
            
            print(f"[调试] OpenAI Whisper 开始转录音频: {audio_path}")
            
            if progress_callback:
                progress_callback(10)
            
            # 获取转录参数
            language = kwargs.get('language')
            beam_size = kwargs.get('beam_size', 3)
            temperature = kwargs.get('temperature', 0.0)
            
            if status_callback:
                status_callback(f"🎵 正在转录音频...")
            
            if progress_callback:
                progress_callback(50)
            
            # 执行转录
            result = self.model.transcribe(
                audio_path,
                language=language,
                beam_size=beam_size,
                temperature=temperature
            )
            
            if progress_callback:
                progress_callback(90)
            
            # 提取文本
            transcribed_text = result.get("text", "").strip()
            
            if progress_callback:
                progress_callback(100)
            
            if status_callback:
                status_callback(f"✅ OpenAI Whisper 转录完成，识别了 {len(transcribed_text)} 个字符")
            
            print(f"[调试] OpenAI Whisper 转录完成，文本长度: {len(transcribed_text)}")
            print(f"[调试] 转录文本预览: {transcribed_text[:100]}...")
            
            return transcribed_text
            
        except Exception as e:
            error_msg = f"OpenAI Whisper 转录失败: {str(e)}"
            print(f"[错误] {error_msg}")
            print(f"[错误跟踪] {traceback.format_exc()}")
            if status_callback:
                status_callback(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": self.model_name,
            "engine": "OpenAI Whisper",
            "loaded": self.is_loaded,
            "description": "OpenAI 官方开源的语音识别模型",
            "supported_languages": ["多语言支持", "中文", "英文等99种语言"],
            "features": ["语音识别", "多语言支持", "时间戳", "词级别对齐"],
            "device": self.device,
            "status": "已加载" if self.is_loaded else "未加载"
        }
    
    def set_device(self, device: str):
        """设置设备 (cpu/cuda)"""
        self.device = device
        print(f"[调试] OpenAI Whisper 设备设置为: {device}")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.model:
                del self.model
                self.model = None
            self.is_loaded = False
            print(f"[调试] OpenAI Whisper 转录器资源已清理")
        except Exception as e:
            print(f"[警告] 清理 OpenAI Whisper 资源时出错: {e}")


def test_whisper_availability() -> tuple[bool, str]:
    """测试 OpenAI Whisper 是否可用"""
    try:
        import whisper
        return True, "OpenAI Whisper 可用 ✓"
    except ImportError:
        return False, "OpenAI Whisper 未安装，请运行: pip install openai-whisper"
    except Exception as e:
        return False, f"OpenAI Whisper 测试失败: {str(e)}"


if __name__ == "__main__":
    # 测试代码
    available, message = test_whisper_availability()
    print(f"OpenAI Whisper 可用性测试: {available} - {message}")
    
    if available:
        transcriber = WhisperTranscriber()
        info = transcriber.get_model_info()
        print(f"模型信息: {info}")
