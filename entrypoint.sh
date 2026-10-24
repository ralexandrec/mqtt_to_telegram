#!/bin/sh
# Inicia servidor HTTP de status na porta $PORT (requerido pelo Render)
python3 -c "
import http.server, os

port = int(os.environ.get('PORT', 5000))

HTML = '''<!DOCTYPE html>
<html lang=\"pt-BR\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>Bertioga Gateway</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      min-height: 100vh;
      background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
      display: flex; align-items: center; justify-content: center;
      font-family: \"Segoe UI\", sans-serif; color: #fff;
    }
    .card {
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 20px;
      padding: 48px 56px;
      text-align: center;
      backdrop-filter: blur(12px);
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    .dot {
      width: 14px; height: 14px;
      background: #00e676;
      border-radius: 50%;
      display: inline-block;
      margin-right: 8px;
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0%,100% { opacity:1; transform:scale(1); }
      50%      { opacity:.5; transform:scale(1.3); }
    }
    h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 12px; }
    .status { font-size: 1.1rem; color: #00e676; margin-bottom: 24px; }
    .info   { font-size: 0.9rem; color: rgba(255,255,255,0.55); line-height: 1.8; }
    .badge  {
      display: inline-block; margin-top: 24px;
      padding: 6px 18px;
      border-radius: 50px;
      background: rgba(0,230,118,0.15);
      border: 1px solid #00e676;
      font-size: 0.8rem; color: #00e676;
    }
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>Bertioga Gateway</h1>
    <p class=\"status\"><span class=\"dot\"></span>Online &amp; Running</p>
    <p class=\"info\">
      Meshtastic MQTT Bridge<br>
      MQTT: platform.meshbrasil.com:1883<br>
      Canal: Bertioga
    </p>
    <span class=\"badge\">mqtt_to_telegram v1.0</span>
  </div>
</body>
</html>'''

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = HTML.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass

srv = http.server.HTTPServer(('0.0.0.0', port), Handler)
srv.serve_forever()
" &

# Inicia o gateway principal em foreground
exec python mesh.py
