---
tags: [vyzkum, f89, prop, ftmo, plan]
datum: 2026-11-25
---
# F89 Porovnání zkoušek FTMO: 1 krok a 2 kroky

Zadání uživatele (2026-11-25): „Ano, porovnej typy zkoušek FTMO.“ Bot ani runner se nemění.

## Pravidla FTMO (web ftmo.com, 25. 11. 2026, účet 100 000 $)
| | 2 kroky | 1 krok |
|---|---|---|
| Cíl | +10 %, pak +5 % | +10 % |
| Denní limit | 5 % počátečního kapitálu od zůstatku o půlnoci SEČ | **3 %** (stejný výpočet) |
| Celkový limit | 10 %, statický (90 000 $) | 10 %, **posuvný podle nejvyššího zůstatku na konci dne** |
| Min. obchodních dní | 4 v každé fázi | neuvedeno |
| Konzistence | – | nejlepší den ≤ 50 % celkového zisku (od 12. 10. 2026; porušení není propad, jen se musí obchodovat dál) |
| Časový limit | žádný | žádný |
| Podíl na zisku | až 90 % | 90 % |
| Cena 100k | 540 € (teď sleva 432 €), **vratná** s první odměnou | 499 € (teď sleva 399 €), **nevratná** |

Zdroje: [2 kroky](https://ftmo.com/en/2-step-challenge/), [1 krok](https://ftmo.com/en/1-step-challenge/), [pravidla](https://ftmo.com/en/trading-objectives/).

## Plán (zapsán PŘED výpočtem)
- **Obchody:** základ měřítka F33 se stopem + RSI(2) ([[F87 Měřítko s F33 se stopem jako v runneru|F87]]), pevné riziko 0,5–3,0 % po 0,25, starty každý měsíc 2003–2023, nejdéle 36 měsíců.
- **2 kroky:** simulace jako v měřítku.
- **1 krok:**
  - denní limit: nejhorší equity dne < zůstatek o půlnoci − 3 %;
  - celkový limit: nejhorší equity < nejvyšší zůstatek na konci dne (od startu) − 10 %;
  - projití: equity na zavření ≥ 110 % a zároveň nejlepší den (uzavřený zisk dne, včetně zavření všech pozic v den projití) ≤ 50 % celkového zisku. Když konzistence nesedí, obchoduje se dál.
- **Bezpečné riziko** každého typu = nejvyšší r s propady ≤ 10 % na celém období. Kontrolně r* vybrané na startech 2003–2014 a ověřené na 2015–2023.
- **Hlavní srovnání:** P24 (prošlo do 24 měsíců) při bezpečném riziku. **Vítěz = vyšší P24**. Když je rozdíl do 5 p. b., rozhodne nižší očekávaná cena za projitou zkoušku (cena / P36; u 2 kroků se poplatek vrací s první odměnou).
- **Popis (nerozhoduje):** financovaný účet 12 měsíců po projití (2 kroky: denní 5 %, celkem 10 % statický; 1 krok: denní 3 %, celkem 10 % posuvný), podíl účtů, které přežijí, a medián zisku bez výběrů.

Skript `scratch/f89_typy_zkousek.py`, výstup `research_data/prop/f89_souhrn.txt`.

## Výsledky (2026-11-25)
Výstup `research_data/prop/f89_souhrn.txt`. Dva kroky se shodují s F87 (P24 17 %, P36 65 %, propadlo 3 %).

| | 2 kroky | 1 krok |
|---|---|---|
| Bezpečné riziko (propadlo ≤ 10 %) | **1,25 %** | 0,75 % |
| Prošlo do 12 / 24 / 36 měsíců | 3 % / **17 %** / 65 % | 1 % / 10 % / 56 % |
| Propadlo | 3 % | 0 % |
| Medián do projití | 27,2 měs. | 28,9 měs. |
| Cena za projitou zkoušku (poplatek / P36) | ~833 €, **vratná** s první odměnou | ~897 €, nevratná |
| Kontrolně: r* z vývoje → kontrola | 1,5 % → propadlo 33 % | 1,0 % → propadlo 32 % |
| Financovaný účet 12 měsíců po projití | přežije 100 %, medián +3,6 % | přežije 100 %, medián +2,2 % |

- 1 krok při 1,0 % by dal P24 46 %, ale propadne 14 % (v kontrole 32 %, opět únor 2020). Denní limit 3 % je na souběžné pozice na indexech moc těsný.
- **Rozhodnutí podle pravidla předem: 2 kroky** (vyšší P24, 17 % proti 10 %). Navíc je poplatek vratný a na financovaném účtu jde riskovat víc.
- Shoda s [[Prop firmy – doporučení]] (FTMO Swing 2 kroky jako první volba).
- **Očekávání na financovaném účtu:** při 1,25 % asi +3,6 % ročně. Na 100 000 $ je to zhruba 3 600 $ ročně před podílem 80–90 %. Je to simulace z minulosti, ne slib.
