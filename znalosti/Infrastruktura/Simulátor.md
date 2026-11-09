---
tags: [infrastruktura]
aktualizovano: 2026-10-29
---
# Simulátor (webová aplikace)

Next.js 16 na Vercelu: https://trading-bot123-fawn.vercel.app – nasazuje se pushem na GitHub `Matej02/trading-bot` (main, kořen `simulator`).
Graf jako TradingView, simulovaný broker s podmínkami MT5 ([[Broker GlobalDynamicMarkets]]), data na serveru v Upstash Redis.
Strategie převedené 1:1 z Pythonu (`lib/strategies.ts`, kontrola shody s Pythonem).
Části: [[Agenti]], [[AI analytik]], [[Zprávy a kalendář]], [[Bot 24-7]], [[Učící režim]], [[Stínové obchody a verdikty]], [[Zdroje dat]].

## Experimenty F13–F16 (2026-11-03/04)
Každý je NEOVĚŘENÝ live experiment. Shoda TS/Python je ve `scripts/compare-f13…f16.ts`.

| Systém | Mentor | TF a trhy | Shoda TS/Python | Výzkum |
|---|---|---|---|---|
| `fm13_ves_m1` | Veselovský | 1m; NAS100fut, SPX500fut, EURUSD, GBPUSD, XAUUSD | 49/49 | [[F13 Veselovský podle PDF a doplňujících pravidel]] |
| `fm14_pat_m15` | Pátek | 15m; NAS100fut, GBPUSD, XAUUSD | 33/34 | [[F14 Pátek podle PDF a doplňujících pravidel]] |
| `fm15_hve_h1` | Hvězda | 1h; 12 trhů s COT | 7/11 při stejné délce historie | [[F15 Hvězda podle PDF, doplňujících pravidel a COT]] |
| `fm16_hak_m15` | Hakimi | 15m; XAUUSD, XAGUSD | 35/35 | [[F16 Hakimi podle PDF a doplňujících pravidel]] |

- Systém může vrátit vlastní TP (cíl daily biasu, protější zóna). Jinak bot počítá TP z RRR.
- **F15 má živě jen ~13 měsíců hodinových dat z Yahoo.** Starší D1 zóny chybí, takže proti testu najde méně signálů. Bez BE.

## Experiment F12 (2026-11-03)
- Systém `fm12_mucka_m1` (`lib/fm12.ts`): Můčka podle PDF a [[Doplňující pravidla k FM PDF|doplňujících pravidel]].
  - Vstup na 1m, 4H a denní svíčky z 1h, zóny a balanční levely z 15m. Bot mu načítá více timeframů (`htf` v definici systému).
  - Trhy EURUSD, GBPUSD, XAUUSD, XAGUSD. NAS100 ne, protože Yahoo dává jen hodiny burzy.
  - Limit na 0,618 je živě vstup trhem na 1m svíčce, která úroveň zasáhne.
  - NEOVĚŘENO, jen live sběr dat. Viz [[F12 Můčka podle doplňujících pravidel]].
- Shoda TS/Python: `scripts/compare-f12.ts` + `scratch/f12_parita.py`.
- Veřejný `/api/tick/status` ukazuje `build` (commit nasazené verze) – kontrola, že se push nasadil.

## Oprava 2026-11-03: stop uvnitř spreadu
- [[Agenti|Risk]] vetuje obchod, když je SL od vstupu blíž než 3× spread, nebo na špatné straně.
- 1m ukázky dávaly na BTC stop 3–7 $ při spreadu ~24 $ a ztrácely −10 až −18 R. Za týden to bylo −56 786 $ z −60 061 $ (281 obchodů).
  Viz [[Export simulátoru 2026-11-03]].

## Experiment F9 (2026-10-29)
Systémy `fm_mss_h4`, `fm_pruraz_h4`, `fm_zona_h4` (`lib/fm.ts`): kombinace FM konceptů, signál na zavření H4, TP 3R, 21 trhů. NEOVĚŘENO, jen live sběr dat. Viz [[F9 Kombinace FM konceptů]].

## Systémy z výzkumu F22–F33 (2026-11-09)
| Systém | Co | Trhy | Registr |
|---|---|---|---|
| `f33_rebal_d1` | [[F33 Rebalancování na konci měsíce|F33]]: SPY vs TLT od začátku měsíce, obchod proti vítězi poslední 3 dny | SPX500mini, NAS100mini | validated |
| `f31_fomc_h1` | [[F31 Drift před FOMC|F31]]: long 14:00 NY den před FOMC → 13:00 NY v den FOMC | SPX500fut, NAS100fut | unvalidated |
| `f29_krypto_mom_d1` | [[F29 Krypto momentum|F29]]: long na týden, když 28denní výnos > 0 | BTCUSD, ETHUSD | unvalidated |
- Nové části kódu:
  - `lib/usCalendar.ts`: svátky NYSE a termíny FOMC, každý rok doplnit;
  - `feeds` v definici systému: pomocné trhy SPY a TLT jsou `feedOnly` v `broker.json`, který by po přegenerování `export_broker_conditions.py` šlo přepsat;
  - výstupy `exitRule: monthEnd / fomcDay`.
