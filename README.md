# Ordläxan (Ordövning)

Enkelfladig webapp (vanilj HTML/CSS/JS) för att öva ord – byggd för barnen Katie och Charlie.
Läxor sparas lokalt i webbläsaren (localStorage). Ingen backend, ingen databas.

## Funktioner

- Skapa/ändra/radera läxor (namn + språk: engelska/tyska + ordpar)
- Arkivera läxor (döljs från startsidan, återställbara, ingår i export)
- Exportera/importera alla läxor som JSON-backup (import lägger till, samma namn ignoreras)
- Fyra övningslägen:
  - 🎯 Klassiskt Förhör
  - ❓ Flervalsquiz
  - 🧩 Matcha Orden
  - 🎧 Lyssna & Stava (ordet läses högt automatiskt innan skrivning)
- Tal via Web Speech API (en-GB / de-DE)
- Listan är sorterad nyast först; redigering bevarar ordning (createdAt)

## Filstruktur

| Fil | Beskrivning |
|---|---|
| `index.html` | Hela appen (HTML+CSS+JS i en fil) |
| `ordovning.service` | systemd-unit som serverar appen på port 8080 |

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

Verifiering:

```bash
ssh root@10.2.1.2 'systemctl is-active ordovning.service; curl -s -o /dev/null -w "%{http_code} %{size_download}\n" http://localhost:8080/'
```

## Utvecklingsnotering

- Syntax-check innan deploy: extrahera `<script>`-delen och kör `node --check`
- Kanonisk kopia: `/a0/usr/projects/Private/ordovning/` (detta repo)
- Deployas via SSH (root) från Agent Zero
