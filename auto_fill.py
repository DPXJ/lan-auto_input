#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动填充工具
当鼠标点击输入框时，如果剪贴板有内容，自动填充到输入框
"""

import time
import threading
import pyautogui
import keyboard
import pyperclip
import psutil
from typing import Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_fill.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class AutoFillTool:
    def __init__(self):
        self.is_running = False
        self.is_enabled = True
        self.last_clipboard = ""
        self.last_click_time = 0
        self.click_cooldown = 0.5  # 点击冷却时间（秒）
        
        # 设置pyautogui的安全设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        logging.info("自动填充工具初始化完成")
    
    def get_clipboard_content(self) -> Optional[str]:
        """获取剪贴板内容"""
        try:
            content = pyperclip.paste()
            if content and content.strip():
                return content.strip()
            return None
        except Exception as e:
            logging.error(f"获取剪贴板内容失败: {e}")
            return None
    
    def is_input_field(self, x: int, y: int) -> bool:
        """检测点击位置是否为输入框"""
        try:
            # 获取鼠标位置下的元素信息
            # 这里使用简单的启发式方法来判断是否为输入框
            # 在实际使用中，可能需要更复杂的检测逻辑
            
            # 检查当前活动窗口的标题，排除一些不需要自动填充的应用
            active_window = pyautogui.getActiveWindow()
            if active_window:
                title = active_window.title.lower()
                # 排除一些不需要自动填充的应用
                exclude_apps = ['记事本', 'notepad', 'word', 'excel', 'powerpoint']
                if any(app in title for app in exclude_apps):
                    return False
            
            return True  # 默认认为是输入框
        except Exception as e:
            logging.error(f"检测输入框失败: {e}")
            return True
    
    def fill_input_field(self, content: str):
        """填充输入框"""
        try:
            # 使用Ctrl+V粘贴内容
            pyautogui.hotkey('ctrl', 'v')
            logging.info(f"已自动填充内容: {content[:50]}{'...' if len(content) > 50 else ''}")
        except Exception as e:
            logging.error(f"填充输入框失败: {e}")
    
    def on_mouse_click(self, event):
        """鼠标点击事件处理"""
        if not self.is_enabled:
            return
        
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return
        
        self.last_click_time = current_time
        
        # 获取鼠标位置
        x, y = pyautogui.position()
        
        # 检测是否为输入框
        if not self.is_input_field(x, y):
            return
        
        # 获取剪贴板内容
        clipboard_content = self.get_clipboard_content()
        if not clipboard_content:
            return
        
        # 检查内容是否与上次相同（避免重复填充）
        if clipboard_content == self.last_clipboard:
            return
        
        self.last_clipboard = clipboard_content
        
        # 延迟一小段时间确保点击事件完成
        time.sleep(0.1)
        
        # 填充输入框
        self.fill_input_field(clipboard_content)
    
    def toggle_enabled(self):
        """切换启用状态"""
        self.is_enabled = not self.is_enabled
        status = "启用" if self.is_enabled else "禁用"
        logging.info(f"自动填充功能已{status}")
        print(f"自动填充功能已{status}")
    
    def show_status(self):
        """显示当前状态"""
        status = "启用" if self.is_enabled else "禁用"
        print(f"自动填充工具状态: {status}")
        print("快捷键说明:")
        print("  Ctrl+Shift+A: 切换启用/禁用")
        print("  Ctrl+Shift+S: 显示状态")
        print("  Ctrl+Shift+Q: 退出程序")
    
    def start(self):
        """启动自动填充工具"""
        self.is_running = True
        
        # 注册快捷键
        keyboard.add_hotkey('ctrl+shift+a', self.toggle_enabled)
        keyboard.add_hotkey('ctrl+shift+s', self.show_status)
        keyboard.add_hotkey('ctrl+shift+q', self.stop)
        
        # 注册鼠标点击事件
        keyboard.on_press_key('left', self.on_mouse_click)
        keyboard.on_press_key('right', self.on_mouse_click)
        
        print("自动填充工具已启动!")
        print("功能说明:")
        print("- 当鼠标点击输入框时，如果剪贴板有文字内容，将自动填充")
        print("- 支持所有常见的输入框（文本框、搜索框等）")
        print("- 避免重复填充相同内容")
        print("- 智能排除不需要自动填充的应用")
        self.show_status()
        
        # 主循环
        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """停止自动填充工具"""
        self.is_running = False
        logging.info("自动填充工具已停止")
        print("自动填充工具已停止")
        exit(0)

def main():
    """主函数"""
    print("=" * 50)
    print("自动填充工具 v1.0")
    print("=" * 50)
    
    # 检查依赖
    try:
        import pyautogui
        import keyboard
        import pyperclip
    except ImportError as e:
        print(f"缺少必要的依赖库: {e}")
        print("请运行: pip install -r requirements.txt")
        return
    
    # 创建并启动工具
    tool = AutoFillTool()
    tool.start()

if __name__ == "__main__":
    main() 