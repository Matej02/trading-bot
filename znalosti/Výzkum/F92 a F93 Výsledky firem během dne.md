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

## Výsledky (2026-11-25)
Výstup `research_data/f88/f92_souhrn.txt`, dodatečný popis `research_data/f88/f93_popis.txt`.

| | F92 den výsledků (gap) | F93 druhý den po reakci |
|---|---|---|
| Obchodů (vývoj / kontrola) | 574 / 680 | 855 / 879 |
| Síto: převis bez nákladů ve vývoji | +0,080 (t 1,65) | **+0,167 (t 6,39)** |
| Vývoj: R / převis / t | +0,002 / +0,077 / 1,59 | **+0,114 / +0,171 / 6,55** |
| Kontrola: R / převis / t | +0,011 / +0,062 / 1,44 | **+0,031 / +0,073 / 2,69** |
| Pesimistické náklady (vývoj / kontrola) | −0,049 / −0,037 | +0,068 / **−0,011** |
| Long / short převis | +0,031 / +0,091 | +0,113 / +0,135 |
| Roky s kladným převisem | 14 z 23 (61 %) | **23 z 23 (100 %)** |
| **Body** | **3/6 – NEPROŠLO** | **5/6 – NEPROŠLO** (jen bod 4) |

**F92:** pokračování v den výsledků je slabé (t 1,4–1,6). Gap už většinu informace obsahuje.

**F93:** zatím nejsilnější efekt výzkumu. Druhý den po silné reakci na výsledky cena pokračuje ve všech 23 letech, u longů i shortů, t 6,5 ve vývoji a 2,7 v kontrole. **Neprošel jen pesimistickými náklady v kontrole** (půl spreadu 0,10 % → −0,011 R; při 0,05 % +0,031 R).
- Efekt slábne: převis 2004–2018 +0,10 až +0,34 R ročně, 2019–2023 jen +0,01 až +0,02, 2024–2026 +0,07 až +0,12.
- Popis: stop 0,5 ATR kontrola R +0,049 (t 2,70), |z| ≥ 3 kontrola R +0,050 (t 3,18). Vybráno až po výsledku, nerozhoduje.
- **Rozhoduje skutečný spread akciových CFD u FTMO v prvních minutách po otevření.** Data brokera akcie neobsahují, změřit to z historie nejde.

**Měřítko (jen popis, test neprošel):**
- Ve stejném riziku 1,25 % jako indexy F93 zkoušku zrychlí (P24 70 % proti 17 %, medián 12,5 proti 27,2), ale propadne 23 % (kontrola 46 %). Až 3 akciové obchody denně při plném riziku jsou moc.
- Dodatečně s menším rizikem na akciové obchody (indexy 1,25 %):

| Riziko F93 | P12 / P24 / P36 | Propadlo (vývoj / kontrola) | Medián |
|---|---|---|---|
| 0,25 % | 8 / 44 / 81 % | 0 / 3 % | 23,7 |
| **0,5 %** | **13 / 62 / 85 %** | **0 / 8 %** | **19,1** |
| 0,75 % | 25 / 68 / 82 % | 0 / 30 % | 15,5 |
| bez F93 (základ) | 3 / 17 / 65 % | 0 / 7 % | 27,2 |

- **Neaktivita:** s F93 klesnou mezery > 30 dní z 51 na 3 za 21 let (udržovací obchody ~0,3 ročně místo 4,5). S F92 na 7.

**Poučení:** u akcií FTMO po výsledcích existuje silný a stálý efekt i během jednoho dne. Je ale malý vůči nákladům. Kdyby skutečné náklady byly do 0,05 % na stranu, F93 by byl nejlepší kandidát na zrychlení zkoušky i vyřešení neaktivity. Podle pravidel zapsaných předem ale neprošel a pravidla se dodatečně nemění.

## Spready akcií u FTMO a jiných firem (2026-11-25, web)
- **FTMO spready akcií nezveřejňuje.** Stránka [Symbols](https://ftmo.com/en/symbols/) má živý přehled jen pro měny, indexy, krypto a komodity. U „Equities CFD“ uvádí jen kontrakt, páku, swap a provizi (0,004 %). Recenze uvádějí jen „ne super úzké“ spready, bez čísel.
- Pro představu: běžný broker CFD (Admiral Markets) uvádí u AAPL typický spread 0,03 $ (~0,013 %, tedy půl spreadu ~0,007 %). To je hluboko pod naším „normálním“ 0,05 %. Spready se ale v prvních minutách po otevření rozšiřují a to z denních dat nezměříme.
- **Jiné firmy s akciemi** (přehled [FXEmpire](https://www.fxempire.com/prop-firms/best/stocks), affiliate, neověřeno na oficiálních stránkách):
  - **Trade The Pool:** skutečné akcie (ne CFD), tedy bez financování přes noc, takže by mohl fungovat i vícedenní [[F88 Drift po výsledcích firem (PEAD)|F88]]. Platforma Trader Evolution (ne MT5), automatika přes SignalStack. Runner by se musel přepsat, indexy jen přes ETF.
  - **FXIFY:** ~28 akciových CFD, MT5, EA povolené, spready neuvedeny.
  - **100X Club:** EA zakázané. **The5ers, Fintokei:** akcie nemají.
- **Jak spread zjistit:** FTMO Free Trial (zdarma, bez omezení počtu). Spready akcií ve webové platformě 15:30–16:00 Praha několik dní po sobě, bez zásahu do runneru. Zakládá uživatel.
