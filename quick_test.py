#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 验证自动填充功能
"""

import time
import pyperclip
import pyautogui

def quick_test():
    """快速测试自动填充功能"""
    print("=" * 50)
    print("快速测试自动填充功能")
    print("=" * 50)
    
    # 准备测试文本
    test_text = f"自动填充测试文本 - {time.strftime('%H:%M:%S')}"
    
    print(f"1. 复制测试文本到剪贴板: {test_text}")
    pyperclip.copy(test_text)
    
    print("2. 请在5秒内点击任意输入框（如浏览器地址栏、搜索框等）")
    print("3. 观察是否自动填充文本")
    
    # 等待5秒
    for i in range(5, 0, -1):
        print(f"倒计时: {i}秒...")
        time.sleep(1)
    
    print("4. 现在执行测试填充...")
    try:
        pyautogui.hotkey('ctrl', 'v')
        print("✓ 测试填充完成！")
        print("如果看到文本被填充，说明功能正常")
    except Exception as e:
        print(f"✗ 测试填充失败: {e}")
    
    print("=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    quick_test() 