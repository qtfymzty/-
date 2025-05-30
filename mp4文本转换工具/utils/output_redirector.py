import sys
import io
import threading
from datetime import datetime
from PyQt5.QtCore import QMetaObject, Qt
from PyQt5.QtWidgets import QApplication


class OutputRedirector(io.StringIO):
    """自定义输出重定向类，将print输出重定向到GUI"""
    
    def __init__(self, text_widget=None, console_output=True):
        super().__init__()
        self.text_widget = text_widget
        self.console_output = console_output
        self.original_stdout = sys.stdout
        
    def write(self, text):
        # 写入到控制台（如果启用）
        if self.console_output:
            self.original_stdout.write(text)
            self.original_stdout.flush()
        
        # 写入到GUI组件（如果可用且文本不为空）
        if self.text_widget and text.strip():
            try:
                def append_text():
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    formatted_text = f"[{timestamp}] {text.rstrip()}"
                    self.text_widget.append(formatted_text)
                    # 自动滚动到底部
                    scrollbar = self.text_widget.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
                
                # 如果在主线程中，直接调用；否则使用信号机制
                if QApplication.instance().thread() == threading.current_thread():
                    append_text()
                else:
                    QMetaObject.invokeMethod(
                        self.text_widget,
                        "append",
                        Qt.QueuedConnection,
                        text.rstrip()
                    )
            except Exception as e:
                # 如果GUI更新失败，至少输出到控制台
                if self.console_output:
                    self.original_stdout.write(f"[GUI输出错误] {e}\n")
    
    def flush(self):
        if self.console_output:
            self.original_stdout.flush()
    
    def __enter__(self):
        """上下文管理器支持"""
        sys.stdout = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """恢复原始输出"""
        sys.stdout = self.original_stdout
