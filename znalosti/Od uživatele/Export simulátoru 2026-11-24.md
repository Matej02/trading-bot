---
tags: [export, kontrola, simulator, demo]
datum: 2026-11-24
---
# Export simulátoru 2026-11-24 (týdenní kontrola)

Soubory: `scratch/exporty/2026-11-24` (obchody, deník, data; poslal uživatel 24. 11.). Kontrola podle [[Simulátor#Týdenní kontrola exportu (pravidla předem, 2026-11-11)|pravidel předem]].

## Stav
- Zůstatek 98 427 $ (start 100 000 $, vrchol 100 291 $). Otevřených pozic 25, z toho 19 momentum.
- Od 19. 11. 81 rozhodnutí, uzavřeno 10 obchodů, dohromady −1 216 $:

| Systém | Obchody | Výsledek |
|---|---|---|
| momentum | 6 | −3 412 $ |
| průraz | 2 | +872 $ |
| FM MSS | 1 | +662 $ |
| FM průraz | 1 | +662 $ |

- Žádné zdvojené signály, žádné hromadné otevírání.
- **Páteční oprava funguje:** v sobotu 21. 11. 0:00 prošly páteční denní signály průrazu (XAU, GBPUSD) agentem „Trh teď“ s důvodem „signál z pátečního zavření“. Zamítl je jiný agent (expozice USD).

## Zjištěné chyby (podle pravidel „opravit hned“)
1. **MT5 demo: děravá historie → špatná SMA200 u RSI(2).**
   - V historii MT5 na PC chybí říjen 2025 až leden 2026 a červenec 2026; červen a srpen jsou jen zčásti.
     - Vidět je to v `scratch/live_mt5`: M1 „75 dní“ sahá kvůli dírám až do 8/2025, H1 stejně.
     - Díry jsou už ve výzkumných H1 z 26. 10., tedy ještě před promazáním mezipaměti 7. 11.
   - Runner počítá SMA200 z 200 denních svíček MT5. S dírami sahá dál do minulosti a vychází moc nízko:
     - 18. 11. SPX SMA200 7 172 proti 7 347 podle úplných dat Yahoo;
     - US30 49 538 proti 50 780.
   - **Důsledek:** RSI(2) SPX long 20. 11. (zavření 18. 11. 7 353) a signál US30 (zavření 19. 11.) by podle úplných dat nebyly. Index byl od 17. 11. pod SMA200. Obchod SPX skončil zhruba +98 $, ale podle pravidla vznikl omylem.
   - Ceny CFD a indexu se jinak shodují (medián rozdílu ~0,01 %). Problém jsou jen chybějící dny.
   - Totéž ovlivňuje FM strategie (M1/H1 přes díry) a výzkumná data brokera 2025–2026.
2. **Simulátor: F46 v zimě vynechává signály.**
   - GC=F (Yahoo) nemá v zimě svíčku 22:00 Londýn (denní přestávka CME 17–18 NY).
   - Signál F46 se bere jen na zavření svíčky 22:00. Pondělí 23. 11. proto bez signálu, čtvrtek 19. 11. svíčku měl.
3. **Simulátor: veto na minimální lot u RSI(2) a F46.**
   - RSI(2) SPX 16. 11.: 0,732 lotu < 1 → neberu. F46 19. 11.: 0,009 < 0,01 → neberu.
   - Runner na MT5 v takovém případě vezme nejmenší lot, pokud riziko u stopu ≤ 0,5 %. Simulátor tak obchoduje méně než demo.

## Jen zapsat
- Momentum −3 412 $ za týden (neověřený systém; o vypnutí rozhoduje uživatel).
- RSI(2) v simulátoru po 16. 11. správně bez signálu, protože index byl pod SMA200.
- F61 zatím bez signálu, první v pátek 27. 11.

## Rozhodnutí
- Uživatel (24. 11.): „Bota necháváme.“ Opravy 1–3 se nabízejí, provedou se jen se souhlasem.

## Bod 1 podrobněji (2026-11-24)
- **Díry jsou stejné ve všech 13 trzích runneru** (`scratch/live_mt5`, M1):
  - chybí skoro celý říjen 2025 až polovina 2/2026 a polovina 6. až polovina 8. 2026;
  - EURUSD má navíc díry skoro celý rok 2026.
  - Je to tedy historie celého terminálu, ne chyba jednoho trhu. Vyšší timeframy (H1, D1) staví MT5 z M1, takže chybí i tam.
- **Dopad podle strategií:**
  - **RSI(2):** SMA200 z 200 denních svíček sahá přes díry dál do minulosti a vychází moc nízko (SPX o ~175 bodů, US30 o ~1 240). Runner tak bere i obchody, kdy je index pod skutečnou SMA200. SMA5 a ATR (poslední dny) jsou v pořádku.
  - **F12–F16, F20:** „75 dní“ M1 kvůli dírám sahá až do 8/2025, struktura D1/H4 se počítá přes chybějící měsíce. Jsou to experimenty bez ověřené výhody.
  - **F33, F31, F29:** používají jen ATR z posledních 20 dní, takže bez dopadu.
- **Oprava bez změny bota:** v MT5 doplnit historii.
  - Zobrazit → Symboly (Ctrl+U) → záložka Sloupce/Bars → symbol, M1, rozsah od 1. 1. 2025 → Vyžádat.
  - Postupně SPX500mini, NAS100mini, US30mini, pak ostatní trhy runneru.
  - Ověří se ze souborů v `scratch/live_mt5` po dalším cyklu runneru.
- **Když broker data nemá:** doplnění chybějících dní z Yahoo v runneru (změna bota, jen se souhlasem).


## Druhá kontrola po doplnění historie (24. 11. 9:28)
- H1 (`scratch/live_mt5/research_data`, 9:01): stejné díry u všech trhů (10/2025–půlka 2/2026, půlka 6.–půlka 8. 2026; EURUSD skoro celý rok 2026). SMA200 u RSI(2) je tak pořád moc nízko.
- M1 (9:28): okno ~108 000 svíček je teď od půlky srpna 2026 úplné (medián ~1 350 svíček za den). FM strategie díry už nezasahují.
- Skripty kontroly: `scratch/kontrola_der_mt5.py` (M1), `scratch/kontrola_der_h1.py` (H1).
