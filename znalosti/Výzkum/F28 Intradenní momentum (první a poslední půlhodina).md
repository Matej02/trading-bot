---
tags: [vyzkum, f28, indexy, intraday]
datum: 2026-11-07
---
# F28 Intradenní momentum (první → poslední půlhodina)

Z [[Fronta nápadů F22–F33|fronty nápadů]]. Jen test, bot se nemění. Skript `scratch/f28_momentum.py`.

## Plán (zapsán PŘED výpočtem)
**Pravidlo** podle Gao, Han, Li a Zhou (2018):
- r1 = otevření svíčky 10:00 NY / zavření svíčky 15:59 NY předchozího dne − 1.
- r1 > 0 → long, r1 < 0 → short.
- **Vstup** na otevření svíčky 15:30 NY, **výstup** na zavření svíčky 15:59 NY. To je 21:30–22:00 Praha, takže živě jen se serverem.
- **DAX** obdobně:
  - r1 = otevření svíčky 9:30 / předchozí zavření 17:29 Frankfurt;
  - obchod 17:00–17:29 Frankfurt.
- **Náklady:** spread brokera podle hodiny a tick na vstupu i výstupu, bez swapu.
- **R** = výsledek / ATR20 denního rozpětí (bez stopu).

**Data, náhoda a pravidla rozhodnutí:** jako v [[F22 Průraz úvodního rozpětí (ORB)|F22]].
- Vývoj HistData SPX+NAS 2010–2019, kontrola broker 2019–2026, druhý zdroj HistData 2019–2025, jiné trhy US30 a DAX.
- Náhoda: stejný směr a stejné okno v náhodný den.
- Pět bodů, ANO jen když platí vše.

## Výsledky (2026-11-07)
- Souhrn: `research_data/f28/f28_souhrn.txt`.

| Část | n | R | t | bez nákladů |
|---|---|---|---|---|
| Vývoj | 4 027 | −0,003 | −1,14 | +0,003 |
| Kontrola | 3 308 | −0,009 | −2,92 | −0,005 |
| Druhý zdroj | 3 007 | −0,013 | −4,11 | −0,009 |
| US30 | 1 636 | −0,015 | −3,41 | – |
| DAX | 1 700 | +0,001 | 0,34 | – |

- Efekt z literatury (data 1993–2013) se v letech 2010–2026 neobjevuje ani bez nákladů. Od 2015 je spíš opačný.

**Rozhodnutí:** neprošel žádný bod → **BEZ VÝHODY.**
