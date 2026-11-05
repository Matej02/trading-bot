---
tags: [od-uzivatele, simulator, export]
datum: 2026-11-05
---
# Export simulátoru 2026-11-05 (live bot na Vercelu)

Soubory od uživatele (kopie v `scratch/exporty/2026-11-05`):
- `obchody-2026-11-05.csv` – 387 uzavřených obchodů;
- `denik-2026-11-05.csv` – 666 rozhodnutí agentů;
- `simulator-data-2026-11-05.json`.

Předchozí: [[Export simulátoru 2026-11-03]].

## Stav účtu
- Zůstatek **34 997 $** ze 100 000 $. Při exportu 3. 11. to bylo 39 851 $, maximum bylo 100 136 $.
- 28 otevřených pozic: 27 Momentum 250 dní, 1 FM průraz H4.

## Kde vznikla ztráta (−65 002 $ za 387 obchodů od 27. 10.)

| Systém | Obchodů | P&L |
|---|---|---|
| Ukázka – EMA 9/21 na 1m (BTC/ETH) | 217 | −35 719 $ |
| Ukázka – BB squeeze na 1m (BTC/ETH) | 162 | −28 656 $ |
| BB squeeze H1 | 2 | −447 $ |
| Momentum 250 dní | 6 | −181 $ |

- Téměř celá ztráta (99 %) je ze dvou **ukázkových** 1m systémů na kryptu. Ty mají SL uvnitř spreadu, viz [[Export simulátoru 2026-11-03]].
- Po nasazení veta „SL aspoň 3× spread“ (build `5dcc5f0`, 4. 11. 18:33) proběhly jen 2 obchody (−106 $). Dopoledne 4. 11. jich bylo 35.
  - Risk vetoval 23 ukázkových signálů, např. „SL je jen 0,8× spread od vstupu“.

## Nové FM systémy F12–F16
- Simulátor je vyhodnocuje každou minutu (poslední svíčka 5. 11. 12:19), zatím bez signálu.
- Sedí to s MT5 demem: podle živých dat MT5 přišel poslední signál F13 XAUUSD 4. 11. 16:34, ještě před nasazením. Dohromady je to asi 14 signálů za 30 dní.
- Futures NQ=F/ES=F a zlato mají v simulátoru zpoždění asi 9 min (Yahoo), forex ne.

## Doporučení
- Ukázkové 1m systémy v nastavení simulátoru vypnout. Nemají výhodu a zkreslují účet i porovnání s demem.
- Momentum a FM systémy nechat běžet.
- Porovnání s MT5 demem ([[FM live test na MT5 demu]]) až budou obchody na obou stranách.
