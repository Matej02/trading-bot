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

## Výsledek
(doplní se po výpočtu)
