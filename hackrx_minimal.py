#!/usr/bin/env python3
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

TOKEN = "96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "HackRx Agent Running"}).encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/hackrx/run':
            # Check authorization
            auth = self.headers.get('Authorization', '')
            if not auth.startswith('Bearer ' + TOKEN):
                self.send_response(401)
                self.end_headers()
                return
            
            # Get request data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                questions = data.get("questions", [])
                answers = [f"Answer {i+1}: {len(q)} chars" for i, q in enumerate(questions)]
                
                response = {"answers": answers}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                response = {"answers": [f"Error: {str(e)}"]}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f"Server starting on port {port}")
    server.serve_forever()
