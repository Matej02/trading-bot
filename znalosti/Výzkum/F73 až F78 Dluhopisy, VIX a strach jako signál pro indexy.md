---
tags: [vyzkum, plan, vix, dluhopisy, indexy]
datum: 2026-11-24
---
# F73 až F78: dluhopisy, VIX a strach jako signál pro indexy

Zadání uživatele (2026-11-24): „Ano, pokračuj s dluhopisy a VIX a pokračuj i dál, a dej mi, až najdeš třeba 5 věcí, které by mohly fungovat.“ Plán je zapsaný **před výpočtem**, pravidla se po výsledku nemění.

**Proč:**
- Od 2019 vydržel jen návrat k průměru na US indexech ([[F42 RSI(2) přísná prověrka|F42]]). Ekonomický důvod: kdo dodá likviditu ve strachu, dostane zaplaceno.
- Tady se strach měří **z jiných trhů** (dluhopisy, VIX, jen) nebo naopak síla (52týdenní maximum). [[F44 Struktura VIX|F44]] (VIX/VIX3M ≥ 1) neprošla; tyto signály jsou jiné.
- Data jen ta, která už máme (bez stahování): Yahoo denní indexy (`f6_*_1d.pkl`), VIX od 1990 (`f44/VIX.json`), TLT od 2003 (`f33/yahoo/TLT.json`), USDJPY denní (`f6_USDJPY_1d.pkl`), broker H1 indexů 2019–2026.

## Společný postup (jako F42 a F44)
- Signál na **zavření dne i** (vše známé při zavření), **vstup long na otevření dne i+1**, **výstup na zavření h-tého dne** (včetně dne vstupu). Pojistný stop 3 ATR20 (low, při gapu za otevírací cenu).
- Náklady: půl spreadu brokera na vstupu i výstupu, swap long za každou noc (středa 3×). R = výsledek / 3 ATR20.
- Nový vstup až po výstupu předchozího.
- **Srovnání (drift):** stejný obchod (vstup, h dní, stop) ze všech dní. **Převis** = průměr signálu − průměr srovnání, Welchův t. Hodnotí se po dnech vstupu (průměr přes trhy).
- **Hlavní trhy:** S&P 500, Nasdaq 100, Dow. **Jiné trhy:** DAX, FTSE, CAC (signál z amerického dne i, vstup na jejich otevření i+1).
- **ANO jen když platí vše (stejně jako F42):**
  1. Vývoj (Yahoo, od začátku dat do 2018): signál > 0, převis > 0, t ≥ 2,0.
  2. Kontrola (Yahoo 2019–2026): signál > 0, převis > 0, t ≥ 1,5.
  3. DAX, FTSE, CAC (celé období): převis > 0 u všech tří.
  4. Broker 2019–2026 (hlavní trhy): signál > 0 a převis > 0.
  5. Převis kladný aspoň v 55 % let (hlavní trhy, celé období).
- Testuje se 6 nápadů najednou, proto se nic neladí a hranice t zůstávají přísné.

## Nápady
| Test | Signál na zavření dne i | Držení h | Vývoj od |
|---|---|---|---|
| **F73 Útěk do dluhopisů** | 5denní výnos TLT ≥ 90. percentil jeho 5denních výnosů za předchozích 252 dní **a** 5denní výnos indexu < 0 | 5 dní | 2004 |
| **F74 Natažený VIX** | VIX ≥ 1,10 × SMA10 VIX | 5 dní | 1990 |
| **F75 Strach odeznívá** | max VIX za posledních 5 dní ≥ 90. percentil VIX za předchozích 252 dní **a** VIX dnes ≤ 0,9 × to maximum | 10 dní | 1991 |
| **F76 Vysoký VIX** | VIX ≥ 30 | 20 dní | 1990 |
| **F77 52týdenní maximum** | zavření indexu = nejvyšší zavření za 252 dní | 20 dní | 1990 |
| **F78 Útěk do jenu** | změna USDJPY za den ≤ −1,5 × ATR20 USDJPY | 5 dní | od dat USDJPY |

## Výsledek (2026-11-24, `scratch/f73_f78.py`, výstup `research_data/f73/souhrn.txt`)
**Neprošel žádný.**

| Test | Vývoj: signál / převis / t | Kontrola: převis / t | Broker: převis | DAX, FTSE, CAC převis | Kladné roky | Body |
|---|---|---|---|---|---|---|
| F73 útěk do dluhopisů | n 157, +0,112 R, převis +0,073, t 1,57 | +0,074 / 0,90 (n 63) | +0,125 | +0,005 / +0,080 / +0,026 | 61 % | 3/5 |
| F74 natažený VIX | +0,116 R, převis +0,076, **t 2,36** | +0,022 / 0,36 | −0,007 | −0,018 / −0,056 / +0,030 | 70 % | 2/5 |
| F75 strach odeznívá | převis +0,049, t 0,88 | −0,041 | −0,074 | +0,024 / +0,153 / −0,041 | 58 % | 1/5 |
| F76 VIX ≥ 30 (20 dní) | +0,350 R, převis +0,216, **t 2,14** | +0,212 / 0,96 (n 24) | +0,341 | −0,096 / +0,078 / +0,139 | 86 % | 3/5 |
| F77 52týdenní maximum | převis −0,043 | −0,050 | +0,025 | +0,035 / −0,103 / −0,111 | 18 % | 1/5 |
| F78 útěk do jenu | převis −0,071 | −0,032 | −0,025 | všechny záporné | 41 % | 0/5 |

**Co z toho plyne:**
- **F74 natažený VIX** fungoval do ~2018 (t 2,36), od 2019 ne. Stejný vzorec jako kalendářní jevy.
- **F76 VIX ≥ 30** má velký převis všude v USA (vývoj, kontrola i broker kolem +0,2 až +0,3 R) a 86 % kladných let. Kontrola má ale jen 24 obchodů (t 0,96) a na DAXu je převis záporný. Podle pravidel **NE**.
  - Jen informace: odpovídá to RSI(2), kupovat strach na US indexech se vyplácí. Jako samostatná strategie je to vzácné (~3 obchody ročně) a pravidlo předem nesplnila.
- **F77**: nákup na 52týdenním maximu je horší než nákup kdykoli (převis kladný jen v 18 % let). Momentum na indexech nefunguje.
- Dluhopisy (F73) a jen (F78) nepřidávají nic navíc k samotnému poklesu indexu.
