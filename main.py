# main.py
import os
import sys
import ctypes
import keyboard
from PyQt5.QtWidgets import QApplication
from core.event_bus import EventBus
from ui.window import OverlayWindow

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not is_admin():
    print("[System] 权限不足！正在呼叫 Windows 提权机制...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception: pass

def setup_global_hotkeys(bus, app):
    print("\n" + "="*40)
    print("🏃 小橙 [特工序列任务引擎] 启动就绪！")
    print("="*40)
    print(" -> F8 : 🚀 执行任务 (定位鼠标 -> 翻窗 -> 抵达 -> 抓钩飞跃)")
    print(" -> F9 : ⏸️ 强行中断 (原地待机)")
    print(" -> F10: ❌ 彻底退出系统\n")
    
    keyboard.add_hotkey('F8', lambda: bus.publish("UI_SET_STATE", "START_MISSION"))
    keyboard.add_hotkey('F9', lambda: bus.publish("UI_SET_STATE", "IDLE"))
    keyboard.add_hotkey('F10', lambda: app.quit())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    bus = EventBus()
    win = OverlayWindow(bus)
    
    setup_global_hotkeys(bus, app)
    sys.exit(app.exec_())