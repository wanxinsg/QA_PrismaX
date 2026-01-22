#!/usr/bin/env python3
"""打印当前队列的 position number list。

通过 Socket.IO 连接获取一次队列更新，然后打印所有的 position numbers。
默认会打印 arm1、arm2、arm3 和 arm4 四个机器人的队列情况。

使用示例:
  python print_queue_positions.py --host 127.0.0.1 --port 8081 \
    --user-id <你的用户ID> --token <你的token>
  
  # 自定义机器人列表
  python print_queue_positions.py --robot-ids arm1 arm2 arm3 arm4

也支持通过环境变量:
  TELE_HOST, TELE_PORT, USER_ID, TOKEN
"""

import argparse
import json
import os
import sys
import time
import socketio

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import load_config


def get_queue_positions(server_url: str, robot_id: str, user_id: str, 
                       token: str, transport: str, timeout: float) -> list:
    """获取指定机器人的队列位置列表。
    
    Args:
        server_url: Socket.IO 服务器地址
        robot_id: 机器人 ID
        user_id: 用户 ID
        token: 认证 token
        transport: Engine.IO 传输方式
        timeout: 超时时间（秒）
        
    Returns:
        队列位置列表，如果失败则返回 None
    """
    # 用于存储队列数据的变量
    queue_data = None
    event_received = False
    
    # 创建 Socket.IO 客户端
    sio = socketio.Client(
        reconnection=False,
        logger=False,
        engineio_logger=False,
    )
    
    @sio.event
    def connect():
        pass
    
    @sio.event
    def connect_error(data):
        print(f"[{robot_id}] Connection error: {data}", file=sys.stderr)
    
    @sio.on("connection_success")
    def on_connection_success(msg):
        pass
    
    @sio.on("queue_update")
    def on_queue_update(data):
        nonlocal queue_data, event_received
        queue_data = data
        event_received = True
    
    try:
        # 连接到 Socket.IO 服务
        sio.connect(
            server_url,
            auth={
                "robotId": robot_id,
                "token": token,
                "userId": user_id
            },
            transports=[transport],
            wait_timeout=10,
        )
        
        # 等待队列更新事件
        deadline = time.time() + timeout
        while time.time() < deadline and not event_received:
            time.sleep(0.1)
        
        if not event_received:
            print(f"[{robot_id}] Timeout waiting for queue_update event", file=sys.stderr)
            return None
        
        # 提取 position numbers
        if queue_data and "queue" in queue_data:
            queue = queue_data["queue"]
            positions = [item.get("position") for item in queue if "position" in item]
            return positions
        else:
            print(f"[{robot_id}] Invalid queue_update data format", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"[{robot_id}] Error: {e}", file=sys.stderr)
        return None
    finally:
        try:
            sio.disconnect()
        except Exception:
            pass


def main() -> None:
    """连接 Socket.IO，获取队列更新，打印所有机器人的 position numbers。"""
    # 从配置文件加载默认值
    config = load_config()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="Print current queue position numbers for multiple robots."
    )
    parser.add_argument(
        "--host",
        default=os.getenv("TELE_HOST", config.host),
        help=f"Server host (default: {config.host})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("TELE_PORT", str(config.port))),
        help=f"Server port (default: {config.port})"
    )
    parser.add_argument(
        "--robot-ids",
        nargs="+",
        default=["arm1", "arm2", "arm3", "arm4"],
        help="Robot IDs to query (default: arm1 arm2 arm3 arm4)"
    )
    parser.add_argument(
        "--user-id",
        default=os.getenv("USER_ID", config.user_id),
        help=f"User ID (default: {config.user_id})"
    )
    parser.add_argument(
        "--token",
        default=os.getenv("TOKEN", config.token),
        help="User token"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Timeout in seconds to wait for queue_update event (default: 15.0)"
    )
    parser.add_argument(
        "--transport",
        default="polling",
        choices=["polling", "websocket"],
        help="Engine.IO transport (default: polling)"
    )
    
    args = parser.parse_args()
    
    # 验证认证信息
    if not args.user_id or not args.token:
        print("Error: USER_ID and TOKEN must be provided", file=sys.stderr)
        print("Provide via environment variables or CLI flags.", file=sys.stderr)
        sys.exit(2)
    
    # 组装 Socket.IO 服务地址
    server_url = f"{config.scheme}://{args.host}:{args.port}"
    print(f"Connecting to {server_url}", file=sys.stderr)
    print(f"Querying robots: {', '.join(args.robot_ids)}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    try:
        all_success = True
        
        # 遍历所有机器人 ID
        for robot_id in args.robot_ids:
            print(f"\n[{robot_id}] Fetching queue...", file=sys.stderr)
            
            positions = get_queue_positions(
                server_url=server_url,
                robot_id=robot_id,
                user_id=args.user_id,
                token=args.token,
                transport=args.transport,
                timeout=args.timeout
            )
            
            if positions is not None:
                print(f"\n{'='*60}")
                print(f"Robot: {robot_id}")
                print(f"Queue Length: {len(positions)}")
                print(f"{'='*60}")
                
                if positions:
                    print(f"Positions: {', '.join(map(str, positions))}")
                    
                    # 检查队列完整性：队列长度应该等于最后一个position的值
                    last_position = positions[-1]
                    queue_length = len(positions)
                    if queue_length != last_position:
                        print(f"\n⚠️  WARNING: Queue length ({queue_length}) does not match last position number ({last_position})!")
                        print(f"   This may indicate missing or duplicate positions in the queue.")
                else:
                    print("Queue is empty")
            else:
                print(f"[{robot_id}] Failed to fetch queue", file=sys.stderr)
                all_success = False
            
            # 在查询下一个机器人前稍作延迟
            if robot_id != args.robot_ids[-1]:
                time.sleep(0.5)
        
        print(f"\n{'='*60}", file=sys.stderr)
        
        if not all_success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
