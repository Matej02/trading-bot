---
tags: [od-uzivatele, simulator, export, tydenni-kontrola]
datum: 2026-11-19
---
# Export simulátoru 2026-11-19

Soubory (kopie v `scratch/exporty/2026-11-19`): `obchody-2026-11-19.csv`, `denik-2026-11-19.csv`, `simulator-data-2026-11-19.json`. Předchozí: [[Export simulátoru 2026-11-14]].

## Oprava zdvojeného běhu: funguje
- Denní momentum 16., 17. a 18. 11. proběhlo **každý den jen jednou** (16:01 a 20:01).
- V historii nejsou žádné duplicitní id. Fantomové řádky z 10. 11. z exportu zmizely.
- Součet uzavřených obchodů (−1 102,09 $) = změna zůstatku. Historie a zůstatek konečně sedí.

## Stav
- Zůstatek **98 897,91 $** (−1 102,09 $ od resetu 9. 11.), vrchol 100 290,84 $. Účet není zastavený.
- 28 otevřených pozic, swapy otevřených pozic −745 $.
- Od 14. 11. bylo 62 rozhodnutí, z toho 2 vzaté.

## Nové uzavřené obchody (podle pravidel, jen zapsat)
- 17. 11.: momentum GBPUSD long −443,63 $ a NZDJPY long −203,93 $ (otočení trendu).
- 19. 11. 03:00: momentum **USDZAR short, SL −745,36 $**.
  - Momentum má záměrně pojistný SL 10σ s rizikem ~0,79 % na trh (`MOM_RISK_PCT`), ne 0,25 % jako ostatní systémy. Ztráta ~0,75 % tedy odpovídá pravidlu, **není to chyba**.
  - USDZAR stoupl za 10 dní z 16,42 na 17,32 (+5,4 %).

## K výzkumu (beze změny bota)
- **Swapy TRY dál rostou:** USDTRY long −385,94 $, EURTRY long −225,15 $, dohromady asi −70 $/den. Otázka trvá: počítal test momenta se swapy u TRY? (viz [[Export simulátoru 2026-11-14]])
- Momentum je zatím největší zdroj ztráty. Rozhoduje se ale až podle pravidel testu, ne podle 10 dní.

## MT5 demo (log)
- 16.–19. 11. bez signálu a bez obchodu.
- 18. 11. runner běžel až od 18:42, protože PC bylo vypnuté.
