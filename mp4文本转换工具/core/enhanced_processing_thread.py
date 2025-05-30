import os
import time
import tempfile
import shutil
import traceback
from typing import Optional, Dict, Any, Callable
from PyQt5.QtCore import QThread, pyqtSignal

try:
    from moviepy import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("[警告] MoviePy 不可用，无法处理视频文件")

try:
    from core.whisper_transcriber import WhisperTranscriber, test_whisper_availability
    WHISPER_TRANSCRIBER_AVAILABLE, whisper_status = test_whisper_availability()
except ImportError:
    WHISPER_TRANSCRIBER_AVAILABLE = False
    whisper_status = "Whisper 转录器模块不可用"

try:
    from core.faster_whisper_transcriber import FasterWhisperTranscriber, test_faster_whisper_availability
    FASTER_WHISPER_TRANSCRIBER_AVAILABLE, faster_whisper_status = test_faster_whisper_availability()
except ImportError:
    FASTER_WHISPER_TRANSCRIBER_AVAILABLE = False
    faster_whisper_status = "Faster-Whisper 转录器模块不可用"

try:
    from core.funasr_transcriber import FunASRTranscriber, test_funasr_availability
    FUNASR_TRANSCRIBER_AVAILABLE, funasr_status = test_funasr_availability()
except ImportError:
    FUNASR_TRANSCRIBER_AVAILABLE = False
    funasr_status = "FunASR 转录器模块不可用"


class EnhancedProcessingThread(QThread):
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    whisper_progress = pyqtSignal(str)
    segment_progress = pyqtSignal(int, int, str)
    processing_details = pyqtSignal(str)
    transcribe_progress = pyqtSignal(int)
    transcribe_status = pyqtSignal(str)
    debug_output = pyqtSignal(str)
    
    def __init__(self, video_path: str, settings: Dict[str, Any]):
        super().__init__()
        self.video_path = video_path
        self.settings = settings
        self.should_stop = False
        
        self.whisper_model = None
        self.faster_whisper_model = None
        self.funasr_transcriber = None
        
        self.temp_dir = None
        self.temp_files = []
        
        print(f"[调试] 处理线程初始化完成")
        print(f"[调试] 视频文件: {video_path}")
        print(f"[调试] 设置: {len(settings)} 个参数")
        self._log_settings()
    
    def _log_settings(self):
        important_settings = [
            'model_type', 'display_model_name', 'use_whisper', 
            'use_funasr_transcriber', 'whisper_model', 'funasr_model'
        ]
        for key in important_settings:
            if key in self.settings:
                print(f"[调试] {key}: {self.settings[key]}")
    
    def run(self):
        try:
            self.status_updated.emit("初始化处理...")
            self.debug_output.emit("开始处理流程")
            
            if not os.path.exists(self.video_path):
                raise Exception(f"视频文件不存在: {self.video_path}")
            
            self.temp_dir = tempfile.mkdtemp(prefix="whisper_extract_")
            print(f"[调试] 临时目录: {self.temp_dir}")
            
            self.progress_updated.emit(10)
            
            audio_path = self.extract_audio()
            if self.should_stop:
                return
            
            self.progress_updated.emit(30)
            
            model_type = self.settings.get('model_type', 'whisper')
            display_name = self.settings.get('display_model_name', '未知模型')
            
            self.transcribe_status.emit(f"正在使用 {display_name} 进行转录...")
            print(f"[调试] 使用模型类型: {model_type}")
            
            if model_type == 'funasr':
                transcribed_text = self.transcribe_with_funasr(audio_path)
            elif model_type in ['whisper', 'faster-whisper']:
                transcribed_text = self.transcribe_with_whisper(audio_path, model_type)
            else:
                self.transcribe_status.emit(f"{model_type} 暂未完全支持，使用 Whisper 回退...")
                transcribed_text = self.transcribe_with_whisper(audio_path, 'whisper')
            
            if self.should_stop:
                return
            
            self.progress_updated.emit(90)
            
            if not transcribed_text or not transcribed_text.strip():
                raise Exception("转录结果为空，可能是音频中没有可识别的语音内容")
            
            self.transcribe_status.emit(f"转录完成，识别了 {len(transcribed_text)} 个字符")
            self.result_ready.emit(transcribed_text)
            self.progress_updated.emit(100)
            self.status_updated.emit("处理完成")
            
        except Exception as e:
            error_msg = f"处理失败: {str(e)}\n\n详细错误:\n{traceback.format_exc()}"
            print(f"[错误] {error_msg}")
            self.error_occurred.emit(error_msg)
        finally:
            self.cleanup()
    
    def extract_audio(self) -> str:
        try:
            if not MOVIEPY_AVAILABLE:
                raise Exception("MoviePy 不可用，无法提取音频")
            
            self.status_updated.emit("正在提取音频...")
            self.processing_details.emit("从视频文件中提取音频轨道...")
            
            audio_filename = "extracted_audio.wav"
            audio_path = os.path.join(self.temp_dir, audio_filename)
            self.temp_files.append(audio_path)
            
            with VideoFileClip(self.video_path) as video:
                audio = video.audio
                if audio is None:
                    raise Exception("视频文件中没有音频轨道")
                
                quality = self.settings.get('quality', '中')
                if quality == '高':
                    fps = 44100
                elif quality == '低':
                    fps = 16000
                else:
                    fps = 22050
                
                self.processing_details.emit(f"以 {fps}Hz 采样率提取音频...")
                
                try:
                    audio.write_audiofile(
                        audio_path,
                        fps=fps
                    )
                except Exception as e1:
                    try:
                        audio.write_audiofile(audio_path)
                    except Exception as e2:
                        try:
                            audio_path_mp3 = audio_path.replace('.wav', '.mp3')
                            self.temp_files.append(audio_path_mp3)
                            audio.write_audiofile(audio_path_mp3)
                            audio_path = audio_path_mp3
                            self.processing_details.emit("已转换为 MP3 格式")
                        except Exception as e3:
                            raise Exception(f"音频提取失败。尝试的方法:\n1. WAV高级: {e1}\n2. WAV基础: {e2}\n3. MP3: {e3}")
            
            if not os.path.exists(audio_path):
                raise Exception("音频提取失败 - 输出文件不存在")
            
            file_size = os.path.getsize(audio_path) / (1024 * 1024)
            if file_size == 0:
                raise Exception("音频提取失败 - 输出文件为空")
            
            self.processing_details.emit(f"音频提取完成 ({file_size:.1f}MB)")
            print(f"[调试] 音频文件: {audio_path} ({file_size:.1f}MB)")
            
            return audio_path
            
        except Exception as e:
            error_msg = f"音频提取失败: {str(e)}"
            print(f"[错误] {error_msg}")
            
            if "verbose" in str(e):
                error_msg += "\n\n解决建议:\n"
                error_msg += "这可能是 MoviePy 版本兼容性问题\n"
                error_msg += "尝试更新 MoviePy: pip install --upgrade moviepy\n"
                error_msg += "或者降级到稳定版本: pip install moviepy==1.0.3"
            
            raise Exception(error_msg)
    
    def transcribe_with_funasr(self, audio_path: str) -> str:
        try:
            if not FUNASR_TRANSCRIBER_AVAILABLE:
                raise Exception(f"FunASR 转录器不可用: {funasr_status}")
            
            if not os.path.exists(audio_path):
                raise Exception(f"音频文件不存在: {audio_path}")
            
            file_size = os.path.getsize(audio_path) / (1024 * 1024)
            if file_size < 0.01:
                raise Exception(f"音频文件太小 ({file_size:.3f}MB)，可能提取失败")
            
            print(f"[调试] 验证音频文件通过: {audio_path} ({file_size:.2f}MB)")
            
            use_api = self.settings.get('funasr_use_api', False)
            mode_text = "在线API" if use_api else "离线本地"
            
            self.transcribe_status.emit(f"正在初始化 FunASR 转录器 ({mode_text})...")
            
            funasr_model_name = self.settings.get('funasr_model', 'paraformer-zh')
            self.funasr_transcriber = FunASRTranscriber(funasr_model_name, use_api)
            
            def progress_callback(progress):
                self.transcribe_progress.emit(progress)
            
            def status_callback(status):
                self.transcribe_status.emit(status)
                self.processing_details.emit(status)
            
            self.funasr_transcriber.load_model(
                progress_callback=progress_callback,
                status_callback=status_callback
            )
            
            if self.should_stop:
                return ""
            
            print(f"[调试] 开始 FunASR {mode_text} 转录...")
            transcribed_text = self.funasr_transcriber.transcribe_audio(
                audio_path,
                progress_callback=progress_callback,
                status_callback=status_callback,
                language=self._get_language_code()
            )
            
            print(f"[调试] FunASR {mode_text} 转录完成，文本长度: {len(transcribed_text)}")
            
            if not transcribed_text or not transcribed_text.strip():
                diagnostic_info = f"FunASR {mode_text} 转录返回空结果\n"
                diagnostic_info += f"音频文件: {audio_path}\n"
                diagnostic_info += f"文件大小: {file_size:.2f}MB\n"
                diagnostic_info += f"模型: {funasr_model_name} ({mode_text})\n"
                diagnostic_info += f"建议尝试:\n"
                diagnostic_info += f"1. 切换到{'离线本地' if use_api else '在线API'}模式\n"
                diagnostic_info += f"2. 使用 Whisper 或 Faster-Whisper 引擎\n"
                diagnostic_info += f"3. 检查音频是否包含语音内容\n"
                diagnostic_info += f"4. 调整音频质量设置"
                
                raise Exception(diagnostic_info)
            
            return transcribed_text
            
        except Exception as e:
            raise Exception(f"FunASR 转录失败: {str(e)}")
    
    def transcribe_with_whisper(self, audio_path: str, model_type: str) -> str:
        try:
            whisper_model_name = self.settings.get('whisper_model')
            
            if not whisper_model_name:
                raise Exception("Whisper 模型名称未设置")
            
            self.transcribe_status.emit(f"正在加载 {model_type.title()} 模型: {whisper_model_name}")
            
            if model_type == 'faster-whisper' and FASTER_WHISPER_TRANSCRIBER_AVAILABLE:
                return self._transcribe_with_faster_whisper_transcriber(audio_path, whisper_model_name)
            elif model_type == 'whisper' and WHISPER_TRANSCRIBER_AVAILABLE:
                return self._transcribe_with_whisper_transcriber(audio_path, whisper_model_name)
            else:
                if FASTER_WHISPER_TRANSCRIBER_AVAILABLE:
                    self.transcribe_status.emit(f"{model_type} 转录器不可用，使用 Faster-Whisper 替代...")
                    return self._transcribe_with_faster_whisper_transcriber(audio_path, whisper_model_name)
                elif WHISPER_TRANSCRIBER_AVAILABLE:
                    self.transcribe_status.emit(f"{model_type} 转录器不可用，使用 OpenAI Whisper 替代...")
                    return self._transcribe_with_whisper_transcriber(audio_path, whisper_model_name)
                else:
                    raise Exception("没有可用的 Whisper 转录器")
                    
        except Exception as e:
            raise Exception(f"Whisper 转录失败: {str(e)}")
    
    def _transcribe_with_faster_whisper_transcriber(self, audio_path: str, model_name: str) -> str:
        try:
            transcriber = FasterWhisperTranscriber(model_name)
            
            def progress_callback(progress):
                self.transcribe_progress.emit(progress)
            
            def status_callback(status):
                self.transcribe_status.emit(status)
                self.processing_details.emit(status)
            
            transcriber.load_model(
                progress_callback=progress_callback,
                status_callback=status_callback
            )
            
            if self.should_stop:
                return ""
            
            transcribed_text = transcriber.transcribe_audio(
                audio_path,
                progress_callback=progress_callback,
                status_callback=status_callback,
                language=self._get_language_code(),
                beam_size=self.settings.get('beam_size', 3)
            )
            
            transcriber.cleanup()
            
            return transcribed_text
            
        except Exception as e:
            raise Exception(f"Faster-Whisper 转录器失败: {str(e)}")
    
    def _transcribe_with_whisper_transcriber(self, audio_path: str, model_name: str) -> str:
        try:
            transcriber = WhisperTranscriber(model_name)
            
            def progress_callback(progress):
                self.transcribe_progress.emit(progress)
            
            def status_callback(status):
                self.transcribe_status.emit(status)
                self.processing_details.emit(status)
            
            transcriber.load_model(
                progress_callback=progress_callback,
                status_callback=status_callback
            )
            
            if self.should_stop:
                return ""
            
            transcribed_text = transcriber.transcribe_audio(
                audio_path,
                progress_callback=progress_callback,
                status_callback=status_callback,
                language=self._get_language_code(),
                beam_size=self.settings.get('beam_size', 3)
            )
            
            transcriber.cleanup()
            
            return transcribed_text
            
        except Exception as e:
            raise Exception(f"OpenAI Whisper 转录器失败: {str(e)}")
    
    def _get_language_code(self) -> Optional[str]:
        language = self.settings.get('language', '自动检测')
        language_map = {
            '自动检测': None,
            '中文': 'zh',
            '英文': 'en',
            '日文': 'ja',
            '韩文': 'ko',
            '法文': 'fr',
            '德文': 'de',
            '西班牙文': 'es',
            '俄文': 'ru'
        }
        return language_map.get(language, None)
    
    def stop(self):
        self.should_stop = True
        self.status_updated.emit("正在停止...")
        print("[调试] 处理线程收到停止信号")
    
    def cleanup(self):
        try:
            if self.funasr_transcriber:
                self.funasr_transcriber.cleanup()
                self.funasr_transcriber = None
            
            if self.whisper_model:
                del self.whisper_model
                self.whisper_model = None
            
            if self.faster_whisper_model:
                del self.faster_whisper_model
                self.faster_whisper_model = None
            
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                print(f"[信息] 临时文件清理完成: {self.temp_dir}")
            
        except Exception as e:
            print(f"[警告] 清理资源时出错: {e}")
