---
tags: [koncept, smc]
aktualizovano: 2026-10-29
---
# SFP – sweep likvidity (swing failure pattern)

Knot za úrovní [[Likvidita|likvidity]] (≥ 0,05 ATR), zavření zpět, hloubka ≤ 0,5 ATR; potvrzení objemem RVOL ≥ 1,5.
Myšlenka: velký hráč vybere stop-lossy a cena se otočí.

Výsledky: fakeout PDH/PDL v [[F5 SMC a volume profile na 1h|F5]] ~0 R; v [[F7 Dokument 6 strategií SMC|F7]] na všech druzích poolů
po nákladech −0,12 až −0,36 R, **bez nákladů −0,03 R (11 895 sweepů)**. Na kryptu sweep častěji pokračuje (breakout).
Navazuje na [[MSS a displacement]], používá [[Killzones a session]].

## Definice z dokumentu
- Bearish SFP: high[i] překročí úroveň likvidity aspoň o 0,05 × ATR, ale close[i] je zpět pod úrovní (býčí zrcadlově).
- Varianta: návrat closem do 2 svíček.
- Průraz hlubší než 0,5 × ATR už není SFP, ale breakout – zahodit.
- Potvrzení objemem: RVOL svíčky ≥ 1,5 (spuštěné stop-lossy).

Zdroj: [[Dokument 6 strategií SMC + Volume Profile|dokumentu 6 strategií]].

## Z materiálů FM (část 1)
- **Šrajer:** sweep pivot equal highs nebo pivot liquidity **do M15 zóny uvnitř 4H zóny**. Nebo sweep → lokální MSS → retest local demand (RR ~3).
- **Kimmel:** dotyk PDH/PDL nebo oblasti předchozího dne na M15, reverzní signál na M5/M1 v 15:30–18:00, **SL 25 % za extrém**.
- **Můčka:** sweep Asia H/L v Londýně jen při Asii ≤ 35 pipů.
- **Objem:** sweep má mít velký objem (stažená svíčka), jinak je to slabý low-volume grab ([[Likvidita]]).

F9 (2026-10-29): jako spouštěč i filtr v 2 208 kombinacích ([[F9 Kombinace FM konceptů]]) – bez výhody.

## Doplněno uživatelem (2026-11-03)
Viz [[Doplňující pravidla k FM PDF]], A6 (SFP v 15m svíčce, FRVP do svíčky, 2–3 ze VAH/VAL/POC v knotu).

## F20 (2026-11-04)
SFP v 15m svíčce + FRVP (2–3 ze VAH/VAL/POC v knotu) bez dalších filtrů: bez nákladů −0,04 R (n 2 100) → samo bez výhody. S 4H/15m biasem, S/D zónou a TP na nahém denním POC OOS +0,78 R (n 27), vývoj +0,28 R, ale na 7 nových trzích −0,43 R (n 48) → bez výhody, viz [[F20 Obecná strategie uživatele (SFP + FRVP)|F20]].
