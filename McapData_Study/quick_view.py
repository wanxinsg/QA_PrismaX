#!/usr/bin/env python3
"""
快速查看 MCAP 文件内容
使用方法：python quick_view.py <mcap文件路径>
"""

import sys
from mcap.reader import make_reader
from pathlib import Path
from datetime import datetime


def quick_view(mcap_path):
    """快速查看 MCAP 文件信息"""
    
    if not Path(mcap_path).exists():
        print(f"❌ 文件不存在: {mcap_path}")
        return
    
    print(f"\n📁 文件: {mcap_path}")
    file_size = Path(mcap_path).stat().st_size / (1024 * 1024)
    print(f"📊 大小: {file_size:.2f} MB\n")
    
    with open(mcap_path, "rb") as f:
        reader = make_reader(f)
        
        try:
            summary = reader.get_summary()
            
            if summary and summary.statistics:
                stats = summary.statistics
                
                print("=" * 70)
                print("📈 统计信息")
                print("=" * 70)
                print(f"消息总数:   {stats.message_count:,}")
                print(f"通道数量:   {stats.channel_count}")
                print(f"Schema数:   {stats.schema_count}")
                
                if stats.message_start_time and stats.message_end_time:
                    start = stats.message_start_time / 1e9
                    end = stats.message_end_time / 1e9
                    duration = end - start
                    
                    print(f"记录时长:   {duration:.2f} 秒 ({duration/60:.2f} 分钟)")
                    print(f"开始时间:   {datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                    print(f"结束时间:   {datetime.fromtimestamp(end).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                
                print()
            
            # 通道信息
            if summary and summary.channels:
                print("=" * 70)
                print("📡 通道列表")
                print("=" * 70)
                
                # 统计每个通道的消息数
                message_counts = {}
                for schema, channel, message in reader.iter_messages():
                    topic = channel.topic
                    if topic not in message_counts:
                        message_counts[topic] = {
                            'count': 0,
                            'total_size': 0,
                            'first_time': None,
                            'last_time': None
                        }
                    
                    message_counts[topic]['count'] += 1
                    message_counts[topic]['total_size'] += len(message.data)
                    
                    if message_counts[topic]['first_time'] is None:
                        message_counts[topic]['first_time'] = message.log_time
                    message_counts[topic]['last_time'] = message.log_time
                
                # 显示每个通道的详细信息
                for i, (channel_id, channel) in enumerate(summary.channels.items(), 1):
                    topic = channel.topic
                    print(f"\n通道 {i}: {topic}")
                    print(f"  └─ 消息编码: {channel.message_encoding}")
                    
                    if topic in message_counts:
                        info = message_counts[topic]
                        duration = (info['last_time'] - info['first_time']) / 1e9
                        fps = info['count'] / duration if duration > 0 else 0
                        avg_size = info['total_size'] / info['count'] if info['count'] > 0 else 0
                        
                        print(f"  └─ 消息数量: {info['count']:,}")
                        print(f"  └─ 平均帧率: {fps:.2f} fps")
                        print(f"  └─ 平均大小: {avg_size/1024:.2f} KB/消息")
                        print(f"  └─ 总数据量: {info['total_size']/1024/1024:.2f} MB")
                
                print("\n" + "=" * 70)
            
            else:
                # 如果没有 summary，手动遍历
                print("\n⚠️  无法获取 summary，正在手动分析...\n")
                
                topics_info = {}
                total_count = 0
                
                for schema, channel, message in reader.iter_messages():
                    topic = channel.topic
                    
                    if topic not in topics_info:
                        topics_info[topic] = {
                            'count': 0,
                            'encoding': channel.message_encoding,
                            'first_seen': message.log_time
                        }
                    
                    topics_info[topic]['count'] += 1
                    total_count += 1
                    
                    # 限制遍历数量，避免太慢
                    if total_count > 10000:
                        print(f"(已分析前 {total_count} 条消息，继续完整分析请直接使用 parse_mcap.py)")
                        break
                
                print("=" * 70)
                print("发现的通道:")
                print("=" * 70)
                for topic, info in topics_info.items():
                    print(f"\n{topic}")
                    print(f"  └─ 消息数: {info['count']:,}")
                    print(f"  └─ 编码: {info['encoding']}")
                
                print(f"\n总共分析了 {total_count:,} 条消息")
                print("=" * 70)
        
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    if len(sys.argv) < 2:
        print("使用方法: python quick_view.py <mcap文件路径>")
        print("\n示例:")
        print("  python quick_view.py ../Feature_CaseDesign/4_Mcap\\ Data/output-20260129/0.mcap")
        print("  python quick_view.py path/to/file.mcap")
        
        # 尝试查找数据文件
        possible_paths = [
            Path("../Feature_CaseDesign/4_Mcap Data/output-20260129"),
            Path("output-20260129"),
            Path(".")
        ]
        
        mcap_files = []
        for base_path in possible_paths:
            if base_path.exists():
                mcap_files.extend(list(base_path.glob("*.mcap")))
        
        if mcap_files:
            print(f"\n发现 {len(mcap_files)} 个 MCAP 文件:")
            for f in mcap_files:
                print(f"  - {f}")
            
            # 自动分析第一个文件
            print(f"\n自动分析第一个文件: {mcap_files[0]}")
            quick_view(str(mcap_files[0]))
        else:
            print("\n❌ 未找到 MCAP 文件")
        
        return
    
    mcap_path = sys.argv[1]
    quick_view(mcap_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  程序被用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
