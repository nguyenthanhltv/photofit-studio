"""Web server for PhotoFit Studio.

Provides web interface for remote access and mobile viewing.
"""

import os
import threading
import logging
import json
from pathlib import Path
from typing import Optional, List
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

logger = logging.getLogger("web_server")


class PhotoFitWebHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for PhotoFit web interface."""
    
    def __init__(self, *args, directory=None, **kwargs):
        self.photofit_app = kwargs.pop('photofit_app', None)
        super().__init__(*args, directory=directory, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self._get_index_html().encode())
        
        elif self.path == '/api/images':
            self._send_json(self._get_image_list())
        
        elif self.path == '/api/stats':
            self._send_json(self._get_stats())
        
        elif self.path.startswith('/api/download/'):
            filename = self.path[14:]  # Remove '/api/download/'
            self._serve_file(filename)
        
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/api/process':
            self._handle_process()
        else:
            self.send_error(404)
    
    def _send_json(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _get_index_html(self):
        """Get HTML for the main page."""
        return """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhotoFit Studio - Web</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #0B0F19;
            color: #E2E8F0;
            min-height: 100vh;
        }
        .header {
            background: #131825;
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #2A3352;
        }
        .header h1 { font-size: 20px; }
        .header .logo { font-size: 24px; margin-right: 8px; }
        .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .stat-card {
            background: #1A2035;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #2A3352;
        }
        .stat-card h3 { font-size: 14px; color: #94A3B8; margin-bottom: 8px; }
        .stat-card .value { font-size: 28px; font-weight: bold; color: #3B82F6; }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 16px;
        }
        .gallery-item {
            background: #1A2035;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #2A3352;
            transition: transform 0.2s;
        }
        .gallery-item:hover { transform: translateY(-4px); }
        .gallery-item img {
            width: 100%;
            height: 200px;
            object-fit: cover;
        }
        .gallery-item .info {
            padding: 12px;
        }
        .gallery-item .name {
            font-size: 14px;
            font-weight: bold;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .btn {
            background: #3B82F6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn:hover { background: #2563EB; }
        .empty { text-align: center; padding: 48px; color: #64748B; }
    </style>
</head>
<body>
    <div class="header">
        <h1><span class="logo">🪪</span> PhotoFit Studio</h1>
        <button class="btn" onclick="location.reload()">🔄 Refresh</button>
    </div>
    <div class="container">
        <div class="stats" id="stats">
            <div class="stat-card">
                <h3>Tổng ảnh</h3>
                <div class="value" id="total">0</div>
            </div>
            <div class="stat-card">
                <h3>Đã xử lý</h3>
                <div class="value" id="processed">0</div>
            </div>
            <div class="stat-card">
                <h3>Thành công</h3>
                <div class="value" id="success">0</div>
            </div>
        </div>
        <h2 style="margin-bottom: 16px;">📁 Ảnh đã xử lý</h2>
        <div class="gallery" id="gallery">
            <div class="empty">Chưa có ảnh nào</div>
        </div>
    </div>
    <script>
        async function loadStats() {
            try {
                const resp = await fetch('/api/stats');
                const data = await resp.json();
                document.getElementById('total').textContent = data.total_processed || 0;
                document.getElementById('processed').textContent = data.total_processed || 0;
                document.getElementById('success').textContent = data.total_success || 0;
            } catch(e) { console.error(e); }
        }
        async function loadImages() {
            try {
                const resp = await fetch('/api/images');
                const images = await resp.json();
                const gallery = document.getElementById('gallery');
                if (images.length === 0) {
                    gallery.innerHTML = '<div class="empty">Chưa có ảnh nào</div>';
                    return;
                }
                gallery.innerHTML = images.map(img => `
                    <div class="gallery-item">
                        <img src="/api/download/${encodeURIComponent(img.name)}" alt="${img.name}">
                        <div class="info">
                            <div class="name">${img.name}</div>
                        </div>
                    </div>
                `).join('');
            } catch(e) { console.error(e); }
        }
        loadStats();
        loadImages();
        setInterval(() => { loadStats(); loadImages(); }, 5000);
    </script>
</body>
</html>"""
    
    def _get_image_list(self):
        """Get list of processed images."""
        images = []
        if self.photofit_app:
            output_folder = getattr(self.photofit_app, 'output_folder', '')
            if output_folder and os.path.exists(output_folder):
                for f in os.listdir(output_folder):
                    if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                        images.append({
                            'name': f,
                            'path': os.path.join(output_folder, f)
                        })
        return images
    
    def _get_stats(self):
        """Get processing statistics."""
        try:
            from .statistics import get_stats
            stats = get_stats()
            return stats.get_summary()
        except:
            return {
                'total_processed': 0,
                'total_success': 0,
                'total_errors': 0,
                'success_rate': 0
            }
    
    def _serve_file(self, filename):
        """Serve a file for download."""
        images = self._get_image_list()
        for img in images:
            if img['name'] == filename:
                filepath = img['path']
                if os.path.exists(filepath):
                    self.send_response(200)
                    if filename.lower().endswith('.jpg'):
                        self.send_header('Content-type', 'image/jpeg')
                    elif filename.lower().endswith('.png'):
                        self.send_header('Content-type', 'image/png')
                    self.send_header('Content-Disposition', f'attachment; filename={filename}')
                    self.end_headers()
                    with open(filepath, 'rb') as f:
                        self.wfile.write(f.read())
                    return
        self.send_error(404)
    
    def _handle_process(self):
        """Handle process request."""
        self.send_error(501)  # Not implemented
    
    def log_message(self, format, *args):
        """Custom log format."""
        logger.info(f"{self.address_string()} - {format % args}")


class PhotoFitWebServer:
    """Web server for PhotoFit Studio."""
    
    def __init__(self, port: int = 8080, output_folder: str = None):
        self.port = port
        self.output_folder = output_folder
        self._server = None
        self._thread = None
        self._running = False
    
    def start(self):
        """Start the web server."""
        if self._running:
            return
        
        # Create web static folder
        self._web_folder = self._create_web_folder()
        
        # Store server reference for handler
        server_ref = self
        
        # Create custom handler
        class CustomHandler(PhotoFitWebHandler):
            def __init__(self, *args, **kwargs):
                kwargs['photofit_app'] = server_ref
                web_folder = kwargs.pop('web_folder', server_ref._web_folder)
                super().__init__(*args, directory=web_folder, **kwargs)
        
        # Start server
        self._server = HTTPServer(('0.0.0.0', self.port), CustomHandler)
        self._running = True
        
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        
        logger.info(f"Web server started at http://localhost:{self.port}")
        print(f"🌐 Web interface: http://localhost:{self.port}")
    
    def _run_server(self):
        """Run the server."""
        try:
            self._server.serve_forever()
        except:
            pass
    
    def stop(self):
        """Stop the web server."""
        if not self._running:
            return
        
        self._running = False
        if self._server:
            self._server.shutdown()
            self._server = None
        
        logger.info("Web server stopped")
    
    def _create_web_folder(self) -> str:
        """Create temporary web folder."""
        import tempfile
        web_folder = tempfile.mkdtemp(prefix='photofit_web_')
        
        # Copy output images if available
        if self.output_folder and os.path.exists(self.output_folder):
            # We'll serve from output folder directly
            pass
        
        return web_folder
    
    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running
    
    def get_url(self) -> str:
        """Get server URL."""
        return f"http://localhost:{self.port}"


# Standalone function
def start_web_server(port: int = 8080, output_folder: str = None) -> PhotoFitWebServer:
    """Start web server.
    
    Args:
        port: Port number
        output_folder: Output folder to serve
        
    Returns:
        PhotoFitWebServer instance
    """
    server = PhotoFitWebServer(port, output_folder)
    server.start()
    return server
