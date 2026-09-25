#!/usr/bin/env python3
"""
VisionBox Server with Built-in 9Router Reverse Proxy
- Phục vụ file giao diện VisionBox (HTML, JS, CSS)
- Tích hợp sẵn Reverse Proxy chuyển tiếp yêu cầu đến 9Router (http://127.0.0.1:20128)
- Giải quyết triệt để 100% lỗi CORS, lỗi NetworkError, lỗi IPv6 ::1 trên Firefox / Chrome / Brave
"""

import os
import sys
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
ROUTER_BASE = os.environ.get("ROUTER_BASE", "http://127.0.0.1:20128").rstrip("/")

class VisionBoxHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Chống trình duyệt cache JS/CSS cũ
        if self.path.endswith(('.js', '.css', '.html')) or self.path == '/' or '?' in self.path:
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        # Mở full CORS cho mọi nguồn
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/proxy/') or self.path.startswith('/v1/'):
            self.forward_to_9router('GET')
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/proxy/') or self.path.startswith('/v1/'):
            self.forward_to_9router('POST')
        else:
            self.send_error(404, "Endpoint not found")

    def forward_to_9router(self, method):
        target_path = self.path
        if target_path.startswith('/proxy/'):
            target_path = '/' + target_path[len('/proxy/'):]

        target_url = ROUTER_BASE + target_path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req_headers = {}
        for h in ['Content-Type', 'Authorization', 'Accept']:
            val = self.headers.get(h)
            if val:
                req_headers[h] = val

        req = urllib.request.Request(
            target_url,
            data=body,
            headers=req_headers,
            method=method
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_bytes = resp.read()
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ['content-length', 'transfer-encoding', 'connection', 'access-control-allow-origin']:
                        self.send_header(k, v)
                self.send_header('Content-Length', str(len(resp_bytes)))
                self.end_headers()
                self.wfile.write(resp_bytes)
        except urllib.error.HTTPError as e:
            err_bytes = e.read()
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in ['content-length', 'transfer-encoding', 'connection', 'access-control-allow-origin']:
                    self.send_header(k, v)
            self.send_header('Content-Length', str(len(err_bytes)))
            self.end_headers()
            self.wfile.write(err_bytes)
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            err_data = json.dumps({
                "error": {
                    "message": f"Không thể kết nối đến 9Router tại {ROUTER_BASE}: {str(e)}"
                }
            }).encode('utf-8')
            self.send_header('Content-Length', str(len(err_data)))
            self.end_headers()
            self.wfile.write(err_data)

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, VisionBoxHandler)
    print(f"==================================================")
    print(f"  VisionBox (Tích hợp 9Router Proxy)")
    print(f"  Giao diện: http://localhost:{PORT} hoặc http://127.0.0.1:{PORT}")
    print(f"  Proxy 9Router: Kết nối trực tiếp {ROUTER_BASE}")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng VisionBox.")
        httpd.server_close()

if __name__ == '__main__':
    main()
