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

## Výsledky (2026-11-19)
Souhrn `research_data/f42/souhrn.txt`. Hodnoceno po dnech vstupu (SPX, NAS, US30).

| Část | Dní vstupu | Signál R | výhra | Srovnání (drift) | Převis | t |
|---|---|---|---|---|---|---|
| Vývoj 1990–2018 | 496 | **+0,087** | 72 % | +0,026 | **+0,061** | **2,84** |
| Kontrola 2019–2026 | 141 | +0,091 | 72 % | +0,026 | +0,065 | 1,63 |
| Broker 2019–2026 | 119 | +0,066 | 71 % | +0,008 | +0,057 | 1,41 |
| DAX 1990–2026 | 266 | +0,051 | 69 % | | +0,035 | 1,05 |
| FTSE 1990–2026 | 267 | +0,056 | 70 % | | +0,060 | 2,05 |
| CAC 1990–2026 | 258 | +0,023 | 69 % | | +0,021 | 0,65 |

- Převis kladný ve 28 z 37 let (76 %). Nejhorší rok 2008 (−0,92), dál 2022 (−0,26) a 1990 (−0,23).

## Rozhodnutí podle pravidel zapsaných předem
**Všech 5 bodů ANO ⇒ VÝHODA.** Druhá strategie po [[F33 Rebalancování na konci měsíce|F33]], která prošla plnou prověrkou.

**Poznámky:**
- **Rozpor s [[F1 Nové třídy signálů|F1]]** („nad driftem t −0,02“): F1 srovnávala s prostým držením indexu. Tady se srovnává se stejnými výstupy v libovolný den nad SMA200, což je férovější test samotného signálu. Obě čísla platí, každé měří něco jiného.
- **Výhoda je malá:** +0,06 R nad driftem a +0,09 R celkem na obchod, asi 17 dní vstupu ročně na US indexech. Při riziku 1 % na obchod je to řádově +1,5 % ročně. Užitečná hlavně v kombinaci s F33.
- **Slabina:** prudké pády (2008, 2022). Stop 3 ATR je jediná ochrana.
- **Podle pravidla uživatele** (100% jistota = všechno předem + sledování dopředu + souhlas):
  - RSI(2) splnila první část;
  - v simulátoru běží od 9. 11. v učícím režimu, sledování dopředu tedy probíhá;
  - na MT5 demu ani live zatím není a bez souhlasu uživatele se nepřidává.
- **Další krok (návrh):** popisná kontrola odolnosti (práh RSI 5/10/15, max. dní 5/10/15). Pravidla se nemění, jen se ověří, že výsledek nestojí na jednom nastavení.
