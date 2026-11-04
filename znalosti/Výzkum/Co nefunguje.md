---
tags: [vyzkum, souhrn]
aktualizovano: 2026-10-29
---
# Co nefunguje (souhrn)

| Co | Kde zjištěno | Proč |
|---|---|---|
| Technické indikátory na H1 | [[Historie v1–v6]] | po nákladech 0 z 60 |
| Krátké timeframy (1m–15m) | [[F2 Více timeframů]], [[F7 Dokument 6 strategií SMC]] | spread velká část SL ([[Náklady brokera]]) |
| SMC: [[SFP – sweep likvidity|SFP]], [[FVG]], [[Order block|OB]], [[MSS a displacement|MSS]] | [[F5 SMC a volume profile na 1h]], [[F7 Dokument 6 strategií SMC]] | ~0 R i bez nákladů |
| [[Volume profile]] (VA, POC, HVN) | F5, F7 | žádná výhoda |
| Průraz mimo zlato/US indexy/BTC | [[F3 Průraz na nových trzích]] | −0,11 R |
| Vstup na menším TF po denním signálu | [[F4 Vstup na menším timeframu]] | užší SL = vyražení |
| [[Momentum L=250]] | [[F1 Nové třídy signálů]] | výnos sežere swap brokera |
| [[COT]], limitky, adaptivní přepínání | [[Historie v1–v6]] | náhoda / drift |

Co funguje aspoň částečně: [[Průraz F2 (proraz_d1)]], [[RSI(2) pullback (mr_rsi2_d1)]].

Doplněno 2026-10-29: SMC koncepty nefungují ani na [[Forex|forexu]] a [[Zlato|zlatě]] s M1 vstupem ([[F7 Dokument 6 strategií SMC]]).

Doplněno 2026-10-29 ([[F8 Strategie z FM PDF]]):
- **S/D zóny po FM na D1, H4 a D v W:** OOS −0,17 až −0,22 R, horší než náhoda.
- **Daily bias jako samostatný obchod:** −0,06 R.
- **Makro skóre (Trading Analyzer):** ~0.
- **Kombinace FM konceptů** (8 spouštěčů × filtry × TP, H1 i H4, 2 208 kombinací): 0 prošlo výběrem ([[F9 Kombinace FM konceptů]]).
- **Entry modely všech mentorů FM přesně podle PDF** (Veselovský, Kimmel, Pátek, Šrajer DT, Můčka, Valchář, Hakimi, Hvězda): OOS −0,04 až −0,44 R ([[F10 Entry modely mentorů FM]]).
- **Můčka podle doplňujících pravidel uživatele** (struktura tělem s momentem, strong/weak po 0,382, zóny s BOS a 25 %, balanční level, killzones, bias, 4H, sweep → MSS → 0,618): nejlepší varianta vývoj −0,18 R, OOS +0,06 R; entry model bez nákladů na nule; NAS100 +0,7 R se na S&P/Dow/DAX neopakuje ([[F12 Můčka podle doplňujících pravidel]]).
- **Pátek podle PDF + B3** (H4 zóny z pivotů, odmítnutí, LH/HL, průraz M5/M15): 2R model −0,07 R, nejlepší varianta v OOS pod náhodou ([[F14 Pátek podle PDF a doplňujících pravidel]]).
