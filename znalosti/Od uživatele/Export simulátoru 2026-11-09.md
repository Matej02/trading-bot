---
tags: [od-uzivatele, simulator, export]
datum: 2026-11-09
---
# Export simulátoru 2026-11-09 (live bot na Vercelu)

Soubory od uživatele (kopie v `scratch/exporty/2026-11-09`):
- `obchody-2026-11-09.csv` – 388 uzavřených obchodů;
- `denik-2026-11-09.csv` – 699 rozhodnutí agentů;
- `simulator-data-2026-11-09.json` – export z 9. 11. 12:07 Praha.

Předchozí: [[Export simulátoru 2026-11-05]].

## Stav účtu
- Zůstatek **34 897 $** ze 100 000 $. Při exportu 5. 11. to bylo 34 997 $.
- Za 5.–9. 11. přibyl jediný uzavřený obchod: Momentum GAUUSD short, zavřený při otočení trendu, −100 $.
- Ztráta −65 102 $ je pořád z 99 % z 1m ukázek (EMA 9/21 −35 719 $, BB squeeze 1m −28 656 $), vypnutých 5. 11. Ostatní systémy dohromady −728 $.
- **28 otevřených pozic:**
  - 26× Momentum 250 dní;
  - 1× FM průraz H4 (USDCHF short, +1,2 R);
  - 1× Průraz F2 (BTC short 0,01 lotu, otevřeno 9. 11. 1:00).
- Plovoucí výsledek přeceněný cenami MT5 v 12:10: asi **−1 370 $**. Swapy otevřených pozic −835 $, dohromady asi −2 200 $. Equity tedy asi 32 700 $.

## Co z toho plyne
1. **Malý účet blokuje obchody.**
   - Od 5. 11. 16:00 vzal simulátor jen 1 z 34 signálů. Zbytek vetoval Risk.
   - Většina vet je „velikost pod minimem brokera (1 lot)“ u indexových mini CFD. Při 0,25 % z 35 tisíc vychází 0,06–0,45 lotu.
   - Další veta jsou expozice na EUR/GBP/JPY (3 pozice stejným směrem).
   - Při 100 000 $ by velká část signálů prošla. Učící data teď zkresluje ztráta z ukázek, ne vlastnosti systémů.
2. **Momentum nese vzhledem k účtu skoro trojnásobné riziko.**
   - Pozice se otevřely 28. 10. při zůstatku ~93 tisíc. Pojistný SL je 10σ a 0,79 % na trh.
   - Součet rizika u SL je ~17 500 $, tedy 50 % dnešního účtu. Denní výkyv proto odpovídá ~1,3 % účtu místo plánovaných 0,5 %.
3. **Swap na tureckou liru.**
   - USDTRY long: −483 $ za 12 dní, tj. −0,64 R. EURTRY: −216 $.
   - Kurzový zisk +467 $ swap úplně smazal. Potvrzuje verdikt Statistika u Momenta: „hrubě t 3,3, sebere to swap brokera“.
4. **FM systémy F12–F16 v simulátoru zatím bez jediného signálu.**
   - MT5 demo mělo za stejnou dobu 2 signály F13 EURUSD:
     - 5. 11. 16:01, provedeno, +220 $;
     - 9. 11. 8:21, neprovedeno, SL 2,6× spread.
   - Simulátor bere M1 z Yahoo, MT5 z brokera. F13 stojí na sweepu o tick, takže shoda zdrojů je jen ~50 % ([[F13 Veselovský podle PDF a doplňujících pravidel|F13]], [[Souhrn testů F21–F33 a přínosy|souhrn bod 10]]).
   - Porovnání simulátor × demo u FM proto nebude 1:1.
5. **Nové F33 / F31 / F29 v simulátoru běží** (poslední zpracované svíčky 6.–9. 11.). Zatím bez signálu, což sedí s MT5 runnerem:
   - F29 tento týden mimo trh (BTC −10,6 %, ETH −16,2 %);
   - F33 až 25. 11.;
   - F31 8. 12.

## Doporučení (rozhoduje uživatel)
- **Zvážit reset účtu simulátoru na 100 000 $** (Nastavení → tlačítko „Smazat účet, pozice i deník a začít znovu“).
  - Export už je uložený, data se neztratí.
  - Po resetu se velikosti pozic i veta Risku srovnají s plánem a začne čisté srovnání s MT5 demem.
- Momentum je neověřené. Pokud zůstane, TRY páry jsou kvůli swapu kandidát na vyřazení (zatím jen poznámka, ne změna).

## Reset 2026-11-09 kolem 12:15
- **Uživatel účet simulátoru resetoval na 100 000 $ a bota znovu aktivoval.**
  - Smazané jsou pozice, deník i uzavřené obchody. Stará data zůstala jen v exportu výše.
- **Nová etapa simulátoru začíná 9. 11. 2026.**
- **Pozor: reset zapne všechny systémy včetně 1m ukázek.**
  - `freshState()` v `lib/bot.ts` dá do nastavení všechny systémy jako zapnuté a uživatelův výběr nezachová.
  - `ukazka_ema_m1` a `ukazka_m1` je proto po resetu potřeba v Nastavení znovu vypnout. Uživatel je 9. 11. vypnul.
  - **Opraveno 9. 11. (commit `3b3426c`, na pokyn uživatele):** `reset()` teď smaže jen účet, pozice a deník. Nastavení i výběr strategií zůstanou. Bot po resetu stojí, dokud ho uživatel znovu neaktivuje. Strategie, které ve starém nastavení chybí, jsou zapnuté.
  - Ověřeno na lokálním simulátoru: ukázky vypnout → reset → ukázky zůstaly vypnuté i po znovunačtení, účet 100 000 $. Text potvrzení resetu to teď říká.
- Od teď jde simulátor férově srovnávat s MT5 demem (také 100 000 $ start).
