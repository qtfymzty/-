import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.main_window import VideoTextExtractor
from utils.dependencies import check_dependencies, WHISPER_AVAILABLE


def main():
    """主应用程序入口点"""
    print("[调试] 启动应用程序")
    
    app = QApplication(sys.argv)
    app.setApplicationName("视频文本提取器")
    app.setApplicationVersion("3.0")
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 设置应用程序图标（如果有的话）
    try:
        app.setWindowIcon(QIcon())  # 可以后续添加图标文件
    except:
        pass
    
    # 检查关键依赖
    missing_deps = check_dependencies()
    
    if missing_deps:
        error_msg = f"缺少必要的依赖包:\n\n"
        for dep in missing_deps:
            error_msg += f"• {dep}\n"
        error_msg += f"\n请安装缺少的包:\n"
        for dep in missing_deps:
            error_msg += f"pip install {dep}\n"
        
        # 显示错误但仍允许程序启动
        print(f"[警告] {error_msg}")
    
    # 创建并显示主窗口
    try:
        window = VideoTextExtractor()
        window.show()
        
        # 显示启动提示
        if missing_deps:
            QMessageBox.warning(
                window, 
                "依赖检查", 
                f"检测到缺少以下依赖包:\n\n" + 
                "\n".join([f"• {dep}" for dep in missing_deps]) +
                f"\n\n程序可以运行，但某些功能可能不可用。\n" +
                f"建议安装缺少的包以获得完整功能。"
            )
        
        print("[调试] 主窗口已显示")
        
        # 启动事件循环
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"[错误] 程序启动失败: {e}")
        import traceback
        print(f"[错误] 详细错误信息:\n{traceback.format_exc()}")
        
        # 显示错误对话框
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("启动错误")
        error_dialog.setText(f"程序启动失败:\n\n{str(e)}")
        error_dialog.setDetailedText(traceback.format_exc())
        error_dialog.exec_()
        
        sys.exit(1)


if __name__ == "__main__":
    # 设置错误处理
    try:
        main()
    except KeyboardInterrupt:
        print("\n[信息] 用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"[严重错误] 程序异常退出: {e}")
        import traceback
        print(f"[错误跟踪]\n{traceback.format_exc()}")
        sys.exit(1)
