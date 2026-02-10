"""
启动服务器脚本
Server startup script
"""

import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 从配置读取端口与 host，无配置时使用默认值
def _get_host_port():
    try:
        from src.config import load_config, get_config
        load_config()
        c = get_config()
        return c.service.host, c.service.port
    except Exception:
        return "0.0.0.0", 8080

if __name__ == "__main__":
    host, port = _get_host_port()
    print("=" * 50)
    print("工具合规扫描 Agent 服务")
    print("=" * 50)
    print("正在启动服务...")
    print(f"Web UI: http://localhost:{port}/ui")
    print(f"API 文档: http://localhost:{port}/docs")
    print(f"健康检查: http://localhost:{port}/health")
    print("=" * 50)
    print()

    try:
        uvicorn.run(
            "src.main:app",
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except OSError as e:
        if getattr(e, "winerror", None) == 10048 or (hasattr(e, "errno") and e.errno == 98):
            print("\n[错误] 端口 {} 已被占用，无法启动服务。".format(port))
            print("请任选其一：")
            print("  1. 关闭占用该端口的程序后重试；")
            print("  2. 修改 config/config.yaml 中 service.port 为其他端口（如 8081），然后重新运行 run.bat。")
            print("\n查看占用端口的程序（Windows 管理员 CMD）：netstat -ano | findstr :{}".format(port))
        else:
            raise
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()
