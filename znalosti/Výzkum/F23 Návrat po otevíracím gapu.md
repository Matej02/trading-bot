---
tags: [vyzkum, f23, indexy, intraday]
datum: 2026-11-07
---
# F23 Návrat po otevíracím gapu

Z [[Fronta nápadů F22–F33|fronty nápadů]]. Jen test, bot se nemění. Skripty: `scratch/f2x_lib.py`, `scratch/f22_f23.py`.

## Plán (zapsán PŘED výpočtem)
**Pravidlo:**
- **Gap:** otevření seance minus předchozí zavření.
  - US: otevření svíčky 9:30 NY minus zavření svíčky 15:59 NY předchozího dne.
  - DAX: 9:00 a 17:29 Frankfurt.
- **Vstup:** když |gap| ≥ **0,3 × ATR20** (denní), obchod **proti gapu** na otevření seance. Gap nahoru → short, dolů → long.
- **TP:** předchozí zavření (vyplnění gapu).
- **SL:** o velikost gapu dál od otevření.
- **Výstup:** US **19:45 Praha**, DAX 17:25 Frankfurt.
- **Náklady:** jako v [[F22 Průraz úvodního rozpětí (ORB)|F22]]. Když SL a TP padnou do stejné minuty, počítá se SL.

**Data, náhoda a pravidla rozhodnutí:** stejné jako v [[F22 Průraz úvodního rozpětí (ORB)|F22]] (5 bodů, ANO jen když platí vše).

## Výsledky (2026-11-07)
Souhrn je v `research_data/f22/gap_souhrn.txt`.

| Část | n | R/obchod | t | long (gap dolů) | short (gap nahoru) | náhoda |
|---|---|---|---|---|---|---|
| Vývoj HistData 2010–19 | 1 682 | **−0,016** | −0,83 | +0,039 | −0,056 | −0,008 |
| Kontrola broker 2019–26 | 1 487 | +0,013 | 0,63 | +0,045 | −0,012 | −0,011 |
| Druhý zdroj HistData 2019–25 | 1 349 | +0,007 | 0,32 | +0,031 | −0,011 | – |
| US30 | 711 | +0,016 | 0,53 | +0,037 | −0,003 | – |
| DAX | 731 | −0,042 | −1,35 | +0,002 | −0,076 | – |

- **Výstupy:** asi 30 % TP (+0,99 R), 28 % SL (−1 R), 42 % čas (−0,05 R). Gap se do 19:45 vyplní zhruba ve třetině případů.
- **Shoda zdrojů:** stejný směr ve 100 % dní, korelace R 0,99.
- Po letech kolem nuly. Nejhorší 2015–2016 a 2019, nejlepší 2014 a 2025.

## Rozhodnutí podle pravidel zapsaných předem
1. Vývoj > 0 a t ≥ 2: **NE** (−0,016).
2. Kontrola > 0 a t ≥ 1,5: **NE** (t 0,63).
3. US30 i DAX > 0: **NE** (DAX −0,042).
4. Lepší než náhoda: **NE** (ve vývoji horší).
5. Druhý zdroj > 0: ANO.

**⇒ BEZ VÝHODY.**

**Co si vezmeme:**
- Gap nahoru se na indexech **nevyplňuje víc, než by čekala náhoda**: shorty jsou ztrátové. Gap dolů se mírně kupuje (longy +0,03–0,05 R), ale to je zase obecný růst indexů jako v [[F22 Průraz úvodního rozpětí (ORB)|F22]].
