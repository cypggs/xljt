#!/usr/bin/env python3
"""
心灵鸡汤生成器 - 简单HTTP代理服务器
仅使用Python标准库，无需额外依赖
"""
import http.server
import socketserver
import json
import subprocess
import os

PORT = 81
LM_STUDIO_URL = "https://lm.cypggs.com/v1/chat/completions"

class SoupHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 添加CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求 - 提供静态文件"""
        if self.path == '/':
            self.path = '/index.html'
        super().do_GET()
    
    def do_POST(self):
        """处理POST请求 - API代理"""
        if self.path == '/api/chat':
            self.handle_chat_proxy()
        else:
            self.send_error(404, "API endpoint not found")
    
    def handle_chat_proxy(self):
        """处理聊天API代理"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "Empty request body")
                return
                
            post_data = self.rfile.read(content_length)
            
            # 解析JSON以验证格式
            try:
                request_json = json.loads(post_data.decode('utf-8'))
                print(f"🔄 收到请求，主题: {self.extract_topic(request_json)}")
            except json.JSONDecodeError as e:
                self.send_error(400, f"Invalid JSON: {str(e)}")
                return
            
            print("📡 转发请求到远程API...")
            
            # 使用curl发送请求（解决SSL兼容性问题）
            curl_cmd = [
                'curl', '-s', '--connect-timeout', '30', '--max-time', '60',
                '-H', 'Content-Type: application/json',
                '-H', 'User-Agent: SoupGenerator/1.0',
                '-d', post_data.decode('utf-8'),
                LM_STUDIO_URL
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                error_msg = f"curl 调用失败: {result.stderr}"
                print(f"❌ {error_msg}")
                self.send_json_error(503, error_msg)
                return
            
            response_data = result.stdout.encode('utf-8')
            
            # 解析响应以验证
            try:
                response_json = json.loads(result.stdout)
                content = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f"✅ 成功生成: {content[:50]}...")
            except json.JSONDecodeError:
                print("⚠️  响应格式异常但继续处理")
            
            # 返回成功响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(response_data)
                
        except subprocess.TimeoutExpired:
            error_msg = "远程API请求超时"
            print(f"❌ {error_msg}")
            self.send_json_error(504, error_msg)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"curl 执行错误: {e.stderr}"
            print(f"❌ {error_msg}")
            self.send_json_error(503, error_msg)
            
        except Exception as e:
            error_msg = f"服务器内部错误: {str(e)}"
            print(f"❌ {error_msg}")
            self.send_json_error(500, error_msg)
    
    def extract_topic(self, request_json):
        """从请求中提取主题信息"""
        try:
            messages = request_json.get('messages', [])
            for msg in messages:
                if 'content' in msg and '关于' in msg['content']:
                    return msg['content'].split('关于')[1].split('的')[0]
        except:
            pass
        return "未知主题"
    
    def send_json_error(self, code, message):
        """发送JSON格式的错误响应"""
        error_response = {
            "error": message,
            "code": code
        }
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

if __name__ == "__main__":
    # 切换到脚本所在目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("🌟 心灵鸡汤生成器启动中...")
    print(f"📱 访问地址: http://localhost:{PORT}")
    print(f"🚀 代理目标: {LM_STUDIO_URL}")
    print("🔧 使用远程API服务，无需本地运行")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), SoupHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ 端口 {PORT} 已被占用，请先停止其他服务")
        else:
            print(f"❌ 服务器启动失败: {e}")