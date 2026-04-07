"""
局域网 HTTP 服务器，正确设置 WebAssembly MIME 类型。
运行后手机访问 http://<电脑IP>:8000
"""
import http.server
import socketserver
import os

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(__file__), "build", "web")

class WasmHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def guess_type(self, path):
        if path.endswith(".wasm"):
            return "application/wasm"
        if path.endswith(".js"):
            return "application/javascript"
        return super().guess_type(path)

    def log_message(self, fmt, *args):
        pass  # 静默日志

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("0.0.0.0", PORT), WasmHandler) as httpd:
    print(f"服务器已启动：http://0.0.0.0:{PORT}")
    print(f"手机访问：http://10.192.33.170:{PORT}")
    httpd.serve_forever()
