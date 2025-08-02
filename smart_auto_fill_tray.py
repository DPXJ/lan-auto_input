#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能自动填充工具 - 系统托盘版本
适合开机启动，后台运行
"""

import threading
import time
import json
import os
import sys
from typing import Optional
import logging

try:
    import pyautogui
    import keyboard
    import pyperclip
    import psutil
    import win32gui
    import win32api
    import win32con
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
except ImportError as e:
    print(f"缺少必要的依赖库: {e}")
    print("请运行: pip install pywin32 pynput pystray Pillow")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_auto_fill_tray.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class SmartAutoFillTray:
    def __init__(self):
        # 工具状态
        self.is_enabled = True
        self.last_clipboard = ""
        self.last_fill_time = 0
        self.fill_cooldown = 0.5
        self.max_content_length = 20000
        
        # 监控线程
        self.clipboard_monitor_thread = None
        self.mouse_monitor_thread = None
        self.stop_monitoring = False
        
        # 当前鼠标位置和状态
        self.current_mouse_x = 0
        self.current_mouse_y = 0
        self.is_mouse_over_input = False
        self.mouse_check_interval = 0.1
        
        # 系统托盘图标
        self.tray_icon = None
        
        # 配置
        self.config_file = "smart_tray_config.json"
        self.load_config()
        
        # 设置pyautogui的安全设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05
        
        logging.info("智能自动填充工具（托盘版）初始化完成")
    
    def load_config(self):
        """加载配置"""
        default_config = {
            "enabled": True,
            "fill_cooldown": 0.5,
            "max_content_length": 20000,
            "mouse_check_interval": 0.1,
            "exclude_apps": ["记事本", "notepad", "word", "excel", "powerpoint"],
            "include_apps": [],
            "hotkeys": {
                "toggle": "ctrl+shift+a",
                "status": "ctrl+shift+s",
                "quit": "ctrl+shift+q"
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    # 合并默认配置
                    for key, value in default_config.items():
                        if key not in self.config:
                            self.config[key] = value
            else:
                self.config = default_config
        except Exception as e:
            logging.error(f"加载配置失败: {e}")
            self.config = default_config
        
        # 应用配置
        self.is_enabled = self.config.get("enabled", True)
        self.fill_cooldown = self.config.get("fill_cooldown", 0.5)
        self.max_content_length = self.config.get("max_content_length", 20000)
        self.mouse_check_interval = self.config.get("mouse_check_interval", 0.1)
    
    def save_config(self):
        """保存配置"""
        try:
            self.config["enabled"] = self.is_enabled
            self.config["fill_cooldown"] = self.fill_cooldown
            self.config["max_content_length"] = self.max_content_length
            self.config["mouse_check_interval"] = self.mouse_check_interval
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
    
    def create_tray_icon(self):
        """创建系统托盘图标"""
        try:
            # 创建一个简单的图标
            image = Image.new('RGB', (64, 64), color='blue')
            draw = ImageDraw.Draw(image)
            draw.text((10, 20), "AF", fill='white')
            
            # 创建菜单
            menu = Menu(
                MenuItem("状态", self.show_status),
                MenuItem("切换启用", self.toggle_enabled),
                MenuItem("测试填充", self.test_fill),
                MenuItem("设置", self.show_settings),
                Menu.SEPARATOR,
                MenuItem("退出", self.stop)
            )
            
            self.tray_icon = Icon("smart_auto_fill", image, "智能自动填充工具", menu)
        except Exception as e:
            logging.error(f"创建系统托盘图标失败: {e}")
    
    def show_status(self):
        """显示状态"""
        status = "启用" if self.is_enabled else "禁用"
        mouse_status = "在输入框上" if self.is_mouse_over_input else "不在输入框上"
        print(f"智能自动填充工具状态: {status}")
        print(f"鼠标状态: {mouse_status}")
        print(f"鼠标位置: ({self.current_mouse_x}, {self.current_mouse_y})")
    
    def toggle_enabled(self):
        """切换启用状态"""
        self.is_enabled = not self.is_enabled
        self.save_config()
        status = "启用" if self.is_enabled else "禁用"
        logging.info(f"智能填充功能已{status}")
        
        # 更新托盘图标
        if self.tray_icon:
            self.tray_icon.title = f"智能自动填充工具 - {status}"
    
    def test_fill(self):
        """测试填充功能"""
        try:
            test_text = f"托盘版测试 - {time.strftime('%H:%M:%S')}"
            pyperclip.copy(test_text)
            logging.info(f"测试文本已复制: {test_text}")
            
            if self.is_mouse_over_input:
                pyautogui.hotkey('ctrl', 'v')
                logging.info("测试填充完成")
            else:
                logging.info("鼠标不在输入框上，跳过填充")
        except Exception as e:
            logging.error(f"测试填充失败: {e}")
    
    def show_settings(self):
        """显示设置"""
        print("当前设置:")
        print(f"  启用状态: {'是' if self.is_enabled else '否'}")
        print(f"  填充冷却时间: {self.fill_cooldown}秒")
        print(f"  最大内容长度: {self.max_content_length}字符")
        print(f"  鼠标检测间隔: {self.mouse_check_interval}秒")
        print(f"  排除应用: {', '.join(self.config.get('exclude_apps', []))}")
        print(f"  包含应用: {', '.join(self.config.get('include_apps', []))}")
    
    def get_clipboard_content(self) -> Optional[str]:
        """获取剪贴板内容"""
        try:
            content = pyperclip.paste()
            if content and content.strip():
                content = content.strip()
                if len(content) > self.max_content_length:
                    content = content[:self.max_content_length]
                return content
            return None
        except Exception as e:
            logging.error(f"获取剪贴板内容失败: {e}")
            return None
    
    def is_input_field(self, x: int, y: int) -> bool:
        """检测鼠标位置是否为输入框"""
        try:
            # 获取鼠标位置下的窗口句柄
            hwnd = win32gui.WindowFromPoint((x, y))
            if not hwnd:
                return False
            
            # 获取窗口标题
            window_title = win32gui.GetWindowText(hwnd)
            
            # 检查排除的应用
            exclude_apps = self.config.get("exclude_apps", [])
            if any(app.lower() in window_title.lower() for app in exclude_apps):
                return False
            
            # 检查包含的应用
            include_apps = self.config.get("include_apps", [])
            if include_apps:
                if not any(app.lower() in window_title.lower() for app in include_apps):
                    return False
            
            return True
        except Exception as e:
            logging.error(f"检测输入框失败: {e}")
            return False
    
    def fill_input_field(self, content: str):
        """填充输入框"""
        try:
            # 使用Ctrl+V粘贴内容
            pyautogui.hotkey('ctrl', 'v')
            logging.info(f"智能填充完成: {content[:50]}{'...' if len(content) > 50 else ''}")
        except Exception as e:
            logging.error(f"填充输入框失败: {e}")
    
    def mouse_monitor(self):
        """鼠标位置监控线程"""
        while not self.stop_monitoring:
            try:
                # 获取当前鼠标位置
                x, y = pyautogui.position()
                
                # 检查位置是否变化
                if x != self.current_mouse_x or y != self.current_mouse_y:
                    self.current_mouse_x = x
                    self.current_mouse_y = y
                    
                    # 检测是否为输入框
                    is_input = self.is_input_field(x, y)
                    
                    if is_input != self.is_mouse_over_input:
                        self.is_mouse_over_input = is_input
                        if is_input:
                            logging.info(f"鼠标进入输入框: ({x}, {y})")
                        else:
                            logging.info(f"鼠标离开输入框: ({x}, {y})")
                
                time.sleep(self.mouse_check_interval)
                
            except Exception as e:
                logging.error(f"鼠标监控错误: {e}")
                time.sleep(1)
    
    def clipboard_monitor(self):
        """剪贴板监控线程"""
        last_content = ""
        
        while not self.stop_monitoring:
            try:
                # 获取当前剪贴板内容
                current_content = self.get_clipboard_content()
                
                # 检查内容是否变化
                if current_content and current_content != last_content:
                    logging.info(f"检测到剪贴板变化: {current_content[:50]}{'...' if len(current_content) > 50 else ''}")
                    
                    # 检查是否可以自动填充
                    if (self.is_enabled and 
                        self.is_mouse_over_input and 
                        current_content != self.last_clipboard):
                        
                        current_time = time.time()
                        if current_time - self.last_fill_time >= self.fill_cooldown:
                            self.last_fill_time = current_time
                            self.last_clipboard = current_content
                            
                            # 延迟一小段时间确保剪贴板稳定
                            time.sleep(0.1)
                            
                            # 执行自动填充
                            self.fill_input_field(current_content)
                        else:
                            logging.info("填充冷却中，跳过")
                    else:
                        if not self.is_mouse_over_input:
                            logging.info("鼠标不在输入框上，跳过自动填充")
                        elif current_content == self.last_clipboard:
                            logging.info("内容与上次相同，跳过自动填充")
                
                last_content = current_content
                time.sleep(0.1)  # 剪贴板检查间隔
                
            except Exception as e:
                logging.error(f"剪贴板监控错误: {e}")
                time.sleep(1)
    
    def start(self):
        """启动工具"""
        logging.info("智能自动填充工具（托盘版）启动中...")
        
        # 创建系统托盘图标
        self.create_tray_icon()
        
        # 注册快捷键
        hotkeys = self.config.get("hotkeys", {})
        keyboard.add_hotkey(hotkeys.get("toggle", "ctrl+shift+a"), self.toggle_enabled)
        keyboard.add_hotkey(hotkeys.get("status", "ctrl+shift+s"), self.show_status)
        keyboard.add_hotkey(hotkeys.get("quit", "ctrl+shift+q"), self.stop)
        
        # 启动监控线程
        self.mouse_monitor_thread = threading.Thread(target=self.mouse_monitor, daemon=True)
        self.clipboard_monitor_thread = threading.Thread(target=self.clipboard_monitor, daemon=True)
        
        self.mouse_monitor_thread.start()
        self.clipboard_monitor_thread.start()
        
        logging.info("智能自动填充工具（托盘版）已启动")
        logging.info("现在复制文本到剪贴板，鼠标悬停在输入框上即可自动填充")
        
        # 启动系统托盘
        if self.tray_icon:
            self.tray_icon.run()
    
    def stop(self):
        """停止工具"""
        logging.info("正在停止智能自动填充工具...")
        
        self.stop_monitoring = True
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.save_config()
        logging.info("智能自动填充工具已停止")
        sys.exit(0)

def main():
    """主函数"""
    print("=" * 50)
    print("智能自动填充工具（托盘版）v5.1")
    print("=" * 50)
    print("适合开机启动，后台运行")
    print("系统托盘图标已创建")
    print("=" * 50)
    
    app = SmartAutoFillTray()
    app.start()

if __name__ == "__main__":
    main() 