import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QGridLayout, QLabel, QPushButton, QLineEdit, QTextEdit, 
                           QProgressBar, QComboBox, QSpinBox, QCheckBox, QFileDialog, 
                           QMessageBox, QGroupBox, QTabWidget, QSplitter, QStatusBar,
                           QMenuBar, QMenu, QToolBar, QTableWidget, QTableWidgetItem,
                           QApplication)
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QFont

from core.processing_thread import ProcessingThread
from ui.settings_dialog import AdvancedSettingsDialog
from utils.dependencies import WHISPER_AVAILABLE, get_version_info, check_ffmpeg, check_file_size, estimate_audio_duration


class VideoTextExtractor(QMainWindow):
    """主应用程序窗口"""
    
    def __init__(self):
        super().__init__()
        try:
            self.setWindowTitle("视频文本提取器 v3.0 (Whisper增强版)")
            self.setGeometry(100, 100, 1200, 800)
            
            # 应用程序设置
            self.settings = QSettings('VideoTextExtractor', 'Settings')
            
            # 初始化变量
            self.video_path = ""
            self.processing_thread = None
            self.whisper_model = None
            self.advanced_settings = {}  # 存储高级设置
            self.advanced_dialog = None  # 高级设置对话框引用
            
            # 检查依赖
            self.ffmpeg_available = check_ffmpeg()
            self.version_info = get_version_info()
            
            # 初始化界面
            self.init_ui()
            self.setup_menu_bar()
            self.setup_toolbar()
            self.setup_status_bar()
            
            # 加载设置
            self.load_settings()
            
            print("[调试] 应用程序初始化完成")
            
        except Exception as e:
            print(f"[错误] 初始化失败: {e}")
            import traceback
            print(f"[错误跟踪]\n{traceback.format_exc()}")
            QMessageBox.critical(None, "初始化错误", f"程序初始化失败:\n\n{str(e)}")
            raise
    
    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 设置背景图片
        try:
            bg_path = os.path.join(os.path.dirname(__file__), "..", "壁纸.png")
            if os.path.exists(bg_path):
                central_widget.setStyleSheet(f"""
                    QWidget#central_widget {{
                        background-image: url({bg_path.replace(chr(92), '/')});
                        background-repeat: no-repeat;
                        background-position: center;
                        background-attachment: fixed;
                    }}
                    QGroupBox {{
                        background-color: rgba(255, 255, 255, 230);
                        border: 2px solid #cccccc;
                        border-radius: 8px;
                        margin-top: 1ex;
                        padding-top: 10px;
                        font-weight: bold;
                    }}
                    QGroupBox::title {{
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px 0 5px;
                        background-color: rgba(255, 255, 255, 200);
                        border-radius: 3px;
                    }}
                    QTabWidget::pane {{
                        background-color: rgba(255, 255, 255, 200);
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                    }}
                    QTabBar::tab {{
                        background-color: rgba(240, 240, 240, 200);
                        border: 1px solid #cccccc;
                        padding: 5px 10px;
                        margin-right: 2px;
                    }}
                    QTabBar::tab:selected {{
                        background-color: rgba(255, 255, 255, 230);
                        border-bottom: none;
                    }}
                    QTextEdit, QLineEdit, QComboBox, QSpinBox {{
                        background-color: rgba(255, 255, 255, 230);
                        border: 1px solid #cccccc;
                        border-radius: 3px;
                        padding: 3px;
                    }}
                    QPushButton {{
                        background-color: rgba(240, 240, 240, 230);
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: rgba(230, 230, 230, 230);
                    }}
                    QPushButton:pressed {{
                        background-color: rgba(220, 220, 220, 230);
                    }}
                """)
                central_widget.setObjectName("central_widget")
                print(f"[调试] 背景图片已加载: {bg_path}")
            else:
                print(f"[警告] 背景图片文件不存在: {bg_path}")
        except Exception as e:
            print(f"[错误] 设置背景图片失败: {e}")
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 创建可调整大小的分割面板
        splitter = QSplitter()
        splitter.setOrientation(1)  # Qt.Vertical
        main_layout.addWidget(splitter)
        
        # 顶部面板 - 控制和设置
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_widget.setLayout(top_layout)
        
        # 文件选择
        self.create_file_selection(top_layout)
        
        # 设置选项卡
        self.create_settings_tabs(top_layout)
        
        # 控制按钮
        self.create_control_buttons(top_layout)
        
        # 进度和状态
        self.create_progress_section(top_layout)
        
        splitter.addWidget(top_widget)
        
        # 底部面板 - 结果
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout()
        bottom_widget.setLayout(bottom_layout)
        
        # 结果选项卡
        self.create_results_section(bottom_layout)
        
        splitter.addWidget(bottom_widget)
        
        # 设置分割器大小
        splitter.setSizes([400, 400])
    
    def create_file_selection(self, parent_layout):
        """创建文件选择区域"""
        file_group = QGroupBox("文件选择")
        file_layout = QHBoxLayout()
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择视频文件...")
        self.browse_button = QPushButton("浏览")
        self.browse_button.clicked.connect(self.browse_file)
        
        self.file_info_label = QLabel("未选择文件")
        self.file_info_label.setStyleSheet("color: gray;")
        
        file_layout.addWidget(QLabel("视频文件:"))
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_button)
        
        file_group_layout = QVBoxLayout()
        file_group_layout.addLayout(file_layout)
        file_group_layout.addWidget(self.file_info_label)
        file_group.setLayout(file_group_layout)
        
        parent_layout.addWidget(file_group)
    
    def create_settings_tabs(self, parent_layout):
        """创建设置选项卡"""
        settings_group = QGroupBox("识别设置")
        settings_layout = QVBoxLayout()
        
        # 创建选项卡组件
        self.settings_tabs = QTabWidget()
        
        # 基础设置选项卡
        basic_tab = QWidget()
        basic_layout = QGridLayout()
        
        # 语言选择
        basic_layout.addWidget(QLabel("语言:"), 0, 0)
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "自动检测", "中文", "英文", "日文", "韩文"
        ])
        basic_layout.addWidget(self.language_combo, 0, 1)
        
        # 音频质量
        basic_layout.addWidget(QLabel("音频质量:"), 1, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["低", "中", "高"])
        self.quality_combo.setCurrentText("中")
        basic_layout.addWidget(self.quality_combo, 1, 1)
        
        # 保存音频选项
        self.save_audio_check = QCheckBox("保存提取的音频文件")
        basic_layout.addWidget(self.save_audio_check, 2, 0, 1, 2)
        
        basic_tab.setLayout(basic_layout)
        self.settings_tabs.addTab(basic_tab, "基础设置")
        
        # Whisper设置选项卡
        if WHISPER_AVAILABLE:
            whisper_tab = QWidget()
            whisper_layout = QGridLayout()
            
            # 模型大小
            whisper_layout.addWidget(QLabel("Whisper模型:"), 0, 0)
            self.whisper_model_combo = QComboBox()
            self.whisper_model_combo.addItems(["tiny", "base", "small", "medium", "large"])
            self.whisper_model_combo.setCurrentText("base")
            whisper_layout.addWidget(self.whisper_model_combo, 0, 1)
            
            # 模型信息
            model_info = QLabel("tiny: 最快 | base: 推荐 | large: 最准确")
            model_info.setStyleSheet("font-size: 10px; color: gray;")
            whisper_layout.addWidget(model_info, 1, 0, 1, 2)
            
            # Beam大小
            whisper_layout.addWidget(QLabel("Beam大小:"), 2, 0)
            self.beam_size_spin = QSpinBox()
            self.beam_size_spin.setRange(1, 10)
            self.beam_size_spin.setValue(3)  # CPU友好的默认值
            whisper_layout.addWidget(self.beam_size_spin, 2, 1)
            
            # Beam大小提示
            beam_info = QLabel("CPU建议使用3-5，GPU可使用更高值")
            beam_info.setStyleSheet("font-size: 9px; color: gray;")
            whisper_layout.addWidget(beam_info, 3, 0, 1, 2)
            
            # 显示时间戳
            self.timestamps_check = QCheckBox("显示时间戳")
            whisper_layout.addWidget(self.timestamps_check, 4, 0, 1, 2)
            
            # GPU加速选项
            self.use_gpu_check = QCheckBox("使用GPU加速（如果可用）")
            self.use_gpu_check.setEnabled(self.check_gpu_available())
            whisper_layout.addWidget(self.use_gpu_check, 5, 0, 1, 2)
            
            # GPU状态提示
            gpu_status = self.get_gpu_status_text()
            gpu_label = QLabel(gpu_status)
            gpu_label.setStyleSheet("font-size: 9px; color: gray;")
            whisper_layout.addWidget(gpu_label, 6, 0, 1, 2)
            
            whisper_tab.setLayout(whisper_layout)
            self.settings_tabs.addTab(whisper_tab, "Whisper设置")
        
        settings_layout.addWidget(self.settings_tabs)
        settings_group.setLayout(settings_layout)
        parent_layout.addWidget(settings_group)
    
    def check_gpu_available(self):
        """检查GPU是否可用"""
        try:
            import torch
            if torch.cuda.is_available():
                # 检查GPU内存
                gpu_memory = torch.cuda.get_device_properties(0).total_memory
                gpu_memory_gb = gpu_memory / (1024**3)
                print(f"[调试] GPU内存: {gpu_memory_gb:.1f} GB")
                return gpu_memory_gb >= 2.0  # 至少需要2GB内存
            return False
        except:
            return False
    
    def get_gpu_status_text(self):
        """获取GPU状态文本"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory
                gpu_memory_gb = gpu_memory / (1024**3)
                return f"检测到GPU: {gpu_name} ({gpu_memory_gb:.1f}GB)"
            else:
                return "未检测到CUDA GPU，将使用CPU处理"
        except:
            return "PyTorch未安装，将使用CPU处理"
    
    def create_control_buttons(self, parent_layout):
        """创建控制按钮"""
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始提取")
        self.start_button.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
        self.start_button.clicked.connect(self.start_extraction)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_extraction)
        
        self.clear_button = QPushButton("清空")
        self.clear_button.clicked.connect(self.clear_results)
        
        self.settings_button = QPushButton("高级设置")
        self.settings_button.clicked.connect(self.show_advanced_settings)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.settings_button)
        button_layout.addStretch()
        
        parent_layout.addLayout(button_layout)
    
    def create_progress_section(self, parent_layout):
        """创建进度区域"""
        progress_group = QGroupBox("进度")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.status_label = QLabel("就绪 - 请选择视频文件")
        
        # 添加文件分割进度条
        self.segment_progress_bar = QProgressBar()
        self.segment_progress_bar.setRange(0, 100)
        self.segment_progress_bar.setValue(0)
        self.segment_progress_bar.setFormat("分段进度: %p%")
        self.segment_progress_bar.hide()
        
        # 添加Whisper进度显示
        self.whisper_status_label = QLabel("")
        self.whisper_status_label.setStyleSheet("""
            color: #2196F3; 
            font-size: 11px; 
            font-family: 'Consolas', 'Monaco', monospace;
            background-color: rgba(255, 255, 255, 200);
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 8px;
            margin: 2px;
        """)
        self.whisper_status_label.setWordWrap(True)
        self.whisper_status_label.hide()
        
        # 添加处理详情显示
        self.processing_details_label = QLabel("")
        self.processing_details_label.setStyleSheet("""
            color: #4CAF50; 
            font-size: 10px;
            background-color: rgba(255, 255, 255, 180);
            border: 1px solid #c8e6c9;
            border-radius: 3px;
            padding: 5px;
            margin: 1px;
        """)
        self.processing_details_label.setWordWrap(True)
        self.processing_details_label.hide()
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.segment_progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.processing_details_label)
        progress_layout.addWidget(self.whisper_status_label)
        
        progress_group.setLayout(progress_layout)
        parent_layout.addWidget(progress_group)
    
    def create_results_section(self, parent_layout):
        """创建结果区域"""
        results_group = QGroupBox("结果")
        results_layout = QVBoxLayout()
        
        # 为不同视图创建选项卡
        self.results_tabs = QTabWidget()
        
        # 文本结果选项卡
        text_tab = QWidget()
        text_layout = QVBoxLayout()
        
        self.text_display = QTextEdit()
        self.text_display.setPlaceholderText("提取结果将在此处显示...")
        self.text_display.setFont(QFont("Consolas", 10))
        
        # 文本控制
        text_controls = QHBoxLayout()
        self.save_button = QPushButton("保存文本")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_text)
        
        self.copy_button = QPushButton("复制全部")
        self.copy_button.clicked.connect(self.copy_text)
        
        text_controls.addWidget(self.save_button)
        text_controls.addWidget(self.copy_button)
        text_controls.addStretch()
        
        text_layout.addWidget(self.text_display)
        text_layout.addLayout(text_controls)
        text_tab.setLayout(text_layout)
        
        self.results_tabs.addTab(text_tab, "文本结果")
        
        # 统计选项卡
        stats_tab = QWidget()
        stats_layout = QVBoxLayout()
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["属性", "值"])
        
        stats_layout.addWidget(self.stats_table)
        stats_tab.setLayout(stats_layout)
        
        self.results_tabs.addTab(stats_tab, "统计信息")
        
        results_layout.addWidget(self.results_tabs)
        results_group.setLayout(results_layout)
        parent_layout.addWidget(results_group)
    
    def setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        open_action = file_menu.addAction('打开视频')
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.browse_file)
        
        file_menu.addSeparator()
        
        save_action = file_menu.addAction('保存结果')
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_text)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('退出')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑')
        
        copy_action = edit_menu.addAction('复制全部')
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(self.copy_text)
        
        clear_action = edit_menu.addAction('清空结果')
        clear_action.setShortcut('Ctrl+L')
        clear_action.triggered.connect(self.clear_results)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具')
        
        start_action = tools_menu.addAction('开始提取')
        start_action.setShortcut('F5')
        start_action.triggered.connect(self.start_extraction)
        
        stop_action = tools_menu.addAction('停止提取')
        stop_action.setShortcut('Esc')
        stop_action.triggered.connect(self.stop_extraction)
        
        tools_menu.addSeparator()
        
        advanced_action = tools_menu.addAction('高级设置')
        advanced_action.setShortcut('F2')
        advanced_action.triggered.connect(self.show_advanced_settings)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        about_action = help_menu.addAction('关于')
        about_action.setShortcut('F1')
        about_action.triggered.connect(self.show_about)
        
        help_action = help_menu.addAction('使用帮助')
        help_action.triggered.connect(self.show_help)
    
    def setup_toolbar(self):
        """设置工具栏"""
        toolbar = self.addToolBar('主工具栏')
        toolbar.setMovable(False)
        
        # 文件操作
        open_action = toolbar.addAction('打开')
        open_action.setToolTip('打开视频文件 (Ctrl+O)')
        open_action.triggered.connect(self.browse_file)
        
        toolbar.addSeparator()
        
        # 处理操作
        start_action = toolbar.addAction('开始')
        start_action.setToolTip('开始文本提取 (F5)')
        start_action.triggered.connect(self.start_extraction)
        
        stop_action = toolbar.addAction('停止')
        stop_action.setToolTip('停止处理 (Esc)')
        stop_action.triggered.connect(self.stop_extraction)
        
        toolbar.addSeparator()
        
        # 结果操作
        save_action = toolbar.addAction('保存')
        save_action.setToolTip('保存结果 (Ctrl+S)')
        save_action.triggered.connect(self.save_text)
        
        copy_action = toolbar.addAction('复制')
        copy_action.setToolTip('复制全部文本 (Ctrl+C)')
        copy_action.triggered.connect(self.copy_text)
        
        clear_action = toolbar.addAction('清空')
        clear_action.setToolTip('清空结果 (Ctrl+L)')
        clear_action.triggered.connect(self.clear_results)
        
        toolbar.addSeparator()
        
        # 设置操作
        settings_action = toolbar.addAction('设置')
        settings_action.setToolTip('高级设置 (F2)')
        settings_action.triggered.connect(self.show_advanced_settings)
    
    def setup_status_bar(self):
        """设置状态栏"""
        self.statusBar().showMessage("就绪 - 请选择视频文件")
        
        # 添加永久状态标签
        self.permanent_status = QLabel()
        self.permanent_status.setText("Whisper: 可用" if WHISPER_AVAILABLE else "Whisper: 不可用")
        self.statusBar().addPermanentWidget(self.permanent_status)
        
        # 添加GPU状态
        gpu_status = "GPU: 可用" if self.check_gpu_available() else "GPU: 不可用"
        self.gpu_status_label = QLabel(gpu_status)
        self.statusBar().addPermanentWidget(self.gpu_status_label)
    
    def start_extraction(self):
        """开始文本提取过程"""
        try:
            if not self.video_path:
                QMessageBox.warning(self, "警告", "请先选择视频文件")
                return
            
            if not os.path.exists(self.video_path):
                QMessageBox.critical(self, "错误", "文件不存在")
                return
            
            # 检查Whisper可用性
            if not WHISPER_AVAILABLE:
                reply = QMessageBox.question(
                    self, 
                    "Whisper不可用", 
                    "Whisper引擎未安装，无法进行语音识别。\n\n"
                    "是否要打开安装说明？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.show_installation_help()
                return
            
            # 检查文件大小
            needs_split, file_size_gb, segments_needed = check_file_size(self.video_path)
            
            if needs_split:
                # 显示大文件处理提醒
                duration = estimate_audio_duration(self.video_path)
                duration_text = f"{int(duration//60)}分{int(duration%60)}秒" if duration else "未知"
                
                reply = QMessageBox.question(
                    self,
                    "大文件处理",
                    f"检测到大文件 ({file_size_gb:.1f}GB, 时长约{duration_text})\n\n"
                    f"将自动分割为 {segments_needed} 个片段进行处理。\n"
                    f"这可能需要较长时间，是否继续？",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
                
                # 显示分段进度条
                self.segment_progress_bar.show()
                self.segment_progress_bar.setMaximum(segments_needed)
                self.segment_progress_bar.setValue(0)
            
            # 获取设置
            settings = {
                'language': self.language_combo.currentText(),
                'quality': self.quality_combo.currentText(),
                'save_audio': self.save_audio_check.isChecked(),
                'whisper_model': self.whisper_model_combo.currentText() if WHISPER_AVAILABLE else 'base',
                'beam_size': self.beam_size_spin.value() if WHISPER_AVAILABLE else 3,
                'show_timestamps': self.timestamps_check.isChecked() if WHISPER_AVAILABLE else False,
                'use_gpu': self.use_gpu_check.isChecked() if WHISPER_AVAILABLE and hasattr(self, 'use_gpu_check') else False,
                'file_size_gb': file_size_gb,
                'needs_split': needs_split,
                'segments_needed': segments_needed
            }
            
            # 合并高级设置
            settings.update(self.advanced_settings)
            
            # 禁用控件
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.browse_button.setEnabled(False)
            
            # 清空结果
            self.text_display.clear()
            self.progress_bar.setValue(0)
            
            # 显示处理状态标签
            self.whisper_status_label.show()
            self.whisper_status_label.setText("准备开始处理...")
            self.processing_details_label.show()
            self.processing_details_label.setText(f"文件大小: {file_size_gb:.1f}GB | 分段: {segments_needed if needs_split else 1}")
              # 启动处理线程
            self.processing_thread = ProcessingThread(self.video_path, settings)
            self.processing_thread.progress_updated.connect(self.update_progress)
            self.processing_thread.status_updated.connect(self.update_status)
            self.processing_thread.result_ready.connect(self.display_result)
            self.processing_thread.error_occurred.connect(self.handle_error)
            self.processing_thread.whisper_progress.connect(self.update_whisper_progress)
            self.processing_thread.segment_progress.connect(self.update_segment_progress)
            self.processing_thread.processing_details.connect(self.update_processing_details)
            
            # 连接调试输出信号（如果存在）
            if hasattr(self.processing_thread, 'debug_output'):
                self.processing_thread.debug_output.connect(self.handle_debug_output)
            
            self.processing_thread.start()
            
        except Exception as e:
            print(f"[错误] 开始提取时发生错误: {e}")
            QMessageBox.critical(self, "启动错误", f"启动处理时发生错误:\n\n{str(e)}")
            self.reset_ui_state()
    
    def stop_extraction(self):
        """停止提取过程"""
        if self.processing_thread:
            self.processing_thread.stop()
            self.processing_thread.wait()
        
        self.update_status("用户停止")
        self.reset_ui_state()
        
        # 隐藏Whisper状态
        if hasattr(self, 'whisper_status_label'):
            self.whisper_status_label.hide()
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        """更新状态信息"""
        self.status_label.setText(message)
        self.statusBar().showMessage(message)
    
    def update_segment_progress(self, current_segment, total_segments, segment_info=""):
        """更新分段进度"""
        if hasattr(self, 'segment_progress_bar'):
            self.segment_progress_bar.setValue(current_segment)
            self.segment_progress_bar.setFormat(f"分段进度: {current_segment}/{total_segments} - {segment_info}")
    
    def update_processing_details(self, details):
        """更新处理详情"""
        if hasattr(self, 'processing_details_label'):
            self.processing_details_label.setText(details)
            QApplication.processEvents()

    def update_whisper_progress(self, message):
        """更新Whisper进度显示"""
        if hasattr(self, 'whisper_status_label'):
            # 解析进度信息，增强可视化
            if "%" in message:
                # 提取百分比
                try:
                    percent_start = message.find('[')
                    percent_end = message.find('%]')
                    if percent_start != -1 and percent_end != -1:
                        percent_str = message[percent_start+1:percent_end]
                        percent = float(percent_str.split('%')[0])
                        
                        # 创建进度条效果
                        bar_length = 30
                        filled_length = int(bar_length * percent / 100)
                        bar = '█' * filled_length + '░' * (bar_length - filled_length)
                        
                        formatted_message = f"🎵 Whisper处理中: [{bar}] {percent:.1f}%\n{message}"
                    else:
                        formatted_message = f"🎵 {message}"
                except:
                    formatted_message = f"🎵 {message}"
            else:
                formatted_message = f"🎵 {message}"
            
            current_text = self.whisper_status_label.text()
            lines = current_text.split('\n') if current_text else []
            lines.append(formatted_message)
            
            # 保留最近的10行
            if len(lines) > 10:
                lines = lines[-10:]
            
            self.whisper_status_label.setText('\n'.join(lines))
            QApplication.processEvents()
    
    def display_result(self, text):
        """显示提取结果"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result_header = f"\n提取结果 ({timestamp})\n"
        result_header += "=" * 50 + "\n\n"
        
        self.text_display.append(result_header)
        self.text_display.append(text)
        
        footer = f"\n\n" + "=" * 50 + "\n"
        footer += f"处理完成！提取了 {len(text)} 个字符\n"
        footer += f"完成时间: {timestamp}"
        
        self.text_display.append(footer)
        
        # 更新统计信息
        self.update_statistics(text, timestamp)
        
        self.save_button.setEnabled(True)
        self.reset_ui_state()
        
        # 隐藏Whisper状态标签
        if hasattr(self, 'whisper_status_label'):
            self.whisper_status_label.hide()
    
    def update_statistics(self, text, timestamp):
        """更新统计表格"""
        stats = [
            ("文本长度", f"{len(text)} 个字符"),
            ("单词数量", f"{len(text.split())} 个单词"),
            ("行数", f"{text.count(chr(10)) + 1} 行"),
            ("处理时间", timestamp),
            ("使用模型", self.whisper_model_combo.currentText() if WHISPER_AVAILABLE else "不适用"),
            ("语言", self.language_combo.currentText()),
            ("音频质量", self.quality_combo.currentText())
        ]
        
        self.stats_table.setRowCount(len(stats))
        for i, (prop, value) in enumerate(stats):
            self.stats_table.setItem(i, 0, QTableWidgetItem(prop))
            self.stats_table.setItem(i, 1, QTableWidgetItem(value))
        
        self.stats_table.resizeColumnsToContents()
    
    def handle_error(self, error_message):
        """处理错误 - 增强版，输出详细错误信息到终端和界面"""
        
        # 输出到终端（控制台）
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[错误 {timestamp}] 处理失败")
        print("=" * 60)
        print(error_message)
        print("=" * 60)
        
        # 显示错误对话框（简化版本，避免过长）
        # 提取主要错误信息（前200个字符）
        short_error = error_message[:200] + "..." if len(error_message) > 200 else error_message
        QMessageBox.critical(self, "处理错误", f"处理过程中发生错误:\n\n{short_error}\n\n详细信息请查看控制台输出。")
        
        # 将完整错误信息添加到结果显示区域
        error_info = f"\n\n❌ 错误 ({datetime.now().strftime('%H:%M:%S')})\n"
        error_info += "=" * 50 + "\n"
        error_info += error_message + "\n"
        error_info += "=" * 50 + "\n"
        
        self.text_display.append(error_info)
        
        # 同时在处理详情中显示错误
        if hasattr(self, 'processing_details_label'):
            self.processing_details_label.setText(f"❌ 处理失败 - 详情请查看结果区域")
            self.processing_details_label.setStyleSheet("""
                color: #f44336; 
                font-size: 10px;
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid #ffcdd2;
                border-radius: 3px;
                padding: 5px;
            """)
        
        # 重置UI状态
        self.reset_ui_state()
        
        # 隐藏Whisper状态标签
        if hasattr(self, 'whisper_status_label'):
            self.whisper_status_label.hide()
    
    def handle_debug_output(self, debug_message):
        """处理调试输出"""
        # 输出到终端
        print(f"[调试] {debug_message}")
        
        # 如果有处理详情标签，也显示在那里
        if hasattr(self, 'processing_details_label'):
            self.processing_details_label.setText(debug_message)
    
    def browse_file(self):
        """浏览视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;所有文件 (*)"
        )
        
        if file_path:
            self.video_path = file_path
            self.file_path_edit.setText(file_path)
            self.update_file_info(file_path)
            self.clear_results()
    
    def update_file_info(self, file_path):
        """更新文件信息显示"""
        try:
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            if size_mb < 1024:
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = f"{size_mb/1024:.1f} GB"
            
            filename = os.path.basename(file_path)
            
            if size_mb > 1000:
                suggestion = "大文件，处理时间可能较长"
                color = "orange"
            elif size_mb > 100:
                suggestion = "中等文件大小"
                color = "blue"
            else:
                suggestion = "小文件，处理速度快"
                color = "green"
            
            self.file_info_label.setText(f"{filename} | {size_str} | {suggestion}")
            self.file_info_label.setStyleSheet(f"color: {color};")
            
        except Exception as e:
            self.file_info_label.setText(f"无法读取文件信息: {e}")
            self.file_info_label.setStyleSheet("color: red;")
    
    def save_text(self):
        """保存提取的文本到文件"""
        text = self.text_display.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "没有文本可保存")
            return
        
        # 生成默认文件名
        if self.video_path:
            base_name = os.path.splitext(os.path.basename(self.video_path))[0]
            default_name = f"{base_name}_提取_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        else:
            default_name = f"提取文本_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存文本文件",
            default_name,
            "文本文件 (*.txt);;Markdown文件 (*.md);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "成功", f"文本已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def copy_text(self):
        """复制所有文本到剪贴板"""
        text = self.text_display.toPlainText()
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage("文本已复制到剪贴板", 2000)
    
    def clear_results(self):
        """清空所有结果"""
        self.text_display.clear()
        self.stats_table.clear()
        self.stats_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.save_button.setEnabled(False)
        self.update_status("就绪 - 请选择视频文件")
        
        # 隐藏并清空Whisper状态
        if hasattr(self, 'whisper_status_label'):
            self.whisper_status_label.hide()
            self.whisper_status_label.setText("")
    
    def show_advanced_settings(self):
        """显示高级设置对话框"""
        # 如果对话框已经打开，就将其置于前台
        if self.advanced_dialog and self.advanced_dialog.isVisible():
            self.advanced_dialog.raise_()
            self.advanced_dialog.activateWindow()
            return
        
        # 创建新的高级设置对话框
        self.advanced_dialog = AdvancedSettingsDialog(self, self.advanced_settings)
        self.advanced_dialog.settings_applied.connect(self.on_advanced_settings_applied)
        
        # 显示对话框
        self.advanced_dialog.show()
        
        # 确保对话框在前台
        self.advanced_dialog.raise_()
        self.advanced_dialog.activateWindow()
    
    def on_advanced_settings_applied(self, settings):
        """处理高级设置应用事件"""
        self.advanced_settings = settings
        print(f"[调试] 高级设置已更新: {len(settings)} 个设置项")
        
        # 保存高级设置到QSettings
        for key, value in settings.items():
            self.settings.setValue(f'advanced_{key}', value)
    
    def show_installation_help(self):
        """显示安装帮助"""
        help_text = """
安装Whisper指南

请按照以下步骤安装Whisper:

1. 打开命令提示符或终端
2. 运行以下命令:
   pip install openai-whisper

3. 如果遇到网络问题，可以使用国内镜像:
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple openai-whisper

4. 安装完成后重启本程序
        """
        QMessageBox.information(self, "安装帮助", help_text.strip())
    
    def show_about(self):
        """显示关于对话框"""
        gpu_info = "可用" if self.check_gpu_available() else "不可用"
        gpu_details = self.get_gpu_status_text()
        
        about_text = f"""
视频文本提取器 v3.0 (Whisper增强版)

使用OpenAI的Whisper从视频文件中提取文本的强大工具。

系统信息:
• Python版本: {sys.version.split()[0]}
• MoviePy: {self.version_info.get('moviepy', '未知')}
• FFmpeg: {'可用' if self.ffmpeg_available else '不可用'}
• Whisper: {'可用' if WHISPER_AVAILABLE else '不可用'}
• PyQt5: 可用
• GPU支持: {gpu_info}
• {gpu_details}

© 2024 视频文本提取器
        """
        QMessageBox.about(self, "关于视频文本提取器", about_text.strip())
    
    def show_help(self):
        """显示使用帮助"""
        help_text = """
视频文本提取器 - 使用帮助

基本使用流程:
1. 点击"浏览"按钮选择视频文件
2. 在"识别设置"中配置语言和质量
3. 如果有GPU，可以在"Whisper设置"中启用GPU加速
4. 点击"开始提取"开始处理
5. 等待处理完成，查看提取结果
6. 可以保存或复制结果文本

快捷键:
• Ctrl+O: 打开视频文件
• F5: 开始提取
• Esc: 停止处理
• Ctrl+S: 保存结果
• Ctrl+C: 复制全部文本
• Ctrl+L: 清空结果
• F2: 打开高级设置
• F1: 关于程序
        """
        help_dialog = QMessageBox(self)
        help_dialog.setWindowTitle("使用帮助")
        help_dialog.setText(help_text.strip())
        help_dialog.setIcon(QMessageBox.Information)
        help_dialog.exec_()
    
    def reset_ui_state(self):
        """重置UI状态"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.browse_button.setEnabled(True)
        
        # 隐藏处理进度显示
        if hasattr(self, 'segment_progress_bar'):
            self.segment_progress_bar.hide()
        if hasattr(self, 'processing_details_label'):
            self.processing_details_label.hide()
        if hasattr(self, 'whisper_status_label'):
            self.whisper_status_label.hide()

    def load_settings(self):
        """加载应用程序设置"""
        # 从QSettings加载之前的设置
        self.language_combo.setCurrentText(self.settings.value('language', '自动检测'))
        self.quality_combo.setCurrentText(self.settings.value('quality', '中'))
        
        if WHISPER_AVAILABLE:
            self.whisper_model_combo.setCurrentText(self.settings.value('whisper_model', 'base'))
            self.beam_size_spin.setValue(int(self.settings.value('beam_size', 5)))
        
        # 加载高级设置
        advanced_keys = [
            'temperature', 'no_speech_threshold', 'compression_ratio_threshold', 
            'logprob_threshold', 'condition_on_previous', 'word_timestamps',
            'prepend_punctuations', 'append_punctuations', 'noise_reduction',
            'normalize_audio', 'silence_detection', 'audio_format', 'auto_segment',
            'segment_length', 'multithread', 'thread_count', 'use_gpu',
            'memory_optimization', 'enable_cache', 'cache_path', 'max_cache_size',
            'output_format', 'include_confidence', 'remove_disfluencies',
            'capitalize_sentences', 'output_directory', 'auto_save', 'backup_files'
        ]
        
        for key in advanced_keys:
            value = self.settings.value(f'advanced_{key}')
            if value is not None:
                self.advanced_settings[key] = value
    
    def save_settings(self):
        """保存应用程序设置"""
        self.settings.setValue('language', self.language_combo.currentText())
        self.settings.setValue('quality', self.quality_combo.currentText())
        
        if WHISPER_AVAILABLE:
            self.settings.setValue('whisper_model', self.whisper_model_combo.currentText())
            self.settings.setValue('beam_size', self.beam_size_spin.value())
        
        # 保存高级设置
        for key, value in self.advanced_settings.items():
            self.settings.setValue(f'advanced_{key}', value)
    
    def closeEvent(self, event):
        """处理应用程序关闭事件"""
        # 关闭高级设置对话框
        if self.advanced_dialog:
            self.advanced_dialog.close()
        
        # 保存设置
        self.save_settings()
        
        # 停止任何运行中的线程
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            self.processing_thread.wait()
        
        event.accept()