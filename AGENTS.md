# AGENTS.md – Glosor

## Översikt

"Glosor" (Zilux IT AB) – enkelbladad webapp (vanilj HTML/CSS/JS, ingen framework, ingen byggsteg) för att öva glosor.

| Fil | Beskrivning |
|---|---|
| `index.html` | Hela appen: HTML + CSS + JS i en enda fil (JS i ett enda `<script>`-block) |
| `server.py` | HTTP-server (endast Python standardbibliotek) som servar appen + loggar användning |
| `användningslogg.txt` | Användningslogg `<tidpunkt> <IP> <funktion>` (gitignored, innehåller IP) |
| `.log_secret` | Hemmelighet för logg-cookies (gitignored, **får aldrig commitas**, skapas automatiskt) |
| `install.sh` / `ordovning.service` | systemd-installation (port via `ORDOVNING_PORT`, standard 8080) |

Data sparas klient-sida i `localStorage` (`ordlaexan_glossaries`).

## Konventioner

- All UI-text, kodkommentarer och commitmeddelanden på **svenska**.
- Ingen nya bibliotek, inget byggsteg. JS-stil: `var`, funktioner, ingen ES6-modulsyntax.
- JS-hjälpfunktioner placeras bredvid relaterad kod (t.ex. `langLabel`/`isoWeek` i "Tillstånd"-sektionen).
- `server.py` använder endast standardbiblioteket.

## Workflow (inlärd rutin)

1. **Utforska först** – läs berörd del av `index.html`/`server.py` innan ändring (appen är en stor fil utan moduler).
2. **Planera icke-triviella ändringar** – presentera plan och få ok innan implementering.
3. **Implementera i befintlig stil** – se Konventioner ovan.
4. **Verifiera alltid innan commit** (se nedan).
5. **Commita/pusha bara när uttryckligen ombedd** – svenska commitmeddelanden, en commit per omtanke (t.ex. `index.html` och `server.py` som separata commits).

## Verifiering

### JS-syntax (ingen `node` på servern)

README:et nämner `node --check`; på denna maskin används esprima i en venv:

```bash
python3 -m venv /tmp/opencode/venv   # en gång
/tmp/opencode/venv/bin/pip install esprima
# Extrahera <script>-blocket ur index.html och pars:
/tmp/opencode/venv/bin/python -c "
import re, esprima
html = open('index.html', encoding='utf-8').read()
esprima.parseScript(re.search(r'<script>(.*?)</script>', html, re.S).group(1), {'tolerant': False})
print('OK')"
```

### Python

```bash
python3 -m py_compile server.py   # radera __pycache__/ efteråt
```

### Livetest av serverändringar – ISOLERAD kopia, aldrig mot produktion

```bash
rm -rf /tmp/opencode/glosortest && mkdir -p /tmp/opencode/glosortest
cp server.py index.html /tmp/opencode/glosortest/
cd /tmp/opencode/glosortest && ORDOVNING_PORT=8091 python3 server.py &
# testa med curl (GET / sätter cookie; /log kräver cookie; 403/429-fall)
kill <PID>   # döda testservern per PID!
rm -rf /tmp/opencode/glosortest
```

**Varning:** `pkill -f <sökväg>` matchar också skallets egen kommandorad och dödar skallet. Använd `pgrep -af "[m]önster"` (hakparent-bus) eller döda per PID.

Produktion (port 8080, systemd-tjänsten) får inte påverkas av tester.

## Servern och loggskyddet

- `server.py` skriver `användningslogg.txt`. Endpoints `/log` (GET och POST – klientens `sendBeacon` skickar GET när ingen data bifogas).
- Skydd i tre lager:
  1. **HMAC-signerad cookie** `glosor_log` (utsänds vid GET /, bunden till klient-IP, 30 dagar, `HttpOnly; SameSite=Lax`). Sekret i `.log_secret` (skapas med 0600 vid första start). Ogiltig/saknad cookie → 403.
  2. **Rate limit** 120 loggeven/h/IP (in-memory, `threading.Lock`) → 429 över taket.
  3. **Feature-allowlist** (`FEATURES` i server.py) – okända namn skrivs som `okänd`.
- Klienten (`logFeature()` i index.html) kräver **inga** ändringar: same-origin `sendBeacon` skickar cookie automatiskt och URL-encoderar featuret.
- **Nytt feature?** Lägg till namnet i BÅDE `FEATURES` (server.py) och `logFeature()`-anropet (index.html).
- IP:en är första värdet i `X-Forwarded-For` (annars peer-IP) – reverse proxy måste sätta den riktiga klient-IP:en, annars försvagas cookie-bindningen.
- `IGNORED_IPS` i server.py för interna IP som inte ska loggas.

## Deploy

1. Pusha till `main`.
2. På servern: pull + `systemctl restart ordovning.service` (eller `--user` beroende på installation – se README).
3. Verifiera:

```bash
ssh root@[IP] 'systemctl is-active ordovning.service; curl -s -o /dev/null -w "%{http_code} %{size_download}\n" http://localhost:8080/'
```
