---
tags: [vyzkum, f13, overeni, histdata]
datum: 2026-11-07
---
# F13 na indexech na delší historii (HistData 2010–2025)

Zadání uživatele (2026-11-07): „klidně je stáhni a zapiš vedle do vaultu, nijak bota neupravuj a nesahej na něj, nech ho, jak je. Jediné, co chci, aby sis to dal vedle, otestoval a dal mi výstup.“

Kontext: [[FM live test na MT5 demu#Kdy reálné peníze (2026-11-07)|Kdy reálné peníze]].
- F13 na NAS100 + SPX500 má v testu na datech brokera (2019-02 až 2026-10) OOS +0,25 R, ale t = 1,3. To není průkazné.
- Demo by výhodu potvrzovalo 8–11 let.

## Plán (zapsán PŘED spuštěním testu)
- **Strategie se nemění:** přesně varianta, která běží na demu: `tf=M1 lvl=liq entry=ob50 tp=tp2`, kód `research_f13_ves.py`.
  - Kód runneru ani výzkumu se neupravuje. Nové skripty jsou vedle v `scratch/f13_hist_*.py`, data v `research_data/histdata/`.
- **Data:** HistData.com, M1 ASCII, SPX/USD → SPX500mini a NSX/USD → NAS100mini, roky 2010–2025 (32 souborů, staženo 2026-11-07).
  - Data začínají 14. 11. 2010.
  - Časy jsou v newyorském čase (EST); posun na UTC se ověří proti datům brokera.
  - **Objem chybí** (všude 0).
- **Nový vzorek:** 2010-11 až 2019-02-20, tedy před začátkem dat brokera. Na těchto letech se nikdy nic neladilo.
- **Kalibrace na překryvu 2019-02-21 až 2025-12-31:** F13 na HistData proti F13 na datech brokera bez objemu. Porovnat počet obchodů, průměr R a shodu jednotlivých obchodů. Když překryv nesedí, nový vzorek se nedá brát vážně.
- **Náklady:** stejný model jako v původním testu (relativní spread brokera podle hodiny + skluz).
- **Zprávy:** ruční kalendář FOMC/NFP/CPI začíná 2021-09, takže v novém vzorku (a ve vývoji 2019–2021 původního testu) se zpravodajské dny nevynechávají. Vliv filtru se změří na letech 2021-09+.

**Pravidla rozhodnutí (pevná):**
- **ANO, ověřená výhoda:**
  - nový vzorek 2010–2019 sám dá průměr **≥ +0,10 R**;
  - a celek (nový vzorek + data brokera 2019–2026) má **t ≥ 2,0**.
- **NE:** cokoliv jiného. F13 jde k [[Co nefunguje|strategiím bez výhody]].
- Na výsledek se nic neladí. Žádné změny parametrů, trhů ani časů.

## Příprava dat (zjištění)
- **HistData je v newyorském čase včetně letního.** Otevření burzy 9:30 a závěr 15:59 sedí v zimě i v létě. To, že by šlo o EST bez letního času, se nepotvrdilo.
- **Data brokera jsou v britském letním čase (konec března až konec října) o 1 h posunutá.** Týká se to testů i demo runneru.
  - Čas serveru je UTC celý rok, ale `fetch_m1` ho čte jako `Europe/London`. V létě tak čas svíčky vyjde o 1 h dřív, než skutečně byl.
  - Doklad: na datech brokera je v létě otevření burzy (13:30 UTC) vidět ve 12:30 a závěr ve 18:59. V zimě sedí na 14:30 a 20:59.
  - Test i demo počítají stejně, takže spolu sedí (shoda signálů). Proti skutečnému času jsou ale v létě časová okna (killzones, 22:00) posunutá o hodinu.
  - V zimě je vše správně.
  - **Bot se podle zadání uživatele neupravoval.** Viz [[MT5 napojení]].
- Pro test jsou HistData ve dvou verzích: „čas jako broker“ (stejný posun jako demo, hlavní test) a „skutečné UTC“ (kontrola). Shoda s brokerem po převodu: korelace minutových výnosů 0,88–0,98.
- **Úplnost dat v obchodních hodinách 8–17 Praha:** NAS100 97–100 % minut, SPX500 75–96 % v letech 2010–2017, od 2018 96–100 %.

## Výsledky (2026-11-07)
Souhrn je v `research_data/histdata/out/f13_hist_souhrn.txt`, skripty v `scratch/f13_hist_prevod.py`, `scratch/f13_hist_test.py`, `scratch/f13_hist_eval.py` a `scratch/f13_hist_graf.py`.

**Kontrola reprodukce:** původní test na datech brokera vychází stejně:
- vývoj +0,18 R (n 127);
- OOS **+0,25 R (n 206, t 1,30)**.

**Kalibrace na překryvu 2019-02 až 2025-12:**

| Data | n | R/obchod | t |
|---|---|---|---|
| broker s objemem (jako demo) | 312 | +0,30 | 1,99 |
| broker bez objemu | 343 | +0,26 | 1,84 |
| HistData, čas jako broker | 375 | **+0,07** | 0,54 |
| HistData, skutečné UTC | 402 | +0,10 | 0,81 |

- Stejné obchody na obou zdrojích: jen **asi 50 %**. U shodných obchodů je R stejné (korelace 1,00).
- Stejná pravidla na stejném období dávají podle zdroje cen +0,26 R nebo +0,07 R. **Výsledek je velmi citlivý na drobnosti v datech.** U skutečné výhody by to tak být nemělo.

**Nový vzorek 2010-11 až 2019-02 (nikdy neladěno):**

| | n | R/obchod | t | výhra |
|---|---|---|---|---|
| **HistData, čas jako broker (hlavní)** | 417 | **−0,11** | −1,06 | 18 % |
| – NAS100 (úplná data) | 264 | −0,04 | −0,31 | 19 % |
| – SPX500 | 153 | −0,23 | −1,46 | 18 % |
| HistData, skutečné UTC | 462 | −0,15 | −1,55 | 17 % |
| náhodné vstupy (stejný SL/TP, směr, čas) | 1106 | +0,04 | 0,65 | 25 % |

- 90% bootstrap interval průměru: **−0,28 až +0,07 R**.
- Je to horší než náhoda. I po přičtení rozdílu zdrojů z překryvu (+0,19 R) by vyšlo jen asi +0,08 R, tedy pod hranicí.
- Po letech: kladné jen 2012 a 2015. Ztrátové roky 2011 (−24 R), 2013 (−16 R) a 2018 (−21 R).

![[F13 indexy – delší historie, kumulativní R.png]]

**Celek** (nový vzorek + broker 2019–2026):
- n 750, **+0,04 R, t 0,42**;
- max. propad **67 R**, součet +27 R za 16 let.

**Filtr zpráv** (od 2021-09):
- broker s filtrem +0,22 R, bez filtru +0,17 R;
- HistData +0,06 R i bez filtru +0,05 R.
- Pomáhá málo, chybějící kalendář před 2021 závěr nemění.

## Rozhodnutí podle pravidel zapsaných předem
- Nový vzorek ≥ +0,10 R: **NE** (−0,11 R).
- Celek t ≥ 2,0: **NE** (t 0,42).
- **⇒ F13 na indexech je BEZ OVĚŘENÉ VÝHODY.**
  - Kladný výsledek 2020–2025 na datech brokera se do minulosti neopakuje.
  - Na jiném zdroji cen se ze stejného období ztratí většina zisku.
  - Je to stejný obraz jako na US30 a DAXu v [[F13 Veselovský podle PDF a doplňujících pravidel|F13]].
- Pro [[FM live test na MT5 demu#Kdy reálné peníze (2026-11-07)|reálné peníze]] tím nezůstává žádný kandidát.
- Demo běží dál beze změny. Uživatel chtěl bota nechat, jak je.
