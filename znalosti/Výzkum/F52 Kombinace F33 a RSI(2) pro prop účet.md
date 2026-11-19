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

## Výsledky (2026-11-19)
Souhrn `research_data/f52/souhrn.txt`. Obchodů: RSI(2) 613 (25,8 ročně), F33 400 (16,8 ročně).

| Část | RSI(2) Sharpe / R za rok / propad | F33 | **Obě** |
|---|---|---|---|
| Vývoj 2003–2018 | 0,83 / +2,72 / −5,0 R | 0,80 / +1,74 / −3,0 R | **1,09 / +4,46 / −5,8 R** |
| Kontrola 2019–2026 | 0,82 / +2,75 / −4,5 R | 0,56 / +1,23 / −4,5 R | **0,97 / +3,99 / −7,3 R** |

- **Korelace měsíčních výsledků F33 a RSI(2): +0,07.** Prakticky nezávislé, ideální kombinace.
- **Největší propad 2003–2026:** obě −7,9 R (RSI(2) −7,3, F33 −4,5).
- **Ztrátové roky kombinace:** jen 2018 (−1,8 R) a 2020 (−6,4 R). Ostatních 22 let kladných.
- **Rozhodnutí podle pravidel předem: všechny 3 body ANO ⇒ KOMBINACE POMÁHÁ.**

**Simulace prop zkoušky** (start každý měsíc, +10 % před −10 % / −5 % za den, max 12 měsíců):

| Riziko na obchod | Prošel | Propadl | Vypršelo | Medián do úspěchu |
|---|---|---|---|---|
| 0,25 % / 0,5 % | 0 % | 0 % | 100 % | – |
| 1 % | 8 % | 0 % | 92 % | 9,9 měs. |
| 2 % | **54 %** | 8 % | 39 % | 7,1 měs. |

- Limit −5 % za den nebyl porušen ani jednou.
- **Prakticky:**
  - při 1 % je to asi **+4 % ročně s propadem do −8 %**: bezpečné, ale zkoušku +10 % s limitem 12 měsíců skoro nesplní. Firma bez časového limitu (FTMO) by ji splnila asi za 2–3 roky;
  - při 2 % asi +8 % ročně, ale propad až −16 % by na financovaném účtu porušil limit −10 %.
  - **Rozumné nastavení pro prop: 1–1,5 % na obchod a firma bez časového limitu.**
- **Výhrady:**
  - účet se v simulaci mění jen při uzavření, propad uvnitř obchodu chybí;
  - souběžně může být až 5 pozic na US indexech (RSI(2) na 3 trzích + F33 na 2), což je v nejhorší den 5× riziko;
  - na malém účtu brání minimální loty (viz [[F42 RSI(2) přísná prověrka|F42]]).
