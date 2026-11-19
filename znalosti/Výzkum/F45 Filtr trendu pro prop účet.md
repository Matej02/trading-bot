---
tags: [vyzkum, f45, trend, prop, riziko]
datum: 2026-11-19
---
# F45 Filtr trendu pro prop účet

Zadání uživatele: „Pokračuj tedy“ (nové typy po [[Souhrn přínosů výzkumu (2026-11-19)|souhrnu]]).

**Proč:**
- U prop účtu rozhoduje poměr zisku a propadu (limit −10 %, [[Cesta k prop účtu]]), ne jen výnos.
- Klasický filtr trendu (Faber 2007: držet index jen nad 10měsíčním průměrem) má podle literatury podobný výnos jako držení, ale **mnohem menší propady**.
- Byl by to základní motor pro prop účet, k němuž se přidají F33 a RSI(2).
- Jen test, bot se nemění.

## Plán (zapsán PŘED výpočtem)
- **Pravidlo:**
  - na zavření posledního obchodního dne měsíce: zavření > SMA 10 měsíčních zavření → **long celý další měsíc**, jinak mimo trh;
  - držení zavření → zavření;
  - náklady: spread brokera při každém vstupu a výstupu a swap long za každou noc v pozici (středa 3×).
- **Srovnání:** stále long (stejné náklady, swap každou noc).
- **Trhy:** SPX, NAS, US30, DAX; portfolio = stejná váha 4 indexů (denní průměr výnosů).
- **Data:**
  - vývoj Yahoo 1990–2018;
  - kontrola Yahoo 2019–2026;
  - druhý zdroj broker H1 → denní 2019–2026.
- **Míry:**
  - CAGR;
  - největší propad (max DD);
  - **Calmar** = CAGR / max DD;
  - Sharpe.

**Pravidla rozhodnutí (portfolio), ANO jen když platí vše:**
1. Max DD filtru < max DD držení, ve vývoji i v kontrole.
2. Calmar filtru > Calmar držení, ve vývoji i v kontrole.
3. Sharpe filtru > Sharpe držení, ve vývoji i v kontrole.
4. Calmar filtru > držení aspoň u 3 ze 4 indexů zvlášť (1990–2026).
5. Broker 2019+: Calmar filtru > držení.

Skript `scratch/f45_trend.py`, výstup `research_data/f45/souhrn.txt`.
