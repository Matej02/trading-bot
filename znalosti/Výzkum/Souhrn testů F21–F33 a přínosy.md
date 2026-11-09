---
tags: [vyzkum, souhrn, prinosy]
datum: 2026-11-08
---
# Souhrn testů F21–F33 a přínosy pro bota

Zadání uživatele (2026-11-08): „dojeď všechny strategie a pak mi vypiš všechny, které jsi projel, které jsou navíc oproti našemu botovi, a rozepiš výhody, které si můžeme vzít“.
- Do bota se zatím nic nedávalo.
- **Bot dnes obsahuje:**
  - v simulátoru [[Průraz F2 (proraz_d1)|Průraz F2]], [[RSI(2) pullback (mr_rsi2_d1)|RSI(2)]], Momentum a FM systémy;
  - na MT5 demu F12–F16 a F20 ([[FM live test na MT5 demu]]).

## Co jsme navíc otestovali
Vše s pravidly rozhodnutí zapsanými předem. Ověřeno na starších letech (HistData/Yahoo), na datech brokera, druhém zdroji cen, jiných trzích a proti náhodě.

| # | Strategie | Verdikt | Hlavní čísla |
|---|---|---|---|
| [[F13 indexy na delší historii (HistData 2010–2025)|F13+]] | Ověření F13 (běží na demu) na 2010–2019 | bez výhody | nové roky −0,11 R, celek t 0,42 |
| [[F21 Noční drift indexů (long přes noc)|F21]] | Noční drift US indexů | bez výhody | +0,012–0,016 R/noc, náhodné okno lepší |
| [[F22 Průraz úvodního rozpětí (ORB)|F22]] | Průraz ranního rozpětí | bez výhody | vývoj −0,027 R, kontrola +0,034 R |
| [[F23 Návrat po otevíracím gapu|F23]] | Vyplnění gapu | bez výhody | −0,016 / +0,013 R |
| [[F24 Filtr volatility pro živé strategie|F24]] | Filtr volatility pro RSI(2) a Průraz | neprošel | RSI(2) kladná v klidném i nervózním trhu |
| [[F25 Párové obchody (relativní hodnota)|F25]] | Párové obchody | bez výhody | +0,018 / +0,006 R |
| [[F26 Průraz po úzkém dni (NR7)|F26]] | NR7 | bez výhody | výhoda jen 1980–1999 |
| [[F27 Pokračování po zprávách (NFP, CPI)|F27]] | Pokračování po NFP/CPI | bez výhody | −0,029 / −0,140 R |
| [[F28 Intradenní momentum (první a poslední půlhodina)|F28]] | Ranní → poslední půlhodina | bez výhody | i bez nákladů ~0 |
| [[F29 Krypto momentum|F29]] | Krypto momentum 4 týdny | **těsně ne** | vývoj t 4,07, kontrola t 1,33; lepší Sharpe než stále long |
| [[F30 Měsíční sezónnost (průběžně)|F30]] | Měsíční sezónnost | bez výhody | +0,058 / −0,102 R |
| [[F31 Drift před FOMC|F31]] | Drift před FOMC | **kandidát** | 2019–26 +0,157 R/událost (t 2,08); 2013–18 ~0 |
| [[F32 Rotace podle relativní síly|F32]] | Rotace 3 z 15 trhů | bez výhody | v kontrole horší než držet vše |
| [[F33 Rebalancování na konci měsíce|F33]] | Rebalancování na konci měsíce | **PROŠLO** | vývoj +0,305 R (t 3,2), kontrola +0,230 R (t 1,57), US30 +0,345, DAX +0,220 |

## Přínosy, které si můžeme vzít

### A. Kandidáti na přidání (až po sledování dopředu, rozhoduje uživatel)
1. **F33 Rebalancování na konci měsíce: nejsilnější výsledek.**
   - Asi 8 obchodů ročně na US indexech (i DAX). Funguje long i short.
   - Slabina: od 2019 je slabší a citlivější na nastavení.
   - Výstup ve 22:00 Praha vyžaduje server, nebo nový test s výstupem v 19:45.
2. **F31 Drift před FOMC:** jen 8× ročně, kladné 2019–2026 na 4 indexech. Ve vývoji 2013–18 nic, proto jen sledovat.
3. **F29 Krypto momentum jako filtr pro krypto v simulátoru:** být mimo BTC/ETH, když je 28denní výnos záporný.
   - Od 2022 +113 % místo −59 %.
   - Hlavně se vyhne propadu 2022 a drahému swapu ETH (−0,7 % týdně).

### B. Potvrzení pro to, co bot už dělá
4. **RSI(2) pullback je stabilnější, než se zdálo:** +0,09 R do 2018 a +0,12 R od 2019, v klidném i nervózním trhu. Nechat beze změny, filtr nepotřebuje.
5. **Vynechávat dny NFP/CPI je správně:** první reakce na zprávu se vrací (F27, 55–60 % stopů).
   - Proto bylo důležité doplnit kalendář zpráv do 2027 (oprava z 2026-11-05).

### C. Řízení rizika
6. **Korelované trhy brát jako jedno riziko:** NAS a SPX (korelace v den události 0,9), XAU a XAG (F25, F31). Dvě pozice stejným směrem na nich jsou skoro dvojité riziko.
   - Návrh pro agenta Risk: limit na součet rizika ve skupině.
7. **Shorty na indexech byly ve všech intradenních testech (F21–F23) ztrátové, longy kladné.** To je obecný růst indexů.
   - Návrh: ověřit stejné rozdělení na vlastních FM systémech F12–F16 (test, ne hned pravidlo).

### D. Metodika a infrastruktura
8. **Ověřovací postup je hotový a znovu použitelný** (`scratch/f2x_lib.py`, HistData 2010+, kalendář zpráv 2010–2021):
   - pravidla předem;
   - starší roky;
   - druhý zdroj;
   - jiné trhy;
   - náhoda;
   - korelované trhy po událostech.
9. **Výhody „jen z posledních let“ jsou podezřelé:** ORB fungoval až od 2018, NR7 jen 1980–99, sezónnost se po 2019 otočila. Vždy ověřit i starší roky.
10. **Pravidla na úrovni M1 (sweep o tick) závisí na zdroji dat** (F13: jen 50 % shodných obchodů). Pravidla podle seance nebo dne mají shodu 95–100 %.
11. **Nálezy v botovi při testech:**
    - Letní posun času o 1 h (čas serveru je UTC, kód ho čte jako Londýn), opravit před 28. 3. 2027, viz [[MT5 napojení]].
    - Kalendář zpráv končil v 10/2026 (opraveno).
    - MT5 nesnese junction (disk C vyčištěn jinak).

## Co se přidalo do bota (2026-11-09)
Na pokyn uživatele („teď přidej ty strategie, které nám mohou pomoct, do bota“) do **simulátoru na Vercelu**. Běží 24/7, takže zvládne i vstupy a výstupy večer.
- **F33** `f33_rebal_d1`: validated, obchoduje i mimo učící režim.
- **F31** `f31_fomc_h1` a **F29** `f29_krypto_mom_d1`: kandidáti. Statistik je bez učícího režimu nepustí na skutečné obchody, ale sbírají stínová data.
- **Beze změny:** RSI(2) a filtr zpráv (potvrzené testy).
- **Do MT5 runneru se nepřidávalo:** F33 vystupuje ve 22:00, F31 vstupuje ve 20:00 a PC je vypnutý od 20:00.
- **Návrhy, které zatím nejsou kód:** limit rizika pro korelované skupiny (NAS/SPX, XAU/XAG), ověřit shorty indexů v F12–F16, oprava letního času před 28. 3. 2027.

## Doplněno 2026-11-09 odpoledne
- **Limit rizika pro korelované trhy** (bod 6) otestován jako [[F34 Limit rizika pro korelované trhy|F34]]: **nezavádět.** RSI(2) by přišla o 50–75 % zisku. Strop 1,5 R by u portfolia od 2019 snížil propad na polovinu, ale do 2018 zhoršil výsledek.
- **F33, F31 a F29 přidány i na MT5 demo**, viz [[FM live test na MT5 demu]]. F33 s výstupem 21:55, v poslední den signálního měsíce nechat PC do 22:00.
