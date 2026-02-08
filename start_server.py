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

if __name__ == "__main__":
    print("=" * 50)
    print("工具合规扫描 Agent 服务")
    print("=" * 50)
    print("正在启动服务...")
    print("Web UI: http://localhost:8080/ui")
    print("API 文档: http://localhost:8080/docs")
    print("健康检查: http://localhost:8080/health")
    print("=" * 50)
    print()
    
    try:
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=8080,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()
