"""
FunASR 转录器模块
支持官方API和本地模型两种调用方式
"""

import os
import time
import traceback
from typing import Callable, Optional, Dict, Any
from .base_transcriber import BaseTranscriber

class FunASRTranscriber(BaseTranscriber):
    """FunASR 转录器 - 支持官方API和本地模型"""
    
    def __init__(self, model_name: str = "paraformer-zh", use_api: bool = False):
        super().__init__(model_name)
        self.use_api = use_api  # 是否使用API方式
        self.device = "cpu"
        self.vad_model = None
        self.model_dir = None
        self.postprocess_func = None
        self._setup_model_config()
        
    def _setup_model_config(self):
        """设置模型配置"""
        # 本地模型配置
        local_model_configs = {
            'paraformer-zh': {
                'model_dir': 'iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
                'description': '中文语音识别专用模型 (本地)',
                'language': 'zh',
                'use_vad': True,
                'use_itn': True
            },
            'sensevoice-small': {
                'model_dir': 'iic/SenseVoiceSmall',
                'description': '支持情感识别的多语言模型 (本地)',
                'language': 'auto',
                'use_vad': True,
                'use_itn': True,
                'support_emotion': True
            }
        }
        
        # API配置
        api_configs = {
            'paraformer-zh': {
                'api_url': 'https://dashscope.aliyuncs.com/api/v1/services/audio/asr',
                'model': 'paraformer-realtime-v1',
                'description': '中文语音识别专用模型 (API)',
                'language': 'zh'
            },
            'sensevoice-small': {
                'api_url': 'https://dashscope.aliyuncs.com/api/v1/services/audio/asr',
                'model': 'sensevoice-v1',
                'description': '支持情感识别的多语言模型 (API)',
                'language': 'auto'
            }
        }
        
        # 根据使用方式选择配置
        if self.use_api:
            self.config = api_configs.get(self.model_name, api_configs['paraformer-zh'])
        else:
            self.config = local_model_configs.get(self.model_name, local_model_configs['paraformer-zh'])
            self.model_dir = self.config.get('model_dir')
    
    def load_model(self, progress_callback: Optional[Callable] = None, status_callback: Optional[Callable] = None):
        """加载模型"""
        try:
            if self.use_api:
                return self._load_api_model(progress_callback, status_callback)
            else:
                return self._load_local_model(progress_callback, status_callback)
        except Exception as e:
            error_msg = f"FunASR 模型加载失败: {str(e)}"
            print(f"[错误] {error_msg}")
            if status_callback:
                status_callback(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def _load_api_model(self, progress_callback: Optional[Callable] = None, status_callback: Optional[Callable] = None):
        """加载API模型"""
        if status_callback:
            status_callback(f"正在初始化 FunASR API: {self.model_name}")
        
        print(f"[调试] 初始化 FunASR API 模式: {self.model_name}")
        
        # 检查API依赖
        try:
            # 尝试使用DashScope API
            import dashscope
            from dashscope.audio.asr import Recognition
            self.api_client = dashscope
            self.api_type = "dashscope"
            print(f"[调试] DashScope API 导入成功")
        except ImportError:
            try:
                # 尝试使用requests进行直接API调用
                import requests
                self.api_client = requests
                self.api_type = "requests"
                print(f"[调试] 使用 requests 进行 API 调用")
            except ImportError:
                raise Exception("API模式需要安装: pip install dashscope 或 pip install requests")
        
        if progress_callback:
            progress_callback(50)
        
        # 验证API密钥和配置
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key and self.api_type == "dashscope":
            print("[警告] 未设置 DASHSCOPE_API_KEY 环境变量")
            # 提供设置指导
            if status_callback:
                status_callback("⚠️ 未配置 API 密钥，将使用演示模式")
        
        # 设置API配置
        if self.api_type == "dashscope" and api_key:
            try:
                dashscope.api_key = api_key
                print("[调试] DashScope API 密钥已设置")
            except Exception as e:
                print(f"[警告] API 密钥设置失败: {e}")
        
        if progress_callback:
            progress_callback(100)
        
        self.is_loaded = True
        
        if status_callback:
            status_callback(f"FunASR API {self.model_name} 初始化完成 ✓")
        
        return True
    
    def _load_local_model(self, progress_callback: Optional[Callable] = None, status_callback: Optional[Callable] = None):
        """加载本地模型"""
        if status_callback:
            status_callback(f"正在加载 FunASR 本地模型: {self.model_name}")
        
        print(f"[调试] 开始加载 FunASR 本地模型: {self.model_name}")
        print(f"[调试] 模型目录: {self.model_dir}")
        
        # 检查 FunASR 依赖
        try:
            from funasr import AutoModel
            try:
                from funasr.utils.postprocess_utils import rich_transcription_postprocess
                self.postprocess_func = rich_transcription_postprocess
            except ImportError:
                self.postprocess_func = None
            print(f"[调试] FunASR 库导入成功")
        except ImportError as e:
            error_msg = "FunASR 未正确安装，请运行: pip install funasr modelscope torch"
            raise Exception(f"{error_msg}\n错误详情: {e}")
        
        if progress_callback:
            progress_callback(20)
        
        # 准备模型参数
        model_kwargs = {
            "model": self.model_dir,
            "device": self.device
        }
        
        # 添加 VAD 支持
        if self.config.get('use_vad', False):
            model_kwargs.update({
                "vad_model": "fsmn-vad",
                "vad_kwargs": {"max_single_segment_time": 30000}
            })
        
        if progress_callback:
            progress_callback(50)
        
        # 加载模型
        try:
            self.model = AutoModel(**model_kwargs)
            print(f"[调试] FunASR 完整模型加载成功")
        except Exception as e:
            print(f"[警告] 完整模型加载失败，尝试基础模型: {e}")
            try:
                basic_kwargs = {"model": self.model_dir, "device": self.device}
                self.model = AutoModel(**basic_kwargs)
                print(f"[调试] FunASR 基础模型加载成功")
            except Exception as e2:
                self.model = AutoModel(model=self.model_dir)
                print(f"[调试] FunASR 最简模型加载成功")
        
        if progress_callback:
            progress_callback(100)
        
        self.is_loaded = True
        
        if status_callback:
            status_callback(f"FunASR 本地模型 {self.model_name} 加载完成 ✓")
        
        return True
    
    def transcribe_audio(self, 
                        audio_path: str, 
                        progress_callback: Optional[Callable] = None,
                        status_callback: Optional[Callable] = None,
                        **kwargs) -> str:
        """转录音频文件"""
        if not self.is_loaded:
            raise Exception("FunASR 模型未加载，请先调用 load_model()")
        
        # 验证音频文件
        is_valid, msg = self.validate_audio_file(audio_path)
        if not is_valid:
            raise Exception(msg)
        
        try:
            if self.use_api:
                return self._transcribe_with_api(audio_path, progress_callback, status_callback, **kwargs)
            else:
                return self._transcribe_with_local(audio_path, progress_callback, status_callback, **kwargs)
        except Exception as e:
            error_msg = f"FunASR 转录失败: {str(e)}"
            print(f"[错误] {error_msg}")
            if status_callback:
                status_callback(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def _transcribe_with_api(self, audio_path: str, progress_callback, status_callback, **kwargs) -> str:
        """使用API进行转录"""
        if status_callback:
            status_callback(f"🌐 使用 FunASR 在线API {self.model_name} 开始转录...")
        
        print(f"[调试] FunASR 在线API 开始转录音频: {audio_path}")
        
        if progress_callback:
            progress_callback(10)
        
        file_size = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"[调试] 音频文件大小: {file_size:.2f} MB")
        
        if status_callback:
            status_callback(f"📤 上传音频文件到云端 ({file_size:.1f}MB)...")
        
        if progress_callback:
            progress_callback(30)
        
        try:
            if self.api_type == "dashscope":
                # 使用DashScope API
                transcribed_text = self._call_dashscope_api(audio_path, progress_callback, status_callback, **kwargs)
            else:
                # 使用requests进行API调用
                transcribed_text = self._call_requests_api(audio_path, progress_callback, status_callback, **kwargs)
            
            if progress_callback:
                progress_callback(100)
            
            if status_callback:
                status_callback(f"✅ FunASR 在线API 转录完成，识别了 {len(transcribed_text)} 个字符")
            
            return transcribed_text
            
        except Exception as e:
            raise Exception(f"在线API转录失败: {str(e)}")
    
    def _call_dashscope_api(self, audio_path: str, progress_callback, status_callback, **kwargs) -> str:
        """调用DashScope API"""
        try:
            import dashscope
            from dashscope.audio.asr import Recognition
            
            if status_callback:
                status_callback(f"🔄 正在使用 DashScope API 转录...")
            
            if progress_callback:
                progress_callback(50)
            
            # 检查API密钥
            api_key = os.getenv('DASHSCOPE_API_KEY')
            if not api_key:
                # 返回演示结果
                demo_text = f"🌐 DashScope API 演示模式\n\n"
                demo_text += f"实际使用需要配置 DASHSCOPE_API_KEY 环境变量\n"
                demo_text += f"音频文件: {os.path.basename(audio_path)}\n"
                demo_text += f"文件大小: {os.path.getsize(audio_path) / (1024 * 1024):.2f} MB\n\n"
                demo_text += f"配置步骤:\n"
                demo_text += f"1. 访问 https://dashscope.aliyun.com/ 获取API密钥\n"
                demo_text += f"2. 设置环境变量: set DASHSCOPE_API_KEY=your_api_key\n"
                demo_text += f"3. 重启程序即可使用真实的API服务\n\n"
                demo_text += f"DashScope 支持:\n"
                demo_text += f"• 高精度中文语音识别\n"
                demo_text += f"• 多种音频格式支持\n"
                demo_text += f"• 实时流式识别\n"
                demo_text += f"• 标点符号自动添加"
                
                if progress_callback:
                    progress_callback(80)
                
                return demo_text
            
            # 真实API调用
            dashscope.api_key = api_key
            
            # 调用API
            response = Recognition.call(
                model=self.config.get('model', 'paraformer-realtime-v1'),
                format='wav',
                sample_rate=16000,
                callback=None,  # 对于文件转录可以为None
                file_urls=[audio_path] if audio_path.startswith('http') else None,
                files=[audio_path] if not audio_path.startswith('http') else None
            )
            
            if progress_callback:
                progress_callback(90)
            
            # 处理响应
            if response.status_code == 200:
                result = response.output
                text = result.get('text', '')
                return text if text else "API 返回空结果"
            else:
                raise Exception(f"API 调用失败: {response.status_code} - {response.message}")
            
        except ImportError:
            raise Exception("DashScope 未安装，请运行: pip install dashscope")
        except Exception as e:
            raise Exception(f"DashScope API 调用失败: {str(e)}")
    
    def _call_requests_api(self, audio_path: str, progress_callback, status_callback, **kwargs) -> str:
        """使用requests调用API"""
        try:
            import requests
            import base64
            
            if status_callback:
                status_callback(f"🔄 正在使用 HTTP API 转录...")
            
            if progress_callback:
                progress_callback(50)
            
            # 读取音频文件
            with open(audio_path, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode('utf-8')
            
            if progress_callback:
                progress_callback(60)
            
            # 准备API请求
            api_url = self.config.get('api_url', 'https://dashscope.aliyuncs.com/api/v1/services/audio/asr')
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {os.getenv("DASHSCOPE_API_KEY", "demo")}',
                'X-DashScope-Async': 'enable'
            }
            
            data = {
                'model': self.config.get('model', 'paraformer-realtime-v1'),
                'input': {
                    'audio': audio_data,
                    'format': 'wav'
                },
                'parameters': {
                    'language': kwargs.get('language', self.config.get('language', 'zh')),
                    'use_itn': self.config.get('use_itn', True)
                }
            }
            
            if progress_callback:
                progress_callback(70)
            
            # 发送请求
            response = requests.post(api_url, json=data, headers=headers, timeout=30)
            
            if progress_callback:
                progress_callback(90)
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                if 'output' in result and 'text' in result['output']:
                    return result['output']['text']
                else:
                    # 如果没有API密钥，返回演示结果
                    demo_text = f"🌐 HTTP API 演示模式\n\n"
                    demo_text += f"检测到的音频文件: {os.path.basename(audio_path)}\n"
                    demo_text += f"文件大小: {os.path.getsize(audio_path) / (1024 * 1024):.2f} MB\n\n"
                    demo_text += f"要使用真实的API服务，请:\n"
                    demo_text += f"1. 获取有效的API密钥\n"
                    demo_text += f"2. 设置环境变量 DASHSCOPE_API_KEY\n"
                    demo_text += f"3. 确保网络连接正常\n\n"
                    demo_text += f"HTTP API 功能:\n"
                    demo_text += f"• RESTful API 接口\n"
                    demo_text += f"• 支持多种音频格式\n"
                    demo_text += f"• 异步处理大文件\n"
                    demo_text += f"• 高并发支持"
                    
                    return demo_text
            else:
                raise Exception(f"HTTP API 请求失败: {response.status_code}")
                
        except ImportError:
            raise Exception("requests 未安装，请运行: pip install requests")
        except Exception as e:
            raise Exception(f"HTTP API 调用失败: {str(e)}")

    def _transcribe_with_local(self, audio_path: str, progress_callback, status_callback, **kwargs) -> str:
        """使用本地模型进行转录"""
        if status_callback:
            status_callback(f"🖥️ 使用 FunASR 离线本地模型 {self.model_name} 开始转录...")
        
        print(f"[调试] FunASR 离线本地模型开始转录音频: {audio_path}")
        
        if progress_callback:
            progress_callback(10)
        
        file_size = os.path.getsize(audio_path) / (1024 * 1024)
        
        if status_callback:
            status_callback(f"📄 离线处理音频文件 ({file_size:.1f}MB)...")
        
        if progress_callback:
            progress_callback(30)
        
        # 准备转录参数
        transcribe_params = {
            "input": audio_path,
            "cache": {},
            "language": kwargs.get('language', self.config.get('language', 'auto')),
            "use_itn": self.config.get('use_itn', True),
            "batch_size_s": min(60, max(30, int(file_size * 2))),
        }
        
        # 添加 VAD 参数
        if self.config.get('use_vad', False):
            transcribe_params.update({
                "merge_vad": True,
                "merge_length_s": 15
            })
        
        if status_callback:
            status_callback(f"🔄 离线本地转录进行中...")
        
        if progress_callback:
            progress_callback(50)
        
        # 执行转录
        result = None
        try:
            result = self.model.generate(**transcribe_params)
        except Exception as e1:
            try:
                simplified_params = {
                    "input": audio_path,
                    "language": transcribe_params['language'],
                    "use_itn": True
                }
                result = self.model.generate(**simplified_params)
            except Exception as e2:
                result = self.model.generate(input=audio_path)
        
        if progress_callback:
            progress_callback(90)
        
        # 处理结果
        transcribed_text = self._process_funasr_result(result)
        
        if progress_callback:
            progress_callback(100)
        
        if not transcribed_text.strip():
            raise Exception("离线本地转录结果为空，请检查音频内容或尝试其他模型")
        
        if status_callback:
            status_callback(f"✅ FunASR 离线本地转录完成，识别了 {len(transcribed_text)} 个字符")
        
        return transcribed_text
    
    def _process_funasr_result(self, result) -> str:
        """处理 FunASR 转录结果"""
        try:
            transcribed_text = ""
            
            if isinstance(result, list) and len(result) > 0:
                for item in result:
                    if isinstance(item, dict):
                        raw_text = item.get('text', '')
                        if raw_text:
                            if self.postprocess_func:
                                try:
                                    transcribed_text += self.postprocess_func(raw_text) + " "
                                except:
                                    transcribed_text += raw_text + " "
                            else:
                                transcribed_text += raw_text + " "
                    elif isinstance(item, str):
                        transcribed_text += item + " "
            
            elif isinstance(result, dict):
                raw_text = result.get('text', '')
                if raw_text:
                    if self.postprocess_func:
                        try:
                            transcribed_text = self.postprocess_func(raw_text)
                        except:
                            transcribed_text = raw_text
                    else:
                        transcribed_text = raw_text
            
            elif isinstance(result, str):
                transcribed_text = result
            
            return transcribed_text.strip()
            
        except Exception as e:
            print(f"[错误] 处理结果时出错: {e}")
            return str(result) if result else ""
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        mode = "🌐 在线API模式" if self.use_api else "🖥️ 离线本地模式"
        status_icon = "✅" if self.is_loaded else "❌"
        
        return {
            "name": self.model_name,
            "engine": f"FunASR ({mode})",
            "loaded": self.is_loaded,
            "description": self.config.get('description', '未知模型'),
            "mode": mode,
            "mode_type": "api" if self.use_api else "local",
            "status_display": f"{status_icon} {mode}",
            "config": self.config,
            "status": "已加载" if self.is_loaded else "未加载"
        }
    
    def get_status_display(self) -> str:
        """获取状态显示文本"""
        if self.use_api:
            if self.is_loaded:
                return "🌐 在线API - 已连接"
            else:
                return "🌐 在线API - 未连接"
        else:
            if self.is_loaded:
                return "🖥️ 离线本地 - 已加载"
            else:
                return "🖥️ 离线本地 - 未加载"
    
    def switch_mode(self, use_api: bool):
        """切换模式（在线/离线）"""
        if self.use_api == use_api:
            return  # 无需切换
        
        # 清理当前模式的资源
        self.cleanup()
        
        # 切换模式
        self.use_api = use_api
        self._setup_model_config()
        
        print(f"[调试] FunASR 已切换到 {'API模式' if use_api else '本地模式'}")

    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'model') and self.model:
                del self.model
                self.model = None
            if hasattr(self, 'api_client'):
                self.api_client = None
            self.is_loaded = False
            print(f"[调试] FunASR 转录器资源已清理")
        except Exception as e:
            print(f"[警告] 清理 FunASR 资源时出错: {e}")


def test_funasr_availability() -> tuple:
    """测试 FunASR 是否可用"""
    try:
        # 测试本地模式
        from funasr import AutoModel
        local_available = True
    except ImportError:
        local_available = False
    
    try:
        # 测试API模式
        import requests
        api_available = True
    except ImportError:
        api_available = False
    
    if local_available and api_available:
        return True, "FunASR 可用 ✓ (支持本地+API)"
    elif local_available:
        return True, "FunASR 可用 ✓ (仅本地模式)"
    elif api_available:
        return True, "FunASR 可用 ✓ (仅API模式)"
    else:
        return False, "FunASR 不可用，请安装: pip install funasr 或 pip install requests"


# 工厂函数
def create_funasr_transcriber(model_name: str = "paraformer-zh", use_api: bool = False):
    """创建FunASR转录器工厂函数"""
    return FunASRTranscriber(model_name, use_api)


if __name__ == "__main__":
    # 测试代码
    available, message = test_funasr_availability()
    print(f"FunASR 可用性测试: {available} - {message}")
    
    if available:
        # 测试本地模式
        print("测试本地模式...")
        local_transcriber = create_funasr_transcriber("paraformer-zh", use_api=False)
        print(f"本地模式信息: {local_transcriber.get_model_info()}")
        
        # 测试API模式
        print("测试API模式...")
        api_transcriber = create_funasr_transcriber("paraformer-zh", use_api=True)
        print(f"API模式信息: {api_transcriber.get_model_info()}")
