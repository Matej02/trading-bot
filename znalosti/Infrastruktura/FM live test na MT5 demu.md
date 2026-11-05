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
- **Přesun:**
  - `git clone` repa, Python 3.13 + balíky (pandas, numba, MetaTrader5, matplotlib);
  - MT5 přihlášený na demo, zapnuté Algoritmické obchodování;
  - `start_fm_demo.cmd` + zástupce ve složce Po spuštění;
  - konec dne vrátit na 22:00 jako v testech.
- **Pozor:** nikdy neběžet zároveň na PC i na VPS se stejným účtem. Mutex chrání jen jeden počítač, dva by mohly zdvojit příkazy. Na PC pak smazat zástupce `FM demo live.lnk`.
