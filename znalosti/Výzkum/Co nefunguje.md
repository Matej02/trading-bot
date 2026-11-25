---
tags: [vyzkum, souhrn]
aktualizovano: 2026-10-29
---
# Co nefunguje (souhrn)

| Co | Kde zjištěno | Proč |
|---|---|---|
| Technické indikátory na H1 | [[Historie v1–v6]] | po nákladech 0 z 60 |
| Krátké timeframy (1m–15m) | [[F2 Více timeframů]], [[F7 Dokument 6 strategií SMC]] | spread velká část SL ([[Náklady brokera]]) |
| SMC: [[SFP – sweep likvidity|SFP]], [[FVG]], [[Order block|OB]], [[MSS a displacement|MSS]] | [[F5 SMC a volume profile na 1h]], [[F7 Dokument 6 strategií SMC]] | ~0 R i bez nákladů |
| SFP v 15m svíčce + FRVP (VAH/VAL/POC v knotu) | [[F20 Obecná strategie uživatele (SFP + FRVP)|F20]] | samo −0,04 R bez nákladů; s biasem/zónou/TP POC na 7 trzích OOS +0,78 R, na 7 nových trzích −0,43 R → bez výhody |
| F13 Veselovský na US indexech (jediný náznak z FM) | [[F13 indexy na delší historii (HistData 2010–2025)|F13 na delší historii]] | na nových letech 2010–2019 −0,11 R (n 417, pod náhodou), celek 2010–2026 +0,04 R, t 0,42; na jiném zdroji cen stejné období +0,07 místo +0,26 R → bez výhody |
| Noční drift US indexů (long 16:00 → 9:30 NY) | [[F21 Noční drift indexů (long přes noc)|F21]] | po nákladech +0,012–0,016 R/noc, ale náhodné okno stejné délky vyšlo lépe, US30 −0,006 R, kontrola t 1,50 → jen růst trhu, ne výhoda načasování |
| Průraz ranního rozpětí 15 min (US indexy, DAX) | [[F22 Průraz úvodního rozpětí (ORB)|F22]] | vývoj 2010–19 −0,027 R, kontrola +0,034 R; funguje jen 2018–25; longy kladné = růst indexů |
| Návrat po otevíracím gapu ≥ 0,3 ATR | [[F23 Návrat po otevíracím gapu|F23]] | vývoj −0,016 R, kontrola +0,013 R, DAX −0,042 R |
| Filtr volatility pro RSI(2) a Průraz | [[F24 Filtr volatility pro živé strategie|F24]] | RSI(2) vydělává i v klidném trhu, u Průrazu se vztah mezi obdobími otočil |
| Párové obchody na H1 (NAS/SPX, XAU/XAG, EUR/GBP, Brent/WTI) | [[F25 Párové obchody (relativní hodnota)|F25]] | vývoj +0,018 R t 1,1, kontrola +0,006 R; spread se do 10 dní nevrací |
| Pokračování po NFP/CPI (směr prvních 15 min) | [[F27 Pokračování po zprávách (NFP, CPI)|F27]] | vývoj −0,029 R, kontrola −0,140 R; první reakce se vrací |
| Měsíční sezónnost z 10 let zpět | [[F30 Měsíční sezónnost (průběžně)|F30]] | vývoj +0,058 R, kontrola −0,102 R; short signály −0,36 R |
| Rotace 3 nejsilnějších z 15 trhů | [[F32 Rotace podle relativní síly|F32]] | vývoj t 0,98; v kontrole horší než držet vše; závisí na zdroji dat |
| Limit rizika pro korelované trhy (1 pozice / strop 1,5 R ve skupině) | [[F34 Limit rizika pro korelované trhy|F34]] | RSI(2) přijde o 50–75 % zisku; portfolio od 2019 má poloviční propad, ale do 2018 horší → nezavádět |
| [[Volume profile]] (VA, POC, HVN) | F5, F7 | žádná výhoda |
| Průraz mimo zlato/US indexy/BTC | [[F3 Průraz na nových trzích]] | −0,11 R |
| Vstup na menším TF po denním signálu | [[F4 Vstup na menším timeframu]] | užší SL = vyražení |
| [[Momentum L=250]] | [[F1 Nové třídy signálů]] | výnos sežere swap brokera |
| [[COT]], limitky, adaptivní přepínání | [[Historie v1–v6]] | náhoda / drift |

Co funguje aspoň částečně: [[Průraz F2 (proraz_d1)]], [[RSI(2) pullback (mr_rsi2_d1)]].

Doplněno 2026-10-29: SMC koncepty nefungují ani na [[Forex|forexu]] a [[Zlato|zlatě]] s M1 vstupem ([[F7 Dokument 6 strategií SMC]]).

Doplněno 2026-10-29 ([[F8 Strategie z FM PDF]]):
- **S/D zóny po FM na D1, H4 a D v W:** OOS −0,17 až −0,22 R, horší než náhoda.
- **Daily bias jako samostatný obchod:** −0,06 R.
- **Makro skóre (Trading Analyzer):** ~0.
- **Kombinace FM konceptů** (8 spouštěčů × filtry × TP, H1 i H4, 2 208 kombinací): 0 prošlo výběrem ([[F9 Kombinace FM konceptů]]).
- **Entry modely všech mentorů FM přesně podle PDF** (Veselovský, Kimmel, Pátek, Šrajer DT, Můčka, Valchář, Hakimi, Hvězda): OOS −0,04 až −0,44 R ([[F10 Entry modely mentorů FM]]).
- **Můčka podle doplňujících pravidel uživatele** (struktura tělem s momentem, strong/weak po 0,382, zóny s BOS a 25 %, balanční level, killzones, bias, 4H, sweep → MSS → 0,618): nejlepší varianta vývoj −0,18 R, OOS +0,06 R; entry model bez nákladů na nule; NAS100 +0,7 R se na S&P/Dow/DAX neopakuje ([[F12 Můčka podle doplňujících pravidel]]).
- **Pátek podle PDF + B3** (H4 zóny z pivotů, odmítnutí, LH/HL, průraz M5/M15): 2R model −0,07 R, nejlepší varianta v OOS pod náhodou ([[F14 Pátek podle PDF a doplňujících pravidel]]).
- **Hvězda podle PDF + B4 + COT** (D v W, level nad levelem, COT index): nejlepší vývoj +0,22 R → OOS −0,17 R, COT filtr nepomohl ([[F15 Hvězda podle PDF, doplňujících pravidel a COT]]).
- **Hakimi podle PDF + B5** (Elliott ZigZagem, Fibo 0,618–0,75, FVG/zóna, RR ≥ 2,5): vybraná +0,07 R OOS jen na zlatě, jinde ztráta ([[F16 Hakimi podle PDF a doplňujících pravidel]]).
- **Šrajer (F17), Valchář (F18), Kimmel model 2 (F19)** podle PDF a všech obrázků: nic nad náhodou; skóre Trading Analyzeru jako filtr OOS zhoršuje ([[F17 Šrajer day a swing podle PDF]], [[F18 Valchář podle PDF a obrázků]], [[F19 Kimmel entry model 2]]).

Doplněno 2026-11-24 ([[F71 a F72 Londýnský průraz a víkendový gap na měnách|F71, F72]]):
- **Londýnský průraz asijského rozpětí** (12 párů, 2010–2026, H1 i M1): hrubě ~0 R, po spreadu −0,06 až −0,10 R, kladných 0 z 10 jiných párů.
- **Návrat víkendového gapu na měnách** (≥ 0,25 ATR, cíl páteční zavření): hrubě kladný, ale ve vývoji 2010–18 po nedělním spreadu −0,08 R, na kovech a křížových párech ztráta.

Doplněno 2026-11-24 ([[F73 až F78 Dluhopisy, VIX a strach jako signál pro indexy|F73–F78]], [[F79 až F81 Halloween, RSI(2) na kryptu a na ropě|F79–F81]]):
- **Strach z jiných trhů jako signál pro indexy** (TLT, natažený VIX, odeznívající VIX, útěk do jenu): nic neprošlo, natažený VIX jen do 2018.
- **Nákup na 52týdenním maximu** (20 dní): horší než nákup kdykoli.
- **RSI(2) na kryptu a ropě**: bez převisu.
- Těsně neprošly (3/5): VIX ≥ 30, útěk do dluhopisů, Halloween.
- **Víkendový pohyb bitcoinu** (návrat k páteční ceně, „CME gap“): ztráta i hrubě (F82).
- **Sudé týdny cyklu FOMC** (Cieslak a kol.): do 2018 t 1,48, od 2019 záporné (F84).

Doplněno 2026-11-25 ([[F85 RSI(2) na akciích|F85]]):
- **RSI(2) na jednotlivých akciích** (členové S&P 500 k danému dni, 72 tis. obchodů, 1996–2026): bez nákladů +0,033 R, po nákladech akciových CFD −0,003 R (vývoj) a −0,011 R (kontrola), převis t 0,89 / 0,15. V prop zkoušce by zvýšila propady z 0 % na 71 %.
- **Drift po výsledcích firem (PEAD) na akciích FTMO** ([[F88 Drift po výsledcích firem (PEAD)|F88]], 2004–2026, 1 734 obchodů): převis nad stejnými obchody ve všech dnech je skutečný (+0,12 R, t 3,7), ale po nákladech akciových CFD R signálu −0,03 / −0,05. Financování ~12 % ročně long i short sežere vícedenní akciové strategie.

Doplněno 2026-11-25 ([[F92 a F93 Výsledky firem během dne|F92, F93]]):
- **Pokračování v den výsledků** (otevření → zavření ve směru gapu, akcie FTMO): převis t 1,6 / 1,4, po pesimistických nákladech ztráta. Gap informaci už obsahuje.
- **Druhý den po výsledcích (F93)** neprošel jen o bod: silný efekt (t 6,5, 23 z 23 let), ale v kontrole po pesimistických nákladech −0,011 R. Není to „nefunguje“, ale „nevíme, jestli to unesou náklady“.
