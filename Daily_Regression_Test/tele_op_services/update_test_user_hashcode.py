#!/usr/bin/env python3
"""
更新测试用户的 hash_code

用途：确保测试用户 1073381 在数据库中有正确的 hash_code，
      以便 Socket.IO 测试可以通过数据库认证（而不仅依赖 TEST_MODE 白名单）

使用方法：
    python update_test_user_hashcode.py --user-id 1073381 --hash-code LrwLmEoJ1YHkrdhZFseU_yfOjX9ue3woI_vDBHvaL8M
"""

import argparse
import sys
import os

# 添加后端目录到路径，以便导入 get_db_connection
backend_dir = "/Users/wanxin/PycharmProjects/Prismax/app-prismax-rp-backend/app_prismax_tele_op_services"
sys.path.insert(0, backend_dir)

# 需要先设置环境变量，因为 app.py 在导入时会读取
os.environ['TEST_MODE'] = 'true'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'thepinai'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/wanxin/PycharmProjects/Prismax/thepinai-compute-key.json'

import sqlalchemy
from app import get_db_connection


def update_user_hashcode(user_id: str, hash_code: str) -> bool:
    """更新指定用户的 hash_code
    
    Args:
        user_id: 用户 ID
        hash_code: 新的 hash_code
        
    Returns:
        True if successful, False otherwise
    """
    try:
        engine = get_db_connection()
        with engine.begin() as conn:
            # 检查用户是否存在
            user_check = conn.execute(
                sqlalchemy.text("""
                    SELECT userid, user_name, email
                    FROM users
                    WHERE userid = :uid
                """),
                {"uid": user_id}
            ).fetchone()
            
            if not user_check:
                print(f"❌ 用户 {user_id} 不存在于数据库中", file=sys.stderr)
                return False
            
            print(f"✅ 找到用户: userid={user_check[0]}, name={user_check[1]}, email={user_check[2]}")
            
            # 更新 hash_code
            result = conn.execute(
                sqlalchemy.text("""
                    UPDATE users
                    SET hash_code = :hash_code
                    WHERE userid = :uid
                """),
                {"uid": user_id, "hash_code": hash_code}
            )
            
            if result.rowcount > 0:
                print(f"✅ 成功更新用户 {user_id} 的 hash_code 为: {hash_code}")
                
                # 验证更新
                verify = conn.execute(
                    sqlalchemy.text("""
                        SELECT hash_code
                        FROM users
                        WHERE userid = :uid
                    """),
                    {"uid": user_id}
                ).fetchone()
                
                if verify and verify[0] == hash_code:
                    print(f"✅ 验证成功: hash_code 已正确更新")
                    return True
                else:
                    print(f"⚠️  验证失败: 读取到的 hash_code 与预期不符", file=sys.stderr)
                    return False
            else:
                print(f"⚠️  没有行被更新", file=sys.stderr)
                return False
                
    except Exception as e:
        print(f"❌ 更新失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="更新测试用户的 hash_code 以支持 Socket.IO 认证测试"
    )
    parser.add_argument(
        "--user-id",
        default="1073381",
        help="用户 ID (默认: 1073381)"
    )
    parser.add_argument(
        "--hash-code",
        default="LrwLmEoJ1YHkrdhZFseU_yfOjX9ue3woI_vDBHvaL8M",
        help="新的 hash_code (默认: LrwLmEoJ1YHkrdhZFseU_yfOjX9ue3woI_vDBHvaL8M)"
    )
    
    args = parser.parse_args()
    
    print(f"准备更新用户 {args.user_id} 的 hash_code...")
    print(f"新 hash_code: {args.hash_code}")
    print()
    
    success = update_user_hashcode(args.user_id, args.hash_code)
    
    if success:
        print("\n✅ 更新完成！现在可以运行 Socket.IO 测试了")
        sys.exit(0)
    else:
        print("\n❌ 更新失败", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
