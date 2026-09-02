# Ordläxan (Ordövning)

Enkelfladig webapp (vanilj HTML/CSS/JS) för att öva ord – byggd för barnen Katie och Charlie.
Läxor sparas lokalt i webbläsaren (localStorage). Ingen backend, ingen databas.

## Funktioner

- Skapa/ändra/radera läxor (namn + språk: engelska/tyska/svenska)
  - Engelska/Tyska: ordpar (utländska + svenska)
  - Svenska: enstaka ord (inga par) – enda övningen är 🎧 Lyssna & Stava
- Arkivera läxor (döljs från startsidan, återställbara, ingår i export)
- Exportera/importera alla läxor som JSON-backup (import lägger till, samma namn ignoreras)
- Fyra övningslägen (engelska/tyska) / ett (svenska):
  - 🎯 Klassiskt Förhör
  - ❓ Flervalsquiz
  - 🧩 Matcha Orden
  - 🎧 Lyssna & Stava (ordet läses högt automatiskt innan skrivning)
- Tal via Web Speech API (en-GB / de-DE / sv-SE)
- Listan är sorterad nyast först; redigering bevarar ordning (createdAt)

## Filstruktur

| Fil | Beskrivning |
|---|---|
| `index.html` | Hela appen (HTML+CSS+JS i en fil) |
| `ordovning.service` | systemd-unit som serverar appen på port 8080 (manuell) |
| `install.sh` | Installationsskript – skapar + startar systemd-unit automatiskt |

## Deploy

Deployas till `/root/ordovning/index.html` på barnens datorer och servas av `ordovning.service` (port **8080**):

| Maskin | IP |
|---|---|
| Katie Pi | `10.2.1.2` |
| Charlie Tower | `10.2.1.37` |

Manuell deploy:

```bash
scp index.html root@10.2.1.2:/root/ordovning/index.html
scp index.html root@10.2.1.37:/root/ordovning/index.html
# http.server läser filen per request – ingen service-omstart behövs
```

### Installation på en ny maskin

Kopiera över `index.html` + `install.sh` till en katalog, gå dit och kör:

```bash
cd /sökväg/till/ordovning    # katalogen som innehåller index.html
./install.sh                  # skapar + startar systemd-tjänsten (port 8080)
```

Skriptet använder `$(pwd)` – tjänsten servar alltid `index.html` där skriptet körs.

| Kör som | Unit-fil | Kommando |
|---|---|---|
| root | `/etc/systemd/system/ordovning.service` | `systemctl` |
| vanlig användare | `~/.config/systemd/user/ordovning.service` | `systemctl --user` |

Underkommandon: `./install.sh stop` · `./install.sh status` · `./install.sh uninstall`

Miljövariabel: `ORDOVNING_PORT` (standard **8080**) för att byta port. Vanlig-användar-tjänst bör aktivera linger (`sudo loginctl enable-linger <user>`) för att köra utan inloggning.

Verifiering:

```bash
ssh root@10.2.1.2 'systemctl is-active ordovning.service; curl -s -o /dev/null -w "%{http_code} %{size_download}\n" http://localhost:8080/'
```

## Utvecklingsnotering

- Syntax-check innan deploy: extrahera `<script>`-delen och kör `node --check`
- Kanonisk kopia: `/a0/usr/projects/Private/ordovning/` (detta repo)
- Deployas via SSH (root) från Agent Zero
