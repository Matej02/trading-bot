"""Vytvori Obsidian vault D:\\Trading bot\\znalosti - propojene poznamky z celeho projektu (graf = "neuronka").
Spusteni znovu poznamky prepise (rucni upravy delej rovnou v Obsidianu a tenhle skript uz nespoustej)."""
import json
import os
import re

ROOT = r"D:\Trading bot\znalosti"

N = {}


def note(path, tags, body):
    N[path] = (tags, body.strip() + "\n")


# ------------------------------------------------------------------ rozcestnik
note("00 Rozcestník", ["rozcestnik"], """
# Trading bot – mozek projektu

Všechno, co jsme o projektu zjistili, jako propojená síť poznámek. Graf (Ctrl+G) ukazuje, jak spolu souvisí.

## Kde začít
- [[Cíl projektu]] a [[Pravidla spolupráce]]
- Co dnes živě obchoduje: [[Průraz F2 (proraz_d1)]] a [[RSI(2) pullback (mr_rsi2_d1)]]
- Co nefunguje a proč: [[Co nefunguje]]

## Výzkum (časová osa)
[[Historie v1–v6]] → [[F1 Nové třídy signálů]] → [[F2 Více timeframů]] → [[F3 Průraz na nových trzích]] →
[[F4 Vstup na menším timeframu]] → [[F5 SMC a volume profile na 1h]] → [[F6 Denní strategie]] →
[[F7 Dokument 6 strategií SMC]]

## Strategie
[[Průraz F2 (proraz_d1)]] · [[RSI(2) pullback (mr_rsi2_d1)]] · [[Momentum L=250]] · [[Time-of-day AUDJPY 23-00]]

## Koncepty
[[SFP – sweep likvidity]] · [[Likvidita]] · [[FVG]] · [[MSS a displacement]] · [[Order block]] ·
[[Supply a demand zóny]] · [[Volume profile]] · [[VWAP]] · [[Killzones a session]] · [[Daily Open a Power of 3]] ·
[[Režim trhu]] · [[Mean reversion]] · [[Trend following]] · [[Turn-of-month]] · [[Carry]] · [[COT]]

## Metodika
[[Plán předem]] · [[Výběr, kontrola, holdout]] · [[Walk-forward]] · [[Náhodné vstupy]] · [[Náklady brokera]] ·
[[Metodické pasti]] · [[Risk management]]

## Infrastruktura
[[Simulátor]] · [[Agenti]] · [[AI analytik]] · [[Zprávy a kalendář]] · [[Bot 24-7]] · [[Učící režim]] ·
[[Stínové obchody a verdikty]] · [[Python bot tv_agent]] · [[MT5 napojení]] · [[Zdroje dat]]

## Trhy
[[Broker GlobalDynamicMarkets]] · [[Zlato]] · [[Bitcoin a krypto]] · [[US indexy]] · [[Forex]]
""")

# ------------------------------------------------------------------ projekt
note("Projekt/Cíl projektu", ["projekt"], """
# Cíl projektu

- Najít strategii, která opravdu funguje: **co nejvyšší úspěšnost**, nebo dobrý poměr výher a proher
  („1 obchod +10 000 a 3× −500 je v pořádku“).
- Kolem ní [[Risk management]] a [[Agenti]], kteří o každém obchodu rozhodují.
- Všechno **zdarma** a jen na demu / v simulaci ([[Pravidla spolupráce]]).
- Od 2026-10-27 večer: v [[Učící režim|učícím režimu]] brát co nejvíc obchodů, i ztrátových, a z dat zjistit, co funguje.

Současný stav: živě [[Průraz F2 (proraz_d1)]] + kandidát [[RSI(2) pullback (mr_rsi2_d1)]]. Přehled neúspěchů: [[Co nefunguje]].
""")

note("Projekt/Pravidla spolupráce", ["projekt", "pravidla"], """
# Pravidla spolupráce

- **Klíče a hesla** (APP_PASSWORD, GEMINI_API_KEY, TICK_SECRET) si uživatel nastavuje ve Vercelu sám – nikdy je neposílat ani nechtít.
- Na web se nepřihlašuje Claude, nastavení na Vercelu mění uživatel.
- Jen demo / simulace, nikdy živé příkazy na reálný účet ([[MT5 napojení]]).
- Všechno zdarma.
- Skripty, data, výstupy i pomocné soubory na **disk D** (`D:\\Trading bot`, pomocné v `scratch`), ne na C.
- Výzkum vždy s [[Plán předem|plánem stanoveným předem]] a se skutečnými [[Náklady brokera|náklady brokera]].
""")

note("Projekt/Historie v1–v6", ["vyzkum", "historie"], """
# Historie v1–v6 (srpen 2026)

Uzavřený výzkum k 2026-08-26: **přes 1 500 kombinací, nic neobstálo.**

- 6 technických strategií × 13 párů × 3 TF – 0 prošlo (náhoda ~4).
- Výstupy (trailing, breakeven, čas) – nic nepřekonalo pevný SL/TP, breakeven nejhorší.
- Adaptivní přepínání strategií – prohrálo s náhodným losováním.
- [[Time-of-day AUDJPY 23-00|Time-of-day]] – efekty reálné, ale po nákladech skoro nula.
- [[COT]] – 0 z 30.
- Pasivní plnění (limitky) – přesně 0,00 (byl to drift, viz [[Metodické pasti]]).
- **Zlato** jako klíčový experiment: spread jen 1,8 % ATR, a strategie stejně nefungují → náklady nebyly příčina ([[Zlato]]).
- Prop firm evaluace: šance projít 45–49 % s nejlepší edge vs 43–47 % bez edge → loterie.

Hlavní poučení: [[Metodické pasti]] (chybějící náklady, překrývající se okna, jednostranný test).
Pokračování: [[F1 Nové třídy signálů]].
""")

# ------------------------------------------------------------------ vyzkum
note("Výzkum/F1 Nové třídy signálů", ["vyzkum", "neproslo"], """
# F1 – nové třídy signálů (2026-10-26) → neprošlo

`research_f1.py`. 40 trhů, rozhodnutí 1× denně, výběr do 2022, holdout 2023+ ([[Výběr, kontrola, holdout]]).

| Rodina | Holdout |
|---|---|
| [[Momentum L=250|Trendové momentum]] | PF 0,98 |
| [[Mean reversion|Návrat k průměru]] na indexech RSI(2)<5 | PF 1,42, ale nad driftem t −0,02 |
| [[Turn-of-month|Přelom měsíce]] | PF 0,76 |
| [[Carry]] | PF 0,82 |

Zjištění o brokerovi: přirážka ~0,7 pipu na stranu, EURUSD živě 1,9 pipu ([[Broker GlobalDynamicMarkets]]).
Další: [[F2 Více timeframů]].
""")

note("Výzkum/F2 Více timeframů", ["vyzkum", "proslo"], """
# F2 – víc timeframů (2026-10-27) → 1 setup prošel

`research_f2.py`. 288 setupů (4 rodiny × 15m/1h/4h/1d × filtr vyššího TF × SL × RRR) na 9 trzích, výběr do 2023, holdout 2024+.

**Prošel: [[Průraz F2 (proraz_d1)]]** – průraz 20denního max/min jen ve směru týdenního trendu, SL 2 ATR, RRR 1:2.
Holdout se swapy +0,34 R, t 3,03, PF 1,64, win 48 %, n 185.

Varování: 86 % holdoutu jsou longy v rostoucích trzích ([[Zlato]], [[US indexy]], [[Bitcoin a krypto|BTC]]).
Krátké TF nic nedaly – 1m je u brokera neobchodovatelný (spread ~70 % SL, [[Náklady brokera]]).
Ověření dál: [[F3 Průraz na nových trzích]], [[F4 Vstup na menším timeframu]].
""")

note("Výzkum/F3 Průraz na nových trzích", ["vyzkum", "neproslo"], """
# F3 – průraz na 27 nových trzích (2026-10-27) → neprošlo

Stejný [[Průraz F2 (proraz_d1)|průraz]] na forexu, EU indexech a ropě: −0,11 R se swapy (t −3,55), bez swapů −0,03 R.
→ Živě jen 9 trhů z [[F2 Více timeframů|F2]]. Edge může být jen silný trend zlata, US indexů a BTC 2024–26 ([[Trend following]]).
""")

note("Výzkum/F4 Vstup na menším timeframu", ["vyzkum", "neproslo"], """
# F4 – denní signál, vstup na menším TF (2026-10-28) → neprošlo

Po průrazu z [[F2 Více timeframů|F2]] čekat na retest nebo pullback k EMA20 na 1h/15m.
Užší SL = víc vyražení šumem, win 27–32 %. Vstup hned zůstává nejlepší.
V letech 2009–2023 byl i vstup hned ~0 R → výsledek [[Průraz F2 (proraz_d1)|F2]] stojí hlavně na 2024–26.
""")

note("Výzkum/F5 SMC a volume profile na 1h", ["vyzkum", "neproslo"], """
# F5 – S/R, SMC a volume profile na 1h (2026-10-28) → nic neprošlo

`research_f5.py`, 39 trhů, 1h svíčky MT5 s tick volume.
Strategie: S/R breakout + retest, fakeout PDH/PDL ([[SFP – sweep likvidity]]), BOS+[[FVG]]+[[Order block]],
[[Supply a demand zóny|S/D 4h]] + HVN, VAL/VAH → POC ([[Volume profile]]), [[Daily Open a Power of 3|denní open + Asie]].

**I bez nákladů ~0 R** (win ~33 % při TP 2R = náhoda). Náklady z toho dělají −0,1 až −0,3 R.
Navazuje: [[F7 Dokument 6 strategií SMC]] (stejné koncepty, přesnější pravidla, M1).
""")

note("Výzkum/F6 Denní strategie", ["vyzkum", "kandidat"], """
# F6 – denní strategie s doloženou výhodou (2026-10-28)

`F6_PLAN.md`, `research_f6.py`, `research_f6b.py`. Yahoo denní data od 1970–2014, 3 období (do 2018 / 2019–23 / 2024+).
Rodiny: [[Mean reversion]] (RSI2, IBS, double seven), [[Trend following]] (Donchian, F2 + trailing), [[Turn-of-month]].

Nic neprošlo formálně, nejlepší kandidát: **[[RSI(2) pullback (mr_rsi2_d1)]]** na [[US indexy|US indexech]] – win ~71 %,
kladný ve všech obdobích. Přidán do [[Simulátor|simulátoru]] jako neověřený.
Portfolio průraz + RSI2 při 0,25 %: 2019+ +2,6 %/rok, DD 7,3 %; 2024+ +7,2 %/rok, DD 1,7 %.
""")

note("Výzkum/F7 Dokument 6 strategií SMC", ["vyzkum", "neproslo"], """
# F7 – 6 strategií z dokumentu uživatele (2026-10-28) → nic neprošlo

`F7_PLAN.md`, `f7_lib.py`, `research_f7*.py`. Dokument „Trading bot – 6 strategií (SMC + Volume Profile)“:
Sweep & Shift ([[SFP – sweep likvidity]] + [[MSS a displacement]] + [[FVG]]), zpřesněná [[Supply a demand zóny|S/D zóna]] (HVN),
rotace ve VA ([[Volume profile]], [[Režim trhu|balance]]), [[VWAP]] trend pullback, breakout z balance, [[Daily Open a Power of 3]].

Data: krypto M1 z Binance 2022–26 (9 mincí), forex/komodity z MT5 jen M15/M5 ([[Zdroje dat]]).
- Věrná pravidla: **< 1 obchod za rok na trh** (dokument tvrdil 1–5 týdně) – filtry se násobí.
- Uvolněné verze a ablace: ztrátové, horší než [[Náhodné vstupy|náhoda]].
- Koncepty na tisících událostí: SFP −0,03 R, VWAP pullback −0,03 R **i bez nákladů**.
Ověřeno [[Walk-forward|walk-forwardem]], Monte Carlem a kontrolou detekcí v grafu.
""")

note("Výzkum/Co nefunguje", ["vyzkum", "souhrn"], """
# Co nefunguje (souhrn)

| Co | Kde zjištěno | Proč |
|---|---|---|
| Technické indikátory na H1 | [[Historie v1–v6]] | po nákladech 0 z 60 |
| Krátké timeframy (1m–15m) | [[F2 Více timeframů]], [[F7 Dokument 6 strategií SMC]] | spread velká část SL ([[Náklady brokera]]) |
| SMC: [[SFP – sweep likvidity|SFP]], [[FVG]], [[Order block|OB]], [[MSS a displacement|MSS]] | [[F5 SMC a volume profile na 1h]], [[F7 Dokument 6 strategií SMC]] | ~0 R i bez nákladů |
| [[Volume profile]] (VA, POC, HVN) | F5, F7 | žádná výhoda |
| Průraz mimo zlato/US indexy/BTC | [[F3 Průraz na nových trzích]] | −0,11 R |
| Vstup na menším TF po denním signálu | [[F4 Vstup na menším timeframu]] | užší SL = vyražení |
| [[Momentum L=250]] | [[F1 Nové třídy signálů]] | výnos sežere swap brokera |
| [[COT]], limitky, adaptivní přepínání | [[Historie v1–v6]] | náhoda / drift |

Co funguje aspoň částečně: [[Průraz F2 (proraz_d1)]], [[RSI(2) pullback (mr_rsi2_d1)]].
""")

# ------------------------------------------------------------------ strategie
note("Strategie/Průraz F2 (proraz_d1)", ["strategie", "ziva"], """
# Průraz F2 (`proraz_d1`)

- Denní graf: zavření nad 20denním maximem (pod minimem) **jen ve směru týdenního trendu** (EMA týdenních svíček).
- SL 2 ATR, TP 1:2 (RRR), drží ~12–15 dní, ~1 obchod za 5 dní na 9 trzích.
- Holdout 2024–26 se swapy: +0,34 R, t 3,03, win 48 % ([[F2 Více timeframů]]).
- Slabiny: 86 % longy ([[Zlato]], [[US indexy]], [[Bitcoin a krypto|BTC]]), na jiných trzích nefunguje ([[F3 Průraz na nových trzích]]),
  2009–23 ~0 R ([[F4 Vstup na menším timeframu]]).
- V [[Simulátor|simulátoru]] jako `validated`, TS = Python 339/339. Typ: [[Trend following]].
- Doplňuje se s [[RSI(2) pullback (mr_rsi2_d1)]] (opačný profil výher).
""")

note("Strategie/RSI(2) pullback (mr_rsi2_d1)", ["strategie", "kandidat"], """
# RSI(2) pullback (`mr_rsi2_d1`)

- Long, když denní zavření > SMA200 a RSI(2) < 10. Ven při zavření nad SMA5, stop 3 ATR(20), nejdéle 10 dní, **bez TP**.
- Jen [[US indexy]] (SPX500mini, NAS100mini, US30mini).
- Úspěšnost **71–73 %**, průměrná výhra +0,35–0,41 R, ztráta −0,51–0,54 R → skutečné RR ~1:0,65–0,8.
  Plný stop jen v ~12 % obchodů, nejhorší −1,4 R (gap). Průměr +0,11–0,14 R na obchod.
- Z [[F6 Denní strategie]], formálně neprošel (kontrola 2019–23 slabá). V [[Simulátor|simulátoru]] neověřený → obchoduje v [[Učící režim|učícím režimu]].
- Typ: [[Mean reversion]]. Opak profilu [[Průraz F2 (proraz_d1)|průrazu]] (málo velkých výher).
""")

note("Strategie/Momentum L=250", ["strategie", "pripravene"], """
# Momentum L=250

Znaménko výnosu za 250 dní na 40 trzích, rozhodnutí v pracovní dny 15:00 UTC, bez TP.
Hrubá edge existuje (holdout t 3,3), polovina je úrok za držení, zbytek sebere přirážka ve swapu brokera ([[Náklady brokera]], [[Carry]]).
V [[Python bot tv_agent|Python botu]] připravené, **nespuštěné** (uživatel nechce). Z [[F1 Nové třídy signálů]]. Typ: [[Trend following]].
""")

note("Strategie/Time-of-day AUDJPY 23-00", ["strategie", "historie"], """
# Time-of-day AUDJPY 23:00 long

Kalendářní efekty z [[Historie v1–v6]]: směr se na holdoutu potvrdil u 14/14, ale po hodinových spreadech zbývá ~0,26 pipu/obchod.
Pozor na rollover 21–22 UTC (spread skáče na desítky pipů) – největší „edge“ byly artefakty ([[Metodické pasti]], [[Forex]]).
""")

# ------------------------------------------------------------------ koncepty
note("Koncepty/SFP – sweep likvidity", ["koncept", "smc"], """
# SFP – sweep likvidity (swing failure pattern)

Knot za úrovní [[Likvidita|likvidity]] (≥ 0,05 ATR), zavření zpět, hloubka ≤ 0,5 ATR; potvrzení objemem RVOL ≥ 1,5.
Myšlenka: velký hráč vybere stop-lossy a cena se otočí.

Výsledky: fakeout PDH/PDL v [[F5 SMC a volume profile na 1h|F5]] ~0 R; v [[F7 Dokument 6 strategií SMC|F7]] na všech druzích poolů
po nákladech −0,12 až −0,36 R, **bez nákladů −0,03 R (11 895 sweepů)**. Na kryptu sweep častěji pokračuje (breakout).
Navazuje na [[MSS a displacement]], používá [[Killzones a session]].
""")

note("Koncepty/Likvidita", ["koncept", "smc"], """
# Likvidita (pooly)

BSL nad / SSL pod: PWH/PWL (váha 3), PDH/PDL a EQH/EQL (2), high/low Asie a Londýna (1).
Pool je vybraný, jakmile cena obchoduje za úrovní. Slouží jako spouštěč ([[SFP – sweep likvidity]]) i cíl TP.
Asie a Londýn viz [[Killzones a session]]. Testováno v [[F5 SMC a volume profile na 1h]] a [[F7 Dokument 6 strategií SMC]].
""")

note("Koncepty/FVG", ["koncept", "smc"], """
# FVG – fair value gap

Býčí: low[i] > high[i−2], zóna mezi nimi, minimálně 0,25 ATR; CE = střed. Vstupní limit na CE po [[MSS a displacement|MSS]].
V [[F7 Dokument 6 strategií SMC|F7]] typická ztráta: cena se vrátí do FVG a pokračuje na SL. Viz též [[Order block]].
""")

note("Koncepty/MSS a displacement", ["koncept", "smc"], """
# MSS a displacement

MSS = zavření tělem za swingem, ze kterého vyšel poslední pohyb do extrému. Platí jen s displacementem:
1–5 svíček, průrazová má tělo ≥ 1 ATR a ≥ 60 % rozsahu, cesta ≥ 2 ATR, efficiency ratio ≥ 0,6, RVOL > 1, nechá [[FVG]].

V [[F7 Dokument 6 strategií SMC|F7]]: po [[SFP – sweep likvidity|SFP]] přijde MSS jen v ~12 % případů (M1), na M15 v 7 %.
Poučení: MSS hledat už od extrému sweepu, na nižším TF se struktura láme uvnitř svíčky spouštěče.
""")

note("Koncepty/Order block", ["koncept", "smc"], """
# Order block

Poslední opačná svíčka před displacementem, který udělal BOS/MSS a nechal [[FVG]]. Obchoduje se jen první dotek.
[[F5 SMC a volume profile na 1h|F5]]: BOS + FVG + OB −0,19 až −0,23 R, bez nákladů +0,02 R. Viz [[MSS a displacement]].
""")

note("Koncepty/Supply a demand zóny", ["koncept", "smc"], """
# Supply a demand zóny

Báze 1–4 malých svíček, odchod displacementem, cena se vzdálí ≥ 3× výšku báze. Skóre 0–4, obchodovat první dotek.
Zpřesnění přes HVN z [[Volume profile|profilu]] báze. [[F5 SMC a volume profile na 1h|F5]] (4h + HVN) −0,35 R;
[[F7 Dokument 6 strategií SMC|F7]] (S2) jen pár obchodů za 4 roky.
""")

note("Koncepty/Volume profile", ["koncept", "volume"], """
# Volume profile (POC, VAH, VAL, HVN, LVN)

Bin = denní ATR / 40, objem svíčky rovnoměrně přes rozsah; POC = nejvíc objemu, Value Area 70 %,
HVN/LVN z vyhlazeného histogramu. Profily denní, kompozitní 20 dní, fixed range.
Strategie: VAL/VAH → POC ([[F5 SMC a volume profile na 1h|F5]], −0,25 R), rotace ve VA a pravidlo 80 % a breakout přes LVN
([[F7 Dokument 6 strategií SMC|F7]], ztrátové). Na forexu jen tick volume. Souvisí s [[Režim trhu]], [[Supply a demand zóny]].
""")

note("Koncepty/VWAP", ["koncept", "volume"], """
# VWAP

Session VWAP s pásmy ±1σ/±2σ, reset na začátku obchodního dne; sklon za 12 svíček M5 / ATR.
Pullback k VWAP v trendu ([[F7 Dokument 6 strategií SMC|F7]], S4): krypto −0,18 R (n 2 495), bez nákladů −0,03 R.
Na komoditách OOS +0,10 R z 68 obchodů = šum. Souvisí s [[Režim trhu]].
""")

note("Koncepty/Killzones a session", ["koncept", "cas"], """
# Killzones a session (NY čas)

Asie 20:00–00:00, London killzone 02:00–05:00, New York 07:00–10:00 (Praha +6 h, v týdnech změny času +5 h).
Obchodní den forex/komodity 17:00–17:00 NY, krypto 00:00 UTC. Čas serveru brokera = Londýn ([[Broker GlobalDynamicMarkets]]).
Filtr killzone v [[F7 Dokument 6 strategií SMC|F7]] výsledek nezlepšil. Viz [[Daily Open a Power of 3]], [[Likvidita]].
""")

note("Koncepty/Daily Open a Power of 3", ["koncept", "cas"], """
# Daily Open a Power of 3

Asie akumuluje, Londýn/NY udělá falešný pohyb pod Daily Open a vybere low Asie, pak hlavní pohyb ve směru biasu.
[[F5 SMC a volume profile na 1h|F5]] (denní open + asijská likvidita) −0,24 R; [[F7 Dokument 6 strategií SMC|F7]] (S6) pár obchodů ročně, ztrátové.
Používá [[Killzones a session]], [[SFP – sweep likvidity]].
""")

note("Koncepty/Režim trhu", ["koncept"], """
# Režim trhu (balance / trend)

Balance: Value Area posledních 3 dní se překrývají ≥ 50 % a cena je uvnitř 20denní kompozitní VA ([[Volume profile]]).
Trend: H4 BOS za posledních 5 dní a cena mimo kompozitní VA. Na BTC ~13 % času balance, ~40 % trend.
Používá [[VWAP]] pullback (trend) a rotace ve VA (balance) v [[F7 Dokument 6 strategií SMC|F7]].
""")

note("Koncepty/Mean reversion", ["koncept", "styl"], """
# Mean reversion (návrat k průměru)

Vysoká úspěšnost, malé výhry. Funguje jen na [[US indexy|indexech]] a jen long ([[F6 Denní strategie]]).
Nejlepší: [[RSI(2) pullback (mr_rsi2_d1)]]. RSI(2)<5 v [[F1 Nové třídy signálů|F1]] neporazil drift. IBS a double seven neprošly.
""")

note("Koncepty/Trend following", ["koncept", "styl"], """
# Trend following

Nízká úspěšnost, velké výhry. [[Průraz F2 (proraz_d1)]] funguje na [[Zlato|zlatě]], [[US indexy|US indexech]] a [[Bitcoin a krypto|BTC]],
jinde ne ([[F3 Průraz na nových trzích]]). Donchian a trailing v [[F6 Denní strategie|F6]] nekonzistentní, forex ztrátový.
Viz též [[Momentum L=250]].
""")

note("Koncepty/Turn-of-month", ["koncept", "sezonnost"], """
# Turn-of-month (přelom měsíce)

Long indexy kolem přelomu měsíce. [[F1 Nové třídy signálů|F1]] holdout PF 0,76; [[F6 Denní strategie|F6]] slabě kladné všude, formálně neprošlo.
""")

note("Koncepty/Carry", ["koncept"], """
# Carry (kladný swap)

[[F1 Nové třídy signálů|F1]]: PF 0,82. Swap brokera má přirážku a platí se oběma směry ([[Náklady brokera]]), takže úrok za držení skoro mizí.
Viz [[Momentum L=250]].
""")

note("Koncepty/COT", ["koncept", "historie"], """
# COT (pozice velkých hráčů)

[[Historie v1–v6]]: 0 z 30. Překrývající se okna nafukovala t-statistiku 1,81× – „nález“ t 2,71 byl ve skutečnosti 0,93 ([[Metodické pasti]]).
""")

# ------------------------------------------------------------------ metodika
note("Metodika/Plán předem", ["metodika"], """
# Plán stanovený předem

Každý výzkumný skript má v hlavičce pravidla a prahy **před** spuštěním; podle výsledku se nemění.
Chrání před přeučením a „hledáním, dokud něco nevyjde“. Viz [[Výběr, kontrola, holdout]], [[Metodické pasti]].
""")

note("Metodika/Výběr, kontrola, holdout", ["metodika"], """
# Výběr, kontrola, holdout

Data se dělí v čase: výběr (ladění) → kontrola → holdout, který se vyhodnotí jen jednou.
Bonferroni podle počtu testovaných kombinací. Skupiny trhů se hodnotí jako celek.
F6: do 2018 / 2019–23 / 2024+; F7: vývoj do 2025-02, OOS od 2025-03. Doplňuje [[Walk-forward]] a [[Náhodné vstupy]].
""")

note("Metodika/Walk-forward", ["metodika"], """
# Walk-forward

12 měsíců výběr nejlepší varianty, 3 měsíce test, posun o 3 měsíce; testovací úseky se spojí.
Použito v [[Historie v1–v6]] a [[F7 Dokument 6 strategií SMC]]. Viz [[Výběr, kontrola, holdout]].
""")

note("Metodika/Náhodné vstupy", ["metodika"], """
# Náhodné vstupy (kontrolní skupina)

Stejný směr, stejný SL v ATR, stejné TP v R a délka držení, ale náhodný den ve stejnou denní dobu.
Strategie musí náhodu porazit aspoň o 0,1 R. Kontrola simulace: náhoda dává zhruba −náklady (−0,08 až −0,25 R).
V [[F7 Dokument 6 strategií SMC|F7]] byla většina strategií **horší než náhoda**. Adaptivní přepínání v [[Historie v1–v6]] taky.
""")

note("Metodika/Náklady brokera", ["metodika", "naklady"], """
# Náklady brokera

- Spread podle hodiny z [[Broker GlobalDynamicMarkets|brokera]] (`simulator/lib/broker.json`), long platí ask.
- EURUSD živě ~1,9 pipu (přirážka ~0,7 pipu na stranu), zlato ~0,6 $, BTC ~24 $, ETH 2,79 $.
- Swapy jako zlomek ceny za den, přirážka se platí oběma směry ([[Carry]], [[Momentum L=250]]).
- Rollover 21–22 UTC neobchodovatelný. 1m je neobchodovatelný (spread ~70 % SL).
- První chyba projektu: backtest bez spreadu, PF 1,22 → 0,69 ([[Metodické pasti]]).
""")

note("Metodika/Metodické pasti", ["metodika"], """
# Metodické pasti

1. **Chybějící náklady** – PF 1,22 se po spreadu změnil na 0,69 ([[Náklady brokera]]).
2. **Překrývající se okna** – nafouknutá t-statistika ([[COT]]).
3. **Jednostranný test** – limitky vypadaly skvěle, druhá strana dala opak; byl to drift.
4. **Look-ahead** – pivot až po potvrzení, profil dne až po konci dne, RVOL jen z minulosti ([[F7 Dokument 6 strategií SMC|F7]]).
5. **Index datetime64[us]** v picklech – na sekundy přes `as_unit("s").asi8`, jinak obchody končí hned (chyba v [[F4 Vstup na menším timeframu|F4]]).
6. Netržní ceny v rolloveru vypadají jako edge ([[Time-of-day AUDJPY 23-00]]).
""")

note("Metodika/Risk management", ["metodika", "risk"], """
# Risk management

- Riziko 0,25 % na obchod, RRR 1:2 (nastavitelné), denní limit 2 %, DD 8 %, cíl +8 % (prop pravidla).
- V [[Učící režim|učícím režimu]] limity 2 %, 8 % a cíl neplatí.
- Hlídá agent Risk ([[Agenti]]). [[RSI(2) pullback (mr_rsi2_d1)|RSI(2)]] má malé drawdowny → snese vyšší riziko.
- Portfolio [[Průraz F2 (proraz_d1)|průraz]] + RSI2: 2019+ +2,6 %/rok, DD 7,3 % ([[F6 Denní strategie]]).
""")

# ------------------------------------------------------------------ infrastruktura
note("Infrastruktura/Simulátor", ["infrastruktura"], """
# Simulátor (webová aplikace)

Next.js 16 na Vercelu: https://trading-bot123-fawn.vercel.app – nasazuje se pushem na GitHub `Matej02/trading-bot` (main, kořen `simulator`).
Graf jako TradingView, simulovaný broker s podmínkami MT5 ([[Broker GlobalDynamicMarkets]]), data na serveru v Upstash Redis.
Strategie převedené 1:1 z Pythonu (`lib/strategies.ts`, kontrola shody s Pythonem).
Části: [[Agenti]], [[AI analytik]], [[Zprávy a kalendář]], [[Bot 24-7]], [[Učící režim]], [[Stínové obchody a verdikty]], [[Zdroje dat]].
""")

note("Infrastruktura/Agenti", ["infrastruktura", "agenti"], """
# Agenti

| Agent | Hlídá | Váha |
|---|---|---|
| Validátor | čerstvost, utečená cena, duplicita | veto |
| Trh teď | víkend, rollover, spread | veto |
| Kalendář | zprávy 30 min před / 15 po ([[Zprávy a kalendář]]) | veto |
| Risk | limity a velikost ([[Risk management]]) | veto |
| Statistik | jen ověřené setupy (`lib/registry.json`) | radí / veto |
| Ďáblův advokát | důvody proti | radí |
| [[AI analytik]] | Gemini posudek | radí, veto až si ho vyslouží |

Každé rozhodnutí se zpětně vyhodnotí ([[Stínové obchody a verdikty]]). Starší verze v Pythonu: [[Python bot tv_agent]].
""")

note("Infrastruktura/AI analytik", ["infrastruktura", "agenti", "ai"], """
# AI analytik (Gemini)

Posoudí signál s kontextem: trend, RSI, spread vůči SL, příští zprávy, vyhlášená čísla a titulky ([[Zprávy a kalendář]]).
Záložní modely při přetížení (flash-latest → 2.5-flash → lite → 2.0-flash), 8 s na pokus.
Fronta: rozhodnutí hned, posudek AI se dopíše později (5 s mezi dotazy).
**Vysloužené veto**: NE se stane vetem až při ≥ 30 vyhodnocených ANO i NE, NE ztrátové a t ≥ 2 (`lib/aiScore.ts`).
Klíč GEMINI_API_KEY nastavuje uživatel ([[Pravidla spolupráce]]). Součást [[Agenti|agentů]].
""")

note("Infrastruktura/Zprávy a kalendář", ["infrastruktura", "data"], """
# Zprávy a kalendář

- Příští zprávy a veto: ForexFactory (cache 1 h, při častém dotazu 429).
- Vyhlášená čísla (skutečnost vs prognóza): FXStreet API (cache 10 min).
- Titulky: Google News + Yahoo Finance RSS s filtrem relevance.
- Nasdaq kalendář nespolehlivý – nepoužívat.
Používá agent Kalendář a [[AI analytik]]. Viz [[Zdroje dat]].
""")

note("Infrastruktura/Bot 24-7", ["infrastruktura"], """
# Bot 24/7

Server budí cron-job.org každých 5 minut na `/api/tick?key=TICK_SECRET` (klíč nastavuje uživatel).
Řídí vždy jen jedno místo: otevřená stránka má přednost, server převezme řízení do 5 min po zavření (lease, zámek v Redis).
Stav: `/api/tick/status`. Součást [[Simulátor|simulátoru]].
""")

note("Infrastruktura/Učící režim", ["infrastruktura"], """
# Učící režim

Předvolba „brát všechno“: obchodují všechny systémy včetně neověřených, Statistik jen radí.
Denní limit 2 %, DD 8 % a cíl +8 % neplatí ([[Risk management]]); momentum zkouší zablokované pozice denně znovu.
Cíl: nasbírat data, co funguje ([[Cíl projektu]], [[Stínové obchody a verdikty]]).
""")

note("Infrastruktura/Stínové obchody a verdikty", ["infrastruktura"], """
# Stínové obchody a verdikty

Každý signál – i zamítnutý – běží jako stínový obchod a zpětně se vyhodnotí, jestli bylo rozhodnutí dobré.
Tabulka „Co funguje“ strategie × trh v Deníku; export CSV/JSON pro rozbor. Z toho se počítá skóre [[AI analytik|AI]] a hodnotí [[Agenti]].
""")

note("Infrastruktura/Python bot tv_agent", ["infrastruktura"], """
# Python bot `tv_agent`

`run_tv_agent.py` + balíček `tv_agent` (signals, agents, pipeline, shadow_eval, setups.json), MT5 demo účet.
4 kódoví agenti, deník `tv_journal.jsonl`, `--evaluate` porovná přijaté vs zamítnuté.
[[Momentum L=250]] připravené, nespuštěné. Webová obdoba: [[Simulátor]], [[Agenti]]. Napojení: [[MT5 napojení]].
""")

note("Infrastruktura/MT5 napojení", ["infrastruktura", "data"], """
# MT5 napojení

`mt5_connector.py` se připojí k přihlášenému terminálu, heslo nikdy v kódu. Demo účet 937584 @ GlobalDynamicMarkets-Demo.
Terminál dá max 100 000 svíček (M1 ~3 měsíce, M15 ~4 roky) – pro delší M1 nastavit „Max. sloupců v grafu“ na neomezeně.
Historie má díry (EURUSD 10/2025–10/2026). Podmínky brokera: `export_broker_conditions.py` → [[Broker GlobalDynamicMarkets]].
""")

note("Infrastruktura/Zdroje dat", ["infrastruktura", "data"], """
# Zdroje dat

| Zdroj | Na co | Poznámka |
|---|---|---|
| Yahoo Finance | denní historie od 1970, živé svíčky v simulátoru | `range=max` vrací měsíční svíčky – použít period1/period2 |
| Binance | krypto živě, M1 historie (data.binance.vision) | skutečný objem |
| [[MT5 napojení|MT5]] | tick volume, náklady brokera | limit 100 000 svíček, díry |
| ForexFactory / FXStreet | [[Zprávy a kalendář]] | FXStreet historii bez webové hlavičky nevydá |
| Dukascopy | – | automatické stahování odmítá (429), nepoužívat |
""")

# ------------------------------------------------------------------ trhy
note("Trhy/Broker GlobalDynamicMarkets", ["trh", "broker"], """
# Broker GlobalDynamicMarkets (demo)

Čas serveru = Londýn (GMT/BST). Živá cena má k forexu přirážku ~0,7 pipu na stranu, indexy a krypto ne.
`tick_value` u US30mini/NAS100mini nesedí 10× – přepočítávat přes `order_calc_profit`.
Minimální lot 1,0 u některých indexů. Podrobně [[Náklady brokera]], [[MT5 napojení]]. Trhy: [[Forex]], [[Zlato]], [[US indexy]], [[Bitcoin a krypto]].
""")

note("Trhy/Zlato", ["trh"], """
# Zlato (XAUUSD)

Nízký spread vůči pohybu (1,8 % ATR na H1) – klíčový experiment [[Historie v1–v6|v6]]: ani tady technické strategie nefungují.
Silný trend 2024–26 nese [[Průraz F2 (proraz_d1)]]. V [[F7 Dokument 6 strategií SMC|F7]] náznak u [[VWAP]] pullbacku, ale šum.
""")

note("Trhy/Bitcoin a krypto", ["trh"], """
# Bitcoin a krypto

Data z Binance ([[Zdroje dat]]). Spread BTC ~24 $, ETH 2,79 $ – na 1m neobchodovatelné ([[Náklady brokera]]).
BTC patří k trhům, kde funguje [[Průraz F2 (proraz_d1)]]. V [[F7 Dokument 6 strategií SMC|F7]] 9 mincí na M1: žádný SMC koncept nemá výhodu,
[[SFP – sweep likvidity|sweepy]] spíš pokračují.
""")

note("Trhy/US indexy", ["trh"], """
# US indexy (SPX500mini, NAS100mini, US30mini)

Jediné místo, kde funguje [[Mean reversion]]: [[RSI(2) pullback (mr_rsi2_d1)]]. Zároveň trend pro [[Průraz F2 (proraz_d1)]].
Data MT5 až od 2019, minimální lot 1,0 u US30/NAS100 ([[Broker GlobalDynamicMarkets]]).
""")

note("Trhy/Forex", ["trh"], """
# Forex

Nejhorší třída pro tenhle broker: přirážka ke spreadu, swapy oběma směry ([[Náklady brokera]]).
Průraz ([[F3 Průraz na nových trzích]]), trend following ([[F6 Denní strategie]]) i SMC ([[F5 SMC a volume profile na 1h]]) ztrátové.
Rollover 21–22 UTC – viz [[Time-of-day AUDJPY 23-00]].
""")

# ------------------------------------------------------------------ zapis + kontrola odkazu
names = {os.path.basename(p): p for p in N}
bad = []
for p, (tags, body) in N.items():
    for m in re.findall(r"\[\[([^\]|#]+)", body):
        if m not in names:
            bad.append((p, m))
if bad:
    raise SystemExit(f"neplatne odkazy: {bad}")
for p, (tags, body) in N.items():
    fp = os.path.join(ROOT, p + ".md")
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    front = "---\ntags: [" + ", ".join(tags) + "]\naktualizovano: 2026-10-29\n---\n"
    open(fp, "w", encoding="utf-8").write(front + body)
# barvy skupin v grafu (neuronka)
os.makedirs(os.path.join(ROOT, ".obsidian"), exist_ok=True)
cols = [("path:Výzkum", 0xE76F51), ("path:Strategie", 0x2A9D8F), ("path:Koncepty", 0xE9C46A), ("path:Metodika", 0x8AB17D),
        ("path:Infrastruktura", 0x6C8EBF), ("path:Trhy", 0xB07CC6), ("path:Projekt", 0xF4A261), ("tag:#rozcestnik", 0xFFFFFF)]
graph = {"colorGroups": [{"query": q, "color": {"a": 1, "rgb": c}} for q, c in cols], "showTags": False,
         "showArrow": False, "lineSizeMultiplier": 1, "nodeSizeMultiplier": 1.2, "repelStrength": 12, "linkDistance": 180}
json.dump(graph, open(os.path.join(ROOT, ".obsidian", "graph.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
links = sum(len(re.findall(r"\[\[", b)) for _, b in N.values())
print(f"{len(N)} poznamek, {links} odkazu -> {ROOT}")
