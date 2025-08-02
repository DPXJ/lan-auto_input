#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能自动填充工具
当剪贴板有新内容且鼠标在输入框上时，自动填充，无需点击
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
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
except ImportError as e:
    print(f"缺少必要的依赖库: {e}")
    print("请运行: pip install pywin32 pynput pystray Pillow")
    exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_auto_fill.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class SmartAutoFillGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("智能自动填充工具 v5.0")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 设置图标和样式
        self.setup_style()
        
        # 工具状态
        self.is_running = False
        self.is_enabled = True
        self.last_clipboard = ""
        self.last_fill_time = 0
        self.fill_cooldown = 0.5  # 填充冷却时间
        self.max_content_length = 1000
        
        # 监控线程
        self.clipboard_monitor_thread = None
        self.mouse_monitor_thread = None
        self.stop_monitoring = False
        
        # 当前鼠标位置和状态
        self.current_mouse_x = 0
        self.current_mouse_y = 0
        self.is_mouse_over_input = False
        self.last_mouse_check_time = 0
        self.mouse_check_interval = 0.1  # 鼠标检测间隔
        
        # 系统托盘相关
        self.tray_icon = None
        self.is_minimized_to_tray = False
        
        # 配置
        self.config_file = "smart_config.json"
        self.load_config()
        
        # 创建界面
        self.create_widgets()
        
        # 设置pyautogui的安全设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05
        
        logging.info("智能自动填充工具初始化完成")
    
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
            "fill_cooldown": 0.5,
            "max_content_length": 20000,
            "mouse_check_interval": 0.1,
            "exclude_apps": ["记事本", "notepad", "word", "excel", "powerpoint"],
            "include_apps": [],
            "hotkeys": {
                "toggle": "ctrl+shift+a",
                "status": "ctrl+shift+w",
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
        title_label = ttk.Label(main_frame, text="智能自动填充工具", font=('Microsoft YaHei', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 状态框架
        status_frame = ttk.LabelFrame(main_frame, text="状态控制", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # 启用状态
        self.enabled_var = tk.BooleanVar(value=self.is_enabled)
        enabled_check = ttk.Checkbutton(
            status_frame, 
            text="启用智能填充", 
            variable=self.enabled_var,
            command=self.toggle_enabled
        )
        enabled_check.grid(row=0, column=0, sticky=tk.W)
        
        # 运行状态
        self.status_label = ttk.Label(status_frame, text="状态: 未运行", foreground="red")
        self.status_label.grid(row=0, column=1, sticky=tk.E)
        
        # 鼠标状态
        self.mouse_status_label = ttk.Label(status_frame, text="鼠标: 未知", foreground="gray")
        self.mouse_status_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 控制按钮
        button_frame = ttk.Frame(status_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        self.start_button = ttk.Button(button_frame, text="启动", command=self.start_tool)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_tool, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="测试剪贴板", command=self.test_clipboard).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="测试填充", command=self.test_fill).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="手动填充", command=self.manual_fill).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="托管到后台", command=self.minimize_to_tray).pack(side=tk.LEFT)
        
        # 设置框架
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # 填充冷却时间
        ttk.Label(settings_frame, text="填充冷却时间(秒):").grid(row=0, column=0, sticky=tk.W)
        self.cooldown_var = tk.DoubleVar(value=self.fill_cooldown)
        cooldown_spin = ttk.Spinbox(
            settings_frame, 
            from_=0.1, 
            to=5.0, 
            increment=0.1, 
            textvariable=self.cooldown_var,
            width=10
        )
        cooldown_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 鼠标检测间隔
        ttk.Label(settings_frame, text="鼠标检测间隔(秒):").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.interval_var = tk.DoubleVar(value=self.mouse_check_interval)
        interval_spin = ttk.Spinbox(
            settings_frame, 
            from_=0.05, 
            to=1.0, 
            increment=0.05, 
            textvariable=self.interval_var,
            width=10
        )
        interval_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # 最大内容长度
        ttk.Label(settings_frame, text="最大内容长度:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.length_var = tk.IntVar(value=self.max_content_length)
        length_spin = ttk.Spinbox(
            settings_frame, 
            from_=100, 
            to=10000, 
            increment=100, 
            textvariable=self.length_var,
            width=10
        )
        length_spin.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # 保存设置按钮
        ttk.Button(settings_frame, text="保存设置", command=self.save_settings).grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=90)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 快捷键说明
        hotkey_frame = ttk.LabelFrame(main_frame, text="快捷键说明", padding="10")
        hotkey_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        hotkeys = self.config.get("hotkeys", {})
        hotkey_text = f"切换启用/禁用: {hotkeys.get('toggle', 'Ctrl+Shift+A')}\n"
        hotkey_text += f"显示状态: {hotkeys.get('status', 'Ctrl+Shift+W')}\n"
        hotkey_text += f"退出程序: {hotkeys.get('quit', 'Ctrl+Shift+Q')}"
        
        ttk.Label(hotkey_frame, text=hotkey_text, justify=tk.LEFT).pack(anchor=tk.W)
    
    def toggle_enabled(self):
        """切换启用状态"""
        self.is_enabled = self.enabled_var.get()
        self.save_config()
        status = "启用" if self.is_enabled else "禁用"
        self.log_message(f"智能填充功能已{status}")
    
    def save_settings(self):
        """保存设置"""
        self.fill_cooldown = self.cooldown_var.get()
        self.mouse_check_interval = self.interval_var.get()
        self.max_content_length = self.length_var.get()
        self.save_config()
        self.log_message("设置已保存")
        messagebox.showinfo("提示", "设置已保存")
    
    def create_tray_icon(self):
        """创建系统托盘图标"""
        try:
            self.log_message("开始创建系统托盘图标...")
            
            # 创建一个简单的图标
            image = Image.new('RGB', (64, 64), color='green' if self.is_enabled else 'red')
            draw = ImageDraw.Draw(image)
            draw.text((10, 20), "AF", fill='white')
            self.log_message("图标创建成功")
            
            # 创建菜单
            menu = Menu(
                MenuItem("显示主窗口", self.show_main_window),
                MenuItem("状态", self.show_status_tray),
                MenuItem("切换启用", self.toggle_enabled),
                MenuItem("测试填充", self.test_fill),
                MenuItem("手动填充", self.manual_fill),
                MenuItem("设置", self.show_settings),
                Menu.SEPARATOR,
                MenuItem("退出", self.stop_tool)
            )
            self.log_message("菜单创建成功")
            
            status_text = "启用" if self.is_enabled else "禁用"
            self.tray_icon = Icon("smart_auto_fill", image, f"智能自动填充工具 - {status_text}", menu)
            self.log_message("托盘图标对象创建成功")
            
            # 绑定双击事件
            self.tray_icon.on_activate = self.show_main_window
            self.log_message("双击事件绑定成功")
            
        except ImportError as e:
            self.log_message(f"缺少必要的库: {e}")
            messagebox.showerror("错误", f"缺少必要的库: {e}\n请运行: pip install pystray Pillow")
            self.tray_icon = None
        except Exception as e:
            self.log_message(f"创建系统托盘图标失败: {e}")
            import traceback
            self.log_message(f"详细错误: {traceback.format_exc()}")
            self.tray_icon = None
    
    def show_main_window(self):
        """显示主窗口"""
        if self.is_minimized_to_tray:
            self.restore_window()
    
    def restore_window(self):
        """恢复主窗口"""
        self.root.deiconify()  # 显示窗口
        self.root.lift()  # 置顶
        self.root.focus_force()  # 获取焦点
        self.is_minimized_to_tray = False
        self.log_message("主窗口已显示")
        
        # 停止托盘图标
        if self.tray_icon:
            try:
                self.tray_icon.stop()
                self.tray_icon = None
            except:
                pass
    
    def show_status_tray(self):
        """显示状态"""
        status = "启用" if self.is_enabled else "禁用"
        mouse_status = "在输入框上" if self.is_mouse_over_input else "不在输入框上"
        
        status_msg = f"智能自动填充工具状态: {status}\n鼠标状态: {mouse_status}\n鼠标位置: ({self.current_mouse_x}, {self.current_mouse_y})"
        messagebox.showinfo("工具状态", status_msg)
    
    def minimize_to_tray(self):
        """托管到后台"""
        if not self.is_running:
            messagebox.showwarning("警告", "请先启动工具")
            return
        
        # 如果已经托管到后台，直接返回
        if self.is_minimized_to_tray:
            return
        
        # 创建简单的系统托盘图标
        try:
            # 创建图标
            image = Image.new('RGB', (32, 32), color='green' if self.is_enabled else 'red')
            draw = ImageDraw.Draw(image)
            draw.text((8, 8), "AF", fill='white')
            
            # 创建菜单
            menu = Menu(
                MenuItem("显示主窗口", self.show_main_window),
                MenuItem("状态", self.show_status_tray),
                MenuItem("切换启用", self.toggle_enabled),
                MenuItem("退出", self.stop_tool)
            )
            
            # 创建托盘图标
            self.tray_icon = Icon("智能自动填充", image, "智能自动填充工具", menu)
            
            # 隐藏主窗口
            self.root.withdraw()
            self.is_minimized_to_tray = True
            
            # 启动托盘图标
            def run_tray():
                try:
                    self.tray_icon.run()
                except:
                    pass
            
            threading.Thread(target=run_tray, daemon=True).start()
            
            self.log_message("工具已托管到系统托盘")
            
        except Exception as e:
            self.log_message(f"创建托盘图标失败: {e}")
            # 如果托盘创建失败，恢复窗口
            self.root.deiconify()
            self.is_minimized_to_tray = False
            messagebox.showerror("错误", "创建系统托盘失败，窗口已恢复")
    
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
        self.log_message("测试填充功能 - 请将鼠标移动到输入框上...")
        threading.Timer(3.0, self.perform_test_fill).start()
    
    def perform_test_fill(self):
        """执行测试填充"""
        try:
            test_text = f"智能填充测试 - {time.strftime('%H:%M:%S')}"
            pyperclip.copy(test_text)
            self.log_message(f"已复制测试文本: {test_text}")
            
            if self.is_mouse_over_input:
                pyautogui.hotkey('ctrl', 'v')
                self.log_message("测试填充完成")
            else:
                self.log_message("鼠标不在输入框上，跳过填充")
        except Exception as e:
            self.log_message(f"测试填充失败: {e}")
    
    def manual_fill(self):
        """手动填充当前鼠标位置"""
        try:
            clipboard_content = self.get_clipboard_content()
            if clipboard_content:
                pyautogui.hotkey('ctrl', 'v')
                self.log_message(f"手动填充完成: {clipboard_content[:50]}{'...' if len(clipboard_content) > 50 else ''}")
            else:
                self.log_message("剪贴板为空，无法填充")
        except Exception as e:
            self.log_message(f"手动填充失败: {e}")
    
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
            self.log_message(f"检测输入框失败: {e}")
            return False
    
    def fill_input_field(self, content: str):
        """填充输入框"""
        try:
            # 使用Ctrl+V粘贴内容
            pyautogui.hotkey('ctrl', 'v')
            self.log_message(f"智能填充完成: {content[:50]}{'...' if len(content) > 50 else ''}")
        except Exception as e:
            self.log_message(f"填充输入框失败: {e}")
    
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
                            self.log_message(f"鼠标进入输入框: ({x}, {y})")
                        else:
                            self.log_message(f"鼠标离开输入框: ({x}, {y})")
                
                # 更新鼠标状态显示
                if self.is_mouse_over_input:
                    self.mouse_status_label.config(text=f"鼠标: 在输入框上 ({x}, {y})", foreground="green")
                else:
                    self.mouse_status_label.config(text=f"鼠标: 不在输入框上 ({x}, {y})", foreground="red")
                
                time.sleep(self.mouse_check_interval)
                
            except Exception as e:
                self.log_message(f"鼠标监控错误: {e}")
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
                    self.log_message(f"检测到剪贴板变化: {current_content[:50]}{'...' if len(current_content) > 50 else ''}")
                    
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
                            self.log_message("填充冷却中，跳过")
                    else:
                        if not self.is_mouse_over_input:
                            self.log_message("鼠标不在输入框上，跳过自动填充")
                        elif current_content == self.last_clipboard:
                            self.log_message("内容与上次相同，跳过自动填充")
                
                last_content = current_content
                time.sleep(0.1)  # 剪贴板检查间隔
                
            except Exception as e:
                self.log_message(f"剪贴板监控错误: {e}")
                time.sleep(1)
    
    def start_tool(self):
        """启动工具"""
        if self.is_running:
            return
        
        self.is_running = True
        self.stop_monitoring = False
        self.status_label.config(text="状态: 运行中", foreground="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 注册快捷键
        hotkeys = self.config.get("hotkeys", {})
        keyboard.add_hotkey(hotkeys.get("toggle", "ctrl+shift+a"), self.toggle_enabled)
        keyboard.add_hotkey(hotkeys.get("status", "ctrl+shift+w"), self.show_status_tray)
        keyboard.add_hotkey(hotkeys.get("quit", "ctrl+shift+q"), self.stop_tool)
        
        # 启动监控线程
        self.mouse_monitor_thread = threading.Thread(target=self.mouse_monitor, daemon=True)
        self.clipboard_monitor_thread = threading.Thread(target=self.clipboard_monitor, daemon=True)
        
        self.mouse_monitor_thread.start()
        self.clipboard_monitor_thread.start()
        
        self.log_message("智能自动填充工具已启动")
        self.log_message("现在复制文本到剪贴板，鼠标悬停在输入框上即可自动填充")
    
    def stop_tool(self):
        """停止工具"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.stop_monitoring = True
        self.status_label.config(text="状态: 已停止", foreground="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.mouse_status_label.config(text="鼠标: 未知", foreground="gray")
        
        self.log_message("智能自动填充工具已停止")
    
    def run(self):
        """运行GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """关闭窗口时的处理"""
        # 如果工具正在运行，则托管到后台而不是关闭
        if self.is_running:
            self.minimize_to_tray()
        else:
            # 如果工具没有运行，则正常关闭
            self.save_config()
            if self.tray_icon:
                self.tray_icon.stop()
            self.root.destroy()

def main():
    """主函数"""
    print("=" * 50)
    print("智能自动填充工具 v5.0")
    print("=" * 50)
    
    app = SmartAutoFillGUI()
    app.run()

if __name__ == "__main__":
    main() 