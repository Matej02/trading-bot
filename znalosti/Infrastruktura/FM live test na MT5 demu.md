---
tags: [infrastruktura, mt5, live]
datum: 2026-11-04
---
# Live test FM strategií na MT5 demu (`run_fm_demo.py`)

Zadání uživatele (2026-11-04): „jako poslední task to celé nasadíme a budeme testovat live na našem demu“.

- **Účet:** 937584 @ GlobalDynamicMarkets-Demo. Runner obchoduje **jen když MT5 hlásí účet jako DEMO**, jinak skončí ([[MT5 napojení]]).
- **Strategie:** přímo Python kód testů, stejná logika jako kontrola shody se simulátorem:

  | Strategie | Trhy | Magic |
  |---|---|---|
  | F12 Můčka | EURUSD, GBPUSD, XAUUSD, XAGUSD, NAS100 | 20261112 |
  | F13 Veselovský | NAS100, SPX500, EURUSD, GBPUSD, XAUUSD | 20261113 |
  | F14 Pátek | NAS100, GBPUSD, XAUUSD | 20261114 |
  | F15 Hvězda | 12 trhů s COT | 20261115 |
  | F16 Hakimi | XAUUSD, XAGUSD | 20261116 |
| F20 obecná strategie uživatele | EURUSD, GBPUSD, USDJPY, XAUUSD, NAS100, SPX500, DAX | 20261120 |

- **Data:** M1 75 dní a H1 6 500 svíček z MT5 každou minutu. Čas serveru (Londýn) se převádí na UTC stejně jako v testech.
  - **Shoda živých dat s testovací historií: 19/19 signálů** (F12, F13, F14 na 6 trzích).
  - F20 (přidáno 2026-11-04 18:50): když je na řadě, stahuje se 180 dní M1 (4H struktura se ze 75 dní na SPX500 neustálila). Shoda vybraných signálů 18/18, viz [[F20 Obecná strategie uživatele (SFP + FRVP)|F20]].
- **Pravidla obchodu:**
  - market order se SL a TP podle strategie;
  - riziko 0,25 % zůstatku, SL aspoň 3× spread;
  - jedna pozice na strategii a trh;
  - intradenní obchody zavře ve 22:00 Praha, F15 nejdéle po 10 dnech.
  - **Od 2026-11-05:** uživatel vypíná PC kolem 20:00, proto se intradenní obchody zavírají v **19:45** a nové se otevírají jen do **19:00**. Test počítá s 22:00; obchod, který by běžel po 19:45, se zavře dřív. F15 (swing) beze změny.
- **Deník** `fm_demo_journal.jsonl`, stav `fm_demo_state.json`.
- **Spuštění:** `py run_fm_demo.py --live` (bez `--live` suchý běh, `--once` jeden cyklus).
  - Spouštět v **samostatném okně Windows**: `Start-Process cmd -ArgumentList '/k','title FM demo live && python -u "D:\Trading bot\run_fm_demo.py" --live'`.
  - Terminál desktop aplikace nepoužívat: jeho Ctrl-C přerušuje pomalý start.
  - MT5 se při startu spustí sám (přihlášení uložené v terminálu).
  - Průběh se zapisuje do `fm_demo_log.txt`, každých 15 min řádek „kontrola …“.
  - **Běží jen při zapnutém PC.** 4.→5. 11. uživatel PC vypnul, takže přes noc nic. Znovu spuštěno 2026-11-05 10:35.
- **F17–F19** (Šrajer, Valchář, Kimmel model 2) zatím v runneru nejsou. Nemají kandidátní režim a v testech byly bez výhody.
- **Všechno je NEOVĚŘENÉ.** Účel je sbírat živá data, ne vydělávat. Viz [[Co nefunguje]].

## Spouštění a ochrany (2026-11-05)
- **Spouštěcí soubor** `start_fm_demo.cmd` (dvojklik):
  - počká 60 s na síť;
  - spustí runner `--live`;
  - když spadne, restartuje ho do minuty, nejvýš 30× po sobě.
- **Jen jedna instance:** Windows mutex `fm_demo_runner`. Druhé spuštění se samo ukončí, takže se příkazy nezdvojí.
- **Vyskakovací upozornění** (od 2026-11-05):
  - když je v MT5 vypnuté Algoritmické obchodování (nejvýš 1× za hodinu);
  - po 5 chybách cyklu po sobě;
  - když spouštěcí soubor vzdá restart po 30 pádech.
- **Znovupřipojení:** po uspání PC nebo restartu terminálu se MT5 připojí znovu a znovu se ověří, že je účet DEMO.
- **Automatický start po přihlášení** si nastavuje uživatel sám. Claude Code ho nesmí vytvořit (bezpečnostní pravidlo proti trvalému spouštění):
  - zástupce `start_fm_demo.cmd` ve složce `shell:startup`, nebo naplánovaná úloha.
  - Nastaveno uživatelem 2026-11-05: `FM demo live.lnk` ve složce Po spuštění.
- **Běží jen při zapnutém PC.** 24/7 bez PC by šlo jen na placeném Windows VPS.
- **Vercel simulátor (live bot) MT5 neumí:** Linux, serverové funkce, MT5 nemá web API. F12–F16 tam ale běží simulovaně 24/7. Demo v MT5 dává skutečné plnění brokera (přirážka ke spreadu, skluz).
- **V MT5 musí být zapnuté tlačítko „Algoritmické obchodování“** (zelené). Jinak broker každý příkaz z Pythonu odmítne.
  - 2026-11-05 bylo vypnuté (`terminal_info().trade_allowed = False`). Uživatel ho zapnul v 11:55 a kontrola ve 12:00 proběhla bez varování na 13/13 trzích.
  - Runner to od té doby hlásí při startu, v každé 15min kontrole i v deníku u odmítnutého signálu.
- **Runner v MT5 není vidět jako robot na grafu:** je to externí Python přes API. Obchody se ukážou v záložkách Obchodování a Historie s komentářem názvu strategie a magic číslem.
- **Ukázkové 1m systémy v simulátoru** uživatel vypnul 2026-11-05 (dělaly 99 % ztráty simulátoru).

## Možnost: virtuální PC (VPS) pro běh 24/7 (návrh 2026-11-05)
- **Musí to být Windows:** MT5 i Python balík MetaTrader5 jsou jen pro Windows. Linux přes Wine jde, ale je křehký.
- **Naměřeno 2026-11-05:**
  - runner 250 MB RAM, špička 430 MB;
  - MT5 320 MB RAM, špička 370 MB;
  - CPU v průměru zhruba 15 % jednoho jádra.
  - S Windows tedy **min. 2 GB RAM, lépe 4 GB a 2 vCPU**. Bezplatné virtuály mívají 1 GB, to je málo.
- **MQL5 VPS od MetaQuotes nejde:** spouští jen roboty v MQL5, ne Python. Runner by se musel přepsat.
- **Pozor:** nikdy neběžet zároveň na PC i na VPS se stejným účtem. Mutex chrání jen jeden počítač, dva by mohly zdvojit příkazy. Na PC pak smazat zástupce `FM demo live.lnk`.

## Přesun na server ve stejném stavu (soupis 2026-11-05)
Ověřeno na PC 2026-11-05: co runner skutečně načítá a co z toho je v repu.

**1. Server**
- Windows Server nebo Windows 10/11, **4 GB RAM, 2 vCPU**, disk aspoň 40 GB. Lokalita Evropa.
- Časové pásmo nastavit na Prahu. Runner počítá v `Europe/Prague` sám, ale log a plánování pak sedí s PC.

**2. Kód**
- `git clone` veřejného repa. Všech 14 souborů, které runner načítá, je v gitu (runner, `start_fm_demo.cmd`, `mt5_connector`, `f7_lib`, `research_f8/f10/f12/f12_ms/f13_ves/f14_pat/f15_hve/f15_cot/f16_hak/f20_user`).
- **Cesta je natvrdo `D:\Trading bot`**: `ROOT` v runneru, cesty v `start_fm_demo.cmd` a `COT_FILE` v `research_f15_cot`. Na serveru bez disku D buď:
  - vytvořit stejnou složku na D (nejjednodušší, když server D má);
  - nebo předem přepsat cesty na „složka skriptu“ (malá úprava, na PC se nic nezmění).
- `research_data/` (5 GB) **není potřeba**. Live bere data jen z MT5 a F15 jede bez COT (`cot="0"`).

**3. Python, stejné verze jako na PC**
- Python 3.13.15. Balíky: metatrader5 5.0.6231, numpy 2.5.3, pandas 3.1.0, numba 0.67.0 (llvmlite 0.49.0), scipy 1.18.1, pytz 2026.5, tzdata 2026.5, python-dateutil 3.0.0, six 1.17.0, PyYAML 6.0.3.
- Stejné verze, aby výpočty vyšly bit po bitu stejně jako v testech a kontrolách shody.

**4. MT5**
- Instalace od brokera (GlobalDynamicMarkets), aby byly stejné symboly: NAS100mini, SPX500mini, GER_30mini, CRUDE_OIL.
- Přihlášení na demo 937584 dělá **uživatel sám** a heslo uloží v terminálu.
- Zapnout **Algoritmické obchodování**.
- **Nástroje → Možnosti → Grafy → Max. svíček v grafu = Neomezeně.** Na PC je 100 000 000. Výchozí hodnota 100 000 by F20 dala jen asi 69 dní M1 místo 180. Signály by se pak lišily, viz problém se 75 dny na SPX.
- Po prvním spuštění chvíli počkat, než se stáhne historie M1 (180 dní, 13 trhů). Do té doby runner hlásí „malo dat“.
- MT5 není potřeba dávat do Po spuštění, `mc.connect()` ho spustí sám.

**5. Spouštění po restartu serveru**
- Automatické přihlášení Windows (Sysinternals Autologon). Runner i MT5 potřebují přihlášenou plochu.
- Zástupce `start_fm_demo.cmd` ve složce Po spuštění, stejně jako na PC.
- Vypnout uspávání. Restarty po aktualizacích Windows mimo obchodní dobu (aktivní hodiny).
- Vzdálenou plochu jen **odpojit** (křížek), nikdy „Odhlásit“, jinak se runner i MT5 zavřou.

**6. Stav a deník (přepnutí)**
1. Na PC zavřít okno „FM demo live“ a smazat zástupce `FM demo live.lnk`.
2. Zkopírovat na server `fm_demo_state.json`, `fm_demo_journal.jsonl` a `fm_demo_log.txt`. Nejsou v gitu, takže deník pokračuje.
3. Spustit runner na serveru.

Otevřené pozice jsou u brokera, ne na PC. Runner na serveru je převezme podle magic čísla, včetně zavírání podle času a desetidenního limitu F15.

**7. Po přesunu**
- Vrátit konec dne na 22:00 jako v testech: `INTRADAY_CLOSE_H = 22.0` a zrušit `INTRADAY_LAST_OPEN_H`.

**8. Upozornění**
- Vyskakovací okna (vypnuté Algo, 5 chyb za sebou, kalendář zpráv) se ukážou jen na ploše serveru. Pro 24/7 je potřeba upozornění na telefon (Telegram/ntfy), token si zřídí uživatel.

**9. Kontrola dema na dálku**
- Obchody, pozice a zůstatek jdou číst i z MT5 na PC přihlášeného na stejný demo účet. Demo smí být přihlášené na dvou terminálech, obchodovat smí jen jeden runner.
- Deník a log jsou na serveru. Číst je přes vzdálenou plochu, nebo je posílat jinam.

**10. Aktualizace kódu**
- Na PC upravit a pushnout. Na serveru `git pull` a restart runneru.

## Průběh demo testu
- **2026-11-05 16:01 – první obchod: F13 EURUSD long**
  - 2,0 lotu @ 1,12134, SL 1,12009, TP 1,12728 (RR 4,75), riziko 250 $ = 0,25 %;
  - plnění přesně na referenční ceně, spread 2 pipy, bez komise;
  - v 18:25 na +1,32 R (+330 $);
  - **zavřeno 19:45 časovým výstupem @ 1,12244 → +220 $ = +0,88 R.** TP ani SL nedosáhl.
    - Nejvýš byl 1,12437 v 19:02 (+2,42 R), nejníž 1,12107 v 16:08 (−0,22 R).
    - **Test by držel do 22:00** (spočteno 6. 11. z M1 MT5): TP ani SL by nezasáhl, zavřel by se na 1,12187 = **+0,42 R (+106 $)**. Dřívější zavření v 19:45 tentokrát pomohlo o +0,46 R. Je to jeden obchod, náhoda.
- **2026-11-06 (NFP):** runner běží od 7:10, kontroly bez chyb, do 12:45 žádný signál. F13 dnes podle testu neobchoduje (zpravodajský den).
- **2026-11-09 (kontrola ve 12:05):** runner od 8:04 bez chyb, kontroly 13/13 trhů, 0 otevřených pozic, zůstatek 100 220 $ (celkem +220 $ = +0,22 %, 1 obchod).
  - 8:21 signál F13 EURUSD short **neproveden: SL jen 2,6× spreadu** (pojistka runneru chce aspoň 3×).
  - F29 v 7:52 rozhodla BTC i ETH tento týden mimo trh (28denní výnos −10,6 % a −16,2 %).
- **2026-11-11 – NÁLEZ: F33 a F31 na demu neotevřou ani jeden obchod, F29 jen BTC.**
  - SL 3 ATR20 a riziko 0,25 % (250 $) nestačí na minimální lot brokera. Ztráta u SL při minimálním lotu:
    - SPX500mini (1 lot) 338 $ = 0,34 %;
    - NAS100mini (1 lot) 2 116 $ = 2,1 %;
    - US30mini 2,3 %;
    - NAS100 (min 0,01) 423 $ = 0,42 %;
    - ETHUSD (1 lot) 288 $ = 0,29 %;
    - BTCUSD (0,01) 69 $ = 0,07 %.
  - Runner by vrátil „velikost pod minimem brokera“. Simulátor má stejné SL i riziko, takže skutečné obchody F33 a F31 vetuje Risk a sbírá jen stínová data.
  - Chyba nasazení z 9. 11.
  - **Opraveno 11. 11. 13:20 (souhlas uživatele „ano, zatím testujeme normálně dál“).**
    - `F2X_MINLOT_MAX_RISK_PCT = 0.5`: když se u F33, F31 a F29 0,25 % nevejde do minimálního lotu, vezme se minimální lot, pokud jeho riziko u SL je nejvýš 0,5 %.
    - Výsledek: SPX500mini 1 lot (0,34 %) a ETH 1 lot (0,29 %) se obchodují, BTC dál 0,25 %. **NAS100mini (2,1 %) dál vynechán**, symbol NAS100 (futures, spread 2,25) se nepoužívá kvůli shodě s testem.
    - FM strategie beze změny. Log i deník teď ukazují skutečné riziko obchodu a u odmítnutí i riziko minimálního lotu.
    - Restart: proces runneru ukončen, smyčka `start_fm_demo.cmd` od Windows ho spustila znovu (13:20:31 LIVE NA DEMU).
  - Malý účet (10 000 Kč) se řeší až před live, demo zůstává na 100 000 $.
  - Kontext: dotaz uživatele, kolik by teoreticky vydělal z 10 000 Kč. F33 je jediná ověřená strategie: 2019–2025 průměrně +4,1 R(ATR) za rok, nejhorší rok 2020 −10,3, nejlepší 2022 +15,6.
    - Při 0,25 % na pozici je to asi +0,34 % ročně (+34 Kč), při 1 % asi +1,4 % (+136 Kč), při 2 % asi +2,7 % (+272 Kč).
    - S 10 000 Kč (~457 $) F33 obchodovat nejde: nejmenší pozice SPX500mini riskuje ~74 % účtu.
- **2026-11-11 – proč demo skoro neobchoduje.** `scratch/demo_replay.py` přehrál funkce CAND runneru na datech MT5 (jen čtení).
  - **Za ~12 týdnů (od 8/2026) je 32 signálů, tj. 2–3 týdně.** Rozdělení: F13 23, F12 4, F16 3, F14 1, F20 1, F15 0. Od 27. 10. jen 5.
  - **Runner žádný signál nepropásl.** Všechny 3 signály během běhu dema (5., 9. a 10. 11.) viděl. Mimo 7–19 h padl jen 1 z 32 signálů a o víkendu žádný, takže večerní vypínání PC skoro nic nestojí.
  - **2 ze 3 signálů zastavilo pravidlo SL ≥ 3× spread:**
    - F13 EURUSD 9. 11.: 2,6× živě, 2,4× podle modelu spreadu v testu. Test F13 má stejné pravidlo, takže by ho vynechal také.
    - F12 XAGUSD 10. 11.: 2,7× živě, 2,4× v modelu. **Test F12 toto pravidlo nemá** a obchod by započítal; jen spread by vzal ~0,4 R.
    - Rozdíl mezi testem a live u F12 (kovy) zatím jen evidovat, neměnit.
- **2026-11-05 – oprava kalendáře zpráv.**
  - Ruční seznam FOMC/NFP/CPI v `f7_lib.py` končil v říjnu 2026. Od listopadu by proto F12, F13 a F20 potichu přestaly vynechávat zpravodajské dny.
  - První takový den by byl 6. 11. (NFP), kdy F13 podle testu neobchoduje.
  - Doplněno z oficiálních rozpisů bls.gov a federalreserve.gov do 12/2027. Na výsledky testů to nemá vliv, nová data jsou jen v budoucnosti.
  - Runner teď při startu a každých 15 min hlásí POZOR, když kalendáři zbývá méně než 45 dní.
  - Restart runneru v 18:29.

## Kdy reálné peníze (2026-11-07)
Otázka uživatele: do kdy testovat, než půjdou na MT5 reálné peníze.

**Co demo ukáže a co ne**
- **Ukáže za 6–8 týdnů:**
  - živé signály se shodují s historií;
  - plnění a spread odpovídají modelu nákladů;
  - runner nevynechá signál, když je PC zapnutý.
- **Neukáže zisk.** Nejlepší kandidát je F13 na indexech (NAS100 + SPX500, varianta `liq/ob50/tp2`, OOS 2022–26):
  - n 206, +0,25 R, sd 2,7 R → **t = 1,3**, takže ani v testu to není statisticky průkazné;
  - 90% bootstrap interval −0,06 až +0,56 R;
  - výhra 23 %, frekvence asi 3,6 obchodu za měsíc;
  - na potvrzení +0,25 R by bylo potřeba 330–490 obchodů, tedy **8–11 let** dema.
- **I při skutečné výhodě +0,25 R** (bootstrap z testu):
  - 3 měsíce (asi 11 obchodů) skončí ztrátou ve 44 % případů;
  - rok (asi 43 obchodů) skončí ztrátou ve 29 % případů;
  - max. propad v testu byl 25 R, nejdelší série ztrát 20.

**Minimální účet** (specifikace dema, reálný účet může mít jiné)
- NAS100mini: min. lot 1, 0,10 $ za bod.
- SPX500mini: min. lot 1, 1 $ za bod.
- SL v testu (medián / p90): NAS 27 / 60 bodů, SPX 7 / 13 bodů.
- Pro riziko 0,25 % je potřeba účet asi 3–5 tis. $.
- Propad 25 R znamená při 0,25 % na obchod −6 % účtu, při 1 % −25 % účtu.

**Návrh**
- Demo nechat do konce prosince jako technickou kontrolu a pak ji vyhodnotit.
- Reálné peníze až u strategie s ověřenou výhodou.
- Rozhodnutí i spuštění na reálném účtu je na uživateli. Runner je schválně zamčený jen na demo.

**Výsledek ověření (2026-11-07):** F13 na indexech na delší historii **neprošla**. Na nových letech 2010–2019 −0,11 R, celek t 0,42, viz [[F13 indexy na delší historii (HistData 2010–2025)|F13 na delší historii]]. Kandidát na reálné peníze teď není žádný. Demo běží dál beze změny (přání uživatele).

**Zjištěný posun času v létě (neopraveno, bot se nemá měnit):** `fetch_m1` čte čas serveru jako Londýn, ale server je UTC celý rok. Od konce března do konce října 2027 tak budou svíčky na demu o 1 h posunuté, stejně jako v testech. Viz [[MT5 napojení]].

## Přihlášení MT5 po 7.–9. 11. 2026 – vyřešeno 10. 11.
- **Příznak:** MT5 spuštěný Windows (zástupce Po spuštění) ukázal okno „Otevřít účet“. Přihlásil se jen MT5 spuštěný z Claude.
- **Příčina (zjištěno 10. 11.):** aplikace Claude desktop je balíčková aplikace Windows (MSIX). Všechno, co Claude spustí, zapisuje do `%APPDATA%` jen virtuálně, do `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\MetaQuotes`.
  - Tam skončilo i funkční uložené přihlášení z 8.–9. 11.
  - Skutečná AppData, kterou čte MT5 spuštěný Windows, ho neměla. Tam skončila i „obnova configu z D“, proto nepomohla.
- **Oprava:**
  - funkční `accounts.dat`, `servers.dat` a `common.ini` zkopírovány do `scratch/mt5_config_claude`; složka není v gitu, heslo je v souborech MT5 zašifrované;
  - `start_fm_demo.cmd` je při prvním spuštění Windows přenese do skutečné AppData, původní zazálohuje do `zaloha_puvodni` a vytvoří značku `preneseno.txt`.
- **Ověřeno 10. 11. 6:50:** dvojklik na `start_fm_demo.cmd` → MT5 přihlášený „937584 - GlobalDynamicMarkets-Demo: Demo účet“, runner „LIVE NA DEMU“.
- **Od teď po startu PC nic dělat nemusíš,** všechno spustí zástupce Po spuštění.
- **Pravidlo:** runner ani MT5 nespouštět z Claude. Běžely by zase s virtuální AppData. Když runner neběží, stačí dvojklik na `start_fm_demo.cmd`.

## Nové strategie z výzkumu F22–F33 na MT5 demu (od 2026-11-09 7:52)
Na pokyn uživatele „chci to na bota na MT5 dát“. Kód: `f2x_live.py` (rozhodování, kalendář NYSE, termíny FOMC, Yahoo SPY/TLT) a `cycle_f2x` + `time_exits` v `run_fm_demo.py`.

| Strategie | Magic | Trhy | Vstup | Výstup |
|---|---|---|---|---|
| F33_rebal ([[F33 Rebalancování na konci měsíce|F33]]) | 20261133 | SPX500mini, NAS100mini | 9:30–9:40 NY dne L−2 (15:30 Praha), signál SPY vs TLT do zavření L−3 | 15:55 NY posledního obchodního dne (21:55 Praha) |
| F31_fomc ([[F31 Drift před FOMC|F31]]) | 20261131 | SPX500mini, NAS100mini | 14:00–14:10 NY den před FOMC (**20:00 Praha – jen když běží PC**) | 13:55 NY v den FOMC |
| F29_krypto ([[F29 Krypto momentum|F29]]) | 20261129 | BTCUSD, ETHUSD | v pondělí při první kontrole (v testu 00:00 UTC), když 28denní výnos > 0 | další pondělí při první kontrole |

- SL všude 3 ATR20 (denní z MT5) jako pojistka, TP 10 R (v testech bez stopu a TP). Riziko 0,25 % jako ostatní.
- **Ověření:**
  - kalendář NYSE: poslední obchodní den sedí 287/287 měsíců (L−2 jinak jen 10/2012, uzávěra kvůli hurikánu Sandy);
  - rozhodnutí F33 shodná s testem 285/285 měsíců;
  - F31 vstup 14:01 ano / 13:59 ne, výstup 13:55;
  - F29 výstup v další pondělí.
- **F33 a vypínání PC ve 20:00:** test s výstupem 19:45 Praha 2010–26: +0,25 R místo +0,34 R. **Od 2019 jen +0,09 R místo +0,23 R**, zisk je v posledních hodinách měsíce.
  - Proto výstup 21:55 jako v testu. **V poslední obchodní den signálního měsíce nechat PC do 22:00** (asi 8× ročně).
  - Když PC vypne dřív, pozice drží stop u brokera a runner ji zavře hned po dalším spuštění (mimo test).
- **F31** proběhne jen v den před FOMC, když bude PC zapnutý ve 20:00 (další 8. 12. 2026).
- **První rozhodnutí F29 (9. 11.):** BTC −10,6 %, ETH −16,2 % za 28 dní → mimo trh.
- Simulátor má stejné strategie od 2026-11-09 (build db85757), viz [[Simulátor]].
- **Sledování (2026-11-09):** runner běží na pozadí (spuštěný z Claude), takže okno chybí.
  - Živý log: dvojklik na `D:\Trading bot\sleduj_runner.cmd`. Zavřením toho okna se runner nevypne.
  - Obchody jsou v MT5 v záložkách Obchodování a Historie (komentář = název strategie).
  - Kontrola každých 15 min ukazuje i „hlídá F33 … / F31 … / F29 …“ s nejbližšími termíny.

