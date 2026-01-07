#!/usr/bin/env python3
"""打印当前队列的 position number list。

通过 Socket.IO 连接获取一次队列更新，然后打印所有的 position numbers。

使用示例:
  python print_queue_positions.py --host 127.0.0.1 --port 8081 \\
    --robot-id arm1 --user-id <你的用户ID> --token <你的token>

也支持通过环境变量:
  TELE_HOST, TELE_PORT, ROBOT_ID, USER_ID, TOKEN
"""

import argparse
import json
import os
import sys
import time
import socketio
from config import load_config


def main() -> None:
    """连接 Socket.IO，获取一次队列更新，打印 position numbers，然后退出。"""
    # 从配置文件加载默认值
    config = load_config()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="Print current queue position numbers."
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
        "--robot-id",
        default=os.getenv("ROBOT_ID", config.robot_id),
        help=f"Robot ID (default: {config.robot_id})"
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
    print(f"Connecting to {server_url} | robotId={args.robot_id}", file=sys.stderr)
    
    # 用于存储队列数据的变量
    queue_data = None
    event_received = False
    
    # 创建 Socket.IO 客户端
    sio = socketio.Client(
        reconnection=False,  # 不需要重连，只获取一次数据
        logger=False,
        engineio_logger=False,
    )
    
    @sio.event
    def connect():
        print(f"[connect] sid={sio.sid}", file=sys.stderr)
    
    @sio.event
    def connect_error(data):
        print(f"[connect_error] {data}", file=sys.stderr)
        sys.exit(1)
    
    @sio.on("connection_success")
    def on_connection_success(msg):
        print(f"[connection_success] Connected successfully", file=sys.stderr)
    
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
                "robotId": args.robot_id,
                "token": args.token,
                "userId": args.user_id
            },
            transports=[args.transport],
            wait_timeout=10,
        )
        
        # 等待队列更新事件
        deadline = time.time() + args.timeout
        while time.time() < deadline and not event_received:
            time.sleep(0.1)
        
        if not event_received:
            print("Error: Timeout waiting for queue_update event", file=sys.stderr)
            sys.exit(1)
        
        # 提取并打印 position numbers
        if queue_data and "queue" in queue_data:
            queue = queue_data["queue"]
            positions = [item.get("position") for item in queue if "position" in item]
            
            if positions:
                # 打印 position numbers，每行一个
                for pos in positions:
                    print(pos)
            else:
                print("Queue is empty or no positions found", file=sys.stderr)
                sys.exit(0)
        else:
            print("Error: Invalid queue_update data format", file=sys.stderr)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        try:
            sio.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    main()

