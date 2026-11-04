---
tags: [vyzkum, f17, fm]
datum: 2026-11-04
---
# F17 – Šrajer (day trading a swing): PDF a obrázky, B6 jako dodatek

Prošel jsem celý text 9 + 24 PDF a všech **89 obrázků** ([[FM obrázky – Jan Šrajer (day)|day]] 18, [[FM obrázky – Jan Šrajer (swing)|swing]] 71).
Swing stojí na skóre Trading Analyzeru; historie 28 párů je v `research_data/fm_score`, ale náklady brokera má jen 15 z nich.
Plán: `F17_PLAN.md`, kód: `research_f17_sra.py` a `research_f17_eval.py`.

## Day trading (M1 data, 6 trhů)
- **Pravidla:**
  - 4H zóna ve směru 4H trendu v discountu nebo premiu, v ní 15m zóna (obr. 14–16);
  - před dotekem vybraná likvidita (equal lows nebo pivot low);
  - vstup limitem na proximal, nebo lokální změna trendu na 5m;
  - SL za distal, TP 2,7 R nebo protější 15m zóna;
  - jen okna 8:30–9:30, 10:30–11:30 a 13:30–16:00.
- **Výsledek:**
  - vybraná varianta (bez 4H trendu, pivot, limit, TP zóna): vývoj −0,01 R (n 61), OOS +0,07 R (n 74); náhoda −0,32 / −0,10 R;
  - s 4H trendem je obchodů málo a v OOS −0,52 R.
  - **Bez doložené výhody.**

## Swing (H1 data, 15 párů se skóre, OOS 2022 až 2024-10)
- **Pravidla:**
  - nejbližší unmitigated D1 supply a demand;
  - lokace Fibo 0,333 / 0,5 / 0,666, vstup v top discountu (obr. 4–8);
  - limit na D1 zónu nebo na 4H zónu uvnitř ní;
  - TP 2R nebo 0,5 (rovnováha);
  - filtr skóre: bias ±5 nebo změna ±2.
- **Výsledek:**
  - vybraná (D1, TP 0,5, bez skóre): vývoj **+0,11 R** (n 497), OOS **−0,27 R** (n 126); náhoda −0,08 / −0,14 R;
  - **skóre Trading Analyzeru jako filtr zhoršilo OOS** (bias −0,37 R, změna −0,38 R).
- **Bez výhody.** Potvrzuje [[Makro skóre měn]] (F8).
