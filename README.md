# Trading bot – v6 (uzavřený výzkum)

> ## Závěr výzkumu k 2026-08-26
>
> Otestováno přes **1 500 kombinací**. Nic neobstálo při poctivém měření.
> Není to výsledek nedostatečného hledání – je to výsledek.
>
> ### Klíčový experiment, který to rozhodl: zlato
>
> Celý projekt narážel na poměr **náklad / velikost pohybu**. U forexu je
> spread ~15 % ATR na H1. U zlata jen **1,8 %** – osmkrát lepší.
>
> Kdyby strategie selhávaly kvůli nákladům, na zlatě by fungovat musely.
> **Nefungují** (2 kandidáti z 24, náhoda dává 3; oba padli na holdoutu).
>
> → Náklady nebyly příčina. Byly jen tím, co dorazilo něco, co už bylo na nule.
> **Ty strategie nemají edge, tečka.**
>
> ### Co všechno padlo (a proč to bylo poctivé měření)
>
> | Přístup | Výsledek | Jak zjištěno |
> |---|---|---|
> | 6 technických strategií × 13 párů × 3 TF | 0 prošlo (náhoda ~4) | walk-forward, skutečné spready |
> | 6 typů výstupů (trailing, breakeven, čas) | žádný nepřekonal pevný SL/TP; breakeven nejhorší | průměr přes 216 kombinací |
> | Adaptivní přepínání strategií | **prohrálo s náhodným losováním** o 16 375 $ | kontrolní skupina |
> | Time-of-day (kalendářní efekty) | −19,3 % ročně | 1 650 obchodů rekonstruovaných z tick dat |
> | COT (pozice velkých hráčů) | 0 z 30 | nepřekrývající se okna + Newey-West |
> | Pasivní plnění (limitky) | **přesně 0,00** | symetrický test obou stran |
> | Zlato a stříbro | 2 z 24 (náhoda 3), oba padli | walk-forward |
>
> ### Tři metodické pasti, do kterých jsem spadl (a vylezl)
>
> 1. **Chybějící náklady** – prvních pár dní backtest nepočítal spread.
>    Profit factor 1,22 se po započtení změnil na 0,69.
> 2. **Překrývající se okna** – u COT nafukovala t-statistiku **1,81×**.
>    „Nález" s t=2,71 se změnil na t=0,93. Tahle chyba je důvod, proč
>    na internetu najdeš spoustu článků „COT funguje".
> 3. **Jednostranný test** – limitky vypadaly na AUDJPY skvěle (+3,17 pipu,
>    t=3,33). Test druhé strany dal −1,42 proti +1,43. Součet 0,004.
>    Byl to celý drift trhu, ne edge.
>
> ### Prop firm evaluace: spočítáno, ne odhadnuto
>
> Monte Carlo s naší nejlepší naměřenou edge: šance projít **45–49 %**.
> Se **žádnou** edge: 43–47 %. Rozdíl 2,5 procentního bodu.
> → Evaluace je z drtivé většiny loterie. Pro spolehlivé projití
> (>80 %) by byla potřeba edge **6–10× větší**, než co lze na veřejných
> cenových datech najít.
>
> ### Co v repu zůstává použitelné
>
> Infrastruktura je funkční a otestovaná: MT5 napojení, risk manager
> hlídající firemní limity, backtest engine se spready/swapy/tick-přesným
> plněním, walk-forward metodika s holdoutem, portfolio runner.
> **Nástroje fungují. Chybí edge, ne nástroje.**
>
> Kdyby ses někdy vracel: každý nový nápad jde tímhle aparátem ověřit
> během hodin, ne měsíců. To je hlavní hodnota, která zbyla.

## F3 – průraz z F2 na 30 trzích, na kterých se nevybíral (2026-10-27) → neprošlo

`research_f3.py` (plán předem v hlavičce), výstup `research_data/f3_verdikt.json`. Setup beze změny
(průraz 20 dní + týdenní trend, SL 2 ATR, RRR 1:2), denní data z MT5, spread brokera + swapy.
Vyřazeny podle nákladů (spread > 10 % SL): USDTRY, EURTRY, XAGUSD; hodnoceno 27 trhů jako skupina.

| | n | úspěšnost | průměr | t | PF |
|---|---|---|---|---|---|
| celá historie se swapy | 3 408 | 34 % | −0,11 R | −3,55 | 0,84 |
| bez swapů | 3 408 | 35 % | −0,03 R | −0,98 | 0,95 |
| 2024+ | 416 | 33 % | −0,21 R | −2,79 | 0,70 |
| kontrola „každý den + trend“ | 7 608 | 35 % | −0,10 R | −5,17 | 0,85 |

**Závěr:** na forexu, evropských indexech a ropě průraz nefunguje → živě zůstává jen 9 trhů z F2.
Zároveň to oslabuje důvěru v samotný F2: výhoda může být jen silný trend zlata, indexů USA a BTC
v letech 2024–26, ne obecná vlastnost průrazu. Bere se jako forward test na demu, ne jako jistota.

## F2 – víc timeframů, cíl vysoká úspěšnost s kladným výsledkem (2026-10-27) → 1 setup prošel

`research_f2.py` (plán předem v hlavičce), `research_f2_detail.py` (swapy, long/short, trhy),
`research_f2_kontrola.py` (kontrolní skupina). 288 setupů (4 rodiny vstupů × 15m/1h/4h/1d × filtr
vyššího timeframu × SL 1/1,5/2 ATR × RRR 1/1,5/2) napříč 9 trhy (BTC, ETH, zlato, EURUSD, GBPUSD,
USDJPY, S&P 500, Nasdaq, DAX), živé spready brokera. Výběr do 2023, holdout 2024+.

**Prošel: průraz 20denního max/min na denním grafu jen ve směru týdenního trendu, SL 2 ATR.**

| | výběr do 2023 (se swapy) | holdout 2024–26 (se swapy) |
|---|---|---|
| RRR 1:2 | +0,09 R, t 1,87 (longy +0,25 R) | **+0,34 R, t 3,03, PF 1,64, win 48 %, n 185** |
| RRR 1:1,5 | +0,06 R, t 1,61 | +0,23 R, t 2,68, PF 1,47, win 51 % |
| kontrola: každý den ve směru trendu, 1:2 | −0,06 R | +0,04 R |

- Vstup na průrazu porazil kontrolu v obou obdobích → není to jen „být long v rostoucím trhu“.
- Ale: holdout je z 86 % longy v silně rostoucích trzích (zlato, indexy, BTC), shorty ve výběru
  prodělávaly (−0,11 R), GBPUSD na holdoutu −0,5 R. Swapy berou ~0,08 R/obchod.
- Frekvence ~0,2 obchodu/den napříč 9 trhy (≈ 1 za 5 dní), drží ~12–15 dní → swing, ne 1–2 obchody denně.
- Krátké timeframy (15m, 1h) nic nedaly; 1m je u tohoto brokera neobchodovatelný (spread ~70 % SL).
- V simulátoru jako `proraz_d1` (signály TS = Python 339/339), v registru `validated`.

## F1 – nové třídy signálů se skutečnými náklady (2026-10-26)

`research_f1.py` (plán stanovený předem v hlavičce), `research_f1_rozklad.py` (rozklad nákladů).
40 trhů (forex, 8 akciových indexů, zlato, ropa, krypto), rozhodnutí 1× denně
v likvidní hodině, výběr do 2022, holdout 2023+, laťka t ≥ 2,25 (4 rodiny), PF ≥ 1,10, n ≥ 100.

| Rodina | Na holdout šlo | Holdout | Výsledek |
|---|---|---|---|
| A trendové momentum (portfolio) | L=250 | PF 0,98, t +0,01 | neprošlo |
| B návrat k průměru, indexy | RSI(2)<5 | PF 1,42, nad driftem t −0,02 | neprošlo |
| C přelom měsíce, indexy | −1 až +4 | PF 0,76, t −1,04 (výběr t +2,15) | neprošlo |
| D carry (kladný swap) | +trend 60 | PF 0,82, t −1,93 | neprošlo |

**Rozklad momenta L=250 na holdoutu** (průzkumný, ne test; průměr na obchod v denních sigmách):
hrubě +2,91 (t 3,3) → po spreadu +2,85 → po férovém swapu (jen úrokový rozdíl) +1,52 (t 1,9)
→ po swapu tohoto brokera −0,03. Polovina hrubého výnosu je úrok za držení (ekonomika, ne
broker), zbytek sebere přirážka brokera ve swapu (platí se oběma směry). I s férovým
swapem pod laťkou. Holdout už je viděný → jediné poctivé ověření je dopředu na nových datech.

**Zjištění o brokerovi (GlobalDynamicMarkets-Demo):**
- Živá cena má k forexu přirážku ~0,7 pipu na stranu (EURUSD 1,9 pipu místo 0,5 v historii);
  historie ticků i svíčky jsou surová cena. Dřívější „symbol_info.spread je nadsazený“ neplatí.
  Indexy a krypto přirážku nemají.
- Historie má díry: EURUSD chybí 2025-10-07 až 2026-10-22 (i D1 a M1, server je nemá),
  další díry 2023 i u indexů. Indexy a ropa začínají až 2019-02-21.
- `tick_value/tick_size` u US30mini a NAS100mini nesedí s `order_calc_profit` (10×) – swapy
  přepočítávat přes `order_calc_profit`. Opraveno i v `mt5_connector.get_pip_value_per_lot`
  (jinak by pozice na těch indexech vyšla 10× větší).

### Momentum v botovi – připravené, NESPUŠTĚNÉ (2026-10-26)

`strategy_momentum.py` (pravidlo) + `tv_agent/momentum.py` (napojení). 40 trhů, rozhodnutí
v pracovní dny v 15:00 UTC (US indexy 19:00), signál ze znaménka výnosu za 250 dní.
Signál se počítá z denních dat **Yahoo Finance** (zdarma), protože historie brokera má díry;
mapování ověřeno proti datům brokera (měsíční korelace 0,95–0,996 u všech 40).
Obchoduje se přes MT5. Bez TP, pojistný SL 10 denních sigma, riziko 0,79 % na trh u SL
(= 1 sigma denně ~80 $ při 100k účtu). Statistik ho vetuje (`setups.json`: unvalidated),
takže i s `--live` zatím nic neotevře – běží jen stínová kniha strategie.

```
python run_tv_agent.py --momentum-check      # co by udělalo dnes – nic nezapíše ani nepošle
python run_tv_agent.py --source momentum     # papírový běh (deník + tv_momentum_book.json)
python run_tv_agent.py --evaluate-momentum   # strategie (stínově) vs. co pustili agenti
```

Ověřeno: pravidlo shodné s `research_f1.py`, logika knih na umělých datech (otevření,
otočení se swapem, opakování po dočasném vetu, konečné veto statistika), kontrolní běh
na živých datech, `order_check` u brokera prošel u 36/40 trhů. US30mini, NAS100mini,
GER_30mini a ESP_35mini mají minimální lot 1,0 = 2–4,5× víc rizika, než je cíl → při
100k účtu je bot neotevře (veto „velikost“), stínová kniha je sleduje dál.

# Historie projektu (starší sekce, čísla v nich jsou překonaná)

> ## ⛔ ZÁSADNÍ KOREKCE (2026-08-21) – ČTI JAKO PRVNÍ
>
> **Všechna čísla o výkonnosti níže v tomhle souboru, která pocházejí z doby
> před 2026-08-21, jsou neplatná.** Backtest do té doby **nepočítal spread**
> (ani swap). Po započtení skutečných nákladů brokera se ukázalo, že žádná
> z testovaných strategií nemá edge:
>
> | Měření portfolia (EURUSD-pullback + EURUSD-bbsqueeze + AUDJPY-bbsqueeze) | Profit factor |
> |---|---|
> | Bez spreadu (původní, chybná čísla) | 1.05 „challenge splněn" |
> | Se skutečným spreadem 2.2 / 3.0 pipu | **0.69** – rozbito o drawdown limit |
> | I s optimistickým spreadem 1.0 / 1.5 pipu | 0.82 – taky rozbito |
>
> **Systematický sken po korekci:** 60 kombinací (6 strategií × 10 párů) na H1
> se skutečnými spready → **prošlo 0**. Čirou náhodou by přitom mělo projít
> ~7,5. Tedy hůř než náhoda.
>
> **Test vyšších timeframů** (H4/D1, 40 kombinací, spread/ATR klesá z ~15 %
> na 2–5 %): výběrovou fází prošly 4 kombinace – náhoda by dala ~5. Na
> holdoutu obstály 2, a to s PF 1.05 a 1.01, spadlé z 1.10–1.53 při výběru.
> To je podpis přeučení, ne edge. A ani ty nepřežijí **swap**
> (AUDJPY −18,2 bodu/noc oba směry; EURUSD −5,95 bodu/noc na long).
>
> **Závěr: po ~100 otestovaných kombinacích nemáme ověřenou edge.**
> Výsledky jsou nerozlišitelné od náhody. Nenasazovat reálné peníze
> ani neplatit za evaluaci u prop firmy na základě čehokoli v tomhle repu.
>
> **Co v repu zůstává hodnotné:** infrastruktura (MT5 napojení, risk manager,
> backtest engine se spready, walk-forward metodika, portfolio runner) je
> funkční a otestovaná. Chybí *strategie*, ne nástroje.
>
> ---
>
> ## Doplněk (2026-08-21, později téhož dne) – dvě další opravy
>
> **1) Spready jsem měřil špatně, byly 3–4× nadhodnocené.**
> Používal jsem `symbol_info.spread` (okamžitý snímek). Skutečné mediány
> z tick dat: EURUSD **0,60** (ne 2,20), GBPUSD **0,80** (ne 2,80),
> AUDJPY **0,90** (ne 3,90). Broker je na náklady výrazně lepší, než jsem tvrdil.
>
> **Přepočet hlavního skenu se správnými spready: 0 z 32 kombinací prošlo**
> (náhoda ~4). Závěr o technických strategiích tedy **platí** – nebyl to
> artefakt přehnaných nákladů.
>
> **2) Rollover okno 21:00–22:00 UTC je neobchodovatelné.**
> Minutová tick data: v 21:00 spread skáče na **19,6 pipu** (AUDJPY),
> **14,9** (GBPUSD), **4,9** (EURUSD), a drží se vysoko celou hodinu.
> Pozor na časování: svíčka s hodinou H se uzavírá v H+1:00, takže
> „efekt hodiny 20" = vstup přesně v 21:00, do té díry. Největší nalezené
> „edge" ležely právě tam → jsou to artefakty netržních cen, ne příležitosti.
>
> ## Jediný validovaný nález: time-of-day efekty
>
> Kalendářní analýza (jiná třída signálu než indikátory) našla 18 stabilních
> efektů s |t| až 9,8. Holdout test (výběr 2016–2022, ověření 2023–2026):
> **směr se potvrdil u 14/14 setupů** (náhoda 7/14, pravděpodobnost 1:16 384).
> Efekty jsou tedy reálné a přetrvávají.
>
> Po započtení skutečných hodinových spreadů + rezervy na skluz ale zbývá málo:
>
> | Setup | Čistý zisk/obchod | Pipů/rok | Holdout t |
> |---|---|---|---|
> | AUDJPY vstup 23:00 long | +0,64 | ~134 | 4,3 |
> | GBPUSD vstup 23:00 long | +0,11 | ~23 | 4,9 |
> | EURUSD vstup 11:00 short | +0,02 | ~5 | 2,0 |
>
> Na holdoutu obstály **3 ze 6** vybraných setupů = přesně náhoda.
> Průměrná edge 0,26 pipu/obchod je **menší než běžný rozptyl skluzu**.
>
> **Stav: jediné, co stojí za další ověření, je AUDJPY 23:00 long.**
> A to ne jako výdělečná strategie, ale jako měření – demo provoz odpoví
> na jedinou otevřenou otázku: jaké jsou skutečné náklady na plnění.
> Pokud reálný náklad překročí ~1,7 pipu, i tenhle setup je nulový.
>
> **Na reálné peníze ani na placenou evaluaci to pořád nestačí.**

# Historická část (čísla níže jsou bez nákladů = neplatná)

## Co to je

Kompletní systém ve třech nezávislých vrstvách:

1. **`risk_manager.py`** – position sizing, max denní ztráta, max drawdown,
   profit target. Běží nezávisle na strategii a je to poslední pojistka,
   která nedovolí botovi porušit pravidla prop firmy.
2. **`strategy.py`** – trend-following pullback na H1 (EMA50/200 filtr trendu,
   pullback k EMA20, ATR-based SL/TP, session filter na London/NY překryv).
   Pravidla jsou vysvětlená v komentářích přímo v souboru.
3. **`backtest_engine.py`** – simuluje bota bar po baru, počítá skutečné
   obchody, equity křivku a statistiky.

Plus napojení na realitu:

4. **`mt5_connector.py`** – připojení k běžícímu MT5 terminálu (Python balíček
   `MetaTrader5`), stažení reálné historie, reálná pip value podle brokera,
   posílání market orderů (s vlastním magic číslem za systém), rekonstrukce
   risk-stavu z historie účtu.
5. **`load_csv_history.py`** – načtení reálných H1 dat z CSV exportu
   (MT5 Historical Data Center nebo jiný data vendor).
6. **`run_backtest_real.py`** – backtest jedné strategie na reálných datech
   (CSV nebo přímo z MT5) – pro rychlé ad-hoc ověření.
7. **`strategy_bbsqueeze.py`** – druhá, nezávisle validovaná strategie
   (Bollinger squeeze breakout) – viz sekce "Portfolio" níže.
8. **`run_live_demo.py`** – live smyčka nad demo účtem, teď jako **portfolio**:
   běží víc nezávislých systémů (pár + strategie) najednou, každý sleduje
   vlastní pozici (podle magic čísla), ale sdílí jeden risk management za
   celý účet. Každou novou H1 svíčku projde všechny systémy, u každého
   vyhodnotí signál a případně pošle (nebo jen zaloguje, viz `--live`)
   market order.

`backtest_engine.py` má i `run_portfolio_backtest()` – backtestuje víc
systémů najednou nad sdíleným risk managerem, přesně jak to běží naostro.
Nutné pro poctivou validaci portfolia (viz níže, proč na tom sešlo).

`generate_sample_data.py` + `run_backtest.py` zůstávají – slouží jen k tomu,
abychom kdykoliv rychle ověřili, že kód **mechanicky funguje** (žádné bugy
v logice), na syntetických datech. Pro cokoliv, co má vypovídací hodnotu,
používej `run_backtest_real.py`.

## Stav k 2026-08-19

- ✅ MT5 terminál nainstalovaný a přihlášený na demo účtu (Global Dynamic
  Markets Limited, server GlobalDynamicMarkets-Demo, účet 937584).
- ✅ Reálná historická data ověřená přímo z terminálu – broker má k
  dispozici přes 10 let H1 historie EUR/USD (od 2016-04-28).
- ✅ Strategie otestována a jedna úprava zavedena na základě reálných dat
  (viz sekce níže) – **out-of-sample profit factor 1.22**, ne jen
  syntetická čísla.
- ✅ Live demo runner hotový, výchozí režim je **dry-run** (nic neposílá,
  jen loguje, co by udělal) – dokud výslovně nespustíš s `--live`.
- ▶️ **Další krok: spustit `run_live_demo.py` (dry-run) a sledovat pár dní,
  než pustíme skutečné demo obchody.**

## Validace na reálných datech – co jsme zjistili a proč

Prvotní backtest na posledních 8000 H1 svíčkách (15 měsíců) vyšel špatně
(profit factor 0.54, zastaveno na max drawdownu). Než jsme cokoliv upravili,
stáhli jsme celou dostupnou historii od brokera (60 000 svíček, 2016–2026)
a rozdělili ji na:

- **trénovací část** (2016-04 až 2023-09, ~7,4 roku) – na týhle jsme
  diagnostikovali problém a zkoušeli úpravy,
- **testovací část** (2023-09 až 2026-08, ~3 roky, 15 000 svíček) – na tuhle
  jsme se **vůbec nedívali**, dokud nebyla finální verze strategie hotová,
  aby výsledek nebyl jen "ušitý na míru" datům, na kterých jsme ladili.

**Diagnóza:** původní strategie měla na trénovacích datech profit factor
jen 0.92 a nejdelší sérii 20 proher za sebou – ztráty přicházely v shlucích
(strategie se opakovaně "prala" se stejným falešným pullbackem místo aby
počkala, až se trh uklidní).

**Co jsme zkusili:**
- Filtr síly trendu (EMA50/200 musí být rozteklé aspoň o 1×ATR) – **zhoršilo
  to výsledek** (0.86), zamítnuto.
- Různé poměry SL/TP (1.0–1.5× ATR SL, 2.5–3.0× ATR TP) – winrate a R:R se
  vzájemně vyrušily skoro přesně, profit factor zůstal ~0.96–1.0 a drawdown
  se **zhoršoval** s těsnějším SL. Jasný signál, že v tomhle vstupním
  pravidle není skrytá žádná "volná" edge, kterou by šlo vydolovat jen
  posunutím SL/TP – zamítnuto, vráceno na původní 1.5/2.5.
- **Cooldown po prohře** (`loss_cooldown_bars=5` v `risk_manager.py`) – po
  ztrátovém obchodu bot 5 hodin nezkouší nový vstup. Tohle jediné pomohlo:
  na trénovacích datech profit factor 0.92 → 0.98, max drawdown -18 %.
  Zavedeno jako nový default v `run_backtest_real.py` i `run_live_demo.py`.

**Výsledek na testovacích (nikdy neviděných) datech s touhle jednou změnou:**

| Metrika | Hodnota |
|---|---|
| Počet obchodů | 130 |
| Winrate | 42.3 % |
| Profit factor | **1.22** |
| Max drawdown | 6.38 % (pod 8% limitem) |
| Výsledek | CHALLENGE SPLNĚN (simulovaně) |

**Buď upřímný k sobě ohledně limitů tohohle výsledku:**
- Je to **jedno** train/test rozdělení, ne více nezávislých oken – 130
  obchodů je slušný vzorek, ale ne důkaz.
- Zisk v testovacím okně není rovnoměrný: rok 2023 (částečný, 35 obchodů)
  byl prakticky na nule (-236 $), skoro všechen zisk je z roku 2024
  (+8619 $, 95 obchodů). Jestli 2024 byl neobvykle příznivý rok pro tenhle
  typ strategie, nebo je to normál, ukáže až demo provoz.
- **Backtest nepočítá spread ani komisi** – reálné demo obchodování bude
  mít o něco horší čísla než tahle tabulka, protože každý obchod platí
  spread při vstupu i výstupu.
- Na trénovacích datech (konkrétně 2016) strategie i s cooldownem pořád
  narazí na max drawdown limit – špatné roky/režimy se budou dít i live,
  risk manager je od toho, aby v takový moment včas zastavil.

Proto další krok není "jedeme live", ale dry-run přes `run_live_demo.py` –
sledovat, jak se to chová v reálném čase se skutečným spreadem, než se
tomu začne věřit naplno.

## Portfolio – proč a jak jsme přidali další strategie/páry

Pullback na EURUSD obchoduje jen ~40×/rok (session filter + přísný vstupní
trigger). Na žádost o vyšší frekvenci jsme prošli otevřený výzkum:

**Zkoušeli jsme 4 archetypy strategií** (pullback, Donchian breakout, RSI
mean-reversion, Bollinger squeeze breakout) přes **walk-forward test** – ne
jedno train/test rozdělení, ale 5 nezávislých ~23měsíčních období za sebou,
na EURUSD:

| Strategie | Pozitivních období (z 5) |
|---|---|
| **bbsqueeze** | **4/5** |
| pullback | 3/5 |
| breakout | 3/5 |
| meanrev | 2/5 |

Bbsqueeze vyšel nejrobustnější. Zároveň to odhalilo, že původní "profit
factor 1.22" u pullback strategie byl citlivější na přesné hranice okna,
než jsme si mysleli – při jiném krájení stejného období vyšlo jen 1.01.
Poučení zapsáno, ne zametnuto pod koberec.

**Otestovali jsme bbsqueeze na 12 párech** stejným walk-forward způsobem.
Prošly jen **EURUSD** (4/5) a **AUDJPY** (4/5, nejkonzistentnější – nikdy
pod PF 0.96). Zbytek (GBPUSD, USDJPY, USDCAD, USDCHF, EURGBP, EURCHF...)
neprokázal spolehlivou edge – nepoužívat je bez další validace.

**Kombinace do portfolia měla nečekaný háček:** když 3 systémy sdílí jeden
účet se stejným rizikem 0.5 %/obchod jako předtím, portfolio narazilo na
max drawdown limit během ~60 obchodů (profit factor 0.67-0.73) – sdílený
rizikový rozpočet se vyčerpal mnohem rychleji, protože systémy mají
korelované špatné fáze. Zkoušeli jsme dát hlavní váhu pullback strategii
("jádro + satelit") – vyšlo to HŮŘ (havarovalo na tréninkových datech),
protože pullback samotný není dost stabilní na větší podíl rizika.
**Rovnoměrné rozdělení rizika mezi systémy vyšlo nejrobustněji.**

**Finální portfolio** (viz `PORTFOLIO` v `run_live_demo.py`), risk 0.17 %
na systém (mírně konzervativnější než namodelovaných 0.2 %, pro rezervu
pod 8% limitem):

| Systém | Pár | Strategie |
|---|---|---|
| EURUSD-pullback | EURUSD | `strategy.py` |
| EURUSD-bbsqueeze | EURUSD | `strategy_bbsqueeze.py` |
| AUDJPY-bbsqueeze | AUDJPY | `strategy_bbsqueeze.py` |

**Výsledek na celé historii 2016–2026** (`run_portfolio_backtest`, risk 0.2 %):

| Metrika | Hodnota |
|---|---|
| Počet obchodů | 1645 (~165/rok, oproti ~40/rok předtím) |
| Winrate | 38.5 % |
| Profit factor | 1.04 |
| Max drawdown | $7218 (90 % z 8% limitu) |
| Roky ziskové/ztrátové | 5 / 9 |
| Nejdelší série proher | 13 |

**Upřímně o limitech:** profit factor 1.04 je skromný, ne ohromující –
ale je to čestné číslo z 1645 obchodů přes 10 let a 2 páry, ne
naoptimalizované na jeden šťastný úsek. Drawdown na 90 % limitu je těsný,
proto risk_pct v produkci (0.17 %) je níž, než co jsme testovali (0.2 %).
Rychlost růstu je pomalejší než dřívější (křehčí) číslo pro samotný
pullback – to je vědomý kompromis: spolehlivost před rychlostí.

## Co udělat teď (v tomhle pořadí)

1. ~~Nainstalovat MT5 terminál a založit demo účet~~ – hotovo (Global
   Dynamic Markets Demo).
2. ~~Stáhnout reálná data, otestovat a rozšířit na portfolio~~ – hotovo,
   viz sekce "Validace" a "Portfolio" výše.
3. **Spustit live smyčku (portfolio, 3 systémy najednou):**
   ```
   python run_live_demo.py
   ```
   (bez `--symbol` – páry a strategie jsou teď dané `PORTFOLIO` seznamem
   v souboru). Bez `--live` jde jen o dry-run log, viz níže.
4. **Až tomu budeš věřit, zapnout skutečné demo obchody:**
   ```
   python run_live_demo.py --live
   ```
   Skript sám odmítne poslat live objednávky na jiný než DEMO účet, pokud
   explicitně nepřidáš `--i-understand-this-is-a-real-account`.
5. **Nechat běžet dost dlouho na statistickou váhu** – s portfoliem cca
   165 obchodů/rok (dřív ~40/rok) – počítej pořád v týdnech,
   ne dnech.
6. **Až tady bude bot konzistentní**, teprve pak dává smysl platit
   za ostrou evaluaci u vybrané firmy.

## Poznámky k `run_live_demo.py`

- Bezpečný default: bez `--live` nic neodešle, jen napíše do konzole a do
  `live_trades_log.csv`, co by udělal.
- `challenge_state.json` se vytvoří automaticky při prvním spuštění
  (zaznamená aktuální balance a čas jako start challenge) – smaž ho, pokud
  chceš odpočet restartovat.
- Risk-management stav (balance, peak, denní ztráta, počet obchodů dnes)
  se při každé iteraci znovu spočítá z historie obchodů na účtu, ne z
  paměti skriptu – takže restart skriptu neztratí přehled o tom, kolik
  už bot dnes obchodoval nebo jak blízko je k limitům.
- Každý systém v `PORTFOLIO` sleduje vlastní pozici podle **magic čísla**
  (unikátní na systém), takže EURUSD-pullback a EURUSD-bbsqueeze mohou mít
  otevřenou pozici současně, aniž by se navzájem blokovaly. Vyžaduje účet
  v **Hedging** režimu (ověřeno funkční na tomhle demo účtu).
- Risk management (balance, denní ztráta, drawdown, cooldown) je **sdílený
  za celý účet** napříč všemi systémy – to je záměr, ne opomenutí, protože
  přesně tak limity hlídá i prop firma. Denní limit obchodů zvýšen ze 4 na
  8 (3 nezávislé systémy).
- Přidání dalšího systému do portfolia: přidat řádek do `PORTFOLIO` v
  `run_live_demo.py` s **novým magic číslem**, a nejdřív ho ověřit přes
  `run_portfolio_backtest()` v kombinaci se zbytkem – samostatný backtest
  nestačí, viz sekce "Portfolio" výše proč.

## Parametry, které jsem zvolil (a proč)

| Parametr | Hodnota | Důvod |
|---|---|---|
| Timeframe | H1 | Dost signálů na rozumné statistiky, ne tak šumové jako M1/M5 |
| Risk/trade | 0.17 % na systém | Sníženo z 0.5 % - 3 systémy na sdíleném účtu by jinak vyčerpaly risk budget mnohem rychleji (viz Portfolio) |
| Max denní ztráta | 4 % | Bezpečná rezerva pod typickým firemním limitem 5 % |
| Max drawdown | 8 % | Bezpečná rezerva pod typickým firemním limitem 10 % |
| SL / TP (obě strategie) | 1.5 ATR / 2.5 ATR | R:R ~1:1.67 – testováno i jinak, tohle vyšlo nejlíp (viz validace) |
| Session filter | 13:00–17:00 UTC | London/NY překryv, nejvyšší likvidita |
| Cooldown po prohře | 5 hodin | Zabraňuje opakovanému vstupu do stejného falešného pullbacku – přidáno po testu na reálných datech |
| Páry | EURUSD, AUDJPY | Jediné, co prošly walk-forward testem (4/5 období) – viz Portfolio |

Všechny tyhle hodnoty jsou startovní bod, ne dogma – další úpravy dělej
stejnou disciplínou jako tuhle: diagnóza na trénovacích datech, ověření
na datech, která jsi při ladění neviděl.
