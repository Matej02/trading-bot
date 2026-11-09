---
tags: [vyzkum, f31, zpravy, fomc]
datum: 2026-11-08
---
# F31 Drift před FOMC

Z [[Fronta nápadů F22–F33|fronty nápadů]]. Jen test, bot se nemění. Skript `scratch/f27_f31.py`.

**Kalendář:**
- 2010–2021: řádná zasedání FOMC podle `research_data/kalendar_2010_2021.json` (federalreserve.gov).
- Od 2021-09: kalendář z `f7_lib`.

## Plán (zapsán PŘED výpočtem)
**Pravidlo** (Lucca a Moench 2015):
- **Long** od otevření svíčky 14:00 NY v den před oznámením do otevření svíčky 13:55 NY v den oznámení, tedy těsně před zveřejněním.
- **Náklady:** spread a tick, swap long za 1 noc (ze středy na čtvrtek 3×).
- **R** = výsledek / ATR20 denního rozpětí, bez stopu.

**Data:**
- **Vývoj:** HistData SPX+NAS 2010-11 až 2019-02.
- **Kontrola:** broker SPX+NAS 2019–2026.
- **Druhý zdroj:** HistData 2019–2025.
- **Jiné trhy:** broker US30 a DAX 2019–2026 (stejné časy NY).

**Srovnání:** stejné okno (14:00 → 13:55 dalšího dne) long v náhodné všední dny bez FOMC. Ukáže běžný růst trhu za 24 h.

**Pravidla rozhodnutí:** 5 bodů jako u [[F22 Průraz úvodního rozpětí (ORB)|F22]] (bod 4 = lepší než stejné okno v jiné dny), ANO jen když platí vše.

## Výsledky (2026-11-08)
Souhrn: `research_data/f27/f31_souhrn.txt`.

| Část | n obchodů | R | t | výhra | stejné okno v jiné dny |
|---|---|---|---|---|---|
| Vývoj HistData 2010–19 | 132 | +0,097 | 2,03 | 48 % | +0,036 |
| Kontrola broker 2019–26 | 104 | **+0,164** | **2,98** | 61 % | +0,037 |
| Druhý zdroj HistData 2019–25 | 104 | +0,219 | 4,05 | 64 % | +0,035 |
| US30 2019–26 | 51 | +0,095 | 1,44 | 71 % | +0,019 |
| DAX 2019–26 | 50 | +0,228 | 2,96 | 68 % | +0,012 |

**Rozhodnutí podle pravidel zapsaných předem:** všech 5 bodů ANO → formálně **VÝHODA.** Je to první test, který prošel.

**Prověrka po výsledku (oprava metodiky, ne posouvání hranic):**
- **Chyba v pravidlech:** SPX a NAS se v den FOMC hýbou spolu (korelace 0,78–0,91), takže 2 obchody na událost nejsou nezávislé. Počítáno po událostech (průměr SPX+NAS):
  - vývoj: n 66, +0,097 R, **t 1,52** (bod 1 by neprošel);
  - kontrola: n 53, +0,157 R, **t 2,08**, výhra 64 %;
  - druhý zdroj: n 54, +0,215 R, t 2,94.
- **Vývoj stojí na roce 2012.** V letech 2011–2012 Fed při tiskové konferenci zveřejňoval ve 12:30 (ne ve 14:00), takže výstup ve 13:55 zachytil i reakci na zprávu (např. QE3 13. 9. 2012).
  - **Vývoj jen 2013–2018 (vše ve 14:00): n 49, +0,020 R, t 0,33.** Žádný drift.
- **Kontrola bez 5 nejlepších událostí:** +0,049 R (t 0,77). Bez 5 nejhorších: +0,259 R.
- Literatura: drift před FOMC byl silný 1994–2011 a po zveřejnění (2015) zeslábl. V letech 2019–2026 se v našich datech objevuje znovu, na všech čtyřech indexech a obou zdrojích.

**⇒ KANDIDÁT, ne ověřená výhoda.**
- Kladné 2019–2026 všude, ale ve vývoji 2013–2018 nic a výsledek stojí na několika událostech.
- Jen 8 obchodů ročně, vstup ve 20:00 Praha (den před FOMC), takže potřebuje zapnutý PC nebo server.
- Před jakýmkoli použitím: sledovat dalších 8–16 FOMC dopředu (bez úprav pravidel) a hodnotit po událostech.

## Live v simulátoru (od 2026-11-09, build db85757)
- Systém `f31_fomc_h1` v `simulator/lib/f2x.ts`, kontrola shody `scripts/compare-f2x.ts` (vstupy 13:00 NY v den před FOMC, výstupy 12:00 NY v den FOMC).
- **Odchylky od testu:** výstup ve 13:00 NY (v testu 13:55, kvůli zpoždění dat Yahoo ~10 min), SL 3 denní ATR jako pojistka. Trhy SPX500fut a NAS100fut (futures 23 h). Termíny FOMC do 2027-12-08 v `usCalendar.ts`.
- V registru Statistika: **unvalidated (kandidát)**.

## Live na MT5 demu (od 2026-11-09)
- `F31_fomc`, magic 20261131, vstup 20:00 Praha jen když běží PC, výstup 13:55 NY. Viz [[FM live test na MT5 demu]].
