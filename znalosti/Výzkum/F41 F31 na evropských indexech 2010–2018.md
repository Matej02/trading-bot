---
tags: [vyzkum, f41, f31, fomc]
datum: 2026-11-19
---
# F41 F31 (drift před FOMC) na evropských indexech 2010–2018

Zadání uživatele (2026-11-19): „Dobře, pokračuj dalším krokem.“

**Proč:** [[F31 Drift před FOMC|F31]] je kandidát:
- silný 2019–2026 (i na DAX +0,228 R);
- ve vývoji 2010–2019 po událostech jen t 1,52.

Chybí nezávislé ověření na jiných trzích v letech 2010–2018. Data DAX a EuroStoxx z HistData jsou nově stažená (2026-11-19). Jen test, bot se nemění. Do bota by šlo jen podle pravidla uživatele (všechno prošlo + sledování dopředu + souhlas).

## Plán (zapsán PŘED výpočtem)
- **Pravidlo F31 beze změny:** long od 14:00 NY v den před oznámením FOMC do 13:55 NY v den oznámení.
- **Kalendář FOMC** jako v F31 (`kalendar_2010_2021.json`, od 2021-09 `f7_lib`).
- **Trhy a data:** HistData DAX (GRXEUR) a EuroStoxx (ETXEUR), 2010-11 až 2018. Čas NY s letním časem, ověřeno na páteční uzávěrce. Chybné ticky (skok > 20 % za minutu) se vyřadí předem.
- **Náklady:** spread brokera a swap long za 1 noc (ze středy na čtvrtek 3×). R = výsledek / ATR20.
- **Hodnotí se po událostech** (průměr DAX a EuroStoxx).
- **Srovnání:** stejné okno ve všech ostatních všedních dnech (převis nad driftem).

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. 2010–2018 po událostech > 0 a t ≥ 1,5.
2. Převis nad stejným oknem v ostatní dny > 0.
3. DAX i EuroStoxx zvlášť > 0.
4. HistData DAX 2019–2025 > 0 (shoda s brokerem z F31).

**Co výsledek znamená:**
- **ANO:** F31 je o krok blíž k „jisté“, ale pořád až po sledování dopředu.
- **NE:** F31 zůstává jen kandidát a efekt je spíš jev posledních let.

Skript `scratch/f41_fomc_evropa.py`, výstup `research_data/f41/souhrn.txt`.

## Výsledky (2026-11-19)
Souhrn `research_data/f41/souhrn.txt`. Chybné ticky vyřazeny: DAX 4 minuty, EuroStoxx 2.

| Část | n událostí | R | t | výhra |
|---|---|---|---|---|
| DAX+ES 2010–2018 | 63 | +0,046 | 0,63 | 60 % |
| stejné okno v ostatní dny | 1959 | +0,017 | 0,53 | 52 % |
| DAX 2010–2018 | 63 | +0,086 | 1,00 | 68 % |
| EuroStoxx 2010–2018 | 62 | +0,003 | 0,05 | 55 % |
| DAX 2019–2025 (HistData) | 52 | **+0,204** | **2,43** | 62 % |

- Převis nad driftem 2010–2018: +0,029 R (t 0,36). Za 2013–2018 +0,018 R.
- **Bod 1 NE ⇒ NEPROŠLO. F31 zůstává jen kandidát.**
- **Co to znamená:**
  - Drift před FOMC je **jev posledních let (od 2019)**, na US i evropských indexech stejně.
  - Před 2019 skoro nebyl, ani na nezávislých trzích.
  - DAX 2019–2025 z druhého zdroje potvrzuje broker (+0,204 vs. +0,228 R), data jsou tedy v pořádku.
  - **Pozor: F31 už v botovi je** (demo i simulátor od 9. 11., přidáno před pravidlem uživatele „jen když 100% jistí“). Podle nového pravidla by tam jako kandidát být neměla.
  - Bez pokynu se ale nic nemění (ani přidání, ani odebrání). **Rozhodne uživatel:**
    - nechat jako sledování dopředu na demu (riziko 0,25 %, 8× ročně);
    - nebo vypnout.
