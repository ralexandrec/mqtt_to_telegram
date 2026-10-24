#!/bin/sh
# Gera mesh.ini em tempo de execução a partir das variáveis de ambiente do Render
# NUNCA commitar segredos no git!

cat > /app/mesh.ini << EOF
[DEFAULT]
Debug = false
SentryDSN = https://123.ingest.sentry.io/456
SentryEnabled = false
OpenWeatherKey = ""

[Telegram]
Admin = ${TELEGRAM_ADMIN_ID}
Room = ${TELEGRAM_ROOM_ID}
RoomLink = ${TELEGRAM_ROOM_LINK}
NotificationsEnabled = false
NotificationsRoom = -1234
Token = ${TELEGRAM_TOKEN}
MapLinkEnabled = false
MapLink = https://meshmap.net/#%%d
NodeIncludeSelf = false
BotInRooms = true

[WebApp]
Port = 5000
RedrawMarkersEvery = 300
APIKey = AIxxxxZA
Enabled = false
Center_Latitude = -23.9618
Center_Longitude = -46.1964
LastHeardDefault = 3600
AirRaidEnabled = false
AirRaidPrivate = aaabbbccc
ExternalURL = https://example.com/
ShortenerService = pls
TLYToken = aaabbb
PLSST = aaabbbb

[Meshtastic]
Admin = !deadbeef
Device = mqtt
DatabaseFile = meshtastic.sqlite
FIFOPath = /tmp/mtg.fifo
FIFOCmdPath = /tmp/mtg.cmd.fifo
NodeLogEnabled = false
NodeLogFile = /tmp/node_log.csv
FIFOEnabled = false
WelcomeMessage = Welcome to our community
WelcomeMessageEnabled = false
MaxHopCount = 5
EncryptionKey = ${MESHTASTIC_ENCRYPTION_KEY}

[APRS]
Enabled = false
ToMeshtastic = false
FromMeshtastic = false
CallSign = N0CALL-1
Password = QwertyLOL123

[MQTT]
Enabled = true
Topic = ${MQTT_TOPIC:-meshdev}
Channel = ${MQTT_CHANNEL:-Bertioga}
Host = ${MQTT_HOST:-platform.meshbrasil.com}
Port = ${MQTT_PORT:-1883}
User = ${MQTT_USER:-meshdev}
Password = ${MQTT_PASSWORD}
EOF

# Inicia servidor HTTP de status na porta \$PORT (requerido pelo Render web_service)
python3 -c "
import http.server, os
port = int(os.environ.get('PORT', 5000))
HTML = b'''<!DOCTYPE html>
<html lang=\"pt-BR\">
<head><meta charset=\"UTF-8\"><title>Bertioga Gateway</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{min-height:100vh;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
display:flex;align-items:center;justify-content:center;
font-family:\"Segoe UI\",sans-serif;color:#fff}
.card{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);
border-radius:20px;padding:48px 56px;text-align:center;
backdrop-filter:blur(12px);box-shadow:0 8px 32px rgba(0,0,0,.4)}
.dot{width:14px;height:14px;background:#00e676;border-radius:50%;
display:inline-block;margin-right:8px;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.3)}}
h1{font-size:2.2rem;font-weight:700;margin-bottom:12px}
.status{font-size:1.1rem;color:#00e676;margin-bottom:24px}
.info{font-size:.9rem;color:rgba(255,255,255,.55);line-height:1.8}
.badge{display:inline-block;margin-top:24px;padding:6px 18px;border-radius:50px;
background:rgba(0,230,118,.15);border:1px solid #00e676;font-size:.8rem;color:#00e676}
</style></head>
<body><div class=\"card\">
<h1>Bertioga Gateway</h1>
<p class=\"status\"><span class=\"dot\"></span>Online &amp; Running</p>
<p class=\"info\">Meshtastic MQTT Bridge<br>Canal: Bertioga</p>
<span class=\"badge\">mqtt_to_telegram v1.0</span>
</div></body></html>'''
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length',len(HTML))
        self.end_headers()
        self.wfile.write(HTML)
    def log_message(self,*a):pass
http.server.HTTPServer(('0.0.0.0',port),H).serve_forever()
" &

exec python mesh.py
