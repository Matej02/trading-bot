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
