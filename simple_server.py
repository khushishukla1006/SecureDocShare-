from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import json
import os

class RequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/upload.html':
            self.path = 'upload.html'
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/api/upload':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse form data
            boundary = self.headers['Content-Type'].split('=')[1]
            parts = post_data.split(bytes(boundary, 'utf-8'))
            
            file_data = None
            title = None
            
            for part in parts:
                if b'file' in part:
                    file_data = part.split(b'\r\n\r\n')[1].strip()
                elif b'title' in part:
                    title_data = part.split(b'\r\n\r\n')[1].strip()
                    title = title_data.decode('utf-8')
            
            if file_data and title:
                # Save file to temporary location
                temp_file = os.path.join('temp', title)
                os.makedirs('temp', exist_ok=True)
                
                with open(temp_file, 'wb') as f:
                    f.write(file_data)
                
                response = {
                    'message': 'File uploaded successfully',
                    'file_path': temp_file
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No file or title provided'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server_address = ('127.0.0.1', 5002)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"Server running at http://127.0.0.1:5002")
    httpd.serve_forever()
