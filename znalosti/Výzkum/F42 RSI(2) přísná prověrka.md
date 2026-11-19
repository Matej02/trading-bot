---
tags: [vyzkum, f42, rsi2, prověrka]
datum: 2026-11-19
---
# F42 RSI(2) přísná prověrka

Zadání uživatele (2026-11-19): „Nechám bota běžet ještě čas, ale zajímá mě, jestli můžeme dál testovat, jelikož hledáme něco, co nám bude fungovat.“

**Proč:**
- [[RSI(2) pullback (mr_rsi2_d1)|RSI(2)]] běží v simulátoru, ale nikdy neprošla plnou prověrkou s pravidly předem.
- [[F1 Nové třídy signálů|F1]]: PF 1,42, ale nad driftem t −0,02. [[F24 Filtr volatility pro živé strategie|F24]]: +0,09 / +0,12 R.
- Rozhodující otázka: **vydělává signál víc než prostý long ve stejném trhu se stejnými výstupy?**
- Jen test, bot se nemění. Další plánované testy: F43 Průraz F2, F44 struktura VIX, F45 filtr trendu pro prop.

## Plán (zapsán PŘED výpočtem)
- **Pravidlo jako v simulátoru:**
  - signál na zavření dne, kdy zavření > SMA200 a RSI(2) < 10;
  - **vstup na otevření dalšího dne**;
  - výstup na zavření dne, kdy zavření > SMA5;
  - stop 3 ATR(20) od vstupu (přes low dne, při gapu za otevírací cenu);
  - nejdéle 10 dní (zavření 10. dne). Bez TP. Nový vstup až po výstupu.
- **Srovnání (drift):** stejné vstupy a výstupy ve **všech** dnech, kdy zavření > SMA200, bez podmínky RSI. Rozhoduje převis signál − srovnání.
- **Náklady:** půl spreadu brokera na vstupu i výstupu a swap long za noc. R = výsledek / 3 ATR (riziko stopu).
- **Korelace:** hodnotí se **po dnech vstupu** (průměr trhů, které ten den vstupují).
- **Data:**
  - vývoj Yahoo 1990–2018 (SPX, NAS, US30);
  - kontrola Yahoo 2019–2026;
  - druhý zdroj broker H1 → denní 2019–2026;
  - jiné trhy DAX, FTSE, CAC (Yahoo, celé období).

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj: signál > 0 a převis > 0 s t ≥ 2,0.
2. Kontrola: signál > 0 a převis > 0 s t ≥ 1,5.
3. DAX, FTSE i CAC: převis > 0.
4. Broker 2019+: signál > 0 a převis > 0.
5. Převis kladný aspoň v 55 % let.

Skript `scratch/f42_rsi2.py`, výstup `research_data/f42/souhrn.txt`.
