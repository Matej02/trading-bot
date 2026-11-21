---
tags: [vyzkum, plan]
datum: 2026-11-21
---
# F69 RSI(2) na H4 US indexů

Zadání uživatele (2026-11-21): „Pokračuj, dokud nezjistíš zase nějakou výhodnou strategii.“ Plán je zapsaný **před výpočtem**, pravidla se po výsledku nemění.

**Proč:**
- Jediné, co od 2019 vydrželo, je návrat k průměru na **amerických** indexech ([[F42 RSI(2) přísná prověrka|F42]]).
- Mimo USA nefunguje ([[F66 až F68 Návrat k průměru (relativní, RSI(2) ve světě, noc po poklesu)|F67]], [[F49 RSI(2) na evropských indexech|F49]]).
- Na H4 by stejný mechanismus dal víc obchodů, což se hodí pro malý účet.

## Data
- **Vývoj:** HistData M1 S&P 500 a Nasdaq 100 (skutečné UTC) 2010-11 až 2018 → H4.
- **Kontrola:** HistData 2019–2025.
- **Broker:** H1 → H4 2019–2026 (čas serveru = UTC, viz [[Oprava času dat brokera (2026-11-21)]]). S&P, Nasdaq, Dow.
- H4 svíčky: bloky po 4 hodinách UTC (00, 04, 08, 12, 16, 20). Víkendy pryč.

## Pravidlo (F42 přenesené na H4)
- Zavření H4 nad SMA200 (H4) a RSI(2) < 10 → long na otevření další H4 svíčky.
- Ven na zavření H4 nad SMA5, stop 3 ATR20 (H4), nejdéle 10 svíček.
- R = výsledek / 3 ATR. Nový vstup až po ukončení předchozího obchodu.
- **Náklady:** spread brokera (medián) na vstupu i výstupu, swap brokera za každou změnu data UTC během držení (středa 3×).
- **Srovnání:** stejné vstupy a výstupy na všech H4 svíčkách nad SMA200 (drift). Převis, Welch t, po svíčkách vstupu (průměr přes trhy).

## ANO jen když platí vše
1. Vývoj (HistData 2010–2018): signál > 0, převis > 0, t ≥ 2,0.
2. Kontrola (HistData 2019–2025): signál > 0, převis > 0, t ≥ 1,5.
3. Broker 2019–2026 (SPX, NAS, US30): signál > 0 a převis > 0.
4. Převis kladný aspoň v 55 % let.
5. **Nezávislost na denním RSI(2):** bez signálů H4, které padnou do 5 obchodních dní po denním signálu RSI(2) na stejném trhu, převis > 0 (HistData celé období).

Skript `scratch/f69_rsi2_h4.py`, výstup `research_data/f69/souhrn.txt`.
