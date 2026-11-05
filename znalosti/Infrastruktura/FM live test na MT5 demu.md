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
    - Test by držel do 22:00. Rozdíl dopočítat 6. 11. z M1 historie.
- **2026-11-05 – oprava kalendáře zpráv.**
  - Ruční seznam FOMC/NFP/CPI v `f7_lib.py` končil v říjnu 2026. Od listopadu by proto F12, F13 a F20 potichu přestaly vynechávat zpravodajské dny.
  - První takový den by byl 6. 11. (NFP), kdy F13 podle testu neobchoduje.
  - Doplněno z oficiálních rozpisů bls.gov a federalreserve.gov do 12/2027. Na výsledky testů to nemá vliv, nová data jsou jen v budoucnosti.
  - Runner teď při startu a každých 15 min hlásí POZOR, když kalendáři zbývá méně než 45 dní.
  - Restart runneru v 18:29.
