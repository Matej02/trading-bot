# F20 – obecná strategie uživatele (část A Doplňujících pravidel) – plán předem, 2026-11-04

**Zdroje, prošlé celé před testem:**
- Doplňující pravidla, část A1–A8. Tady je Word hlavní zdroj, protože jde o vlastní strategii uživatele.
- Navazující Základy FM, text i všechny obrázky:
  - Volume (7 lekcí, 49 obr.);
  - Likvidita (8 lekcí, 12 obr.);
  - Price Action (13 lekcí, 32 obr.);
  - Supply & Demand (12 lekcí, 136 obr.).
- Pojmové poznámky ve vaultu: SFP, Volume profile, Market structure, S/D zóny.

## Pravidla (s odkazy)
1. **Top-down bias:**
   - Obchod jen ve směru hlavní 4H struktury. Poslední BOS 4H nesmí být starší než 30 dní [A2 tabulka stáří, A8 ranní analýza, A1 „větší TF = větší váha“].
   - Podklad v Základech:
     - PA Struktura trhu s2: „vyšší TF je vždy signifikantnější“;
     - PA Interní vs Externí MS s2: externí určuje trend;
     - S/D day trading teorie s2.
   - Struktura je stroj F12: BOS = zavření tělem za weak levelem s momentem, weak level až po pullbacku 0,382 [A2, PA MS značení s2].
   - Varianta `bias`: `4H` / `4H15` (navíc hlavní 15m struktura stejným směrem, BOS ≤ 5 dní [A2]) / `zadny` (pro vrstvový test).
2. **POI, kde se má SFP stát:**
   - Knot SFP musí sáhnout do aktivní S/D zóny 4H nebo 15m ve směru obchodu [A4, A6 „reakce na zónu“, S/D DT praxe s2–s3 obr 99–110].
   - Zóna je stejná jako v F12:
     - base před impulzem, který udělal BOS [A4 „kvalitní zóna způsobila BOS“];
     - hranice přes těla [A4];
     - stáří 4H 30 dní / 15m 5 dní;
     - po zásahu hlouběji než 25 % platí jen ten dotek [A4, S/D obr 9–10 kanál 0,75].
   - Nebo knot sáhne na POC předchozího dne ±0,1 ATR15 [A8 „1D: POC/nPOC předchozího dne“, Volume POC/nPOC s4, s7].
   - Varianta `poi`: `zona` / `zonapoc` / `zadne`.
3. **Likvidita a SFP na 15m** [A6 „SFP v 15m svíčce“, Likvidita Kde je likvidita s2–s4 („major highs/lows, pivotní body“), PA S/R s3 „fakeout“]:
   - 15m svíčka knotem překoná nevybraný 15m swing (pivot N = 5, nejvýš 2 dny starý) o ≥ 0,05 ATR15.
   - Uzavře zpět za všemi vybranými swingy. Swing je pak vybraný.
4. **FRVP do svíčky SFP** [A6, A7 „row size 250, VA 70 %“, Volume obr 2 nastavení FRVP]:
   - Profil z M1 svíček uvnitř 15m svíčky: 250 řádků přes její rozsah (nejmenší krok 1 tick).
   - Spočítá se POC, VAH a VAL a kolik z nich leží v knotu, na straně sweepu za tělem.
   - Varianta `vp`: `2` (aspoň 2 ze 3) / `3` (3 ze 3, „ideál“) / `0` (bez filtru).
5. **Objem sweepu** [Likvidita s Volume s7 „výběr likvidity s VELKÝM volume“, Likvidita shrnutí s3, obr Likvidita 3–8 („jedná se / nejedná se o výběr LQ“), A7 MA 50]:
   - Objem 15m svíčky SFP > SMA 50 objemu 15m.
   - Varianta `vol`: 1 / 0.
6. **Čas a zprávy:**
   - Svíčka SFP se zavře mezi 9:00 a 20:00 Praha (Londýn 9–17, NY 14–22 [A1]; overlap 14:30–17 [Volume TS profil s5]). Konec v 20:00 je předpoklad, aby obchod měl čas do 22:00.
   - Žádný vstup v den FOMC/NFP/CPI od 2 h před do 1 h po zprávě: NFP/CPI 12:30–15:30, FOMC 18:00–21:00 [A8 „nevstupovat před red news“].
7. **Vstup** (varianta `entry`):
   - `close`: trhem po zavření svíčky SFP [A6 SFP jako entry model].
   - `mss`: první 1m MSS (stroj F12 na 1m, close tělem) ve směru obchodu do 60 min, vstup trhem [A6 „MSS na 5/3/1m“].
   - `poc`: limit na POC svíčky SFP do 60 min [Volume POC s6 „POC klíčová věc na grafu“].
   - Každý vstup se ruší, když cena dřív trefí SL.
8. **SL** za extrém knotu SFP + 0,1 ATR15 [Likvidita: stop-lossy za extrémem]. Riziko musí být ≥ 3× spread, jinak obchod není (pravidlo živého bota). Riziko ≤ 4 ATR15 (původně 2 ATR15; změněno před vyhodnocením, protože vstup po 1m MSS má medián rizika 2,65 ATR15 a strop by ho skoro celý vyřadil – zkušební běh EURUSD, bez pohledu na výsledky).
9. **TP** (varianta `tp`):
   - `2R`;
   - `liq`: nejbližší nevybraný opačný 15m swing za poslední 2 dny, ≥ 1,5 R, strop 6 R [S/D DT praxe s3 „highs jako target“, Likvidita obr 6 „target zpět na POC“];
   - `poc`: nejbližší neotestovaný denní POC za 5 dní ve směru, ≥ 1,5 R, strop 6 R [A4 „POC a HVN spíš magnet / cíl pro TP“, Volume nPOC s7 „magnet“].
10. **Výstup** nejpozději ve 22:00 Praha (day trading). Bez BE a bez částečných výběrů, část A je neuvádí. Jedna pozice na trh, nejvýš 2 obchody denně.

## Předpoklady (co v pravidlech není)
- **Objem:** broker tick volume. Základy doporučují CME futures (Volume správná data s3, Likvidita s Volume s2–s4), ale minutovou historii futures nemáme.
- **Swing pivot N = 5** na 15m („jasně viditelný swing, drobné výkyvy se neznačí“ [A2]). ZigZag ze screenshotů 6E ve vaultu není (Rozpory).
- **Stroj struktury:** kmin = 1,5 ATR (jako F12 live).
- **POC/HVN uvnitř zóny** [A4 „kvalitní zóna obsahuje HVN nebo POC“] se kvůli složitosti nekontroluje. Zóny jsou jen ty, které udělaly BOS.

## Trhy a vyhodnocení
- **Trhy:** EURUSD, GBPUSD, USDJPY, XAUUSD, NAS100, SPX500, DAX (GER30).
  - Forex a zlato mají data od 2017, indexy od 2019.
  - BTC vynechán: M1 data až od 2022-09, takže nemá vývojové období (uživatel ho jinak obchoduje [A4 BTCUSDC, A3 BTC]).
- **Mřížka:** 3 bias × 3 poi × 3 vp × 2 vol × 3 entry × 3 tp = 486 variant.
- **Výběr** jen na vývoji do 2021 (n ≥ 30), OOS 2022–26.
- **Kontroly:**
  - náhoda se stejným trhem, směrem, časem a vzdáleností SL/TP;
  - běh bez nákladů;
  - průměry podle parametrů (vrstvy) a jednotlivé trhy.
- **Výhoda** = vybraná varianta kladná na OOS a lepší než náhoda; filtry `vp`/`vol`/`poi` musí v průměru zlepšovat i na OOS.

## Zjištěno při zkušebním běhu (před vyhodnocením)
- EURUSD: 49 % SFP má SL za knotem blíž než 3× spread brokera (1,9 pipu) → vyřazeno pravidlem živého bota.
- Objem svíčky SFP je nad SMA 50 v 93 % případů → filtr `vol` skoro nic neodfiltruje.
