#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版自动填充工具
使用更准确的鼠标监听和更好的输入框检测
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
import os
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
    from pynput import mouse
except ImportError as e:
    print(f"缺少必要的依赖库: {e}")
    print("请运行: pip install pywin32 pynput")
    exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_fill.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ImprovedAutoFillGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("改进版自动填充工具 v4.0")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # 设置图标和样式
        self.setup_style()
        
        # 工具状态
        self.is_running = False
        self.is_enabled = True
        self.last_clipboard = ""
        self.last_click_time = 0
        self.click_cooldown = 0.3  # 减少冷却时间
        self.max_content_length = 1000
        
        # 鼠标监听器
        self.mouse_listener = None
        
        # 配置
        self.config_file = "improved_config.json"
        self.load_config()
        
        # 创建界面
        self.create_widgets()
        
        # 设置pyautogui的安全设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05  # 减少延迟
        
        logging.info("改进版自动填充工具初始化完成")
    
    def setup_style(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置颜色
        self.root.configure(bg='#f0f0f0')
        
        # 设置字体
        default_font = ('Microsoft YaHei', 9)
        self.root.option_add('*Font', default_font)
    
    def load_config(self):
        """加载配置"""
        default_config = {
            "enabled": True,
            "click_cooldown": 0.3,
            "max_content_length": 1000,
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
        self.click_cooldown = self.config.get("click_cooldown", 0.3)
        self.max_content_length = self.config.get("max_content_length", 1000)
    
    def save_config(self):
        """保存配置"""
        try:
            self.config["enabled"] = self.is_enabled
            self.config["click_cooldown"] = self.click_cooldown
            self.config["max_content_length"] = self.max_content_length
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="改进版自动填充工具", font=('Microsoft YaHei', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 状态框架
        status_frame = ttk.LabelFrame(main_frame, text="状态控制", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # 启用状态
        self.enabled_var = tk.BooleanVar(value=self.is_enabled)
        enabled_check = ttk.Checkbutton(
            status_frame, 
            text="启用自动填充", 
            variable=self.enabled_var,
            command=self.toggle_enabled
        )
        enabled_check.grid(row=0, column=0, sticky=tk.W)
        
        # 运行状态
        self.status_label = ttk.Label(status_frame, text="状态: 未运行", foreground="red")
        self.status_label.grid(row=0, column=1, sticky=tk.E)
        
        # 控制按钮
        button_frame = ttk.Frame(status_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        self.start_button = ttk.Button(button_frame, text="启动", command=self.start_tool)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_tool, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="测试剪贴板", command=self.test_clipboard).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="测试填充", command=self.test_fill).pack(side=tk.LEFT)
        
        # 设置框架
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # 点击冷却时间
        ttk.Label(settings_frame, text="点击冷却时间(秒):").grid(row=0, column=0, sticky=tk.W)
        self.cooldown_var = tk.DoubleVar(value=self.click_cooldown)
        cooldown_spin = ttk.Spinbox(
            settings_frame, 
            from_=0.1, 
            to=2.0, 
            increment=0.1, 
            textvariable=self.cooldown_var,
            width=10
        )
        cooldown_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 最大内容长度
        ttk.Label(settings_frame, text="最大内容长度:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.length_var = tk.IntVar(value=self.max_content_length)
        length_spin = ttk.Spinbox(
            settings_frame, 
            from_=100, 
            to=10000, 
            increment=100, 
            textvariable=self.length_var,
            width=10
        )
        length_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # 保存设置按钮
        ttk.Button(settings_frame, text="保存设置", command=self.save_settings).grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 快捷键说明
        hotkey_frame = ttk.LabelFrame(main_frame, text="快捷键说明", padding="10")
        hotkey_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        hotkeys = self.config.get("hotkeys", {})
        hotkey_text = f"切换启用/禁用: {hotkeys.get('toggle', 'Ctrl+Shift+A')}\n"
        hotkey_text += f"显示状态: {hotkeys.get('status', 'Ctrl+Shift+S')}\n"
        hotkey_text += f"退出程序: {hotkeys.get('quit', 'Ctrl+Shift+Q')}"
        
        ttk.Label(hotkey_frame, text=hotkey_text, justify=tk.LEFT).pack(anchor=tk.W)
    
    def toggle_enabled(self):
        """切换启用状态"""
        self.is_enabled = self.enabled_var.get()
        self.save_config()
        status = "启用" if self.is_enabled else "禁用"
        self.log_message(f"自动填充功能已{status}")
    
    def save_settings(self):
        """保存设置"""
        self.click_cooldown = self.cooldown_var.get()
        self.max_content_length = self.length_var.get()
        self.save_config()
        self.log_message("设置已保存")
        messagebox.showinfo("提示", "设置已保存")
    
    def test_clipboard(self):
        """测试剪贴板内容"""
        try:
            content = pyperclip.paste()
            if content:
                self.log_message(f"剪贴板内容: {content[:100]}{'...' if len(content) > 100 else ''}")
            else:
                self.log_message("剪贴板为空")
        except Exception as e:
            self.log_message(f"获取剪贴板失败: {e}")
    
    def test_fill(self):
        """测试填充功能"""
        self.log_message("测试填充功能 - 请在3秒内点击任意输入框...")
        threading.Timer(3.0, self.perform_test_fill).start()
    
    def perform_test_fill(self):
        """执行测试填充"""
        try:
            test_text = f"测试填充 - {time.strftime('%H:%M:%S')}"
            pyperclip.copy(test_text)
            self.log_message(f"已复制测试文本: {test_text}")
            pyautogui.hotkey('ctrl', 'v')
            self.log_message("测试填充完成")
        except Exception as e:
            self.log_message(f"测试填充失败: {e}")
    
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 限制日志行数
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.log_text.delete("1.0", f"{len(lines) - 100}.0")
    
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
            self.log_message(f"获取剪贴板内容失败: {e}")
            return None
    
    def is_input_field(self, x: int, y: int) -> bool:
        """检测点击位置是否为输入框"""
        try:
            # 获取鼠标位置下的窗口句柄
            hwnd = win32gui.WindowFromPoint((x, y))
            if not hwnd:
                return True
            
            # 获取窗口标题
            window_title = win32gui.GetWindowText(hwnd)
            self.log_message(f"点击窗口: {window_title}")
            
            # 检查排除的应用
            exclude_apps = self.config.get("exclude_apps", [])
            if any(app.lower() in window_title.lower() for app in exclude_apps):
                self.log_message(f"排除应用: {window_title}")
                return False
            
            # 检查包含的应用
            include_apps = self.config.get("include_apps", [])
            if include_apps:
                if not any(app.lower() in window_title.lower() for app in include_apps):
                    self.log_message(f"不在包含列表中: {window_title}")
                    return False
            
            return True
        except Exception as e:
            self.log_message(f"检测输入框失败: {e}")
            return True
    
    def fill_input_field(self, content: str):
        """填充输入框"""
        try:
            # 使用Ctrl+V粘贴内容
            pyautogui.hotkey('ctrl', 'v')
            self.log_message(f"已自动填充内容: {content[:50]}{'...' if len(content) > 50 else ''}")
        except Exception as e:
            self.log_message(f"填充输入框失败: {e}")
    
    def on_mouse_click(self, x, y, button, pressed):
        """鼠标点击事件处理"""
        if not pressed or not self.is_enabled or not self.is_running:
            return
        
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return
        
        self.last_click_time = current_time
        
        self.log_message(f"检测到鼠标点击: ({x}, {y})")
        
        # 检测是否为输入框
        if not self.is_input_field(x, y):
            return
        
        # 获取剪贴板内容
        clipboard_content = self.get_clipboard_content()
        if not clipboard_content:
            self.log_message("剪贴板为空，跳过填充")
            return
        
        # 检查内容是否与上次相同（避免重复填充）
        if clipboard_content == self.last_clipboard:
            self.log_message("内容与上次相同，跳过填充")
            return
        
        self.last_clipboard = clipboard_content
        
        # 延迟一小段时间确保点击事件完成
        time.sleep(0.1)
        
        # 填充输入框
        self.fill_input_field(clipboard_content)
    
    def start_tool(self):
        """启动工具"""
        if self.is_running:
            return
        
        self.is_running = True
        self.status_label.config(text="状态: 运行中", foreground="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 注册快捷键
        hotkeys = self.config.get("hotkeys", {})
        keyboard.add_hotkey(hotkeys.get("toggle", "ctrl+shift+a"), self.toggle_enabled)
        keyboard.add_hotkey(hotkeys.get("quit", "ctrl+shift+q"), self.stop_tool)
        
        # 启动鼠标监听器
        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.mouse_listener.start()
        
        self.log_message("改进版自动填充工具已启动")
        self.log_message("现在可以复制文本，然后点击任意输入框进行自动填充")
    
    def stop_tool(self):
        """停止工具"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.status_label.config(text="状态: 已停止", foreground="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # 停止鼠标监听器
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        self.log_message("改进版自动填充工具已停止")
    
    def run(self):
        """运行GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """关闭窗口时的处理"""
        if self.is_running:
            self.stop_tool()
        self.save_config()
        self.root.destroy()

def main():
    """主函数"""
    print("=" * 50)
    print("改进版自动填充工具 v4.0")
    print("=" * 50)
    
    app = ImprovedAutoFillGUI()
    app.run()

if __name__ == "__main__":
    main() 