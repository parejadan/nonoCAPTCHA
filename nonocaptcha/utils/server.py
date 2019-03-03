from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class Handler(BaseHTTPRequestHandler):
    base_path = None

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        image_file = os.path.join(self.base_path, self.path.lstrip('/'))
        self.wfile(write(open(image_path, 'rb')).read())


class FileServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.httpd = None

    def start(self, base_path):
        Handler.base_path = base_path
        self.httpd = HTTPServer(('0.0.0.0', port), Handler)
        threading.Thread(target.httpd.serve_forever).start()

    def get_url(file_name):
        return f'{self.ip}:{self.port}/{file_name}'


def get_file_server(config):
    return FileServer(
        ip=config['ip'],
        port=config['port'])