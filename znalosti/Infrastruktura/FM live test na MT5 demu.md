---
tags: [infrastruktura, mt5, live]
datum: 2026-11-04
---
# Live test FM strategií na MT5 demu (`run_fm_demo.py`)

Zadání uživatele (2026-11-04): „jako poslední task to celé nasadíme a budeme testovat live na našem demu“.

- **Účet:** 937584 @ GlobalDynamicMarkets-Demo. Runner obchoduje **jen když MT5 hlásí účet jako DEMO**, jinak skončí ([[MT5 napojení]]).
- **Strategie:** přímo Python kód testů, stejná logika jako kontrola shody se simulátorem:

  | Strategie | Trhy | Magic |
  |---|---|---|
  | F12 Můčka | EURUSD, GBPUSD, XAUUSD, XAGUSD, NAS100 | 20261112 |
  | F13 Veselovský | NAS100, SPX500, EURUSD, GBPUSD, XAUUSD | 20261113 |
  | F14 Pátek | NAS100, GBPUSD, XAUUSD | 20261114 |
  | F15 Hvězda | 12 trhů s COT | 20261115 |
  | F16 Hakimi | XAUUSD, XAGUSD | 20261116 |

- **Data:** M1 75 dní a H1 6 500 svíček z MT5 každou minutu. Čas serveru (Londýn) se převádí na UTC stejně jako v testech.
  - **Shoda živých dat s testovací historií: 19/19 signálů** (F12, F13, F14 na 6 trzích).
- **Pravidla obchodu:**
  - market order se SL a TP podle strategie;
  - riziko 0,25 % zůstatku, SL aspoň 3× spread;
  - jedna pozice na strategii a trh;
  - intradenní obchody zavře ve 22:00 Praha, F15 nejdéle po 10 dnech.
- **Deník** `fm_demo_journal.jsonl`, stav `fm_demo_state.json`.
- **Spuštění:** `py run_fm_demo.py --live` (bez `--live` suchý běh, `--once` jeden cyklus). Spuštěno 2026-11-04 18:21 v terminálu.
- **F17–F19** (Šrajer, Valchář, Kimmel model 2) zatím v runneru nejsou. Nemají kandidátní režim a v testech byly bez výhody.
- **Všechno je NEOVĚŘENÉ.** Účel je sbírat živá data, ne vydělávat. Viz [[Co nefunguje]].
