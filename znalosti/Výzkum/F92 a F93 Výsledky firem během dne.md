---
tags: [vyzkum, f92, f93, akcie, vysledky, prop, plan]
datum: 2026-11-25
---
# F92 a F93 Výsledky firem během dne

Zadání uživatele (2026-11-25): „Ano, pokračuj.“ (po [[Fronta nápadů F92–F96]]). Bot ani runner se nemění.

**Proč:**
- [[F88 Drift po výsledcích firem (PEAD)|F88]] našel u akcií FTMO skutečné pokračování ceny po výsledcích (převis +0,12 R za 20 dní, t 3,7). Vícedenní držení ale zabilo financování CFD.
- Obchod během dne financování neplatí. Je častý a pro prop účet nemá riziko přes noc.

## Plán (zapsán PŘED výpočtem)
**Data:** výsledky z EDGAR (8-K 2.02, 40 firem, 2004-09 až 2026-11, vyčištění jako F88), denní ceny Yahoo (`research_data/f85/yahoo_us.pkl`).

**F92 – den výsledků během dne:**
- Jen události přijaté před 9:30 nebo po 16:00 NY (otevření pak už výsledek obsahuje). Den reakce D jako v F88.
- Gap = otevření D / zavření D−1 − 1.
- z = gap / směrodatná odchylka denních výnosů akcie za 60 dní před D. Index se neodečítá, protože otevírací ceny indexu z Yahoo jsou 2004–2008 chybné (55 % dní = včerejší zavření).
- **|z| ≥ 2 → vstup na otevření D ve směru gapu, výstup na zavření D.**

**F93 – druhý den po výsledcích:**
- Všechny události, den reakce D a z = nadvýnos akcie nad S&P 500 za den D (zavření → zavření) / směrodatná odchylka za 60 dní, přesně jako F88.
- **|z| ≥ 2 → vstup na otevření D+1 ve směru reakce, výstup na zavření D+1.**

**Společné:**
- Stop **1 ATR(20)** z dne před vstupem (pro F92 ATR do D−1). Zásah přes low/high dne = výsledek −1 R (pesimisticky, neznáme pořadí). Jednotka R = 1 ATR.
- Náklady na stranu: půl spreadu 0,05 % + provize 0,004 %. Bez financování (zavírá se týž den). Pesimisticky půl spreadu 0,10 %.
- **Srovnání:** stejný obchod (stejná akcie, směr a stop, otevření → zavření) ve všech dnech daného období. Převis = R signálu − tento průměr. Vyhodnocení po dnech vstupu, t-test průměru převisu.
- **Období:** vývoj 2004-09 až 2016, kontrola 2017–2026.

**Pravidla rozhodnutí, každý test zvlášť, ANO jen když platí vše:**
1. Síto: převis bez nákladů ve vývoji > 0 (jinak NE).
2. Vývoj: R signálu > 0, převis > 0, t ≥ 3,0.
3. Kontrola: R signálu > 0, převis > 0, t ≥ 2,0.
4. Pesimistické náklady: R signálu > 0 ve vývoji i kontrole.
5. Obě strany: převis longů > 0 i převis shortů > 0 (celé období).
6. Převis kladný aspoň v 60 % let.

**Měřítko prop zkoušky (jen při ANO, jinak popis):**
- základ F33 se stopem + RSI(2) ([[F87 Měřítko s F33 se stopem jako v runneru|F87]]) proti základ + F92/F93;
- nejvýš 3 akciové obchody denně, přednost nejvyšší |z|;
- kritérium z [[Strategie výzkumu a měřítko prop zkoušky]]: medián −20 % nebo P12 +10 p. b., propadlo ≤ 10 %, ve vývoji i kontrole zvlášť;
- navíc počet 30denních mezer bez obchodu.

**Popis (nerozhoduje):** stop 0,5 / 2 ATR a bez stopu, práh |z| 1,5 a 3, long a short zvlášť, počty obchodů po letech.

**Omezení dat:** denní data neznají cenu v prvních minutách. Otevírací cena Yahoo = oficiální otevření burzy, CFD může mít v první minutě horší cenu. Pokrývá to částečně pesimistický spread.

Skript `scratch/f92_vysledky_den.py`, výstup `research_data/f88/f92_souhrn.txt`.
