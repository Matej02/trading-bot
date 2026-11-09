---
tags: [vyzkum, f34, risk, korelace]
datum: 2026-11-09
---
# F34 Limit rizika pro korelované trhy

Zadání uživatele (2026-11-09): „ano“ na otázku, zda udělat limit rizika pro trhy, které se hýbou spolu, a nejdřív otestovat, jak by změnil výsledky RSI(2). Vychází z [[Souhrn testů F21–F33 a přínosy|souhrnu]], bod 6. Skript `scratch/f34_korelace.py`.

## Plán (zapsán PŘED výpočtem)
**Skupiny:**
- US indexy: SPX500, NAS100, US30 (i futures varianty);
- evropské indexy: DAX, FTSE, CAC, EuroStoxx, IBEX;
- kovy: XAU, XAG;
- krypto: BTC, ETH.
- Forex už hlídá Risk přes expozici měn.

**Pravidla k porovnání:**
- **A – veto:** ve skupině smí být jen 1 otevřená pozice stejným směrem. Další se nebere. Signály ze stejného dne v pořadí SPX, NAS, US30 (atd.).
- **B – strop 1,5:** součet rizika otevřených pozic ve skupině a směru ≤ 1,5násobek rizika obchodu. Nová pozice dostane jen zbytek, pod 0,25 se nebere.

**Obchody** (historie z testů, 1 R = riziko jednoho obchodu, P&L se počítá při výstupu):
1. RSI(2) pullback na US indexech (F6, 1995–2026);
2. Průraz F2 na 9 trzích (F4 varianta A, 2009–2026);
3. Portfolio RSI(2) + Průraz + F33 (F33 od 2003).

**Měří se:**
- součet R;
- maximální propad v R;
- MAR = součet / propad;
- nejhorší měsíc;
- vše zvlášť do 2018 a od 2019.

**Pravidla rozhodnutí (pevná):** pravidlo se zavede, jen když v obou obdobích:
1. **MAR je vyšší** než bez limitu;
2. **součet R klesne nejvýš o 25 %.**

Když projdou obě pravidla, vybere se to s vyšším MAR od 2019.

## Výsledky (2026-11-09)
Souhrn: `research_data/f34/f34_souhrn.txt`.

| Obchody | Období | Bez limitu | A (1 pozice ve skupině) | B (strop 1,5 R) |
|---|---|---|---|---|
| RSI(2) US indexy | do 2018 | +55,8 R, propad 5,1, MAR 10,96 | +14,2 R, MAR 2,78 | +25,6 R, MAR 5,05 |
| | od 2019 | +25,7 R, propad 7,1, MAR 3,61 | +10,4 R, MAR 2,61 | +13,1 R, MAR 2,68 |
| Průraz F2 | do 2018 | −11,5 R (indexy v datech až od 2019) | beze změny | beze změny |
| | od 2019 | +50,2 R, propad 30,4, MAR 1,65 | +27,6 R, MAR 1,04 | +38,9 R, MAR 1,40 |
| Portfolio RSI(2) + Průraz + F33 | do 2018 | +127,9 R, propad 19,8, MAR 6,47 | +53,4 R, MAR 2,67 | +81,4 R, MAR 4,19 |
| | od 2019 | +104,8 R, **propad 41,6**, MAR 2,52 | +60,4 R, propad 21,6, MAR 2,80 | +84,8 R, **propad 22,5**, MAR **3,77** |

**Rozhodnutí podle pravidel zapsaných předem:** ani jedno pravidlo neprošlo u žádné sady → **NEZAVÁDĚT.**
- **RSI(2) vydělává právě tím, že kupuje propad na všech US indexech zároveň.** Limit jí bere 50–75 % zisku.
- **U portfolia od 2019 by strop B snížil maximální propad na polovinu (41,6 → 22,5 R) za −19 % zisku.** Do 2018 ale zisk i MAR zhoršil.
- Pokud by uživatel někdy chtěl nižší propady za cenu nižšího zisku, strop B je kandidát. Je to rozhodnutí o riziku, ne o výhodě.
