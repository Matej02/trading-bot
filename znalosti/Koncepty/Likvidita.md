---
tags: [koncept, smc]
aktualizovano: 2026-10-29
---
# Likvidita (pooly)

BSL nad / SSL pod: PWH/PWL (váha 3), PDH/PDL a EQH/EQL (2), high/low Asie a Londýna (1).
Pool je vybraný, jakmile cena obchoduje za úrovní. Slouží jako spouštěč ([[SFP – sweep likvidity]]) i cíl TP.
Asie a Londýn viz [[Killzones a session]]. Testováno v [[F5 SMC a volume profile na 1h]] a [[F7 Dokument 6 strategií SMC]].

## Definice z dokumentu
- BSL nad / SSL pod: PWH/PWL, PDH/PDL, high/low Asie a Londýna, EQH/EQL, poslední potvrzené swingy.
- EQH/EQL: aspoň 2 swingy v toleranci 0,1 × ATR a s rozestupem ≥ 5 svíček.
- Váha: PWH/PWL = 3, PDH/PDL a EQH/EQL = 2, session high/low = 1.
- Pool je vybraný, jakmile cena obchoduje za úrovní; vybraný přestává být cílem.

Zdroj: [[Dokument 6 strategií SMC + Volume Profile|dokumentu 6 strategií]].

## Z materiálů FM (část 1)
- **Proč existuje:** velcí hráči vstupují limitem a potřebují market protistranu.
  Tu najdou v SL (95 % SL se plní jako market), v buy/sell stopech na průrazech a u VWAP ([[FM Základy tradingu]]).
- **ERL vs IRL** (Veselovský, Kimmel): externí = swing H/L, PDH/PDL, lokální H/L, Asie; interní = FVG, BPR, iFVG.
  **Trh chodí z IRL do ERL a zpět.** Interní target je „méně bolesti hlavy“ (Kimmel).
- **Sweep s objemem:**
  - **High-volume grab** = silný knot a rychlý návrat; při otevření LO/NY a při zprávách je to signál obratu.
  - **Low-volume grab** (Asie, svátky, noc) = choppy návrat, slabý signál.
- **Bez výběru likvidity nevstupovat** (Veselovský, Můčka, Valchář: „vstupuji až po vybrání likvidity“).
- **Equal highs a pivotní likvidita** jako spouštěč do zóny: [[FM Strategie – Jan Šrajer (day + swing)|Šrajerovy entry modely 1–3]].
- Session H/L (Londýn, Asie) = zásobník stop lossů → [[Killzones a session]].

## Doplněno uživatelem (2026-11-03)
Viz [[Doplňující pravidla k FM PDF]], B2 (externí = swingy, interní = FVG; když se vybírá externí, Michal neobchoduje).
