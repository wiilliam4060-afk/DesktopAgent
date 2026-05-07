# Desktop_Agent/core/logger.py
import datetime

def log_info(module_name, message):
    """全局统一格式的日志输出"""
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{module_name}] {message}")

def log_error(module_name, message):
    """全局错误日志输出"""
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [❌ {module_name} ERROR] {message}")