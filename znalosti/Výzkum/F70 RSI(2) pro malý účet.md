---
tags: [vyzkum, plan, maly-ucet]
datum: 2026-11-21
---
# F70 RSI(2) pro malý účet

Zadání uživatele (2026-11-21): „Vylepši RSI(2) pro malý účet.“ Plán je zapsaný **před výpočtem**. Bot a runner se nemění; případná změna až s výslovným souhlasem.

**Výchozí stav:**
- Live účet bude asi 10 000 Kč (~457 $) ([[Požadavky a nápady uživatele|11. 11.]]).
- U brokera je nejmenší pozice US indexů 1 lot = 1 $/bod.
- Stop RSI(2) 3 ATR je na SPX ~400 bodů, tedy ~400 $ (~90 % malého účtu).
- I na demu (100 000 $) se kvůli stropu 0,5 % na nejmenší lot obchoduje fakticky jen SPX. NAS a US30 riskují 2–3 %.

## Část A: popis (nerozhoduje)
Broker 2019–2026, pravidlo [[F42 RSI(2) přísná prověrka|F42]], 1 lot na trh. Spočítá se:
- počet obchodů;
- zisk v $ celkem a po letech;
- největší propad v $;
- nejhorší obchod v $;
- riziko u stopu v $ (medián a 90. percentil).

Z toho vyjde potřebný účet, aby:
1. riziko u stopu bylo ≤ 1 % (a ≤ 2 %);
2. největší historický propad byl ≤ 20 % účtu.

Totéž pro hypotetický mikro kontrakt 0,01 lotu, jaký mají jiní brokeři.

## Část B: varianty (pravidla předem)
Velikost pozice: riziko u stopu = 1 % účtu na obchod (bez skládání), výsledek obchodu v % = 1 % × R, kde R = výsledek / vzdálenost stopu.

| Varianta | Popis |
|---|---|
| V0 | F42 jak je: SPX, NAS, US30, každý vlastní pozice, stop 3 ATR |
| V1 | jen SPX, stop 3 ATR |
| V2 | jedna pozice napříč SPX, NAS, US30 (při souběhu přednost SPX > NAS > US30), stop 3 ATR |
| V3 | jen SPX, stop 2 ATR |
| V4 | jen SPX, stop 1,5 ATR |

**Měřítka:**
- výnos % ročně;
- největší propad %;
- **MAR = výnos ročně / největší propad.**

**Výběr pro malý účet:**
- vítěz = nejvyšší MAR ve **vývoji (Yahoo 1990–2018)**;
- potvrdí se, když v **kontrole (Yahoo 2019–2026)** i u **brokera 2019–2026** má kladný výnos a MAR aspoň 80 % nejlepší varianty v daném období;
- když nepotvrdí, zůstává V0.

**Popis navíc:** u každé varianty průměr R, úspěšnost a počet obchodů za rok.

Skript `scratch/f70_rsi2_maly_ucet.py`, výstup `research_data/f70/souhrn.txt`.

## Výsledek (2026-11-21)
Souhrn: `research_data/f70/souhrn.txt`.

### A: kolik RSI(2) stojí a vydělává na 1 lot (broker 2019–2026)
| Trh | Obchodů | Zisk celkem | Největší propad | Riziko u stopu medián / 90 % | Na 457 $ (1 lot) | Mikro 0,01 lotu |
|---|---|---|---|---|---|---|
| SPX | 56 | +919 $ | 388 $ | 174 / 267 $ | 38 % účtu | 0,4 % |
| NAS | 48 | +3 185 $ | 1 179 $ | 832 / 1 440 $ | 182 % | 1,8 % |
| US30 | 58 | +6 825 $ | 2 071 $ | 1 252 / 1 796 $ | 274 % | 2,7 % |

**Potřebný účet při 1 lotu a riziku ≤ 1 % u stopu (90. percentil):**
- SPX ~27 tis. $, NAS ~144 tis. $, US30 ~180 tis. $;
- s mikro kontraktem 0,01 lotu 267 $, 1 440 $ a 1 796 $.

### B: varianty při riziku 1 % u stopu
| Varianta | Vývoj 1990–2018 MAR | Kontrola 2019–26 MAR | Broker 2019–26 výnos / propad / MAR |
|---|---|---|---|
| **V0** 3 trhy, 3 ATR | **0,47** (+2,5 %/rok) | 0,55 | **+1,6 %/rok / 3,7 % / 0,43** |
| V1 jen SPX | 0,34 | 0,57 | +0,6 % / 2,6 % / 0,24 |
| V2 jedna pozice napříč | 0,20 | 0,64 | +0,4 % / 2,5 % / 0,15 |
| V3 SPX stop 2 ATR | 0,30 | 0,47 | +0,7 % / 3,6 % / 0,20 |
| V4 SPX stop 1,5 ATR | 0,20 | 0,13 | +0,0 % / 5,5 % / 0,01 |

**Rozhodnutí podle pravidel předem:**
- vítěz je **V0, tedy současné pravidlo**; potvrzeno v kontrole i u brokera;
- užší stop výhodu ničí, protože návrat k průměru potřebuje prostor;
- omezení na jeden trh nebo jednu pozici snižuje výnos víc než propad.

### Co z toho plyne
1. **Pravidla RSI(2) pro malý účet měnit nejde.** Lepší varianta neexistuje.
2. **Překážka je velikost kontraktu u brokera** (nejmenší pozice 1 $/bod).
   - S 10 000 Kč se RSI(2) u tohoto brokera obchodovat nedá: 1 lot SPX riskuje ~38 % účtu, NAS a US30 víc než celý účet.
   - **Řešení je broker nebo účet s mikro kontraktem 0,01 lotu.** Na 457 $ pak SPX riskuje ~0,4 %, NAS ~1,8 % a US30 ~2,7 % u stopu.
   - Celé V0 při ~1 % riziku chce zhruba 1 800 $ i s mikro kontrakty, nebo na 457 $ jen SPX.
   - Výběr brokera je na uživateli.
3. **Na demu se dnes obchoduje fakticky V1 (jen SPX).** Strop 0,5 % na nejmenší lot pustí jen SPX; NAS a US30 riskují 0,8–1,8 %. Sledování dopředu tak ověřuje slabší variantu (MAR 0,24 místo 0,43).
   - Návrh: strop pro RSI(2) na demu zvednout na 2 %, aby demo obchodovalo testovanou V0.
   - Jen se souhlasem uživatele.
4. **Očekávání:** V0 při 1 % riziku dává ~1,6–2,7 % ročně. Na 10 000 Kč je to ~160–270 Kč ročně, největší propad ~4–5 %.

