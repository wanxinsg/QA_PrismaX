#!/usr/bin/env python3
"""
查看 MCAP 文件中的关节状态数据
可以查看具体的关节位置、速度、力矩等信息
"""

import sys
from mcap.reader import make_reader
from pathlib import Path
import struct


def parse_cdr_joint_state(data):
    """
    解析 CDR 编码的 JointState 消息
    
    JointState 消息格式（ROS 2）:
    - header (Header)
    - name[] (string array)
    - position[] (double array)
    - velocity[] (double array)
    - effort[] (double array)
    """
    try:
        # CDR 格式解析（简化版）
        # 注意：这是一个简化的解析器，可能需要根据实际消息格式调整
        
        offset = 0
        
        # 跳过 CDR header (4 bytes)
        offset += 4
        
        # 解析 Header
        # timestamp (int32 sec + uint32 nanosec)
        if len(data) < offset + 8:
            return None
        
        sec = struct.unpack_from('<i', data, offset)[0]
        offset += 4
        nanosec = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        
        timestamp = sec + nanosec / 1e9
        
        # 跳过 frame_id string
        if len(data) < offset + 4:
            return None
        string_len = struct.unpack_from('<I', data, offset)[0]
        offset += 4 + string_len
        
        # 对齐到 4 字节边界
        if offset % 4 != 0:
            offset += 4 - (offset % 4)
        
        # 解析 name array
        if len(data) < offset + 4:
            return None
        name_count = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        
        names = []
        for _ in range(name_count):
            if len(data) < offset + 4:
                break
            name_len = struct.unpack_from('<I', data, offset)[0]
            offset += 4
            if len(data) < offset + name_len:
                break
            name = data[offset:offset + name_len].decode('utf-8').rstrip('\x00')
            names.append(name)
            offset += name_len
            # 对齐
            if offset % 4 != 0:
                offset += 4 - (offset % 4)
        
        # 解析 position array
        if len(data) < offset + 4:
            return {"timestamp": timestamp, "names": names, "positions": [], "velocities": [], "efforts": []}
        
        pos_count = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        
        positions = []
        for _ in range(pos_count):
            if len(data) < offset + 8:
                break
            pos = struct.unpack_from('<d', data, offset)[0]
            positions.append(pos)
            offset += 8
        
        # 解析 velocity array
        velocities = []
        if len(data) >= offset + 4:
            vel_count = struct.unpack_from('<I', data, offset)[0]
            offset += 4
            for _ in range(vel_count):
                if len(data) < offset + 8:
                    break
                vel = struct.unpack_from('<d', data, offset)[0]
                velocities.append(vel)
                offset += 8
        
        # 解析 effort array
        efforts = []
        if len(data) >= offset + 4:
            eff_count = struct.unpack_from('<I', data, offset)[0]
            offset += 4
            for _ in range(eff_count):
                if len(data) < offset + 8:
                    break
                eff = struct.unpack_from('<d', data, offset)[0]
                efforts.append(eff)
                offset += 8
        
        return {
            "timestamp": timestamp,
            "names": names,
            "positions": positions,
            "velocities": velocities,
            "efforts": efforts
        }
    
    except Exception as e:
        return None


def view_joint_data(mcap_path, topic, max_messages=10, show_raw=False):
    """
    查看指定 topic 的关节数据
    
    Args:
        mcap_path: MCAP 文件路径
        topic: 要查看的 topic
        max_messages: 显示的最大消息数
        show_raw: 是否显示原始数据
    """
    print(f"\n{'='*80}")
    print(f"查看关节数据: {topic}")
    print(f"{'='*80}\n")
    
    if not Path(mcap_path).exists():
        print(f"❌ 文件不存在: {mcap_path}")
        return
    
    message_count = 0
    first_time = None
    
    with open(mcap_path, "rb") as f:
        reader = make_reader(f)
        
        for schema, channel, message in reader.iter_messages():
            if channel.topic != topic:
                continue
            
            message_count += 1
            
            if first_time is None:
                first_time = message.log_time
            
            relative_time = (message.log_time - first_time) / 1e9
            
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"消息 #{message_count}")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"  时间戳:     {message.log_time} ns")
            print(f"  相对时间:   {relative_time:.3f} 秒")
            print(f"  序列号:     {message.sequence}")
            print(f"  数据大小:   {len(message.data)} bytes")
            
            # 解析关节状态
            joint_state = parse_cdr_joint_state(message.data)
            
            if joint_state:
                print(f"\n  📊 关节状态:")
                
                if joint_state['names']:
                    print(f"     关节名称: {', '.join(joint_state['names'])}")
                
                if joint_state['positions']:
                    print(f"\n     🔵 位置 (Position):")
                    for i, pos in enumerate(joint_state['positions']):
                        joint_name = joint_state['names'][i] if i < len(joint_state['names']) else f"Joint{i}"
                        print(f"        [{i}] {joint_name:20s}: {pos:10.6f} rad ({pos*180/3.14159:.2f}°)")
                
                if joint_state['velocities']:
                    print(f"\n     🟢 速度 (Velocity):")
                    for i, vel in enumerate(joint_state['velocities']):
                        joint_name = joint_state['names'][i] if i < len(joint_state['names']) else f"Joint{i}"
                        print(f"        [{i}] {joint_name:20s}: {vel:10.6f} rad/s")
                
                if joint_state['efforts']:
                    print(f"\n     🔴 力矩 (Effort):")
                    for i, eff in enumerate(joint_state['efforts']):
                        joint_name = joint_state['names'][i] if i < len(joint_state['names']) else f"Joint{i}"
                        print(f"        [{i}] {joint_name:20s}: {eff:10.6f} Nm")
            
            else:
                print(f"\n  ⚠️  无法解析关节状态数据")
                
                if show_raw:
                    print(f"\n  原始数据 (前 100 字节):")
                    print(f"     {message.data[:100].hex()}")
            
            print()
            
            if message_count >= max_messages:
                print(f"... (已显示 {max_messages} 条消息，使用 --max 参数查看更多)")
                break
        
        if message_count == 0:
            print(f"❌ 未找到 topic: {topic}")
            print(f"\n可用的 topics:")
            
            # 重新读取显示所有 topics
            f.seek(0)
            reader = make_reader(f)
            topics_seen = set()
            for schema, channel, message in reader.iter_messages():
                if channel.topic not in topics_seen:
                    topics_seen.add(channel.topic)
                    print(f"  - {channel.topic}")
                if len(topics_seen) >= 20:  # 限制显示数量
                    break
        else:
            print(f"✅ 共显示 {message_count} 条消息")


def list_topics(mcap_path):
    """列出 MCAP 文件中的所有 topics"""
    print(f"\n📋 MCAP 文件中的所有通道:\n")
    
    with open(mcap_path, "rb") as f:
        reader = make_reader(f)
        
        try:
            summary = reader.get_summary()
            
            if summary and summary.channels:
                for i, (channel_id, channel) in enumerate(summary.channels.items(), 1):
                    print(f"{i}. {channel.topic}")
                    print(f"   └─ 编码: {channel.message_encoding}")
            else:
                # 手动遍历
                topics = {}
                for schema, channel, message in reader.iter_messages():
                    if channel.topic not in topics:
                        topics[channel.topic] = channel.message_encoding
                
                for i, (topic, encoding) in enumerate(topics.items(), 1):
                    print(f"{i}. {topic}")
                    print(f"   └─ 编码: {encoding}")
        
        except Exception as e:
            print(f"❌ 错误: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='查看 MCAP 文件中的关节状态数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有通道
  python view_joint_data.py ../Feature_CaseDesign/4_Mcap\ Data/output-20260129/0.mcap --list
  
  # 查看左臂主控制器数据（前10条）
  python view_joint_data.py ../Feature_CaseDesign/4_Mcap\ Data/output-20260129/0.mcap --topic /robot/arm_left_lead/joint_states
  
  # 查看前50条消息
  python view_joint_data.py ../Feature_CaseDesign/4_Mcap\ Data/output-20260129/0.mcap --topic /robot/arm_left_lead/joint_states --max 50
  
  # 显示原始数据
  python view_joint_data.py ../Feature_CaseDesign/4_Mcap\ Data/output-20260129/0.mcap --topic /robot/arm_left_lead/joint_states --raw
        """
    )
    
    parser.add_argument('mcap_file', help='MCAP 文件路径')
    parser.add_argument('--topic', '-t', help='要查看的 topic')
    parser.add_argument('--max', '-m', type=int, default=10, help='显示的最大消息数（默认: 10）')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有 topics')
    parser.add_argument('--raw', '-r', action='store_true', help='显示原始数据')
    
    args = parser.parse_args()
    
    if not Path(args.mcap_file).exists():
        # 尝试补全路径
        possible_path = Path("../Feature_CaseDesign/4_Mcap Data/output-20260129") / args.mcap_file
        if possible_path.exists():
            args.mcap_file = str(possible_path)
        else:
            print(f"❌ 文件不存在: {args.mcap_file}")
            return
    
    if args.list:
        list_topics(args.mcap_file)
    elif args.topic:
        view_joint_data(args.mcap_file, args.topic, args.max, args.raw)
    else:
        # 默认显示左臂主控制器
        print("ℹ️  未指定 topic，使用默认: /robot/arm_left_lead/joint_states")
        print("   使用 --list 查看所有可用的 topics\n")
        view_joint_data(
            args.mcap_file, 
            "/robot/arm_left_lead/joint_states", 
            args.max, 
            args.raw
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  程序被用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
