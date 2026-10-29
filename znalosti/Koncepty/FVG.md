---
tags: [koncept, smc]
aktualizovano: 2026-10-29
---
# FVG – fair value gap

Býčí: low[i] > high[i−2], zóna mezi nimi, minimálně 0,25 ATR; CE = střed. Vstupní limit na CE po [[MSS a displacement|MSS]].
V [[F7 Dokument 6 strategií SMC|F7]] typická ztráta: cena se vrátí do FVG a pokračuje na SL. Viz též [[Order block]].

## Definice z dokumentu
- Bullish FVG na svíčce i: low[i] > high[i−2], zóna [high[i−2], low[i]]; bearish high[i] < low[i−2].
- Minimum 0,25 × ATR, menší ignorovat. CE = střed mezery.
- Mitigace = první dotek; zneplatnění = close za vzdáleným okrajem; max stáří 100 svíček.

Zdroj: [[Dokument 6 strategií SMC + Volume Profile|dokumentu 6 strategií]].

## Z materiálů FM (část 1)
- **FVG** = mezera mezi svíčkou 1 a 3 kolem impulzivní svíčky 2. **Reakce na 50 %** (Můčka, Hakimi).
  **Close za FVG ho ruší** (Veselovský). FVG ve směru trendu, jinak magnet a target.
- **iFVG:** FVG proražený closem, otočí směr a slouží jako zóna v novém směru.
- **BPR:** býčí a medvědí FVG se překrývají; BPR je část, do které nezasahují knoty.
- **Gap vs FVG:** gap se musí zaplnit celý a je to target, ne vstup.
- Vstup po MSS do **první FVG s 0,382** (Veselovský), na M5 přednostně FVG (Můčka).

F9 (2026-10-29): jako spouštěč i filtr v 2 208 kombinacích ([[F9 Kombinace FM konceptů]]) – bez výhody.
