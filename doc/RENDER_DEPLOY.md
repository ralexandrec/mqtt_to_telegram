# Deploy no Render — Aprendizados e Boas Práticas

## Visão Geral da Arquitetura

```
GitHub (público)          Render (seguro)
─────────────────         ─────────────────
Dockerfile                TELEGRAM_TOKEN       ← env var
entrypoint.sh             MQTT_PASSWORD        ← env var
mesh.ini.example          MESHTASTIC_KEY       ← env var
código fonte              MQTT_HOST/PORT/USER  ← env var
                          TELEGRAM_ADMIN_ID    ← env var
❌ mesh.ini               TELEGRAM_ROOM_ID     ← env var
❌ .env                   TELEGRAM_ROOM_LINK   ← env var
```

## ⚠️ REGRA DE OURO — Segurança de Segredos

**NUNCA commitar segredos no Git.** Isso inclui:
- Tokens de bots (Telegram, Slack, Discord)
- Senhas de MQTT, banco de dados, APIs
- Chaves de criptografia
- API keys de qualquer serviço

### O que vai no Git ✅
- `Dockerfile`
- `entrypoint.sh` (gera config em runtime)
- `mesh.ini.example` (com valores placeholder)
- `requirements.txt`
- Código fonte

### O que NUNCA vai no Git ❌
- `.env`
- `mesh.ini` com credenciais reais
- Qualquer arquivo com tokens/senhas

---

## Como Enviar Variáveis de Ambiente ao Render

### Via API (automatizado — preferido para CI/CD)

```bash
RENDER_API_KEY="rnd_xxxxxxxxxxxx"
SERVICE_ID="srv-xxxxxxxxxxxx"

curl -s -X PUT "https://api.render.com/v1/services/${SERVICE_ID}/env-vars" \
  -H "Authorization: Bearer ${RENDER_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '[
    {"key": "TELEGRAM_TOKEN",   "value": "seu_token_aqui"},
    {"key": "MQTT_HOST",        "value": "broker.exemplo.com"},
    {"key": "MQTT_PORT",        "value": "1883"},
    {"key": "MQTT_USER",        "value": "usuario"},
    {"key": "MQTT_PASSWORD",    "value": "senha_secreta"},
    {"key": "MQTT_TOPIC",       "value": "meshdev"},
    {"key": "MQTT_CHANNEL",     "value": "NomeDoCanal"},
    {"key": "TELEGRAM_ADMIN_ID","value": "123456789"},
    {"key": "TELEGRAM_ROOM_ID", "value": "123456789"},
    {"key": "TELEGRAM_ROOM_LINK","value": "https://t.me/seu_bot"}
  ]'
```

> ⚠️ O `PUT` **substitui todas** as variáveis. Inclua sempre todas no payload
> para não deletar variáveis existentes acidentalmente.

### Via Painel Web (manual)
`dashboard.render.com` → seu serviço → **Environment** → Add Environment Variable

---

## Padrão: Gerar Config em Runtime via entrypoint.sh

Em vez de commitar `mesh.ini` com segredos, o `entrypoint.sh` gera o arquivo
na inicialização do container a partir das variáveis de ambiente:

```sh
#!/bin/sh
cat > /app/mesh.ini << EOF
[Telegram]
Token = ${TELEGRAM_TOKEN}
Admin = ${TELEGRAM_ADMIN_ID}
Room  = ${TELEGRAM_ROOM_ID}
...

[MQTT]
Host     = ${MQTT_HOST}
Port     = ${MQTT_PORT}
User     = ${MQTT_USER}
Password = ${MQTT_PASSWORD}
Topic    = ${MQTT_TOPIC}
Channel  = ${MQTT_CHANNEL}
EOF

exec python mesh.py
```

---

## Tipo de Serviço no Render

| Tipo | Plano | Observação |
|------|-------|------------|
| `web_service` | Free ✅ | Requer HTTP na `$PORT` — adicionar health-check server |
| `background_worker` | Pago ❌ | Ideal para bots — sem necessidade de HTTP |
| `cron_job` | Pago ❌ | Para tarefas agendadas |

### Solução para plano Free: health-check HTTP server

Como o plano free exige `web_service`, o `entrypoint.sh` sobe um servidor HTTP
mínimo em background na porta `$PORT` antes de iniciar a app principal:

```sh
python3 -c "
import http.server, os
port = int(os.environ.get('PORT', 5000))
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, *a): pass
http.server.HTTPServer(('0.0.0.0', port), H).serve_forever()
" &

exec python mesh.py
```

---

## Keep-Alive no Plano Free

No plano free, o Render **hiberna o serviço após 15 min de inatividade**.
Solução: usar o [UptimeRobot](https://uptimerobot.com) (gratuito) para fazer
ping a cada 5 minutos na URL do serviço.

```
Monitor type: HTTP(S)
URL: https://seu-servico.onrender.com
Interval: 5 minutes
```

---

## Armadilhas Conhecidas (Lições Aprendidas)

### 1. `configparser` não expande variáveis de shell
```ini
# ❌ NÃO funciona — lê literalmente "${PORT:-5000}"
Port = ${PORT:-5000}

# ✅ Gerar o arquivo via entrypoint.sh com os valores resolvidos
```

### 2. `sed` global pode sobrescrever campos indevidos
```sh
# ❌ Substitui TODOS os "Port =" no arquivo, inclusive o do MQTT
sed -i "s/^Port = .*/Port = ${PORT}/" mesh.ini

# ✅ Gerar o arquivo inteiro via heredoc no entrypoint.sh
```

### 3. Tipo de serviço no Render não pode ser alterado via API
A API retorna `{"message":"only web services allowed for plan"}` ao tentar
criar `background_worker` no plano free. Solução: deletar e recriar ou usar
o painel web.

### 4. Root topic do MQTT deve corresponder ao broker
O broker `platform.meshbrasil.com` aceita apenas o root topic `meshdev`.
Usar `msh` (padrão do Meshtastic) resulta em mensagens rejeitadas silenciosamente.

### 5. Secrets expostos no histórico do Git
Se um segredo for acidentalmente commitado, **purgar o histórico completo**:

```bash
# Remover arquivo do tracking
git rm --cached arquivo_com_segredo

# Purgar de todo histórico
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch arquivo_com_segredo' \
  --prune-empty --tag-name-filter cat -- --all

# Limpar refs antigas
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin main --force
```

> ⚠️ Mesmo após o force push, **rotacionar os tokens/senhas expostos**,
> pois o GitHub pode ter cacheado os dados.

---

## Variáveis de Ambiente deste Projeto

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| `TELEGRAM_TOKEN` | Token do bot via BotFather | ✅ |
| `TELEGRAM_ADMIN_ID` | Seu user ID numérico no Telegram | ✅ |
| `TELEGRAM_ROOM_ID` | ID do chat onde o bot opera | ✅ |
| `TELEGRAM_ROOM_LINK` | Link do chat/bot | ✅ |
| `MQTT_HOST` | Endereço do broker MQTT | ✅ |
| `MQTT_PORT` | Porta do broker (1883 sem TLS) | ✅ |
| `MQTT_USER` | Usuário do broker | ✅ |
| `MQTT_PASSWORD` | Senha do broker | ✅ |
| `MQTT_TOPIC` | Root topic (`meshdev` para MeshBrasil) | ✅ |
| `MQTT_CHANNEL` | Nome do canal Meshtastic | ✅ |
| `MESHTASTIC_ENCRYPTION_KEY` | PSK base64 do canal (para cifrar/decifrar) | ✅ |
| `TELEGRAM_SUBSCRIBERS` | IDs (separados por vírgula) pré-inscritos no broadcast | ➖ |
| `TELEGRAM_SUBSCRIBERS_FILE` | Caminho do JSON de inscritos (padrão `subscribers.json`) | ➖ |

---

## Broadcast para inscritos (Meshtastic → todos que falaram com o bot)

Toda mensagem recebida do canal **Bertioga** é enviada para o `TELEGRAM_ROOM_ID`
**e** para todo usuário que já interagiu com o bot em chat privado.

- **Inscrição automática:** qualquer mensagem/comando em privado com o bot
  registra o `chat_id` (handler `register_subscriber`, grupo -1) e o bot
  responde "✅ Inscrito!".
- **Remoção automática:** se o usuário bloquear o bot (erro `Forbidden`), ele
  sai da lista.
- **Armazenamento:** arquivo JSON `subscribers.json` no container
  (`mtg/connection/telegram/subscribers.py`).

> ⚠️ No Render free o disco é efêmero: o arquivo some a cada deploy/restart.
> A cada novo inscrito o log mostra `New subscriber X (all: a,b,c)` —
> copie essa lista para a env var `TELEGRAM_SUBSCRIBERS` para mantê-la.
> Alternativa futura: banco externo grátis (Upstash Redis / Neon Postgres).

## Lições do downlink (Telegram → rádio)

- O firmware descarta pacotes MQTT sem o **channel hash** correto
  (xor dos bytes do nome ^ xor dos bytes do PSK; Bertioga = **178**).
- O rádio `!459dd94b` não tem Wi-Fi: usa `proxy_to_client`, ou seja, só recebe
  do MQTT enquanto o app do celular estiver conectado (Bluetooth + internet).
