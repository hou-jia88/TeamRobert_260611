"""
查看对话日志工具
可以查看、搜索和分析用户与助手的对话记录
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import glob

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_log_files():
    """获取所有日志文件"""
    log_dir = Path(__file__).parent / "logs"
    if not log_dir.exists():
        print("❌ logs 目录不存在，还没有任何日志")
        return []
    
    log_files = sorted(glob.glob(str(log_dir / "chat_*.log")), reverse=True)
    return log_files

def view_latest_log(lines=50):
    """查看最新的日志"""
    log_files = get_log_files()
    if not log_files:
        return
    
    latest_log = log_files[0]
    print("=" * 80)
    print(f"📋 最新日志文件: {os.path.basename(latest_log)}")
    print("=" * 80)
    
    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            # 显示最后 N 行
            display_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            print(f"\n显示最后 {len(display_lines)} 条记录:\n")
            for line in display_lines:
                print(line.rstrip())
            
            print(f"\n总共 {len(all_lines)} 条记录")
            
    except Exception as e:
        print(f"❌ 读取日志失败: {e}")

def search_logs(keyword):
    """搜索包含关键词的日志"""
    log_files = get_log_files()
    if not log_files:
        return
    
    print("=" * 80)
    print(f"🔍 搜索关键词: '{keyword}'")
    print("=" * 80)
    
    found_count = 0
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if keyword.lower() in line.lower():
                        date_str = os.path.basename(log_file).replace('chat_', '').replace('.log', '')
                        print(f"\n📅 {date_str} | 第 {line_num} 行:")
                        print(f"   {line.rstrip()}")
                        found_count += 1
        except Exception as e:
            continue
    
    if found_count == 0:
        print(f"\n⚠️  未找到包含 '{keyword}' 的记录")
    else:
        print(f"\n✅ 共找到 {found_count} 条相关记录")

def show_statistics():
    """显示日志统计信息"""
    log_files = get_log_files()
    if not log_files:
        print("❌ 没有日志文件")
        return
    
    print("=" * 80)
    print("📊 对话日志统计")
    print("=" * 80)
    
    total_messages = 0
    user_messages = 0
    bot_messages = 0
    
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                total_messages += len(lines)
                
                for line in lines:
                    if '👤 用户' in line:
                        user_messages += 1
                    elif '🤖 助手' in line:
                        bot_messages += 1
        except:
            continue
    
    print(f"\n📁 日志文件数量: {len(log_files)}")
    print(f"💬 总消息数: {total_messages}")
    print(f"👤 用户消息: {user_messages}")
    print(f"🤖 助手回复: {bot_messages}")
    
    if user_messages > 0:
        avg_bot_reply = bot_messages / user_messages
        print(f"📈 平均每条用户消息的回复数: {avg_bot_reply:.2f}")
    
    # 显示最近的日志文件
    print(f"\n📅 最近的日志文件:")
    for log_file in log_files[:5]:
        file_size = os.path.getsize(log_file)
        date_str = os.path.basename(log_file).replace('chat_', '').replace('.log', '')
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        print(f"  • {formatted_date} | {file_size/1024:.2f} KB")

def tail_log(wait=False):
    """实时监控日志（类似 tail -f）"""
    log_files = get_log_files()
    if not log_files:
        print("❌ 没有日志文件")
        return
    
    latest_log = log_files[0]
    print("=" * 80)
    print(f"📡 实时监控日志: {os.path.basename(latest_log)}")
    print("按 Ctrl+C 退出")
    print("=" * 80)
    
    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            # 先跳到文件末尾
            f.seek(0, 2)
            
            print("\n等待新消息...\n")
            while True:
                line = f.readline()
                if line:
                    print(line.rstrip())
                else:
                    if not wait:
                        break
                    import time
                    time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\n✅ 监控已停止")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TeamRobert 对话日志查看器')
    parser.add_argument('--view', '-v', type=int, nargs='?', const=50, default=None,
                       help='查看最新日志，可选参数指定行数（默认50）')
    parser.add_argument('--search', '-s', type=str, help='搜索关键词')
    parser.add_argument('--stats', '-t', action='store_true', help='显示统计信息')
    parser.add_argument('--tail', '-f', action='store_true', help='实时监控日志')
    
    args = parser.parse_args()
    
    if args.view is not None:
        view_latest_log(args.view)
    elif args.search:
        search_logs(args.search)
    elif args.stats:
        show_statistics()
    elif args.tail:
        tail_log(wait=True)
    else:
        # 默认显示统计和最新日志
        show_statistics()
        print("\n")
        view_latest_log(20)

if __name__ == "__main__":
    main()
