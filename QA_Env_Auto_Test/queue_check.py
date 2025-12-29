


"""QA 脚本：通过 Socket.IO 订阅指定机器人房间的队列事件(queue_update)。

用途:
- 连接后端 Socket.IO 服务，监听 queue_update、connection_success 等事件
- 用于联调/监控队列变化与排队状态

认证:
- 需要提供用户 ID 与 Token，需与后端 users.userid / users.hash_code 一致

使用示例:
  python queue_check.py --host 127.0.0.1 --port 8081 \\
    --robot-id arm1 --user-id <你的用户ID> --token <你的token>

也支持通过环境变量:
  HOST, PORT, ROBOT_ID, USER_ID, TOKEN
"""

import argparse
import json
import os
import sys
import socketio


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器，支持从环境变量读取默认值。"""
    parser = argparse.ArgumentParser(
        description="Listen to Socket.IO queue_update events for a robot room."
    )
    parser.add_argument("--host", default=os.getenv("HOST", "localhost"), help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8081")), help="Server port (default: 8081)")
    parser.add_argument("--robot-id", default=os.getenv("ROBOT_ID", "arm1"), help="Robot ID to join (default: arm1)")
    parser.add_argument("--user-id", default=os.getenv("USER_ID", ""), help="User ID (must match users.userid)")
    parser.add_argument("--token", default=os.getenv("TOKEN", ""), help="User token (must match users.hash_code)")
    # 本地 Tele-Op 服务默认只使用 polling，避免 WebSocket 升级问题；
    # 如需强制 WebSocket，可显式传入 --transport websocket
    parser.add_argument(
        "--transport",
        default="polling",
        choices=["polling", "websocket"],
        help="Engine.IO transport (default: polling; use websocket only if server supports it)",
    )
    return parser


def validate_auth(user_id: str, token: str) -> None:
    """校验最小认证信息是否提供，不满足时退出(Exit Code 2)。"""
    missing = []
    if not user_id:
        missing.append("USER_ID / --user-id")
    if not token:
        missing.append("TOKEN / --token")
    if missing:
        print(f"Missing required auth parameters: {', '.join(missing)}", file=sys.stderr)
        print("Provide via environment variables or CLI flags.", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    """入口函数：解析参数、建立 Socket.IO 连接并监听队列事件。"""
    # 解析命令行参数
    parser = build_parser()
    args = parser.parse_args()

    # 最小认证参数校验（仅检查是否为空）
    validate_auth(args.user_id, args.token)

    # 组装 Socket.IO 服务地址
    server_url = f"http://{args.host}:{args.port}"
    print(f"Connecting to {server_url} | robotId={args.robot_id}")

    # 创建 Socket.IO 客户端
    # - reconnection=True 开启自动重连
    # - reconnection_attempts=0 表示无限次重连
    # 注意：transports 需要在 connect() 时传入，不能作为 Client 构造参数
    sio = socketio.Client(
        reconnection=True,
        reconnection_attempts=0,  # unlimited
        logger=False,
        engineio_logger=False,
    )

    @sio.event
    def connect():
        # 连接成功回调
        print(f"[connect] sid={sio.sid}")

    @sio.event
    def disconnect():
        # 断开连接回调
        print("[disconnect] disconnected from server")

    @sio.event
    def connect_error(data):
        # 连接错误回调，打印错误信息
        print(f"[connect_error] {data}", file=sys.stderr)

    @sio.on("connection_success")
    def on_connection_success(msg):
        # 后端主动下发的连接成功消息，原样美化输出
        try:
            pretty = json.dumps(msg, ensure_ascii=False)
        except Exception:
            pretty = str(msg)
        print(f"[connection_success] {pretty}")

    @sio.on("queue_update")
    def on_queue_update(data):
        # 队列状态变更事件，打印当前队列信息（JSON）
        try:
            pretty = json.dumps(data, ensure_ascii=False)
        except Exception:
            pretty = str(data)
        print(f"[queue_update] {pretty}")

    try:
        # 连接到 Socket.IO 服务
        # - 通过 auth 透传 robotId/userId/token 进行身份校验
        # - transports 仅使用指定的传输方式（默认 websocket）
        sio.connect(
            server_url,
            auth={"robotId": args.robot_id, "token": args.token, "userId": args.user_id},
            transports=[args.transport],
            wait_timeout=10,
        )
        # 阻塞等待事件（直到进程被中断）
        sio.wait()
    except KeyboardInterrupt:
        # Ctrl+C 时优雅退出
        print("\nInterrupted by user. Closing connection...")
    finally:
        try:
            # 确保断开连接
            sio.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    main()

