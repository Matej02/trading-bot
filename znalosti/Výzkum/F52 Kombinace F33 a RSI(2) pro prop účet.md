---
tags: [vyzkum, f52, portfolio, prop, f33, rsi2]
datum: 2026-11-19
---
# F52 Kombinace F33 a RSI(2) pro prop účet

Zadání uživatele (2026-11-19): „Ano, pokračuj kombinací F33 a RSI2.“

**Proč:** jediné dvě ověřené strategie ([[F33 Rebalancování na konci měsíce|F33]], [[F42 RSI(2) přísná prověrka|RSI(2)]]). Otázky:
- doplňují se, tedy dávají spolu lepší poměr zisku a propadu?
- jaké riziko na obchod by na prop účtu (zkouška +10 %, limit −10 % celkem a −5 % za den, [[Cesta k prop účtu]]) dávalo nejlepší šanci?

Nehledá se nová výhoda, jen kombinace ověřených pravidel beze změny. Bot se nemění.

## Plán (zapsán PŘED výpočtem)
- **Obchody z testů beze změny pravidel:**
  - F33: SPX + NAS, Yahoo 2003–2026;
  - RSI(2): SPX + NAS + US30, Yahoo 2003–2026.
- **Jednotka rizika = 3 ATR** (SL obou strategií živě):
  - u F33 se výsledek přepočítá R_ATR / 3;
  - u RSI(2) už je výsledek v 3 ATR.
- **Každá pozice riskuje stejné % účtu.** Souběžné pozice jsou povolené (jako v botovi).
- **Účet se přepočítává při uzavření obchodů** (ne průběžně). Propad uvnitř obchodu tedy chybí, ale ztráta obchodu je omezená stopem.
- **Rozhodovací body (zapsány předem):**
  1. Korelace měsíčních výsledků F33 a RSI(2) < 0,5 (rozložení rizika).
  2. Sharpe kombinace (měsíčně) > Sharpe každé zvlášť, ve vývoji 2003–2018 i v kontrole 2019–2026.
  3. Největší propad kombinace (v R) < součet největších propadů obou zvlášť.
- **Popis (nerozhoduje):** simulace prop zkoušky při riziku 0,25 / 0,5 / 1 / 2 % na obchod.
  - Start každý měsíc 2003–2025.
  - Úspěch = +10 % dřív než −10 % celkem nebo −5 % za den.
  - Časový limit 12 měsíců.
  - Podíl úspěchů, neúspěchů a vypršení, medián doby do úspěchu.

Skript `scratch/f52_kombinace.py`, výstup `research_data/f52/souhrn.txt`.
