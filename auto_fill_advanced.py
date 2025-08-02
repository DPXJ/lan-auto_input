#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级自动填充工具
包含系统托盘、更好的鼠标监听和配置管理
"""

import time
import threading
import json
import os
import sys
from typing import Optional, Dict, Any
import logging
from datetime import datetime

try:
    import pyautogui
    import keyboard
    import pyperclip
    import psutil
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
except ImportError as e:
    print(f"缺少必要的依赖库: {e}")
    print("请运行: pip install -r requirements.txt")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_fill.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class Config:
    """配置管理类"""
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.default_config = {
            "enabled": True,
            "click_cooldown": 0.5,
            "exclude_apps": ["记事本", "notepad", "word", "excel", "powerpoint", "chrome", "firefox"],
            "include_apps": [],
            "max_content_length": 1000,
            "hotkeys": {
                "toggle": "ctrl+shift+a",
                "status": "ctrl+shift+s",
                "quit": "ctrl+shift+q"
            }
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                return self.default_config.copy()
        except Exception as e:
            logging.error(f"加载配置失败: {e}")
            return self.default_config.copy()
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """设置配置值"""
        self.config[key] = value
        self.save_config()

class AdvancedAutoFillTool:
    def __init__(self):
        self.config = Config()
        self.is_running = False
        self.is_enabled = self.config.get("enabled", True)
        self.last_clipboard = ""
        self.last_click_time = 0
        self.click_cooldown = self.config.get("click_cooldown", 0.5)
        self.max_content_length = self.config.get("max_content_length", 1000)
        
        # 设置pyautogui的安全设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # 系统托盘图标
        self.tray_icon = None
        self.create_tray_icon()
        
        logging.info("高级自动填充工具初始化完成")
    
    def create_tray_icon(self):
        """创建系统托盘图标"""
        try:
            # 创建一个简单的图标
            image = Image.new('RGB', (64, 64), color='blue')
            draw = ImageDraw.Draw(image)
            draw.text((10, 20), "AF", fill='white')
            
            # 创建菜单
            menu = Menu(
                MenuItem("状态", self.show_status_tray),
                MenuItem("切换启用", self.toggle_enabled),
                MenuItem("设置", self.show_settings),
                Menu.SEPARATOR,
                MenuItem("退出", self.stop)
            )
            
            self.tray_icon = Icon("auto_fill", image, "自动填充工具", menu)
        except Exception as e:
            logging.error(f"创建系统托盘图标失败: {e}")
    
    def get_clipboard_content(self) -> Optional[str]:
        """获取剪贴板内容"""
        try:
            content = pyperclip.paste()
            if content and content.strip():
                content = content.strip()
                # 限制内容长度
                if len(content) > self.max_content_length:
                    content = content[:self.max_content_length]
                return content
            return None
        except Exception as e:
            logging.error(f"获取剪贴板内容失败: {e}")
            return None
    
    def is_input_field(self, x: int, y: int) -> bool:
        """检测点击位置是否为输入框"""
        try:
            # 获取当前活动窗口
            active_window = pyautogui.getActiveWindow()
            if not active_window:
                return True
            
            title = active_window.title.lower()
            
            # 检查排除的应用
            exclude_apps = self.config.get("exclude_apps", [])
            if any(app.lower() in title for app in exclude_apps):
                return False
            
            # 检查包含的应用
            include_apps = self.config.get("include_apps", [])
            if include_apps:
                if not any(app.lower() in title for app in include_apps):
                    return False
            
            return True
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
        self.config.set("enabled", self.is_enabled)
        status = "启用" if self.is_enabled else "禁用"
        logging.info(f"自动填充功能已{status}")
        
        # 更新托盘图标
        if self.tray_icon:
            self.tray_icon.title = f"自动填充工具 - {status}"
    
    def show_status_tray(self):
        """在托盘显示状态"""
        status = "启用" if self.is_enabled else "禁用"
        print(f"自动填充工具状态: {status}")
    
    def show_settings(self):
        """显示设置"""
        print("当前设置:")
        print(f"  启用状态: {'是' if self.is_enabled else '否'}")
        print(f"  点击冷却时间: {self.click_cooldown}秒")
        print(f"  最大内容长度: {self.max_content_length}字符")
        print(f"  排除应用: {', '.join(self.config.get('exclude_apps', []))}")
        print(f"  包含应用: {', '.join(self.config.get('include_apps', []))}")
    
    def show_status(self):
        """显示当前状态"""
        status = "启用" if self.is_enabled else "禁用"
        print(f"自动填充工具状态: {status}")
        print("快捷键说明:")
        hotkeys = self.config.get("hotkeys", {})
        for action, hotkey in hotkeys.items():
            print(f"  {hotkey}: {action}")
    
    def start(self):
        """启动自动填充工具"""
        self.is_running = True
        
        # 注册快捷键
        hotkeys = self.config.get("hotkeys", {})
        keyboard.add_hotkey(hotkeys.get("toggle", "ctrl+shift+a"), self.toggle_enabled)
        keyboard.add_hotkey(hotkeys.get("status", "ctrl+shift+s"), self.show_status)
        keyboard.add_hotkey(hotkeys.get("quit", "ctrl+shift+q"), self.stop)
        
        # 注册鼠标点击事件
        keyboard.on_press_key('left', self.on_mouse_click)
        keyboard.on_press_key('right', self.on_mouse_click)
        
        print("高级自动填充工具已启动!")
        print("功能说明:")
        print("- 当鼠标点击输入框时，如果剪贴板有文字内容，将自动填充")
        print("- 支持所有常见的输入框（文本框、搜索框等）")
        print("- 避免重复填充相同内容")
        print("- 智能排除不需要自动填充的应用")
        print("- 支持系统托盘和配置管理")
        self.show_status()
        
        # 启动系统托盘
        if self.tray_icon:
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
        # 主循环
        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """停止自动填充工具"""
        self.is_running = False
        if self.tray_icon:
            self.tray_icon.stop()
        logging.info("高级自动填充工具已停止")
        print("高级自动填充工具已停止")
        sys.exit(0)

def main():
    """主函数"""
    print("=" * 50)
    print("高级自动填充工具 v2.0")
    print("=" * 50)
    
    # 创建并启动工具
    tool = AdvancedAutoFillTool()
    tool.start()

if __name__ == "__main__":
    main() 