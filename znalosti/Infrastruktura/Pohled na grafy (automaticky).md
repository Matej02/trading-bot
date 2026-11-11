---
tags: [infrastruktura, grafy]
datum: 2026-11-11
---
# Pohled na grafy (automaticky)

Zadání uživatele (2026-11-11): „Potřebuju vyřešit, abys reálně sledoval TradingView“. Upřesnění:
- „Neber to z MT5, tam nejsou dobrá data“;
- „Nechávám zapnutý PC, takže u toho nejsem. Musí to být plně automatické, bez mého dozoru nebo pomoci.“
- Claude se spouští se startem PC (nastavil uživatel 11. 11.).

## Proč ne TradingView
- TradingView výslovně uvádí: „All our features are for manual use only.“ Automatický sběr dat (skripty, API, roboti, snímání obrazovky) zakazuje a trestá blokací, opakovaně i trvalou ([podpora TradingView](https://www.tradingview.com/support/solutions/43000674726-why-is-my-account-banned-due-to-suspicious-activity/)).
- Bezplatná verze nemá API na data. Alerty do bota (webhook) jdou jen v placeném plánu (Essential a vyšší) se zapnutým dvoufázovým ověřením.
- Data feed bota z TradingView proto nestavět. Naplánované prohlížení TradingView v prohlížeči bylo vytvořené a před prvním během vypnuté.

## Jak to běží
- **Naplánovaná úloha v aplikaci Claude** `pohled-na-grafy`, v pracovní dny v **8:05 (Londýn)** a **14:05 (New York)**.
  - Úloha běží jen při spuštěné aplikaci Claude, ta se teď zapíná s PC.
- **Data:** Yahoo Finance, zdarma, bez účtu a bez přihlášení (stejný zdroj, jaký už používá simulátor).
  - Trhy: EURUSD=X, GBPUSD=X a futures zlato GC=F, NAS100 NQ=F, SPX500 ES=F.
  - Futures se od CFD liší o pár bodů a jsou zpožděné asi o 10 min.
  - Kontrola 11. 11.: úplnost 15m a 5m dat 98–100 %. Bias pravidel F13 vyšel na všech 5 trzích stejně jako z MT5 brokera.
- **Skript** `scratch/grafy_yahoo.py`:
  - nakreslí obrázek: vlevo denní graf (den 17:00–17:00 NY, PDH/PDL), vpravo 15m v pražském čase (Asie, Londýn, NY; čáry PDH, PDL, Asie H/L, NY open);
  - vypíše úrovně a bias podle pravidel F13.
- **Claude si obrázky prohlédne** a napíše rozbor: bias, sweep likvidity, co hlídat v killzone. Bias zapíše se živou cenou (`grafy_yahoo.py zapis TRH SMER`).
- **Výstup:**
  - poznámka `Grafy/Pohled na grafy RRRR-MM-DD.md`;
  - obrázky v `Přílohy/Grafy/` (jen na disku, ne v gitu);
  - deník `scratch/grafy/claude_bias.jsonl` (také mimo git).
- **Hranice:** žádný web ani TradingView, MT5 a runner se nespouští ani nemění, bez commitu a pushe. Poznámky commituje hlavní relace při pondělní kontrole.
- **Zadání úlohy** je uložené v `scratch/pohled_na_grafy_uloha.md`.

## Vyhodnocení (pravidla předem, 2026-11-11)
- `grafy_yahoo.py vyhodnot` porovná každý zápis s koncem obchodního dne (17:00 NY), data z Yahoo:
  - **směr:** cena na konci dne vůči ceně při zápisu;
  - **cíl:** PDH (long) nebo PDL (short) zasažen po zápisu do konce dne.
  - Stejně se hodnotí bias podle pravidel F13. Neutrální se nepočítá.
- **Rozhodnutí až po ≥ 30 obchodních dnech a ≥ 100 zápisech long/short.** Čtení grafu přidává hodnotu, jen když platí obojí:
  - směr Claude je lepší než 50 % se z ≥ 1,65;
  - a je lepší než bias pravidel.
- Do té doby rozbor **neovlivňuje bota ani simulátor**. Je to záznam pro výzkum, ne obchodní doporučení.

## Data feed bota
- MT5 runner musí brát ceny od brokera, u kterého obchoduje: za ně se plní příkazy a podle nich se trefí SL/TP.
- Cizí feed se s brokerem rozchází. U F13 byla shoda Yahoo × broker jen ~50 %, protože sweep stojí na jednom ticku.
- Slabina MT5 je historie s dírami (EURUSD chybí 10/2025–10/2026). Testy proto jedou na HistData a Yahoo.
- Lepší data = výběr lepšího brokera před live (spolu s malým účtem).
