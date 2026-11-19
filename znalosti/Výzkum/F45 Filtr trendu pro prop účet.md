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

## Výsledky (2026-11-19)
Souhrn `research_data/f45/souhrn.txt`. Portfolio SPX, NAS, US30, DAX.

| Část | Filtr: CAGR / max DD / Calmar / Sharpe | Držení: CAGR / max DD / Calmar / Sharpe |
|---|---|---|
| Vývoj 1990–2018 | +7,5 % / −24,6 % / 0,31 / 0,67 | +8,1 % / −65,3 % / 0,12 / 0,52 |
| Kontrola 2019–2026 | +8,8 % / −14,9 % / 0,59 / **0,79** | +14,0 % / −33,7 % / 0,42 / **0,82** |
| Broker 2019–2026 | +9,6 % / −16,9 % / 0,57 / 0,89 | +14,0 % / −33,8 % / 0,41 / 0,77 |

- **Po indexech:** Calmar lepší u SPX, NAS a DAX. U US30 stejný (0,12).
- **Body 1, 2, 4, 5 ANO. Bod 3 NE** (Sharpe v kontrole 0,79 proti 0,82). **⇒ BEZ VÝHODY** podle pravidel předem, do bota ne.
- **Popis (fakt, nic se nemění):**
  - Filtr spolehlivě **zhruba poloviční propady** (2008: −13 % místo −40 %, 2022: −11 % místo −21 %).
  - Daní za to je nižší výnos v rostoucích letech (2019: +7 % místo +27 %).
  - Jako zdroj výhody to není. Jako **řízení rizika** pro prop účet je to doložený poznatek: prosté držení indexu má od 2019 propad −34 %, a to by limit −10 % porušilo i při malé páce.
