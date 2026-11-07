---
tags: [vyzkum, f24, filtr, zive-strategie]
datum: 2026-11-07
---
# F24 Filtr volatility pro živé strategie

Z [[Fronta nápadů F22–F33|fronty nápadů]]. Jen test, bot ani simulátor se nemění. Skript `scratch/f24_vol.py`.

## Plán (zapsán PŘED výpočtem)
**Obchody:** stávající historie živých strategií, beze změny pravidel.
- [[RSI(2) pullback (mr_rsi2_d1)|RSI(2) pullback]]: `research_data/f6_obchody.csv`, MR1 long na SPX500, NAS100 a US30, Yahoo denní data od 1995.
  - Popisně i evropské indexy z F6 (DAX, FTSE, CAC, EuroStoxx, IBEX), které živě neběží.
- [[Průraz F2 (proraz_d1)|Průraz F2]]: `research_data/f4_obchody.csv`, varianta „A základ (F2)“ na 9 živých trzích, od 2009.

**Míra volatility v den signálu:** 20denní směrodatná odchylka denních log výnosů. Její percentil proti posledním 252 dnům, jen z dat do předchozího dne (bez pohledu dopředu). Denní ceny z F6 (Yahoo).

**Hypotézy (jedna na strategii, bez dalšího hledání):**
- **RSI(2):** obchody při percentilu **≥ 50** (nervózní trh) jsou lepší než při < 50.
- **Průraz:** obchody při percentilu **< 50** (klidný trh) jsou lepší než při ≥ 50.

**Období:** vývoj do 2018-12-31, kontrola 2019-01-01 až 2026-10.

**Pravidla rozhodnutí, filtr projde jen když platí vše:**
1. **Vývoj:** průměr ponechaných − průměr vyřazených > 0, Welchův t ≥ 2,0.
2. **Kontrola:** rozdíl > 0.
3. **Kontrola:** vyřazené obchody mají průměr ≤ 0. Filtr nesmí vyhodit skutečný zisk.

## Výsledky (2026-11-07)
Souhrn je v `research_data/f24/f24_souhrn.txt`.

**RSI(2) pullback, US indexy (filtr: ponechat percentil ≥ 50):**

| Období | Vše | Ponechané (nervózní trh) | Vyřazené (klidný trh) | Rozdíl, t |
|---|---|---|---|---|
| Vývoj do 2018 | n 599, +0,093 R | n 242, +0,059 R | n 357, **+0,116 R** | −0,057, t −1,36 |
| Kontrola 2019+ | n 218, +0,118 R | n 80, +0,132 R | n 138, **+0,109 R** | +0,023, t 0,32 |

- Po čtvrtinách percentilu: 0–25 % +0,147 R, 25–50 % +0,073, 50–75 % +0,091, 75–100 % +0,064.
- **RSI(2) vydělává v klidném i nervózním trhu**, v klidném ve vývoji dokonce víc. Filtr by vyhodil zisk.
- **Dobrá zpráva:** samotná RSI(2) je kladná v obou obdobích: +0,09 R od 1995, +0,12 R od 2019.
- Evropské indexy (popisně): vývoj +0,056 R, kontrola −0,008 R. Filtr nepomáhá ani tam.

**Průraz F2, 9 živých trhů (filtr: ponechat percentil < 50):**

| Období | Vše | Ponechané (klidný trh) | Vyřazené (nervózní trh) | Rozdíl, t |
|---|---|---|---|---|
| Vývoj do 2018 | n 298, −0,039 R | n 175, +0,028 R | n 123, −0,134 R | +0,162, t 1,01 |
| Kontrola 2019+ | n 556, +0,090 R | n 304, +0,022 R | n 252, **+0,172 R** | −0,150, t −1,25 |

- Vztah k volatilitě se mezi obdobími otočil. Po čtvrtinách: nejvyšší volatilita (75–100 %) je nejlepší (+0,215 R), 50–75 % nejhorší (−0,092 R). To je šum, ne pravidlo.

## Rozhodnutí podle pravidel zapsaných předem
- **RSI(2):** NE (vývoj rozdíl −0,057, t −1,36; vyřazené v kontrole +0,109 R).
- **Průraz F2:** NE (vývoj t 1,01; kontrola rozdíl −0,150; vyřazené +0,172 R).
- **⇒ Filtr volatility neprošel u žádné strategie. Živé strategie nechat beze změny.**

**Co si vezmeme:**
- RSI(2) je kladná napříč režimy volatility a v obou obdobích. Je stabilnější, než se zdálo.
- U Průrazu je výsledek kontroly (+0,09 R) tažen hlavně obdobím vysoké volatility. Nefiltrovat, ale počítat s tím, že v klidném trhu bude slabší.
