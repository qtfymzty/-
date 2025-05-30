import os
import tempfile
import time
from datetime import datetime, timedelta
from PyQt5.QtCore import QThread, pyqtSignal
from moviepy import VideoFileClip
from utils.dependencies import WHISPER_AVAILABLE, estimate_audio_duration, calculate_segment_duration

if WHISPER_AVAILABLE:
    import whisper


class EnhancedProcessingThread(QThread):
    """增强的处理线程，支持文件分割和详细进度显示"""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    whisper_progress = pyqtSignal(str)
    segment_progress = pyqtSignal(int, int, str)
    processing_details = pyqtSignal(str)
    # 添加调试输出信号以保持兼容性
    debug_output = pyqtSignal(str)
    
    def __init__(self, video_path, settings):
        super().__init__()
        self.video_path = video_path
        self.settings = settings
        self.should_stop = False
        self.temp_dir = None
        # 添加兼容性属性
        self.is_running = True
        self.whisper_model = None
        self.temp_audio_path = None
        self._start_time = None
    
    def stop(self):
        """停止处理"""
        self.should_stop = True
        self.is_running = False
    
    def run(self):
        """主处理流程"""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="whisper_extract_")
            
            # 输出开始信息
            start_msg = f"开始处理文件: {self.video_path}"
            print(f"[信息] {start_msg}")
            self.debug_output.emit(start_msg)
            self.processing_details.emit(start_msg)
            
            # 检查是否需要分割
            if self.settings.get('needs_split', False):
                self.process_large_file()
            else:
                self.process_single_file()
                
        except Exception as e:
            import traceback
            error_msg = f"处理过程中发生错误: {str(e)}"
            error_detail = traceback.format_exc()
            
            # 输出到终端
            print(f"[错误] {error_msg}")
            print(f"[错误详情] {error_detail}")
            
            # 输出到界面
            self.debug_output.emit(f"错误: {error_msg}")
            self.debug_output.emit(f"错误详情:\n{error_detail}")
            self.processing_details.emit(f"❌ {error_msg}")
            
            # 发送错误信号
            self.error_occurred.emit(f"{error_msg}\n\n错误详情:\n{error_detail}")
        finally:
            self.cleanup_temp_files()
    
    def process_large_file(self):
        """处理大文件（分割处理）"""
        try:
            segments_needed = self.settings.get('segments_needed', 1)
            msg = f"开始分割大文件为 {segments_needed} 个片段"
            print(f"[信息] {msg}")
            self.processing_details.emit(msg)
            
            # 获取音频总时长
            total_duration = estimate_audio_duration(self.video_path)
            if total_duration is None:
                error_msg = "无法获取文件时长信息"
                print(f"[错误] {error_msg}")
                self.error_occurred.emit(error_msg)
                return
            
            segment_duration, _ = calculate_segment_duration(
                total_duration, 
                self.settings.get('file_size_gb', 0)
            )
            
            all_transcripts = []
            
            for i in range(segments_needed):
                if self.should_stop:
                    break
                
                start_time = i * segment_duration
                end_time = min((i + 1) * segment_duration, total_duration)
                
                self.segment_progress.emit(i, segments_needed, f"片段 {i+1}")
                msg = f"处理片段 {i+1}/{segments_needed} ({self.format_time(start_time)} - {self.format_time(end_time)})"
                print(f"[信息] {msg}")
                self.processing_details.emit(msg)
                
                # 提取音频片段
                audio_path = self.extract_audio_segment(start_time, end_time, i)
                if audio_path is None:
                    continue
                
                # 转录音频片段
                transcript = self.transcribe_audio_with_progress(audio_path, i+1, segments_needed)
                if transcript:
                    # 为每个片段添加时间标记
                    time_marker = f"\n[片段 {i+1}: {self.format_time(start_time)} - {self.format_time(end_time)}]\n"
                    all_transcripts.append(time_marker + transcript)
            
            # 合并所有转录结果
            if all_transcripts:
                final_transcript = "\n".join(all_transcripts)
                success_msg = f"成功处理 {len(all_transcripts)} 个片段"
                print(f"[成功] {success_msg}")
                self.processing_details.emit(f"✅ {success_msg}")
                self.result_ready.emit(final_transcript)
            else:
                error_msg = "未能提取到任何文本内容"
                print(f"[错误] {error_msg}")
                self.error_occurred.emit(error_msg)
                
        except Exception as e:
            import traceback
            error_msg = f"大文件处理失败: {str(e)}"
            error_detail = traceback.format_exc()
            print(f"[错误] {error_msg}")
            print(f"[错误详情] {error_detail}")
            self.debug_output.emit(f"错误: {error_msg}\n详情: {error_detail}")
            self.error_occurred.emit(f"{error_msg}\n\n{error_detail}")
    
    def process_single_file(self):
        """处理单个文件"""
        try:
            msg = "提取音频文件..."
            print(f"[信息] {msg}")
            self.processing_details.emit(msg)
            
            # 提取音频
            audio_path = self.extract_audio_full()
            if audio_path is None:
                return
            
            # 转录音频
            transcript = self.transcribe_audio_with_progress(audio_path, 1, 1)
            if transcript:
                success_msg = "单文件处理完成"
                print(f"[成功] {success_msg}")
                self.processing_details.emit(f"✅ {success_msg}")
                self.result_ready.emit(transcript)
            else:
                error_msg = "转录失败"
                print(f"[错误] {error_msg}")
                self.error_occurred.emit(error_msg)
                
        except Exception as e:
            import traceback
            error_msg = f"单文件处理失败: {str(e)}"
            error_detail = traceback.format_exc()
            print(f"[错误] {error_msg}")
            print(f"[错误详情] {error_detail}")
            self.debug_output.emit(f"错误: {error_msg}\n详情: {error_detail}")
            self.error_occurred.emit(f"{error_msg}\n\n{error_detail}")
    
    def extract_audio_segment(self, start_time, end_time, segment_index):
        """提取音频片段"""
        try:
            msg = f"提取音频片段 {segment_index+1}..."
            print(f"[信息] {msg}")
            self.whisper_progress.emit(msg)
            
            # 使用moviepy提取音频片段
            with VideoFileClip(self.video_path) as video:
                audio_clip = video.subclipped(start_time, end_time).audio
                audio_path = os.path.join(self.temp_dir, f"segment_{segment_index}.wav")
                # 移除不支持的verbose参数，使用logger=None来抑制输出
                audio_clip.write_audiofile(audio_path, logger=None)
                audio_clip.close()
            
            success_msg = f"片段 {segment_index+1} 音频提取成功"
            print(f"[成功] {success_msg}")
            self.whisper_progress.emit(f"✅ {success_msg}")
            return audio_path
            
        except Exception as e:
            import traceback
            error_msg = f"提取片段 {segment_index+1} 失败: {str(e)}"
            error_detail = traceback.format_exc()
            print(f"[错误] {error_msg}")
            print(f"[错误详情] {error_detail}")            
            self.whisper_progress.emit(f"❌ {error_msg}")
            self.debug_output.emit(f"片段提取错误: {error_msg}\n详情: {error_detail}")
            return None
    
    def extract_audio_full(self):
        """提取完整音频"""
        try:
            msg = "提取音频文件..."
            print(f"[信息] {msg}")
            self.whisper_progress.emit(msg)
            
            with VideoFileClip(self.video_path) as video:
                audio_path = os.path.join(self.temp_dir, "audio.wav")
                # 移除不支持的verbose参数，使用logger=None来抑制输出
                video.audio.write_audiofile(audio_path, logger=None)
            
            success_msg = "音频提取成功"
            print(f"[成功] {success_msg}")
            self.whisper_progress.emit(f"✅ {success_msg}")
            return audio_path
            
        except Exception as e:
            import traceback
            error_msg = f"音频提取失败: {str(e)}"
            error_detail = traceback.format_exc()
            print(f"[错误] {error_msg}")
            print(f"[错误详情] {error_detail}")
            self.debug_output.emit(f"音频提取错误: {error_msg}\n详情: {error_detail}")
            self.error_occurred.emit(f"{error_msg}\n\n{error_detail}")
            return None
    
    def transcribe_audio_with_progress(self, audio_path, segment_num, total_segments):
        """使用Whisper转录音频并显示进度"""
        try:
            model_name = self.settings.get('whisper_model', 'base')
            msg = f"加载Whisper模型 ({model_name})..."
            print(f"[信息] {msg}")
            self.whisper_progress.emit(msg)
            
            # 加载模型
            model = whisper.load_model(model_name)
            
            msg = f"开始转录片段 {segment_num}/{total_segments}..."
            print(f"[信息] {msg}")
            self.whisper_progress.emit(msg)
            
            # 设置转录参数
            options = {
                'language': self.get_language_code(),
                'beam_size': self.settings.get('beam_size', 5),
                'temperature': self.settings.get('temperature', 0.0),
                'no_speech_threshold': self.settings.get('no_speech_threshold', 0.6),
                'compression_ratio_threshold': self.settings.get('compression_ratio_threshold', 2.4),
                'logprob_threshold': self.settings.get('logprob_threshold', -1.0),
                'condition_on_previous_text': self.settings.get('condition_on_previous', True),
                'word_timestamps': self.settings.get('word_timestamps', False)
            }
            
            # 过滤None值
            options = {k: v for k, v in options.items() if v is not None}
            
            # 开始转录
            start_time = time.time()
            result = model.transcribe(audio_path, **options)
            end_time = time.time()
            
            processing_time = end_time - start_time
            success_msg = f"片段 {segment_num} 转录完成 (耗时: {processing_time:.1f}秒)"
            print(f"[成功] {success_msg}")
            self.whisper_progress.emit(f"✅ {success_msg}")
            
            # 提取文本
            text = result.get('text', '').strip()
            
            # 如果启用了时间戳
            if self.settings.get('show_timestamps', False) and 'segments' in result:
                formatted_text = self.format_with_timestamps(result['segments'])
                return formatted_text
            else:
                return text
                
        except Exception as e:
            import traceback
            error_msg = f"转录片段 {segment_num} 失败: {str(e)}"
            error_detail = traceback.format_exc()
            print(f"[错误] {error_msg}")
            print(f"[错误详情] {error_detail}")
            self.whisper_progress.emit(f"❌ {error_msg}")
            self.debug_output.emit(f"转录错误: {error_msg}\n详情: {error_detail}")
            return None
    
    def get_language_code(self):
        """获取语言代码"""
        language_mapping = {
            '中文': 'zh',
            '英文': 'en',
            '日文': 'ja',
            '韩文': 'ko',
            '法文': 'fr',
            '德文': 'de',
            '西班牙文': 'es',
            '俄文': 'ru',
            '自动检测': None
        }
        
        language = self.settings.get('language', '自动检测')
        return language_mapping.get(language, None)
    
    def format_with_timestamps(self, segments):
        """格式化带时间戳的文本"""
        formatted_text = []
        for segment in segments:
            start_time = self.format_time(segment['start'])
            end_time = self.format_time(segment['end'])
            text = segment['text'].strip()
            formatted_text.append(f"[{start_time} - {end_time}] {text}")
        
        return '\n'.join(formatted_text)
    
    def format_time(self, seconds):
        """格式化时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                print(f"[信息] 临时文件清理完成: {self.temp_dir}")
                self.debug_output.emit(f"临时文件清理完成: {self.temp_dir}")
        except Exception as e:
            error_msg = f"清理临时文件失败: {str(e)}"
            print(f"[警告] {error_msg}")
            self.debug_output.emit(f"警告: {error_msg}")
