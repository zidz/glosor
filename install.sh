#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Ordläxan (ordovning) – installationsskript
#
# Skapar en systemd-unit som serverar index.html ur DEN KATALOG där du kör
# skriptet ($(pwd)). Verifiera att index.html ligger i katalogen först.
#
#   * Kör som root            → system-tjänst: /etc/systemd/system/ordovning.service
#   * Kör som vanlig användare → user-tjänst:   ~/.config/systemd/user/ordovning.service
#
# Användning:
#   ./install.sh            installerar/uptar tjänsten och startar den
#   ./install.sh stop       stänger tjänsten (men behåller den)
#   ./install.sh status     visar status
#   ./install.sh uninstall  tar bort tjänsten helt
#
# Miljövariabler:
#   ORDOVNING_PORT  port (standard: 8080)
# ---------------------------------------------------------------------------
set -euo pipefail

APP_DIR="$(pwd)"          # systemd-tjänsten serverar .html-filen HÄR
PORT="${ORDOVNING_PORT:-8080}"
UNIT_NAME="ordovning.service"
CMD="${1:-install}"

err() { echo "⚠️  $*" >&2; exit 1; }

# --- Validering -------------------------------------------------------------
PYTHON_BIN="$(command -v python3 || true)"
[ -n "$PYTHON_BIN" ] || err "python3 hittades inte i PATH – installera den först."

if [ ! -f "$APP_DIR/index.html" ]; then
  err "index.html hittades inte i $(pwd). Kör skriptet i den katalog där index.html ligger."
fi

# --- Bestäm om det är system- eller user-tjänst -----------------------------
IS_ROOT=0
[ "$(id -u)" -eq 0 ] && IS_ROOT=1

if [ "$IS_ROOT" -eq 1 ]; then
  UNIT_PATH="/etc/systemd/system/$UNIT_NAME"
  SC=(systemctl)
  WANTED_BY="multi-user.target"
else
  UNIT_PATH="$HOME/.config/systemd/user/$UNIT_NAME"
  SC=(systemctl --user)
  WANTED_BY="default.target"
fi

# --- Skriv unit-filen --------------------------------------------------------
write_unit() {
  mkdir -p "$(dirname "$UNIT_PATH")"
  cat > "$UNIT_PATH" <<EOF
[Unit]
Description=Ordläxan – ordövningsapp (serverad från $APP_DIR)
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=$PYTHON_BIN -m http.server $PORT --bind 0.0.0.0 --directory $APP_DIR
Restart=on-failure
RestartSec=3

[Install]
WantedBy=$WANTED_BY
EOF
  echo "ℹ️  Skrev unit-fil: $UNIT_PATH"
}

port_in_use() {
  command -v ss >/dev/null 2>&1 || return 1
  ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "[:.]$PORT$"
}

# --- Underkommandon ----------------------------------------------------------
case "$CMD" in
  install)
    port_in_use && err "Port $PORT används redan av en annan process – välj en annan med ORDOVNING_PORT eller stoppa den (se: ss -ltnp)."
    write_unit
    "${SC[@]}" daemon-reload
    "${SC[@]}" enable "$UNIT_NAME" >/dev/null 2>&1 || true
    "${SC[@]}" restart "$UNIT_NAME"

    if [ "$IS_ROOT" -eq 0 ]; then
      if loginctl enable-linger "$(id -un)" 2>/dev/null; then
        echo "ℹ️  Linger aktiverad – tjänsten körs även utan inloggning."
      else
        echo "ℹ️  OBS: för att tjänsten ska köra även när du är utloggad, kör:"
        echo "       sudo loginctl enable-linger $(id -un)"
      fi
    fi

    sleep 1
    if ! "${SC[@]}" is-active --quiet "$UNIT_NAME"; then
      err "Tjänsten startade inte – kolla loggen: ${SC[*]} status $UNIT_NAME"
    fi

    LOCAL_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
    echo ""
    echo "✅  Ordläxan är installerad och körs!"
    echo "    Port:       $PORT"
    echo "    Enhet:      $(id -un)"
    echo "    Unit-fil:   $UNIT_PATH"
    [ -n "$LOCAL_IP" ] && echo "    Adress:     http://$LOCAL_IP:$PORT"
    echo "    Status:     ${SC[*]} status $UNIT_NAME"
    echo "    Logg:       ${SC[*]} cat -n $UNIT_NAME"
    ;;

  stop)
    "${SC[@]}" stop "$UNIT_NAME"
    echo "✅  Tjänst $UNIT_NAME stoppad."
    ;;

  status)
    "${SC[@]}" status "$UNIT_NAME" --no-pager
    ;;

  uninstall)
    "${SC[@]}" stop "$UNIT_NAME" 2>/dev/null || true
    "${SC[@]}" disable "$UNIT_NAME" 2>/dev/null || true
    rm -f "$UNIT_PATH"
    "${SC[@]}" daemon-reload
    echo "✅  Tjänst $UNIT_NAME borttagen ($UNIT_PATH)."
    ;;

  *)
    echo "Användning: $0 [install|stop|status|uninstall]"
    exit 1
    ;;
esac
