import sys
import os

# 确保工作目录正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frontend.server import app

if __name__ == '__main__':
    print("=" * 50)
    print("狼人杀多Agent对战平台 - 前端服务器")
    print("=" * 50)
    print(f"访问地址: http://127.0.0.1:5000")
    print(f"健康检查: http://127.0.0.1:5000/api/health")
    print(f"API文档: http://127.0.0.1:5000/api/roles/info")
    print("=" * 50)
    print("按 Ctrl+C 停止服务器")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)
