from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                           QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox, 
                           QFileDialog, QMessageBox, QGroupBox, QTabWidget, 
                           QSlider, QLineEdit)
from PyQt5.QtCore import pyqtSignal, Qt


class AdvancedSettingsDialog(QWidget):
    """高级设置对话框"""
    settings_applied = pyqtSignal(dict)  # 添加信号用于传递设置
    
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("高级设置")
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # 设置窗口图标和样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton:pressed {
                background-color: #d9d9d9;
            }
        """)
        
        # 保存当前设置
        self.current_settings = current_settings or {}
        self.init_ui()
        self.load_current_settings()
        
        # 设置窗口居中
        self.center_window()
    
    def center_window(self):
        """将窗口居中显示"""
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # Whisper高级设置选项卡
        whisper_tab = self.create_whisper_tab()
        tab_widget.addTab(whisper_tab, "Whisper设置")
        
        # 音频处理设置选项卡
        audio_tab = self.create_audio_tab()
        tab_widget.addTab(audio_tab, "音频处理")
        
        # 性能设置选项卡
        performance_tab = self.create_performance_tab()
        tab_widget.addTab(performance_tab, "性能优化")
        
        # 输出设置选项卡
        output_tab = self.create_output_tab()
        tab_widget.addTab(output_tab, "输出设置")
        
        layout.addWidget(tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("应用")
        self.apply_button.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
        self.apply_button.clicked.connect(self.apply_settings)
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept_settings)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.close)
        
        self.reset_button = QPushButton("重置为默认")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_whisper_tab(self):
        """创建Whisper设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Whisper模型设置
        model_group = QGroupBox("模型设置")
        model_layout = QGridLayout()
        
        model_layout.addWidget(QLabel("温度参数:"), 0, 0)
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(0, 100)
        self.temperature_slider.setValue(0)
        self.temperature_label = QLabel("0.0")
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(f"{v/100:.1f}")
        )
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_label)
        model_layout.addLayout(temp_layout, 0, 1)
        
        model_layout.addWidget(QLabel("无语音阈值:"), 1, 0)
        self.no_speech_slider = QSlider(Qt.Horizontal)
        self.no_speech_slider.setRange(0, 100)
        self.no_speech_slider.setValue(60)
        self.no_speech_label = QLabel("0.6")
        self.no_speech_slider.valueChanged.connect(
            lambda v: self.no_speech_label.setText(f"{v/100:.1f}")
        )
        speech_layout = QHBoxLayout()
        speech_layout.addWidget(self.no_speech_slider)
        speech_layout.addWidget(self.no_speech_label)
        model_layout.addLayout(speech_layout, 1, 1)
        
        model_layout.addWidget(QLabel("压缩比阈值:"), 2, 0)
        self.compression_slider = QSlider(Qt.Horizontal)
        self.compression_slider.setRange(100, 500)
        self.compression_slider.setValue(240)
        self.compression_label = QLabel("2.4")
        self.compression_slider.valueChanged.connect(
            lambda v: self.compression_label.setText(f"{v/100:.1f}")
        )
        comp_layout = QHBoxLayout()
        comp_layout.addWidget(self.compression_slider)
        comp_layout.addWidget(self.compression_label)
        model_layout.addLayout(comp_layout, 2, 1)
        
        model_layout.addWidget(QLabel("对数概率阈值:"), 3, 0)
        self.logprob_slider = QSlider(Qt.Horizontal)
        self.logprob_slider.setRange(-300, 0)
        self.logprob_slider.setValue(-100)
        self.logprob_label = QLabel("-1.0")
        self.logprob_slider.valueChanged.connect(
            lambda v: self.logprob_label.setText(f"{v/100:.1f}")
        )
        log_layout = QHBoxLayout()
        log_layout.addWidget(self.logprob_slider)
        log_layout.addWidget(self.logprob_label)
        model_layout.addLayout(log_layout, 3, 1)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # 其他Whisper设置
        other_group = QGroupBox("其他设置")
        other_layout = QGridLayout()
        
        self.condition_on_previous_check = QCheckBox("基于前文条件")
        self.condition_on_previous_check.setChecked(True)
        other_layout.addWidget(self.condition_on_previous_check, 0, 0)
        
        self.word_timestamps_check = QCheckBox("单词级时间戳")
        other_layout.addWidget(self.word_timestamps_check, 0, 1)
        
        self.prepend_punctuations_check = QCheckBox("添加标点符号")
        self.prepend_punctuations_check.setChecked(True)
        other_layout.addWidget(self.prepend_punctuations_check, 1, 0)
        
        self.append_punctuations_check = QCheckBox("尾随标点符号")
        self.append_punctuations_check.setChecked(True)
        other_layout.addWidget(self.append_punctuations_check, 1, 1)
        
        other_group.setLayout(other_layout)
        layout.addWidget(other_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_audio_tab(self):
        """创建音频处理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 音频处理设置
        audio_group = QGroupBox("音频处理设置")
        audio_layout = QGridLayout()
        
        audio_layout.addWidget(QLabel("降噪强度:"), 0, 0)
        self.noise_reduction_slider = QSlider(Qt.Horizontal)
        self.noise_reduction_slider.setRange(0, 100)
        self.noise_reduction_slider.setValue(30)
        self.noise_reduction_label = QLabel("30%")
        self.noise_reduction_slider.valueChanged.connect(
            lambda v: self.noise_reduction_label.setText(f"{v}%")
        )
        noise_layout = QHBoxLayout()
        noise_layout.addWidget(self.noise_reduction_slider)
        noise_layout.addWidget(self.noise_reduction_label)
        audio_layout.addLayout(noise_layout, 0, 1)
        
        audio_layout.addWidget(QLabel("音量标准化:"), 1, 0)
        self.normalize_check = QCheckBox("启用音量标准化")
        self.normalize_check.setChecked(True)
        audio_layout.addWidget(self.normalize_check, 1, 1)
        
        audio_layout.addWidget(QLabel("静音检测:"), 2, 0)
        self.silence_detection_check = QCheckBox("启用静音检测")
        audio_layout.addWidget(self.silence_detection_check, 2, 1)
        
        audio_layout.addWidget(QLabel("音频格式:"), 3, 0)
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["WAV", "MP3", "FLAC"])
        audio_layout.addWidget(self.audio_format_combo, 3, 1)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # 音频分段设置
        segment_group = QGroupBox("音频分段设置")
        segment_layout = QGridLayout()
        
        self.auto_segment_check = QCheckBox("自动分段处理")
        segment_layout.addWidget(self.auto_segment_check, 0, 0)
        
        segment_layout.addWidget(QLabel("分段长度(分钟):"), 1, 0)
        self.segment_length_spin = QSpinBox()
        self.segment_length_spin.setRange(1, 60)
        self.segment_length_spin.setValue(10)
        segment_layout.addWidget(self.segment_length_spin, 1, 1)
        
        segment_group.setLayout(segment_layout)
        layout.addWidget(segment_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_performance_tab(self):
        """创建性能优化选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 处理设置
        processing_group = QGroupBox("处理设置")
        processing_layout = QGridLayout()
        
        self.multithread_check = QCheckBox("启用多线程处理")
        self.multithread_check.setChecked(True)
        processing_layout.addWidget(self.multithread_check, 0, 0)
        
        processing_layout.addWidget(QLabel("线程数:"), 0, 1)
        self.thread_count_spin = QSpinBox()
        self.thread_count_spin.setRange(1, 16)
        self.thread_count_spin.setValue(4)
        processing_layout.addWidget(self.thread_count_spin, 0, 2)
        
        self.gpu_check = QCheckBox("使用GPU加速（如果可用）")
        processing_layout.addWidget(self.gpu_check, 1, 0, 1, 2)
        
        self.memory_optimization_check = QCheckBox("内存优化模式")
        processing_layout.addWidget(self.memory_optimization_check, 2, 0, 1, 2)
        
        processing_group.setLayout(processing_layout)
        layout.addWidget(processing_group)
        
        # 缓存设置
        cache_group = QGroupBox("缓存设置")
        cache_layout = QGridLayout()
        
        self.enable_cache_check = QCheckBox("启用模型缓存")
        self.enable_cache_check.setChecked(True)
        cache_layout.addWidget(self.enable_cache_check, 0, 0)
        
        cache_layout.addWidget(QLabel("缓存路径:"), 1, 0)
        self.cache_path_edit = QLineEdit()
        self.cache_path_edit.setText("./whisper_cache")
        cache_layout.addWidget(self.cache_path_edit, 1, 1)
        
        self.browse_cache_button = QPushButton("浏览")
        self.browse_cache_button.clicked.connect(self.browse_cache_path)
        cache_layout.addWidget(self.browse_cache_button, 1, 2)
        
        cache_layout.addWidget(QLabel("最大缓存大小(GB):"), 2, 0)
        self.max_cache_size_spin = QSpinBox()
        self.max_cache_size_spin.setRange(1, 50)
        self.max_cache_size_spin.setValue(5)
        cache_layout.addWidget(self.max_cache_size_spin, 2, 1)
        
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_output_tab(self):
        """创建输出设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 文本输出设置
        text_group = QGroupBox("文本输出设置")
        text_layout = QGridLayout()
        
        text_layout.addWidget(QLabel("输出格式:"), 0, 0)
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["纯文本", "带时间戳", "SRT字幕", "VTT字幕", "JSON格式"])
        text_layout.addWidget(self.output_format_combo, 0, 1)
        
        self.include_confidence_check = QCheckBox("包含置信度分数")
        text_layout.addWidget(self.include_confidence_check, 1, 0, 1, 2)
        
        self.remove_disfluencies_check = QCheckBox("移除语音不流畅")
        text_layout.addWidget(self.remove_disfluencies_check, 2, 0, 1, 2)
        
        self.capitalize_sentences_check = QCheckBox("句首字母大写")
        self.capitalize_sentences_check.setChecked(True)
        text_layout.addWidget(self.capitalize_sentences_check, 3, 0, 1, 2)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)
        
        # 文件输出设置
        file_group = QGroupBox("文件输出设置")
        file_layout = QGridLayout()
        
        file_layout.addWidget(QLabel("默认输出目录:"), 0, 0)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText("./output")
        file_layout.addWidget(self.output_dir_edit, 0, 1)
        
        self.browse_output_button = QPushButton("浏览")
        self.browse_output_button.clicked.connect(self.browse_output_path)
        file_layout.addWidget(self.browse_output_button, 0, 2)
        
        self.auto_save_check = QCheckBox("自动保存结果")
        file_layout.addWidget(self.auto_save_check, 1, 0)
        
        self.backup_files_check = QCheckBox("创建备份文件")
        file_layout.addWidget(self.backup_files_check, 1, 1)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def browse_cache_path(self):
        """浏览缓存路径"""
        path = QFileDialog.getExistingDirectory(self, "选择缓存目录")
        if path:
            self.cache_path_edit.setText(path)
    
    def browse_output_path(self):
        """浏览输出路径"""
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_dir_edit.setText(path)
    
    def _safe_bool(self, value):
        """安全地转换为布尔值"""
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(value, (int, float)):
            return bool(value)
        else:
            return False
    
    def _safe_float(self, value, default=0.0):
        """安全地转换为浮点数"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                return float(value)
            else:
                return default
        except (ValueError, TypeError):
            return default
    
    def _safe_int(self, value, default=0):
        """安全地转换为整数"""
        try:
            if isinstance(value, (int, float)):
                return int(value)
            elif isinstance(value, str):
                return int(float(value))
            else:
                return default
        except (ValueError, TypeError):
            return default
    
    def load_current_settings(self):
        """加载当前设置"""
        if not self.current_settings:
            return
        
        try:
            # 使用安全转换函数加载Whisper设置
            temp_val = self._safe_float(self.current_settings.get('temperature', 0))
            self.temperature_slider.setValue(int(temp_val * 100))
            
            no_speech_val = self._safe_float(self.current_settings.get('no_speech_threshold', 0.6))
            self.no_speech_slider.setValue(int(no_speech_val * 100))
            
            comp_val = self._safe_float(self.current_settings.get('compression_ratio_threshold', 2.4))
            self.compression_slider.setValue(int(comp_val * 100))
            
            log_val = self._safe_float(self.current_settings.get('logprob_threshold', -1.0))
            self.logprob_slider.setValue(int(log_val * 100))
            
            # 加载布尔设置
            self.condition_on_previous_check.setChecked(
                self._safe_bool(self.current_settings.get('condition_on_previous', True))
            )
            self.word_timestamps_check.setChecked(
                self._safe_bool(self.current_settings.get('word_timestamps', False))
            )
            self.prepend_punctuations_check.setChecked(
                self._safe_bool(self.current_settings.get('prepend_punctuations', True))
            )
            self.append_punctuations_check.setChecked(
                self._safe_bool(self.current_settings.get('append_punctuations', True))
            )
            
            # 加载音频设置
            noise_val = self._safe_int(self.current_settings.get('noise_reduction', 30))
            self.noise_reduction_slider.setValue(noise_val)
            
            self.normalize_check.setChecked(
                self._safe_bool(self.current_settings.get('normalize_audio', True))
            )
            self.silence_detection_check.setChecked(
                self._safe_bool(self.current_settings.get('silence_detection', False))
            )
            
            # 加载性能设置
            self.multithread_check.setChecked(
                self._safe_bool(self.current_settings.get('multithread', True))
            )
            
            thread_val = self._safe_int(self.current_settings.get('thread_count', 4))
            self.thread_count_spin.setValue(thread_val)
            
            self.gpu_check.setChecked(
                self._safe_bool(self.current_settings.get('use_gpu', False))
            )
            self.memory_optimization_check.setChecked(
                self._safe_bool(self.current_settings.get('memory_optimization', False))
            )
            
            # 加载字符串设置
            cache_path = self.current_settings.get('cache_path', './whisper_cache')
            if isinstance(cache_path, str):
                self.cache_path_edit.setText(cache_path)
            
            output_dir = self.current_settings.get('output_directory', './output')
            if isinstance(output_dir, str):
                self.output_dir_edit.setText(output_dir)
            
        except Exception as e:
            print(f"[警告] 加载设置时出错: {e}")
            # 出错时使用默认值
            self.reset_to_defaults()
    
    def validate_settings(self):
        """验证设置的有效性"""
        errors = []
        
        # 验证路径
        cache_path = self.cache_path_edit.text().strip()
        if cache_path and not self._is_valid_path(cache_path):
            errors.append("缓存路径格式无效")
        
        output_dir = self.output_dir_edit.text().strip()
        if output_dir and not self._is_valid_path(output_dir):
            errors.append("输出目录路径格式无效")
        
        # 验证数值范围
        if self.thread_count_spin.value() < 1:
            errors.append("线程数必须大于0")
        
        if self.max_cache_size_spin.value() < 1:
            errors.append("缓存大小必须大于0")
        
        return errors
    
    def _is_valid_path(self, path):
        """检查路径格式是否有效"""
        import os
        try:
            os.path.normpath(path)
            return True
        except:
            return False
    
    def apply_settings(self):
        """应用设置"""
        # 验证设置
        errors = self.validate_settings()
        if errors:
            QMessageBox.warning(
                self, 
                "设置验证失败", 
                "以下设置存在问题:\n\n" + "\n".join(errors)
            )
            return
        
        settings = self.get_current_settings()
        self.settings_applied.emit(settings)
        QMessageBox.information(self, "成功", "设置已应用并验证通过")
    
    def accept_settings(self):
        """确定并关闭"""
        self.apply_settings()
        self.close()
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        reply = QMessageBox.question(
            self, 
            "确认重置", 
            "确定要重置所有设置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 重置所有控件为默认值
            self.temperature_slider.setValue(0)
            self.no_speech_slider.setValue(60)
            self.compression_slider.setValue(240)
            self.logprob_slider.setValue(-100)
            self.condition_on_previous_check.setChecked(True)
            self.word_timestamps_check.setChecked(False)
            self.prepend_punctuations_check.setChecked(True)
            self.append_punctuations_check.setChecked(True)
            
            self.noise_reduction_slider.setValue(30)
            self.normalize_check.setChecked(True)
            self.silence_detection_check.setChecked(False)
            self.audio_format_combo.setCurrentText("WAV")
            self.auto_segment_check.setChecked(False)
            self.segment_length_spin.setValue(10)
            
            self.multithread_check.setChecked(True)
            self.thread_count_spin.setValue(4)
            self.gpu_check.setChecked(False)
            self.memory_optimization_check.setChecked(False)
            self.enable_cache_check.setChecked(True)
            self.cache_path_edit.setText("./whisper_cache")
            self.max_cache_size_spin.setValue(5)
            
            self.output_format_combo.setCurrentText("纯文本")
            self.include_confidence_check.setChecked(False)
            self.remove_disfluencies_check.setChecked(False)
            self.capitalize_sentences_check.setChecked(True)
            self.output_dir_edit.setText("./output")
            self.auto_save_check.setChecked(False)
            self.backup_files_check.setChecked(False)
    
    def get_current_settings(self):
        """获取当前所有设置"""
        settings = {
            # Whisper设置
            'temperature': self.temperature_slider.value() / 100.0,
            'no_speech_threshold': self.no_speech_slider.value() / 100.0,
            'compression_ratio_threshold': self.compression_slider.value() / 100.0,
            'logprob_threshold': self.logprob_slider.value() / 100.0,
            'condition_on_previous': self.condition_on_previous_check.isChecked(),
            'word_timestamps': self.word_timestamps_check.isChecked(),
            'prepend_punctuations': self.prepend_punctuations_check.isChecked(),
            'append_punctuations': self.append_punctuations_check.isChecked(),
            
            # 音频处理设置
            'noise_reduction': self.noise_reduction_slider.value(),
            'normalize_audio': self.normalize_check.isChecked(),
            'silence_detection': self.silence_detection_check.isChecked(),
            'audio_format': self.audio_format_combo.currentText(),
            'auto_segment': self.auto_segment_check.isChecked(),
            'segment_length': self.segment_length_spin.value(),
            
            # 性能设置
            'multithread': self.multithread_check.isChecked(),
            'thread_count': self.thread_count_spin.value(),
            'use_gpu': self.gpu_check.isChecked(),
            'memory_optimization': self.memory_optimization_check.isChecked(),
            'enable_cache': self.enable_cache_check.isChecked(),
            'cache_path': self.cache_path_edit.text(),
            'max_cache_size': self.max_cache_size_spin.value(),
            
            # 输出设置
            'output_format': self.output_format_combo.currentText(),
            'include_confidence': self.include_confidence_check.isChecked(),
            'remove_disfluencies': self.remove_disfluencies_check.isChecked(),
            'capitalize_sentences': self.capitalize_sentences_check.isChecked(),
            'output_directory': self.output_dir_edit.text(),
            'auto_save': self.auto_save_check.isChecked(),
            'backup_files': self.backup_files_check.isChecked()
        }
        
        return settings
