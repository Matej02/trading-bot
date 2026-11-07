---
tags: [vyzkum, f22, indexy, intraday]
datum: 2026-11-07
---
# F22 Průraz úvodního rozpětí (ORB)

Z [[Fronta nápadů F22–F33|fronty nápadů]].
- Zadání uživatele (2026-11-07): „nešlo by to udělat, že to otestuješ? A ne že to zapneme do bota?“ Jen test, bot se nemění.
- Skripty: `scratch/f2x_lib.py`, `scratch/f22_f23.py`.

## Plán (zapsán PŘED výpočtem)
**Pravidlo:**
- **Úvodní rozpětí (OR):** maximum a minimum prvních 15 minut seance:
  - US indexy 9:30–9:45 NY;
  - DAX 9:00–9:15 Frankfurt.
  - Potřeba aspoň 10 minutových svíček.
- **Vstup:** první M5 svíčka (v okně 2 h po konci OR), která **zavře nad** maximem OR → long. Zavře pod minimem → short. Vstup na otevření další minuty, jeden obchod denně.
- **SL:** druhá strana OR. Den se vynechá, když je OR užší než 3× spread.
- **Výstup:**
  - US: **19:45 Praha** (tak by to šlo obchodovat s PC zapnutým do 20:00);
  - DAX: 17:25 Frankfurt;
  - jinak SL. Bez TP.
  - Popisně i výstup v 15:55 NY.
- **Náklady:** spread brokera podle hodiny, 1 tick na vstupu i výstupu. Stop se vyplní za horší z cen SL a otevření svíčky. R = zisk / riziko.

**Data:**
- **Vývoj:** HistData SPX+NAS 2010-11 až 2019-02.
- **Kontrola:** broker SPX+NAS 2019-02 až 2026-10 (čas posunutý na skutečné UTC).
- **Druhý zdroj:** HistData 2019-02 až 2025-12.
- **Jiné trhy:** broker US30 a DAX 2019–2026.

**Náhoda:** jiný den stejného období, stejný čas vstupu, směr a SL v násobcích ATR, stejný výstup. Tři opakování.

**Pravidla rozhodnutí (pevná), ANO jen když platí vše:**
1. Vývoj > 0 a t ≥ 2,0.
2. Kontrola > 0 a t ≥ 1,5.
3. US30 i DAX > 0.
4. Lepší než náhoda ve vývoji i v kontrole.
5. Druhý zdroj > 0.

## Výsledky (2026-11-07)
Souhrn je v `research_data/f22/orb_souhrn.txt`.

| Část | n | R/obchod | t | long | short | náhoda |
|---|---|---|---|---|---|---|
| Vývoj HistData 2010–19 | 3 996 | **−0,027** | −1,50 | +0,015 | −0,073 | −0,013 |
| Kontrola broker 2019–26 | 3 306 | **+0,034** | 1,67 | +0,077 (t 2,9) | −0,014 | −0,024 |
| Druhý zdroj HistData 2019–25 | 3 241 | +0,029 | 1,41 | +0,054 | +0,002 | – |
| US30 | 1 582 | −0,003 | −0,13 | +0,031 | −0,037 | – |
| DAX | 1 656 | +0,042 | 1,09 | +0,111 | −0,025 | – |

- **Shoda zdrojů:** stejný směr v 95 % dní, korelace R 0,88. Pravidlo na úrovni seance je na zdroji dat skoro nezávislé, na rozdíl od F13.
- Výstup na zavření NY (15:55) místo 19:45 Praha: vývoj −0,024 R, kontrola +0,061 R. Stejný obraz.
- **Po letech se to zlomilo:** 2010–2017 skoro každý rok ztráta (nejhůř 2015 −53 R), 2018–2025 zisk (2021 +43 R, 2025 +35 R), 2026 zatím −20 R. Na nových letech by se výsledek z let 2019+ neudržel.

## Rozhodnutí podle pravidel zapsaných předem
1. Vývoj > 0 a t ≥ 2: **NE** (−0,027 R).
2. Kontrola > 0 a t ≥ 1,5: ANO (t 1,67).
3. US30 i DAX > 0: **NE** (US30 −0,003).
4. Lepší než náhoda: **NE** (ve vývoji horší).
5. Druhý zdroj > 0: ANO.

**⇒ BEZ VÝHODY.**

**Co si vezmeme:**
- Na indexech táhnou výsledek **longy**, shorty jsou ve ztrátě. Stejně tak v [[F23 Návrat po otevíracím gapu|F23]] a [[F21 Noční drift indexů (long přes noc)|F21]]. Je to obecný růst indexů, ne výhoda vstupu.
- Long-only ORB tím ale není kandidát: ve vývoji je jen +0,015 R (t 0,6). Byl by to výběr dodatečně podle výsledku.
- Ranní průraz fungoval v letech 2018–2025, předtím ne. Strategie postavené na posledních letech potřebují ověření na letech před 2019.
