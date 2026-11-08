---
tags: [vyzkum, fronta, plan]
datum: 2026-11-07
---
# Fronta nápadů F22–F33

## Stav
| # | Výsledek |
|---|---|
| [[F22 Průraz úvodního rozpětí (ORB)|F22]] ORB | **bez výhody**: vývoj −0,027 R, kontrola +0,034 R; funguje jen 2018–2025 |
| [[F23 Návrat po otevíracím gapu|F23]] gap | **bez výhody**: vývoj −0,016 R, kontrola +0,013 R |
| [[F24 Filtr volatility pro živé strategie|F24]] filtr volatility | **neprošel**; RSI(2) je kladná v klidném i nervózním trhu (+0,09 R / +0,12 R) |
| [[F25 Párové obchody (relativní hodnota)|F25]] páry | **bez výhody**: vývoj +0,018 R (t 1,1), kontrola +0,006 R; 75 % obchodů končí časem |
| [[F26 Průraz po úzkém dni (NR7)|F26]] NR7 | **bez výhody**: vývoj +0,032 R, kontrola −0,039 R; výhoda jen 1980–1999 |
| [[F27 Pokračování po zprávách (NFP, CPI)|F27]] zprávy | **bez výhody**: vývoj −0,029 R, kontrola −0,140 R; první reakce se vrací |
| [[F28 Intradenní momentum (první a poslední půlhodina)|F28]] intradenní momentum | **bez výhody**, i bez nákladů ~0 |
| [[F29 Krypto momentum|F29]] krypto momentum | **bez výhody, těsně**: vývoj t 4,07, kontrola t 1,33 (hranice 1,5); Sharpe lepší než stále long |
| [[F30 Měsíční sezónnost (průběžně)|F30]] sezónnost | **bez výhody**: vývoj +0,058 R (t 2,5), kontrola −0,102 R (t −3,3) |
| [[F31 Drift před FOMC|F31]] drift před FOMC | **formálně prošel, po prověrce KANDIDÁT**: 2019–26 +0,157 R/událost (t 2,08), 2013–18 ~0 |
| [[F32 Rotace podle relativní síly|F32]] rotace | **bez výhody**: vývoj t 0,98, v kontrole horší Sharpe než držet vše |
| [[F33 Rebalancování na konci měsíce|F33]] rebalancování | **PROŠLO (všech 5 bodů po měsících)**: vývoj +0,305 R (t 3,2), kontrola +0,230 R (t 1,57), US30 +0,345, DAX +0,220 |

**Shrnutí a přínosy:** [[Souhrn testů F21–F33 a přínosy]]


Zadání uživatele (2026-11-07): „rozepiš minimálně 10 dalších strategií, které vyzkoušíme a něco si z nich vezmeme. Zatím mi je jen rozepiš, do kterých se pustíš. Na bota stále nesahej.“

## Společný postup pro každý nápad
Poučení z [[F13 indexy na delší historii (HistData 2010–2025)|F13 na delší historii]] a [[F21 Noční drift indexů (long přes noc)|F21]].

1. **Plán a pravidla rozhodnutí do vaultu PŘED výpočtem.** Po výsledku se nic neladí.
2. **Vývoj** na starších letech (HistData 2010–2019, Yahoo denní data). **Kontrola** na datech brokera 2019–2026.
3. **Druhý zdroj cen.** Výsledek nesmí záviset na drobnostech v datech.
4. **Jiné trhy**, kde dává smysl, že by to mělo fungovat taky.
5. **Srovnání s náhodou** (stejný SL/TP, směr a čas) a s prostým držením trhu.
6. **Náklady jako u brokera:** spread podle hodiny, tick, swap (ze středy na čtvrtek 3×).
7. **Čas:** data brokera se v létě posunou na skutečné UTC (viz [[MT5 napojení]]).
8. **Bot se nemění.** Skripty v `scratch/f2x_*`, data v `research_data/f2x`, výsledek do vaultu.
   - Do simulátoru nebo na demo až po úspěšném testu a po souhlasu uživatele.
10. **Korelované trhy (SPX a NAS) hodnotit po událostech/dnech, ne jako nezávislé obchody** (poučení z F31, 2026-11-08).
9. **Pravidla na úrovni M1 (sweep o tick) se nepoužívají.** Nejmenší rámec pro signál je M5, raději H1 nebo D1.

## Nápady

| # | Nápad | Jak (návrh pravidel) | Proč by mohl fungovat | Data | Kdy by se obchodoval |
|---|---|---|---|---|---|
| **F22** | **Průraz úvodního rozpětí (ORB)** | První 5 a 15 min seance US indexů (15:30) a DAXu (9:00). Vstup na zavření M5 za rozpětím, SL na druhé straně, ven 19:45 (a 22:00 pro srovnání). | Ráno se tvoří směr dne. Doloženo na QQQ (Zarattini a Aziz 2023). | HistData SPX/NAS 2010–25, broker 2019–26 (+DAX, US30) | 9:00–19:45, PC zapnutý |
| **F23** | **Návrat po otevíracím gapu** | Mezera mezi včerejším zavřením a otevřením seance > 0,3 ATR → obchod proti gapu, TP na včerejším zavření, SL 1 gap, ven 19:45. | Přeskočené ceny se často vyplní. Data o nočním pohybu máme hotová z F21. | stejná jako F22 | 15:30–19:45 |
| **F24** | **Filtr volatility pro živé strategie** ([[Průraz F2 (proraz_d1)|Průraz F2]], [[RSI(2) pullback (mr_rsi2_d1)|RSI(2)]]) | Jeden předem daný filtr: percentil 20denní volatility. RSI(2) jen ve vyšší volatilitě, průraz jen v nižší. Plus řízení velikosti pozice podle volatility. | Návrat k průměru po propadu bývá silnější v nervózním trhu (Connors, filtr VIX). | Yahoo denní od 1990, broker | jako dnes (denní signál) |
| **F25** | **Párové obchody (relativní hodnota)** | Z-skóre logaritmického rozdílu cen dvojic: NAS100/SPX500, XAU/XAG, Brent/WTI, EURUSD/GBPUSD. Vstup při \|z\| > 2, ven při z = 0, stop \|z\| > 4 nebo 10 dní. | Úplně nová rodina, na směru trhu nezávisí. Dvojice drží pohromadě fundamenty. | broker H1 (73 trhů), HistData SPX/NAS | H1 signál, kdykoliv |
| **F26** | **Průraz po úzkém dni (NR7 / inside day)** | Po nejužším dni ze 7 (nebo vnitřním dni) stop příkazy nad a pod jeho rozpětím. SL na druhé straně, ven po 3 dnech nebo trailing 2 ATR. | Po stažení volatility přichází rozšíření (Crabel). Denní, levné na náklady. | Yahoo denní od 1990, broker H1 → D1, 20+ trhů | denní, příkazy ráno |
| **F27** | **Pokračování po zprávách (NFP, CPI)** | Ve 14:45 vstup ve směru prvních 15 minut po zprávě, pokud byl pohyb > 0,5 ATR15m. SL za extrémem, TP 2R nebo ven 19:45. US indexy, zlato, EURUSD. | Trh zprávu „trávi“ několik hodin. | HistData + broker; kalendář 2010–2021 doplnit z bls.gov | 14:30–19:45 |
| **F28** | **Intradenní momentum (první → poslední půlhodina)** | Znaménko výnosu od včerejšího zavření do 10:00 NY určí směr obchodu 15:30–16:00 NY (21:30–22:00 Praha). | Doloženo na S&P (Gao, Han, Li a Zhou 2018). Malý pohyb, ale hodně obchodů. | HistData SPX/NAS, broker | **21:30–22:00**, jen se serverem |
| **F29** | **Krypto momentum 1–4 týdny** | BTC/ETH: long, když je 1–4týdenní výnos nad nulou, jinak mimo trh (nebo short). Týdenní přepočet. | Doloženo na kryptu (Liu a Tsyvinski 2021). Simulátor krypto obchoduje 24/7. | Binance denní od 2017 (skutečný objem), broker | denní, simulátor 24/7 |
| **F30** | **Měsíční sezónnost (průběžně, bez lovení)** | Pro každý trh a měsíc se směr určí jen z předchozích 10 let. Obchoduje se celý další měsíc. Hodnotí se jen roky, které model ještě neviděl. | Kandidát z [[Sezónnost|poznámky o sezónnosti]] (JPY v březnu, CAD v zimě). Průběžné vyhodnocení brání lovení náhod. | Yahoo denní FX, indexy, zlato, ropa od 2000 | měsíčně |
| **F31** | **Drift před FOMC** | Long S&P/NAS 24 h před oznámením FOMC (14:00 NY den předem → 14:00 NY v den oznámení). | Doloženo (Lucca a Moench 2015). Jen 8× ročně, statistika bude slabá, ale levné. | HistData + broker; data FOMC 2010–2021 z federalreserve.gov | vstup 20:00 Praha, spíš server |
| **F32** | **Rotace podle relativní síly** | Měsíčně long 3 nejsilnější z ~15 trhů podle 6měsíčního výnosu očištěného o volatilitu. Varianta long/short. | Průřezové momentum je doložené napříč trhy (Asness a kol.). Liší se od neúspěšného [[Momentum L=250]] (to bylo na jednom trhu). | Yahoo denní, broker H1 → D1 | měsíčně |
| **F33** | **Rebalancování na konci měsíce** | Když akcie v měsíci výrazně předběhly dluhopisy, short indexů poslední 3 obchodní dny měsíce (a naopak). | Penzijní fondy prodávají, co vyrostlo (Harvey a kol.). Liší se od [[Turn-of-month]], směr se mění podle měsíce. | Yahoo denní (indexy + dluhopisové ETF) | denní, pár dní v měsíci |

## Pořadí
1. **První vlna** (data máme, obchodovatelné při zapnutém PC, nejsilnější podklady):
   - **F22 ORB**;
   - **F23 gap**;
   - **F24 filtr volatility pro živé strategie** (přímo se týká toho, co běží);
   - **F25 párové obchody**.
2. **Druhá vlna:** F26 NR7, F27 zprávy, F28 intradenní momentum, F29 krypto momentum.
3. **Třetí vlna:** F30 sezónnost, F31 FOMC, F32 rotace, F33 rebalancování.

## Co si vezmeme i z neúspěchu
- **F22, F23 a F28:** jak se chová otevření a závěr seance. To se hodí i pro výstupy ostatních strategií (např. 19:45 vs. 22:00).
- **F24:** pravidlo řízení velikosti pozice podle volatility, použitelné pro celého bota.
- **F25:** které dvojice drží pohromadě, ať víme, které strategie si navzájem zdvojují riziko.
- **F27 a F31:** jak velký je pohyb kolem zpráv, tedy podklad pro agenta Kalendář v simulátoru.

## Potřebná data ke stažení (zeptat se uživatele před stažením)
- Yahoo denní: část už je z [[F6 Denní strategie|F6]].
- Binance denní BTC/ETH (data.binance.vision).
- Archiv termínů NFP/CPI 2010–2021 (bls.gov) a FOMC 2010–2021 (federalreserve.gov).
- Případně další indexy z HistData: DAX, FTSE, CAC, EuroStoxx, Nikkei.
