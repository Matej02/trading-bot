---
tags: [infrastruktura, data, oprava]
datum: 2026-11-21
---
# Oprava času dat brokera (2026-11-21)

Zadání uživatele: „Udělej všechny 3 kroky.“ (aktualizace Next.js, letní posun času v botovi, hodinová data zlata).

## Co bylo špatně
- **Server brokera má čas UTC celý rok.**
  - Ověřeno na futures GC=F (Yahoo, UTC): korelace hodinových výnosů zlata
    - bez posunu: léto 0,96, zima 0,86–1,00 po měsících;
    - s posunem ±1 h: ~0.
  - Ověřeno i na 15min datech: otevření NY v červenci ve 13:30, v lednu ve 14:30, vždy v surovém čase.
  - Únor 2026 má korelaci jen 0,21; jde o vadná data, ne o posun.
- **Runner (`run_fm_demo.py`) četl čas serveru jako londýnský.** Týkalo se to `fetch_m1` a H1 pro F15 přes `research_f8.load`. V britském letním čase byly svíčky o 1 h dřív než skutečnost. V zimě to vychází stejně.
- **Výzkumné skripty F35, F38, F46, F48, F50/F51, F58, F60, F62 a F64** přičítaly v létě +1 h k **surovým** H1 brokera.
  - Tak se letní hodiny posunuly na UTC+1, tedy o hodinu špatně.
  - Odtud „díra ve 23:00 Londýn v létě“ a hodinový rozdíl proti futures zjištěný v [[F61 a F62 Ověření kandidátů (přelom měsíce v Evropě, zlato v Asii)|F62]]. Ve skutečnosti je to denní přestávka zlata.
- **Správně byla:**
  - M1 z `research_f7_data` (`research_data/f10`) jsou převedená jako Londýn. +1 h v `f2x_lib.load_m1` je u nich proto správná oprava.
  - Denní testy (seskupení podle data UTC) posun neměly.

## Co je opraveno
- **Runner:**
  - `fetch_m1` bere čas serveru přímo jako UTC;
  - `fetch_h1` ukládá skutečný londýnský čas, takže `research_f8.load` z něj udělá skutečné UTC;
  - záloha je `scratch/run_fm_demo_zaloha_2026-11-21.py`;
  - test bez MT5 `scratch/test_cas_runneru.py` prošel: v zimě i v létě M1 = surové UTC a H1 po načtení = surové UTC.
  - **V zimě se chování nemění.** Runner, který běží od 7:10, načte nový kód při příštím spuštění.
- **Výzkumné skripty:** posun se nahradil nulou s poznámkou. Původní výstupy jsou v `souhrn_pred_opravou_casu.txt` ve složkách f38, f46, f48, f50, f58, f60, f61, f63.

## Přepočet testů se správným časem
**Žádný verdikt se nezměnil.**

| Test | Před opravou | Po opravě |
|---|---|---|
| F35 fixing FX, kontrola EURUSD | +0,003 R, t 0,04 | +0,018 R, t 0,22 |
| F38 drift před ECB, kontrola | převis +0,045, t 0,45 | převis +0,036, t 0,36 |
| F48 gotobi, kontrola | převis −0,000 | převis −0,001 |
| F50 krypto pondělí, kontrola | t 1,43 (NE) | t 1,50 (ANO), vývoj ale t 1,05 → bez výhody |
| F58 měny v místních hodinách, broker | převis −0,007 | převis −0,014 |
| F60 drift při otevření Evropy | bez výhody | bez výhody |
| **F46 zlato v Asii, vývoj (broker 2009–18)** | převis t 5,10, n 1 793 | převis t 4,04, n 755 |
| **F46 kontrola (broker 2019–26)** | převis t 2,03 | převis t 2,12 |
| F46 stříbro / nejhorší třetina let | +0,004 / −0,001 | −0,000 / −0,007 → pořád NEPROŠLO |
| F64 hodiny BTC, broker 2022–26 | převis +0,000 | převis −0,005 |
| **F62: broker XAU posledních 2 let, přesné okno F46** | +0,051 R (n 118) | **+0,002 R** (n 226), stejně jako GC=F +0,003 |

## Co z toho plyne pro F46
- Se správným časem má zlato v asijské seanci převis **2009–2026 v datech brokera**, ale **poslední 2 roky na obou zdrojích nulu**.
- Kladný výsledek brokera v F62 způsobil chybný posun.
- F46 zůstává v simulátoru jen jako sledování dopředu s nízkou důvěrou. Simulátor bere čas z Yahoo ve skutečném UTC, takže obchoduje správné okno.
- Na MT5 ne.

## Co se nepřepočítávalo
- Testy FM strategií F8–F20 běžely na M1 a H1 převedených jako Londýn. Mají tedy v létě stejný posun jako dosavadní runner.
- Žádná z nich výhodu neměla, proto se nepřepočítávají.
- Po opravě runneru se ale **v létě budou obchody F12–F16 a F20 na demu lišit od testů o hodinu**. Budou ve skutečném čase, stejně jako simulátor.
