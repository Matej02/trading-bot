---
tags: [vyzkum, f49, rsi2, evropa]
datum: 2026-11-19
---
# F49 RSI(2) na evropských indexech

Zadání uživatele (2026-11-19): „Dobře, pokračuj dalšími testy.“

**Proč:**
- [[F42 RSI(2) přísná prověrka|RSI(2)]] prošla na US indexech. Na MT5 demu ale kvůli minimálnímu lotu obchoduje jen SPX.
- V F42 byly DAX, FTSE a CAC kladné jen jako „jiné trhy“ (převis +0,035 / +0,060 / +0,021), bez vlastní kontroly.
- Teď plná prověrka na evropských indexech. Kdyby prošla, víc obchodů ze stejné ověřené výhody.
- Jen test, bot se nemění. Do MT5 jen podle pravidla uživatele (velká šance + souhlas).

## Plán (zapsán PŘED výpočtem)
- **Pravidlo RSI(2) beze změny proti F42:**
  - signál zavření > SMA200 a RSI(2) < 10;
  - vstup na otevření dalšího dne;
  - výstup zavření > SMA5, stop 3 ATR20, nejdéle 10 dní;
  - nový vstup až po výstupu.
- **Srovnání (drift):** stejné vstupy a výstupy ve všech dnech nad SMA200.
- **Trhy:** DAX, FTSE, CAC, EuroStoxx 50, IBEX 35.
- **Hodnotí se po dnech vstupu** (průměr trhů, které ten den vstupují). Náklady brokera, R = výsledek / 3 ATR.
- **Data:**
  - vývoj Yahoo 1990–2018 (EuroStoxx od 2007);
  - kontrola Yahoo 2019–2026;
  - druhý zdroj broker H1 → denní 2019–2026.

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj: signál > 0 a převis > 0 s t ≥ 2,0.
2. Kontrola: signál > 0 a převis > 0 s t ≥ 1,5.
3. Aspoň 4 z 5 trhů zvlášť (celé období): převis > 0.
4. Broker 2019+: signál > 0 a převis > 0.
5. Převis kladný aspoň v 55 % let.

Skript `scratch/f49_rsi2_evropa.py`, výstup `research_data/f49/souhrn.txt`.
