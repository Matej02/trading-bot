#!/bin/sh
# Stazeni HistData M1 ASCII (SPXUSD, NSXUSD) 2010-2025, po jednom souboru s pauzou.
cd "/d/Trading bot/research_data/histdata/zip" || exit 1
UA="Mozilla/5.0 (research download)"
for P in SPXUSD NSXUSD; do
  p=$(echo $P | tr 'A-Z' 'a-z')
  for Y in $(seq 2010 2025); do
    f="HISTDATA_COM_ASCII_${P}_M1${Y}.zip"
    [ -s "$f" ] && { echo "ma $f"; continue; }
    ref="https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/${p}/${Y}"
    tk=$(curl -s -A "$UA" "$ref" | grep -o 'name="tk" id="tk" value="[0-9a-f]*"' | head -1 | sed 's/.*value="//;s/"//')
    [ -z "$tk" ] && { echo "BEZ TOKENU $P $Y"; continue; }
    curl -s -A "$UA" -e "$ref" -X POST "https://www.histdata.com/get.php" \
      --data "tk=$tk&date=$Y&datemonth=$Y&platform=ASCII&timeframe=M1&fxpair=$P" -o "$f"
    if head -c 2 "$f" | grep -q PK; then echo "ok $f $(wc -c < "$f")"; else echo "CHYBA $f"; head -c 200 "$f"; echo; rm -f "$f"; fi
    sleep 3
  done
done
