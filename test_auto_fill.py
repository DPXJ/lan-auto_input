#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动填充工具测试脚本
用于测试和验证自动填充功能
"""

import time
import pyautogui
import pyperclip
import keyboard
from typing import Optional

def test_clipboard():
    """测试剪贴板功能"""
    print("测试剪贴板功能...")
    
    # 测试文本
    test_text = "这是一个测试文本 - " + time.strftime("%H:%M:%S")
    
    # 复制到剪贴板
    pyperclip.copy(test_text)
    print(f"已复制文本到剪贴板: {test_text}")
    
    # 读取剪贴板
    clipboard_content = pyperclip.paste()
    print(f"从剪贴板读取: {clipboard_content}")
    
    if clipboard_content == test_text:
        print("✓ 剪贴板功能正常")
        return True
    else:
        print("✗ 剪贴板功能异常")
        return False

def test_mouse_position():
    """测试鼠标位置获取"""
    print("\n测试鼠标位置获取...")
    
    try:
        x, y = pyautogui.position()
        print(f"当前鼠标位置: ({x}, {y})")
        print("✓ 鼠标位置获取正常")
        return True
    except Exception as e:
        print(f"✗ 鼠标位置获取失败: {e}")
        return False

def test_window_detection():
    """测试窗口检测"""
    print("\n测试窗口检测...")
    
    try:
        active_window = pyautogui.getActiveWindow()
        if active_window:
            print(f"当前活动窗口: {active_window.title}")
            print("✓ 窗口检测正常")
            return True
        else:
            print("✗ 无法获取活动窗口")
            return False
    except Exception as e:
        print(f"✗ 窗口检测失败: {e}")
        return False

def test_hotkey():
    """测试快捷键功能"""
    print("\n测试快捷键功能...")
    print("请在5秒内按 Ctrl+Shift+T 来测试快捷键...")
    
    key_pressed = False
    
    def on_hotkey():
        nonlocal key_pressed
        key_pressed = True
        print("✓ 快捷键检测正常")
    
    keyboard.add_hotkey('ctrl+shift+t', on_hotkey)
    
    start_time = time.time()
    while time.time() - start_time < 5:
        if key_pressed:
            break
        time.sleep(0.1)
    
    if not key_pressed:
        print("✗ 快捷键检测失败或超时")
        return False
    
    return True

def test_auto_fill_simulation():
    """测试自动填充模拟"""
    print("\n测试自动填充模拟...")
    print("请将鼠标移动到任意输入框，然后点击...")
    print("程序将模拟Ctrl+V操作...")
    
    # 准备测试文本
    test_text = f"自动填充测试 - {time.strftime('%H:%M:%S')}"
    pyperclip.copy(test_text)
    print(f"已准备测试文本: {test_text}")
    
    print("请在5秒内点击输入框...")
    time.sleep(5)
    
    try:
        # 模拟Ctrl+V
        pyautogui.hotkey('ctrl', 'v')
        print("✓ 自动填充模拟成功")
        return True
    except Exception as e:
        print(f"✗ 自动填充模拟失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("自动填充工具功能测试")
    print("=" * 50)
    
    tests = [
        ("剪贴板功能", test_clipboard),
        ("鼠标位置获取", test_mouse_position),
        ("窗口检测", test_window_detection),
        ("快捷键功能", test_hotkey),
        ("自动填充模拟", test_auto_fill_simulation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n正在测试: {test_name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！工具应该可以正常工作。")
    else:
        print("⚠️  部分测试失败，请检查环境配置。")
    
    print("=" * 50)

def interactive_test():
    """交互式测试"""
    print("\n交互式测试模式")
    print("输入 'quit' 退出测试")
    
    while True:
        print("\n请选择测试项目:")
        print("1. 测试剪贴板")
        print("2. 测试鼠标位置")
        print("3. 测试窗口检测")
        print("4. 测试快捷键")
        print("5. 测试自动填充")
        print("6. 运行所有测试")
        print("quit. 退出")
        
        choice = input("\n请输入选择: ").strip().lower()
        
        if choice == 'quit':
            break
        elif choice == '1':
            test_clipboard()
        elif choice == '2':
            test_mouse_position()
        elif choice == '3':
            test_window_detection()
        elif choice == '4':
            test_hotkey()
        elif choice == '5':
            test_auto_fill_simulation()
        elif choice == '6':
            run_all_tests()
        else:
            print("无效选择，请重新输入")

def main():
    """主函数"""
    print("自动填充工具测试程序")
    print("请选择测试模式:")
    print("1. 自动运行所有测试")
    print("2. 交互式测试")
    
    choice = input("请输入选择 (1-2): ").strip()
    
    if choice == '1':
        run_all_tests()
    elif choice == '2':
        interactive_test()
    else:
        print("无效选择")

if __name__ == "__main__":
    main() 